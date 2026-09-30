#!/usr/bin/env python3
"""Bounded Phase 1 acquisition and baseline runner for the pinned SwitchBench inputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import resource
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "upstream" / "source"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))
CORPUS = SOURCE / "results" / "switchbench_natural_v1_events.json"
ALARMS = SOURCE / "results" / "switchbench_natural_v1_leaderboard" / "alarms" / "tifxyz-doctor_coherent-normal-step__default.json"
PATCHES = ROOT / "data" / "patches"
MANIFEST = ROOT / "manifests" / "phase1-acquired-files.tsv"
RESULTS = ROOT / "results" / "baseline"
COMMIT = "d7401a7087710875e8e168e6d30410919d1739b9"
LIMIT_BYTES = 200 * (1 << 20)
WALL_LIMIT_SECONDS = 15 * 60
EXPECTED = {
    "hits": 24,
    "events": 213,
    "false_alarms": 70,
    "per_100mm": 0.42646495768486786,
    "coverage": [237, 237],
    "settings": {"match_mm": 1.0, "fa_dedup_mm": 0.5, "per_patch_cap": 3, "bootstrap": 2000, "seed": 20260925},
}


class WallTimeExceeded(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_phase0_inputs() -> None:
    rows = list(csv.DictReader((ROOT / "manifests" / "acquired-files.tsv").open(), delimiter="\t"))
    bad = []
    for row in rows:
        path = ROOT / row["path"]
        if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256_file(path) != row["sha256"]:
            bad.append(row["path"])
    if bad:
        raise RuntimeError(f"immutable Phase 0 input verification failed: {bad[:3]}")


def required_remote():
    from huggingface_hub import get_bucket_paths_info
    from tools.switchbench_kit.corpus import read_corpus, scored_patch_ids

    raw = read_corpus(CORPUS)
    source = raw["patch_source"]
    patch_ids = scored_patch_ids(raw)
    names = ("x.tif", "y.tif", "z.tif", "mask.tif", "meta.json")
    prefix = source["prefix"].rstrip("/")
    paths = [f"{prefix}/{patch}/{name}" for patch in patch_ids for name in names]
    remote = {}
    for offset in range(0, len(paths), 100):
        batch = paths[offset:offset + 100]
        info = list(get_bucket_paths_info(source["bucket"], batch, token=False))
        remote.update({item.path: int(item.size) for item in info})
        print(f"preflight {min(offset + len(batch), len(paths))}/{len(paths)} paths", flush=True)
    missing = [path for path in paths if path.rsplit("/", 1)[-1] in names[:3] and path not in remote]
    if missing:
        raise RuntimeError(f"required remote geometry absent: {missing[0]}")
    selected = [path for path in paths if path in remote]
    expected = sum(remote[path] for path in selected)
    if expected > LIMIT_BYTES:
        raise RuntimeError(f"preflight transfer {expected} bytes exceeds {LIMIT_BYTES} byte data limit")
    return raw, patch_ids, source, selected, remote, expected


def write_manifest(source, remote: dict[str, int]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    source_rows = [
        ("source", "upstream/source/tools/__init__.py", 0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "tools/__init__.py"),
        ("source", "upstream/source/tools/switchbench_kit/__init__.py", 894, "6bf6978122b2005913a9abe8b4843a7222b440f2b172846f3d4a99608f2fe95e", "tools/switchbench_kit/__init__.py"),
        ("source", "upstream/source/tools/switchbench_kit/geometry.py", 4612, "1ae021025d9ac6b09ffc6bdaa7d8d0bb8783703f4a0fced79a737a7f423b2347", "tools/switchbench_kit/geometry.py"),
        ("source", "upstream/source/tools/switchbench_kit/report.py", 4396, "3bc71ddf0f632bbcf53beabcf70d76db3ec123ab1d920cb5914d8022d4377ee9", "tools/switchbench_kit/report.py"),
    ]
    with MANIFEST.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(("kind", "path", "commit", "bytes", "sha256", "url"))
        for kind, path, size, digest, remote_path in source_rows:
            local = ROOT / path
            if local.stat().st_size != size or sha256_file(local) != digest:
                raise RuntimeError(f"pinned source verification failed: {path}")
            writer.writerow((kind, path, COMMIT, size, digest,
                             f"https://raw.githubusercontent.com/lightsgoblack/scroll-audits/{COMMIT}/{remote_path}"))
        for remote_path in sorted(remote):
            relative = remote_path.split("/unverified_patches/", 1)[1]
            local = PATCHES / relative
            if not local.is_file() or local.stat().st_size != remote[remote_path]:
                raise RuntimeError(f"geometry verification failed: {remote_path}")
            writer.writerow(("geometry", str(local.relative_to(ROOT)), COMMIT, local.stat().st_size, sha256_file(local),
                             f"hf://{source['bucket']}/{remote_path}"))


def acquire() -> None:
    check_phase0_inputs()
    raw, patch_ids, source, selected, remote, expected = required_remote()
    existing = sum(path.stat().st_size for path in PATCHES.rglob("*") if path.is_file()) if PATCHES.exists() else 0
    if existing and existing > LIMIT_BYTES:
        raise RuntimeError(f"existing geometry {existing} bytes exceeds {LIMIT_BYTES} byte data limit")
    from huggingface_hub import download_bucket_files
    to_get = []
    for remote_path in selected:
        relative = remote_path.split("/unverified_patches/", 1)[1]
        destination = PATCHES / relative
        if destination.is_file() and destination.stat().st_size == remote[remote_path]:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        to_get.append((remote_path, str(destination)))
    for offset in range(0, len(to_get), 100):
        batch = to_get[offset:offset + 100]
        download_bucket_files(source["bucket"], batch, raise_on_missing_files=True, token=False)
        print(f"downloaded {min(offset + len(batch), len(to_get))}/{len(to_get)} files", flush=True)
    actual = sum(path.stat().st_size for path in PATCHES.rglob("*") if path.is_file())
    if actual > LIMIT_BYTES:
        raise RuntimeError(f"downloaded geometry {actual} bytes exceeds {LIMIT_BYTES} byte data limit")
    write_manifest(source, {path: remote[path] for path in selected})
    out = {"corpus_sha256": sha256_file(CORPUS), "patches": len(patch_ids), "expected_transfer_bytes": expected,
           "data_bytes": actual, "downloaded_files": len(to_get), "source": source}
    print(json.dumps(out, indent=1, sort_keys=True))


def _on_alarm(_signum, _frame):
    raise WallTimeExceeded(f"scoring exceeded {WALL_LIMIT_SECONDS} seconds")


def score() -> None:
    check_phase0_inputs()
    if not MANIFEST.is_file():
        raise RuntimeError("Phase 1 acquisition manifest is absent")
    signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(WALL_LIMIT_SECONDS)
    started = time.monotonic()
    try:
        from tools.switchbench_kit.alarms import load_alarms
        from tools.switchbench_kit.corpus import load_benchmark
        from tools.switchbench_kit.scoring import score as score_unmodified
        bench = load_benchmark(CORPUS, PATCHES)
        result = score_unmodified(bench, load_alarms(ALARMS, bench, detector="tifxyz-doctor (coherent-normal-step)"))
    finally:
        signal.alarm(0)
    elapsed = time.monotonic() - started
    usage = resource.getrusage(resource.RUSAGE_SELF)
    observed = {
        "hits": result["recall"]["hits"], "events": result["recall"]["events"],
        "false_alarms": result["false_alarms"]["count"], "per_100mm": result["false_alarms"]["per_100mm"],
        "coverage": result["coverage"]["patches"],
        "settings": {k: result["settings"][k] for k in EXPECTED["settings"]},
    }
    exact = {k: observed[k] == EXPECTED[k] for k in ("hits", "events", "false_alarms", "coverage", "settings")}
    exact["per_100mm"] = observed["per_100mm"] == EXPECTED["per_100mm"]
    comparison = {"expected": EXPECTED, "observed": observed, "exact": exact, "all_exact": all(exact.values()),
                  "displayed": {"per_100mm_2dp": format(observed["per_100mm"], ".2f")},
                  "resources": {"wall_seconds": elapsed, "peak_rss_bytes_macos": int(usage.ru_maxrss),
                                "wall_limit_seconds": WALL_LIMIT_SECONDS}}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "score.json").write_text(json.dumps(result, indent=1) + "\n")
    (RESULTS / "comparison.json").write_text(json.dumps(comparison, indent=1) + "\n")
    print(json.dumps(comparison, indent=1, sort_keys=True))
    if not comparison["all_exact"]:
        raise RuntimeError("baseline differs from published values")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("acquire", "score"))
    args = parser.parse_args()
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
    if args.action == "acquire":
        acquire()
    else:
        score()
