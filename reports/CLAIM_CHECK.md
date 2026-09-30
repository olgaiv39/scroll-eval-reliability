# Claim check

This map identifies the saved local evidence for each public claim in the case study

| Claim | Evidence location | Status |
|---|---|---|
| One fixed detector export and pinned commit were audited | `protocol/plan.md`, `results/invariance/variants.json` → `prerequisites.corpus_sha256`, `prerequisites.alarm_sha256` | Established |
| Original baseline is 24/213, 70 false alarms, 0.42646495768486786 per 100 mm and 237/237 coverage | `results/baseline/score.json` → `recall.hits`, `recall.events`, `false_alarms.count`, `false_alarms.per_100mm`, `coverage.patches` and `results/invariance/validation.json` → `prerequisites.baseline.all_exact` | Established |
| 23 protocol-order variants span 56–70 false alarms with median 63 | `results/invariance/summary.json` → `order_variants.n`, `order_variants.false_alarm_count` and `results/invariance/variants.json` → `variants[0:23].false_alarms` | Established |
| Lowest observed order count is 56 for `permutation_15`, 20% below original | `results/invariance/summary.json` → `order_variants.minimum` and `results/invariance/variants.json` → `variants[0].false_alarms`, `variants[18].false_alarms`, `variants[18].delta_false_alarms` | Established |
| Recall, coverage and denominator stayed fixed for point estimates | `results/invariance/variants.json` → `variants[*].hits`, `events`, `coverage`, `negative_mm` and `results/invariance/validation.json` → `checks`, `baseline_denominator` | Established |
| Order variants and roundtrip preserve point multisets | `results/invariance/variants.json` → `variants[0:24].equivalence.point_multisets_identical` and `scripts/experiment.py` → `transform`, `equivalence`, `transformation_errors`, `validate_saved` | Established |
| Duplicate insertion preserves support and doubles adjacent multiplicity | `results/invariance/variants.json` → `variants[24].equivalence.unique_support_identical`, `multiplicity_exactly_doubled`, `adjacent_copy_after_each_original` and `scripts/experiment.py` → `transform`, `equivalence`, `transformation_errors`, `validate_saved` | Established |
| Roundtrip and duplicate controls each retain 70 false alarms | `results/invariance/variants.json` → `variants[23].false_alarms`, `variants[24].false_alarms` | Established |
| Selected patch retained 8 versus 6 alarms and scored 1 versus 0 false alarms | `results/invariance/selected_real_patch_example.json` → `selected_after_experiment`, `original.retained_count`, `permutation_15.retained_count`, `verified_saved_counts` | Established, post-experiment selection |
| Upstream deduplication is greedy and input-order dependent | `upstream/source/tools/switchbench_kit/scoring.py` → `dedup` and module documentation, `upstream/source/tools/switchbench_kit/README.md` → scoring description | Source-reported |
| Point-estimate workers sum to 259.0369584389846 seconds and largest measured RSS is 257171456 bytes | `results/invariance/variants.json` → `variants[*].wall_seconds`, `variants[*].peak_rss_bytes_macos` and `reports/phase2.md` → LOCALLY_MEASURED resources | Established |
| Bootstrap intervals at selected extremes are descriptive | `results/invariance/summary.json` → `extremes`, `reports/phase2.md` → LOCALLY_MEASURED | Established as interpretation boundary |
| Saved validation ran without scoring or bootstrap | `results/invariance/validation.json` → `status`, `scoring_invoked`, `bootstrap_invoked`, `checks` | Established |
| Alarm order causes score sensitivity in this fixed setting | `results/invariance/variants.json` → `variants[*].false_alarms` plus transformation validation in `results/invariance/validation.json` → `checks` | Supported local interpretation |
| Detector improvement, a global minimum, ranking reversal, annotation validity, benchmark invalidity or generalization | No comparable evidence in this study | Not established and omitted from headline claims |

Upstream attribution and license statements are sourced from `upstream/source/README.md` → License and citation material and `upstream/source/pyproject.toml` → `project.license`
