# Phase 2 alarm representation audit

## SOURCE_REPORTED

- The pinned primary row reports 24 of 213 hits, 70 false alarms, 0.42646495768486786 false alarms per 100 mm and 237 of 237 patch coverage
- The pinned scorer performs greedy false-alarm deduplication in input order at 0.5 mm

## LOCALLY_MEASURED

- All 16 Phase 0 and all 1186 Phase 1 manifest records matched their bytes and SHA-256 values before scoring
- The Phase 1 composition is 4 source files and 1182 geometry or metadata files
- The earlier 1185 figure counts the 237 times 5 requested candidate paths before the bucket omitted three optional mask files for auto_grown_w20230702185753, auto_grown_w20231007101619 and auto_grown_w20231031143852
- Corpus and alarm SHA-256 values matched the pins and every run matched the geometry fingerprint
- Three wrapper invariant fixtures passed for deterministic permutation, duplicate insertion and missing versus empty versus null states
- All 25 variants passed their recorded equivalence checks and retained 24 of 213 hits with 237 of 237 coverage and the same 16414.00981220263 mm denominator

| Variant set | False alarms | Rate per 100 mm |
|---|---:|---:|
| Original | 70 | 0.42646495768486786 |
| Reverse | 63 | 0.3838184619163811 |
| Lexicographic xyz | 68 | 0.4142802446081574 |
| Permutations 0 to 19 | 65, 61, 69, 59, 65, 63, 66, 64, 62, 57, 62, 60, 62, 62, 65, 56, 61, 63, 69, 66 | 0.3411719661478943 to 0.4203726011465126 |
| Lossless JSON roundtrip | 70 | 0.42646495768486786 |
| Exact duplicate insertion | 70 | 0.42646495768486786 |

- Across the 23 order variants the count minimum, median and maximum were 56, 63 and 70 and rates were 0.3411719661478943, 0.3838184619163811 and 0.42646495768486786
- The minimum permutation_15 differs from baseline by minus 14 false alarms and minus 0.08529299153697356 per 100 mm or minus 20 percent
- The selected minimum bootstrap interval was 0.11527014133768143 to 0.6418447464727696 and the reused original interval was 0.1448535786954164 to 0.825909951303734
- These selected-extreme intervals are descriptive and not selection-adjusted inference
- The selected post-experiment real-patch explanation is results/invariance/selected_real_patch_example.json where the same points retain 6 versus 8 alarms and score 0 versus 1 false alarms on one patch
- Point-estimate runs totaled 259.0369584389846 seconds with maximum measured peak RSS 257171456 bytes and no watchdog interruption

## INFERRED

- Alarm ordering causes numerical sensitivity in false-alarm scoring for this fixed detector export
- Recall and coverage did not change in this audit
- No ranking reversal, benchmark invalidity or practical-significance conclusion was evaluated

## Gate

AUDIT_COMPLETE_SENSITIVE
