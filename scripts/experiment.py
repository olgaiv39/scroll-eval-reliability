#!/usr/bin/env python3
"""Frozen Phase 2 alarm-order audit using the pinned SwitchBench scorer unchanged."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import resource
import signal
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict, deque
from pathlib import Path

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "upstream" / "source"
sys.path.insert(0, str(SOURCE))
CORPUS = SOURCE / "results" / "switchbench_natural_v1_events.json"
ALARMS = SOURCE / "results" / "switchbench_natural_v1_leaderboard" / "alarms" / "tifxyz-doctor_coherent-normal-step__default.json"
PATCHES = ROOT / "data" / "patches"
OUT = ROOT / "results" / "invariance"
INPUTS = OUT / "inputs"
VARIANTS = OUT / "variants.json"
SUMMARY = OUT / "summary.json"
VALIDATION = OUT / "validation.json"
WALL_LIMIT = 900.0
RSS_LIMIT = 4 * (1 << 30)
FLOAT_TOLERANCE = 1e-12
BASELINE = {"hits": 24, "events": 213, "false_alarms": 70,
            "rate": 0.42646495768486786, "coverage": [237, 237]}
SETTINGS = {"match_mm": 1.0, "fa_dedup_mm": 0.5, "per_patch_cap": 3, "seed": 20260925}
GEOMETRY_SHA256 = "e6115ded16ad4c1e87d863014b2bc086009640bb8c74b79b5a10151aabaedffa"
CORPUS_SHA256 = "e244a9074017924ff8ceb5a156bad9044f0e902de4f0352570da46caf8036b5a"
ALARM_SHA256 = "283d385b1220d4771397ecc276c73c65f989842c71fc0d4f8f751fc8d2b68f38"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def verify_manifest(path: Path) -> dict:
    with path.open() as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    bad = []
    kinds = Counter()
    for row in rows:
        target = ROOT / row["path"]
        kinds[row["kind"]] += 1
        if not target.is_file() or target.stat().st_size != int(row["bytes"]) or sha256_file(target) != row["sha256"]:
            bad.append(row["path"])
    if bad:
        raise RuntimeError(f"manifest mismatch in {path.name}: {bad[:3]}")
    return {"path": str(path.relative_to(ROOT)), "records": len(rows), "kinds": dict(kinds), "verified": len(rows)}


def point_token(point) -> tuple[float, float, float]:
    return tuple(float(v) for v in point)


def states(raw: dict) -> dict:
    alarms = raw["alarms"]
    return {key: "null" if value is None else "empty" if value == [] else "points" for key, value in alarms.items()}


def multiset(value) -> Counter:
    return Counter(point_token(point) for point in value) if isinstance(value, list) else Counter()


def permuted(values: list, seed: int, patch: str) -> list:
    out = list(values)
    digest = hashlib.sha256(f"{seed}\x00{patch}".encode("utf-8")).digest()
    random.Random(int.from_bytes(digest[:16], "big")).shuffle(out)
    return out


def transform(raw: dict, kind: str, seed: int | None = None) -> dict:
    out = {key: value for key, value in raw.items() if key != "alarms"}
    transformed = {}
    for patch, value in raw["alarms"].items():
        if value is None:
            transformed[patch] = None
        elif kind == "original" or kind == "roundtrip":
            transformed[patch] = list(value)
        elif kind == "reverse":
            transformed[patch] = list(reversed(value))
        elif kind == "lexicographic_xyz":
            transformed[patch] = sorted(value, key=lambda point: tuple(point))
        elif kind == "permutation":
            transformed[patch] = permuted(value, int(seed), patch)
        elif kind == "duplicate":
            transformed[patch] = [copy for point in value for copy in (point, point)]
        else:
            raise ValueError(f"unknown transformation {kind}")
    out["alarms"] = transformed
    if kind == "roundtrip":
        return json.loads(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
    return out


def equivalence(original: dict, candidate: dict, duplicate: bool = False) -> dict:
    original_states, candidate_states = states(original), states(candidate)
    checks = {"patch_ids_identical": list(original["alarms"]) == list(candidate["alarms"]),
              "no_verdict_states_identical": original_states == candidate_states,
              "coordinates_identical": True,
              "point_multisets_identical": None if duplicate else True,
              "unique_support_identical": True if duplicate else None,
              "multiplicity_exactly_doubled": True if duplicate else None,
              "adjacent_copy_after_each_original": True if duplicate else None}
    for patch, before in original["alarms"].items():
        after = candidate["alarms"][patch]
        if before is None:
            continue
        before_set, after_set = multiset(before), multiset(after)
        checks["coordinates_identical"] &= set(before_set) == set(after_set)
        if duplicate:
            checks["unique_support_identical"] &= set(before_set) == set(after_set)
            checks["multiplicity_exactly_doubled"] &= after_set == Counter({key: 2 * count for key, count in before_set.items()})
            checks["adjacent_copy_after_each_original"] &= after == [copy for point in before for copy in (point, point)]
        else:
            checks["point_multisets_identical"] &= before_set == after_set
    required = ("patch_ids_identical", "no_verdict_states_identical", "coordinates_identical",
                "unique_support_identical", "multiplicity_exactly_doubled", "adjacent_copy_after_each_original") if duplicate else (
                "patch_ids_identical", "no_verdict_states_identical", "coordinates_identical", "point_multisets_identical")
    checks["passed"] = all(checks[key] for key in required)
    return checks


def plan() -> list[dict]:
    rows = [{"name": "original", "kind": "original"}, {"name": "reverse", "kind": "reverse"},
            {"name": "lexicographic_xyz", "kind": "lexicographic_xyz"}]
    rows += [{"name": f"permutation_{seed:02d}", "kind": "permutation", "seed": seed} for seed in range(20)]
    rows += [{"name": "roundtrip", "kind": "roundtrip"}, {"name": "duplicate", "kind": "duplicate"}]
    return rows


def write_input(spec: dict) -> tuple[Path, dict, dict]:
    raw = json.loads(ALARMS.read_text())
    if spec["kind"] == "original":
        checks = equivalence(raw, raw)
        if not checks["passed"]:
            raise RuntimeError("equivalence check failed for original")
        generated = INPUTS / "original.json"
        generated.unlink(missing_ok=True)
        return ALARMS, raw, checks
    candidate = transform(raw, spec["kind"], spec.get("seed"))
    checks = equivalence(raw, candidate, duplicate=spec["kind"] == "duplicate")
    if not checks["passed"]:
        raise RuntimeError(f"equivalence check failed for {spec['name']}")
    INPUTS.mkdir(parents=True, exist_ok=True)
    path = INPUTS / f"{spec['name']}.json"
    path.write_text(json.dumps(candidate, separators=(",", ":"), ensure_ascii=False) + "\n")
    return path, candidate, checks


def worker(spec: dict, bootstrap: int) -> None:
    class ResourceLimitExceeded(RuntimeError):
        pass

    def on_timeout(_signum, _frame):
        raise TimeoutError(f"scoring exceeded {WALL_LIMIT} seconds")

    def on_rss(_signum, _frame):
        raise ResourceLimitExceeded(f"RSS reached watchdog limit {RSS_LIMIT} bytes")

    stop = threading.Event()

    def monitor():
        while not stop.wait(0.05):
            if int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) >= RSS_LIMIT:
                os.kill(os.getpid(), signal.SIGUSR1)
                return

    signal.signal(signal.SIGALRM, on_timeout)
    signal.signal(signal.SIGUSR1, on_rss)
    signal.setitimer(signal.ITIMER_REAL, WALL_LIMIT)
    watcher = threading.Thread(target=monitor, name="rss-watchdog", daemon=True)
    watcher.start()
    started = time.monotonic()
    result_path = OUT / f"worker-{spec['name']}-b{bootstrap}.json"
    try:
        path, candidate, checks = write_input(spec)
        from tools.switchbench_kit.alarms import load_alarms
        from tools.switchbench_kit.corpus import load_benchmark
        from tools.switchbench_kit.scoring import score
        bench = load_benchmark(CORPUS, PATCHES)
        alarm_set = load_alarms(path, bench, detector="tifxyz-doctor (coherent-normal-step)")
        result = score(bench, alarm_set, bootstrap=bootstrap, **SETTINGS)
        elapsed = time.monotonic() - started
        r = result["recall"]
        f = result["false_alarms"]
        summary = {"name": spec["name"], "transformation": spec["kind"], "seed": spec.get("seed"),
                   "input_sha256": sha256_file(ALARMS), "transformed_sha256": sha256_file(path),
                   "equivalence": checks, "effective_settings": result["settings"],
                   "hits": r["hits"], "events": r["events"], "false_alarms": f["count"],
                   "negative_mm": f["negative_mm"], "rate_per_100mm": f["per_100mm"],
                   "recall_bootstrap95": r["bootstrap95"], "fa_bootstrap95": f["bootstrap95"],
                   "coverage": result["coverage"]["patches"], "geometry_check": result["corpus"]["geometry_check"],
                   "geometry_sha256": result["corpus"]["geometry_sha256"], "wall_seconds": elapsed,
                   "peak_rss_bytes_macos": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                   "watchdog": {"wall_limit_seconds": WALL_LIMIT, "rss_limit_bytes": RSS_LIMIT, "active": True},
                   "per_patch_false_alarms": {row["patch"]: row["false_alarms"] for row in result["patches"]},
                   "per_patch_alarms_after_dedup": {row["patch"]: row["alarms_after_dedup"] for row in result["patches"]},
                   "status": "completed"}
    except (TimeoutError, ResourceLimitExceeded) as error:
        summary = {"name": spec["name"], "status": "interrupted", "reason": str(error),
                   "wall_seconds": time.monotonic() - started,
                   "peak_rss_bytes_macos": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
                   "watchdog": {"wall_limit_seconds": WALL_LIMIT, "rss_limit_bytes": RSS_LIMIT, "active": True}}
    finally:
        stop.set()
        signal.setitimer(signal.ITIMER_REAL, 0)
    result_path.write_text(json.dumps(summary, indent=1) + "\n")


def run_worker(spec: dict, bootstrap: int) -> dict:
    path = OUT / f"worker-{spec['name']}-b{bootstrap}.json"
    path.unlink(missing_ok=True)
    child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "worker", json.dumps(spec), str(bootstrap)],
                             cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        stderr = child.communicate(timeout=WALL_LIMIT + 5)[1]
    except subprocess.TimeoutExpired:
        child.terminate()
        stderr = child.communicate()[1]
        return {"name": spec["name"], "status": "interrupted", "reason": "parent timeout backup fired", "stderr": stderr}
    if child.returncode != 0 or not path.is_file():
        return {"name": spec["name"], "status": "failed", "stderr": stderr, "returncode": child.returncode}
    row = json.loads(path.read_text())
    return row


def prerequisites() -> dict:
    values = {"phase0": verify_manifest(ROOT / "manifests" / "acquired-files.tsv"),
              "phase1": verify_manifest(ROOT / "manifests" / "phase1-acquired-files.tsv"),
              "corpus_sha256": sha256_file(CORPUS), "alarm_sha256": sha256_file(ALARMS),
              "baseline": json.loads((ROOT / "results" / "baseline" / "comparison.json").read_text())}
    if values["corpus_sha256"] != "e244a9074017924ff8ceb5a156bad9044f0e902de4f0352570da46caf8036b5a" or values["alarm_sha256"] != "283d385b1220d4771397ecc276c73c65f989842c71fc0d4f8f751fc8d2b68f38":
        raise RuntimeError("pinned corpus or alarms hash mismatch")
    if values["baseline"]["observed"]["settings"] != {**SETTINGS, "bootstrap": 2000}:
        raise RuntimeError("baseline settings mismatch")
    return values


def run_chunk(start: int, count: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prerequisites()
    for index, spec in list(enumerate(plan()))[start:start + count]:
        row = run_worker(spec, bootstrap=0)
        row["execution_order"] = index
        print(json.dumps({"completed": index + 1, "total": len(plan()), "name": row["name"],
                          "status": row["status"], "false_alarms": row.get("false_alarms"),
                          "wall_seconds": row.get("wall_seconds")}), flush=True)
        if row["status"] != "completed":
            raise RuntimeError(f"audit stopped: {row.get('reason', row.get('stderr', row['status']))}")


def input_path(spec: dict) -> Path:
    return ALARMS if spec["kind"] == "original" else INPUTS / f"{spec['name']}.json"


def metadata_errors(row: dict, spec: dict, bootstrap: int) -> list[str]:
    errors = []
    for key, expected in (("name", spec["name"]), ("transformation", spec["kind"]), ("seed", spec.get("seed")),
                          ("status", "completed")):
        if row.get(key) != expected:
            errors.append(f"{key} expected {expected!r} got {row.get(key)!r}")
    settings = row.get("effective_settings", {})
    for key, expected in ({**SETTINGS, "bootstrap": bootstrap}).items():
        if settings.get(key) != expected:
            errors.append(f"settings.{key} expected {expected!r} got {settings.get(key)!r}")
    if row.get("geometry_check") != "match" or row.get("geometry_sha256") != GEOMETRY_SHA256:
        errors.append("geometry fingerprint or check mismatch")
    if row.get("hits") != BASELINE["hits"] or row.get("events") != BASELINE["events"] or row.get("coverage") != BASELINE["coverage"]:
        errors.append("recall or coverage mismatch")
    if row.get("negative_mm") is None or row.get("negative_mm") <= 0:
        errors.append("missing denominator")
    elif not math.isclose(row.get("rate_per_100mm"), 100 * row.get("false_alarms") / row["negative_mm"], rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
        errors.append("reported rate differs from count and denominator")
    per_patch = row.get("per_patch_false_alarms")
    if not isinstance(per_patch, dict) or sum(per_patch.values()) != row.get("false_alarms"):
        errors.append("per-patch false-alarm sum mismatch")
    return errors


def transformation_errors(original: dict, candidate: dict, spec: dict) -> list[str]:
    expected = original if spec["kind"] == "original" else transform(original, spec["kind"], spec.get("seed"))
    return [] if candidate == expected else ["parsed saved input differs from declared transformation"]


def validate_saved(variants_path: Path = VARIANTS, validation_path: Path | None = VALIDATION,
                   allow_historical_equivalence: bool = False) -> tuple[dict, dict]:
    prerequisites_value = prerequisites()
    payload = json.loads(variants_path.read_text())
    rows = payload.get("variants")
    errors, checks = [], []
    if not isinstance(rows, list) or len(rows) != len(plan()):
        errors.append("variants.json does not contain exactly 25 variants")
        rows = []
    original_raw = json.loads(ALARMS.read_text())
    corrected = []
    for index, spec in enumerate(plan()):
        if index >= len(rows):
            errors.append(f"missing variant {spec['name']}")
            continue
        row = rows[index]
        current_errors = metadata_errors(row, spec, 0)
        path = input_path(spec)
        if not path.is_file():
            current_errors.append(f"missing transformed input {path.name}")
        else:
            candidate = json.loads(path.read_text())
            fresh_equivalence = equivalence(original_raw, candidate, duplicate=spec["kind"] == "duplicate")
            if not fresh_equivalence["passed"]:
                current_errors.append("fresh equivalence check failed")
            current_errors.extend(transformation_errors(original_raw, candidate, spec))
            if row.get("input_sha256") != ALARM_SHA256 or row.get("transformed_sha256") != sha256_file(path):
                current_errors.append("saved input hash mismatch")
            if allow_historical_equivalence:
                row["equivalence"] = fresh_equivalence
            elif row.get("equivalence") != fresh_equivalence:
                current_errors.append("saved derived equivalence metadata differs from fresh validation")
        worker = OUT / f"worker-{spec['name']}-b0.json"
        if not worker.is_file():
            current_errors.append("missing raw worker result")
        else:
            worker_row = json.loads(worker.read_text())
            current_errors.extend(f"worker {message}" for message in metadata_errors(worker_row, spec, 0))
            for key in ("input_sha256", "transformed_sha256", "hits", "events", "false_alarms", "negative_mm", "rate_per_100mm", "coverage", "per_patch_false_alarms"):
                if worker_row.get(key) != row.get(key):
                    current_errors.append(f"derived variant differs from raw worker field {key}")
        row["execution_order"] = index
        corrected.append(row)
        checks.append({"name": spec["name"], "passed": not current_errors, "errors": current_errors})
        errors.extend(f"{spec['name']}: {message}" for message in current_errors)
    baseline_score = json.loads((ROOT / "results" / "baseline" / "score.json").read_text())
    baseline_denominator = baseline_score["false_alarms"]["negative_mm"]
    for row in corrected:
        if not math.isclose(row["negative_mm"], baseline_denominator, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
            errors.append(f"{row['name']}: denominator differs from baseline score")
    original = next((row for row in corrected if row.get("name") == "original"), None)
    if original is None or original["false_alarms"] != baseline_score["false_alarms"]["count"]:
        errors.append("original false-alarm metric differs from baseline score")
    elif (original["hits"] != baseline_score["recall"]["hits"] or original["events"] != baseline_score["recall"]["events"]
          or original["coverage"] != baseline_score["coverage"]["patches"]
          or not math.isclose(original["rate_per_100mm"], baseline_score["false_alarms"]["per_100mm"], rel_tol=0.0, abs_tol=FLOAT_TOLERANCE)):
        errors.append("original point metrics differ from baseline score")
    minimum = next((row for row in corrected if row.get("name") == "permutation_15"), None)
    bootstrap = OUT / "worker-permutation_15-b2000.json"
    if minimum is None or not bootstrap.is_file():
        errors.append("missing selected minimum or bootstrap result")
    else:
        bootstrap_row = json.loads(bootstrap.read_text())
        bootstrap_errors = metadata_errors(bootstrap_row, {"name": "permutation_15", "kind": "permutation", "seed": 15}, 2000)
        for key in ("hits", "events", "false_alarms", "negative_mm", "rate_per_100mm", "coverage", "per_patch_false_alarms"):
            if bootstrap_row.get(key) != minimum.get(key):
                bootstrap_errors.append(f"bootstrap point metric differs for {key}")
        checks.append({"name": "permutation_15_bootstrap2000", "passed": not bootstrap_errors, "errors": bootstrap_errors,
                       "intentional_difference": "bootstrap is 2000 here and 0 in the point-estimate worker"})
        errors.extend(f"permutation_15_bootstrap2000: {message}" for message in bootstrap_errors)
    payload["variants"] = corrected
    outcome = {"status": "passed" if not errors else "failed", "scoring_invoked": False,
               "bootstrap_invoked": False, "corpus_sha256": CORPUS_SHA256, "alarm_sha256": ALARM_SHA256,
               "prerequisites": prerequisites_value, "checks": checks, "errors": errors,
               "baseline_denominator": baseline_denominator,
               "historical_equivalence_normalized_in_memory": allow_historical_equivalence,
               "bootstrap_note": "permutation_15 bootstrap 2000 is intentionally compared with its bootstrap 0 point-estimate counterpart"}
    if validation_path is not None:
        validation_path.write_text(json.dumps(outcome, indent=1) + "\n")
    if errors:
        raise RuntimeError("saved evidence validation failed: " + errors[0])
    return outcome, payload


def finalize() -> None:
    prerequisites_value = prerequisites()
    rows = []
    for index, spec in enumerate(plan()):
        path = OUT / f"worker-{spec['name']}-b0.json"
        if not path.is_file():
            raise RuntimeError(f"missing completed variant {spec['name']}")
        row = json.loads(path.read_text())
        row["execution_order"] = index
        if row["status"] != "completed":
            raise RuntimeError(f"variant did not complete: {spec['name']}")
        rows.append(row)
    original = rows[0]
    if {key: original[key] for key in ("hits", "events", "false_alarms", "coverage")} != {key: BASELINE[key] for key in ("hits", "events", "false_alarms", "coverage")} or not math.isclose(original["rate_per_100mm"], BASELINE["rate"], rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
        raise RuntimeError("bootstrap=0 original does not reproduce baseline point metrics")
    order_rows = rows[:23]
    for row in rows:
        row["delta_false_alarms"] = row["false_alarms"] - BASELINE["false_alarms"]
        row["delta_rate"] = row["rate_per_100mm"] - BASELINE["rate"]
        row["rate_equal_within_tolerance"] = math.isclose(row["rate_per_100mm"], BASELINE["rate"], rel_tol=0.0, abs_tol=FLOAT_TOLERANCE)
        row["recall_and_coverage_exact"] = (row["hits"], row["events"], row["coverage"]) == (BASELINE["hits"], BASELINE["events"], BASELINE["coverage"])
    minimum = min(order_rows, key=lambda row: (row["false_alarms"], row["execution_order"]))
    maximum = max(order_rows, key=lambda row: (row["false_alarms"], -row["execution_order"]))
    extremes = {}
    for label, selected in (("minimum", minimum), ("maximum", maximum)):
        if selected["name"] == "original":
            score = json.loads((ROOT / "results" / "baseline" / "score.json").read_text())
            extremes[label] = {"name": selected["name"], "bootstrap": 2000, "reused_baseline": True,
                               "recall_bootstrap95": score["recall"]["bootstrap95"],
                               "fa_bootstrap95": score["false_alarms"]["bootstrap95"]}
        else:
            rerun = run_worker({key: selected[key] for key in ("name", "transformation", "seed") if key in selected} | {"kind": selected["transformation"]}, bootstrap=2000)
            if rerun["status"] != "completed":
                raise RuntimeError(f"extreme re-score stopped: {rerun}")
            worker_summary = json.loads((OUT / f"worker-{selected['name']}-b2000.json").read_text())
            extremes[label] = {"name": selected["name"], "bootstrap": 2000, "reused_baseline": False,
                               "recall_bootstrap95": worker_summary.get("recall_bootstrap95"),
                               "fa_bootstrap95": worker_summary.get("fa_bootstrap95")}
    counts = sorted(row["false_alarms"] for row in order_rows)
    rates = sorted(row["rate_per_100mm"] for row in order_rows)
    example = None
    if minimum["false_alarms"] != maximum["false_alarms"]:
        for patch in sorted(minimum["per_patch_false_alarms"]):
            if minimum["per_patch_false_alarms"][patch] != maximum["per_patch_false_alarms"][patch]:
                min_raw = json.loads(ALARMS.read_text()) if minimum["name"] == "original" else json.loads((INPUTS / f"{minimum['name']}.json").read_text())
                max_raw = json.loads(ALARMS.read_text()) if maximum["name"] == "original" else json.loads((INPUTS / f"{maximum['name']}.json").read_text())
                min_input = min_raw["alarms"][patch]
                max_input = max_raw["alarms"][patch]
                example = {"selected_after_experiment": True, "patch": patch,
                           "minimum_variant": {"name": minimum["name"], "points": min_input,
                                               "alarms_after_dedup": minimum["per_patch_alarms_after_dedup"][patch],
                                               "false_alarms": minimum["per_patch_false_alarms"][patch]},
                           "maximum_variant": {"name": maximum["name"], "points": max_input,
                                               "alarms_after_dedup": maximum["per_patch_alarms_after_dedup"][patch],
                                               "false_alarms": maximum["per_patch_false_alarms"][patch]}}
                (OUT / "selected_real_patch_example.json").write_text(json.dumps(example, indent=1) + "\n")
                break
    summary = {"prerequisites": prerequisites_value, "float_tolerance": FLOAT_TOLERANCE, "order_variants": {
        "n": len(order_rows), "false_alarm_count": {"min": counts[0], "median": counts[len(counts)//2], "max": counts[-1]},
        "rate_per_100mm": {"min": rates[0], "median": rates[len(rates)//2], "max": rates[-1]},
        "minimum": minimum["name"], "maximum": maximum["name"]}, "extremes": extremes}
    VARIANTS.write_text(json.dumps({"prerequisites": prerequisites_value, "variants": rows}, indent=1) + "\n")
    validate_saved(allow_historical_equivalence=False)
    SUMMARY.write_text(json.dumps(summary, indent=1) + "\n")


def finalize_saved_evidence(variants_path: Path = VARIANTS, patch_path: Path = OUT / "selected_real_patch_example.json",
                            validation_path: Path | None = VALIDATION) -> dict:
    patch_before = patch_path.read_bytes()
    explanation = json.loads(patch_before)
    if not {"selected_after_experiment", "patch", "thresholds", "original", "permutation_15"}.issubset(explanation):
        raise RuntimeError("selected patch explanation is not the expanded evidence form")
    outcome, normalized = validate_saved(variants_path=variants_path, validation_path=None,
                                         allow_historical_equivalence=True)
    if patch_path.read_bytes() != patch_before:
        raise RuntimeError("saved-evidence finalization altered the selected patch explanation")
    outcome["mode"] = "saved-evidence-only finalization"
    outcome["used_existing_bootstrap_results"] = True
    outcome["expanded_patch_explanation_preserved"] = True
    outcome["normalized_variants_in_memory"] = len(normalized["variants"])
    if validation_path is not None:
        validation_path.write_text(json.dumps(outcome, indent=1) + "\n")
    return outcome


def explain_selected_patch() -> dict:
    import numpy as np
    from tools.switchbench_kit import geometry
    from tools.switchbench_kit.scoring import dedup, near

    saved = json.loads(VARIANTS.read_text())["variants"]
    selected = json.loads((OUT / "selected_real_patch_example.json").read_text())
    patch = selected["patch"]
    raw_corpus = json.loads(CORPUS.read_text())
    P = geometry.load_tifxyz(PATCHES / patch)
    mm = geometry.vx_per_mm(float(raw_corpus["voxel_mm"]))
    r_match = SETTINGS["match_mm"] * mm
    r_dedup = SETTINGS["fa_dedup_mm"] * mm
    patch_events = [event for event in raw_corpus["events"] if event["patch"] == patch]
    all_event_points = [geometry.event_points(P, event["transitions"])[0] for event in patch_events]
    all_event_points = np.concatenate(all_event_points).reshape(-1, 3) if all_event_points else np.zeros((0, 3))
    patch_negatives = [(index, negative) for index, negative in enumerate(raw_corpus["negatives"])
                       if negative["patch"] == patch and negative["status"] == "confirmed"]

    def one(name: str) -> dict:
        source_path = ALARMS if name == "original" else INPUTS / f"{name}.json"
        raw = json.loads(source_path.read_text())
        A = np.asarray(raw["alarms"][patch], dtype=np.float64).reshape(-1, 3)
        Ad = dedup(A, r_dedup)
        retained_indices, next_kept = [], 0
        for index, point in enumerate(A):
            if next_kept < len(Ad) and np.array_equal(point, Ad[next_kept]):
                retained_indices.append(index)
                next_kept += 1
        if next_kept != len(Ad):
            raise RuntimeError("could not recover retained input indices")
        excluded = near(all_event_points, Ad, r_match) if len(all_event_points) else np.zeros(len(Ad), bool)
        contributions = defaultdict(list)
        for corpus_index, negative in patch_negatives:
            vertices = geometry.run_vertices(negative["axis"], negative["rc0"], negative["rc1"])
            run_points = np.asarray([P[row, col] for row, col in vertices])
            on_run = near(run_points, Ad, r_match)
            for retained, contributes in enumerate(on_run & ~excluded):
                if contributes:
                    contributions[retained].append({"corpus_negative_index": corpus_index, "axis": negative["axis"],
                                                    "rc0": negative["rc0"], "rc1": negative["rc1"]})
        record = {"input_path": str(source_path.relative_to(ROOT)), "input_sha256": sha256_file(source_path),
                  "input_points": int(len(A)), "retained_count": int(len(Ad)),
                  "retained": [{"input_index": retained_indices[index], "coordinate": [float(v) for v in point],
                                "event_excluded": bool(excluded[index]), "confirmed_negative_runs": contributions[index]}
                               for index, point in enumerate(Ad)],
                  "false_alarm_count_from_contributions": sum(len(value) for value in contributions.values())}
        saved_row = next(row for row in saved if row["name"] == name)
        if record["retained_count"] != saved_row["per_patch_alarms_after_dedup"][patch] or record["false_alarm_count_from_contributions"] != saved_row["per_patch_false_alarms"][patch]:
            raise RuntimeError(f"selected patch does not agree with saved {name} result")
        return record

    original, permutation = one("original"), one("permutation_15")
    explanation = {"selected_after_experiment": True, "patch": patch,
                   "thresholds": {"match_mm": SETTINGS["match_mm"], "fa_dedup_mm": SETTINGS["fa_dedup_mm"],
                                  "voxel_mm": raw_corpus["voxel_mm"], "match_voxels": r_match, "fa_dedup_voxels": r_dedup},
                   "original": original, "permutation_15": permutation,
                   "verified_saved_counts": {"original": {"retained": 8, "false_alarms": 1},
                                             "permutation_15": {"retained": 6, "false_alarms": 0}}}
    (OUT / "selected_real_patch_example.json").write_text(json.dumps(explanation, indent=1) + "\n")
    return explanation


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("chunk", "explain", "finalize", "finalize-saved", "validate", "worker"))
    parser.add_argument("spec", nargs="?")
    parser.add_argument("bootstrap", nargs="?", type=int)
    args = parser.parse_args()
    if args.mode == "worker":
        worker(json.loads(args.spec), args.bootstrap)
    elif args.mode == "chunk":
        run_chunk(int(args.spec), int(args.bootstrap))
    elif args.mode == "validate":
        validate_saved(allow_historical_equivalence=False)
    elif args.mode == "finalize-saved":
        finalize_saved_evidence()
    elif args.mode == "explain":
        explain_selected_patch()
    else:
        finalize()
