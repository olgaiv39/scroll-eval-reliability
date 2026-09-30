# Alarm-order sensitivity in one SwitchBench evaluation

## Question

Can equivalent representations of one fixed SwitchBench alarm export change its reported score on this Intel Mac

## Source-reported facts

The audited detector is `tifxyz-doctor coherent-normal-step default` from the SwitchBench v1 leaderboard material in [lightsgoblack/scroll-audits at pinned commit d7401a7087710875e8e168e6d30410919d1739b9](https://github.com/lightsgoblack/scroll-audits/tree/d7401a7087710875e8e168e6d30410919d1739b9)

The upstream materials report 24 hits from 213 counted events, 70 false alarms, 0.42646495768486786 false alarms per 100 mm and 237/237 patch coverage for this row

The upstream scorer documents greedy false-alarm deduplication in input order: it drops an alarm within the 0.5 mm deduplication radius of an already retained alarm

## Frozen local protocol

The local audit used the exact pinned v1 corpus and shipped alarm JSON, with corpus SHA-256 `e244a9074017924ff8ceb5a156bad9044f0e902de4f0352570da46caf8036b5a` and alarm SHA-256 `283d385b1220d4771397ecc276c73c65f989842c71fc0d4f8f751fc8d2b68f38`

It fixed match radius 1 mm, false-alarm deduplication radius 0.5 mm, per-patch cap 3 and scorer seed 20260925

The 23 order variants were original, reverse, lexicographic xyz and independent deterministic per-patch permutations for seeds 0 through 19 in that order

Lossless JSON roundtrip and exact duplicate insertion were representation controls outside the 23 order variants

Order variants and roundtrip preserve each patch’s point multiset, coordinates, patch keys and no-verdict states

Duplicate insertion preserves unique point support and coverage, doubles point multiplicity and places each copied point beside its original

## Locally measured results

All 25 point-estimate runs used bootstrap 0 and retained 24/213 hits, 237/237 coverage and denominator 16414.00981220263 mm

| Variant group | False alarms | False alarms per 100 mm |
|---|---:|---:|
| Original | 70 | 0.42646495768486786 |
| Reverse | 63 | 0.3838184619163811 |
| Lexicographic xyz | 68 | 0.4142802446081574 |
| Permutations 0–19 | 56–69 | 0.3411719661478943–0.4203726011465126 |
| Order variants, min / median / max | 56 / 63 / 70 | 0.3411719661478943 / 0.3838184619163811 / 0.42646495768486786 |
| Lossless JSON roundtrip | 70 | 0.42646495768486786 |
| Exact duplicate insertion | 70 | 0.42646495768486786 |

`permutation_15` was the minimum order variant with 56 false alarms, 14 fewer than original and 20% below original’s count

The original was the maximum by the prespecified protocol tie rule

Figure [study.svg](study.svg) shows all 23 order variants in protocol order with a zero-based false-alarm axis

The selected minimum and maximum were rescored with bootstrap 2000, reusing the baseline interval for original

Their false-alarm intervals were 0.11527014133768143–0.6418447464727696 for `permutation_15` and 0.1448535786954164–0.825909951303734 for original

These selected-extreme intervals are descriptive and are not selection-adjusted inference

## Mechanism example

The post-experiment selected patch [`auto_grown_20260420125348089_region_000`](../results/invariance/selected_real_patch_example.json) retained 8 alarms in original order and 6 in `permutation_15`

It scored 1 and 0 false alarms respectively after event exclusion

The evidence records retained input indices and coordinates, thresholds and confirmed-negative-run contributions

In original order, retained input index 7 at `[3786.31298828125, 5091.5684814453125, 16288.715576171875]` contributes to confirmed negative run 1297, while no retained `permutation_15` alarm contributes

This explanatory example was selected after the experiment and is not independent confirmatory evidence

## Resources and validation

The 25 bootstrap-zero point-estimate worker times sum to 259.0369584389846 seconds

That figure is neither total project time nor time including the selected bootstrap runs

The maximum measured point-estimate peak RSS was 257171456 bytes

The baseline bootstrap-2000 run took 8.382670513994526 seconds and measured 242675712 bytes peak RSS

Saved-evidence validation passed 26 checks without invoking scoring or bootstrap

It verifies acquired manifests, pins, declared transformations reconstructed from original parsed content, settings, geometry fingerprint, denominator, counts, rates and bootstrap-to-point-estimate agreement

Saved-evidence validation establishes internal consistency of stored evidence and does not independently reproduce score computations

## Interpretation and limits

For this detector export and corpus snapshot, alarm ordering changed the measured false-alarm score while recall and coverage remained fixed

This is a measured sensitivity of scoring to alarm order, not a detector improvement or a global minimum claim

The study did not test ranking changes, annotation validity, practical significance, other detector exports or generalization to other corpus snapshots

The active watchdog used macOS `ru_maxrss` normalized to bytes, so its platform-specific units limit portability of that implementation detail

## Reproduction

Use [`README.md`](../README.md) for commands to read saved evidence, validate it locally and reproduce the baseline computation

Validation and score reproduction require already acquired local inputs and the existing environment, so a fresh clone alone is insufficient

Use `validate` or `finalize-saved` for preserved evidence and do not use legacy `finalize` on it

## Attribution

Upstream code is MIT and upstream derived label files and scan data are CC BY-NC 4.0 under the upstream terms

This independent study does not imply acceptance or endorsement by ScrollPrize or upstream maintainers
