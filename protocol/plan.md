# Phase 0 local analysis plan

Timestamped 2026-09-30T22:52:13+0200 local analysis plan for a later bounded reproduction and alarm-export sensitivity audit

This is not public preregistration or a blind test

Upstream code and results have already been seen and source inspection establishes order-dependent greedy alarm deduplication

## Pinned primary analysis

- Primary detector is tifxyz-doctor coherent-normal-step default
- Inputs are the exact pinned v1 corpus and shipped alarm export at commit d7401a7087710875e8e168e6d30410919d1739b9
- Corpus is results/switchbench_natural_v1_events.json with SHA-256 e244a9074017924ff8ceb5a156bad9044f0e902de4f0352570da46caf8036b5a
- Alarm export is results/switchbench_natural_v1_leaderboard/alarms/tifxyz-doctor_coherent-normal-step__default.json with SHA-256 283d385b1220d4771397ecc276c73c65f989842c71fc0d4f8f751fc8d2b68f38
- Keep event selection seed 20260925, full coverage, xyz coordinates, match radius 1 mm, false-alarm dedup radius 0.5 mm, per-patch cap 3 and all denominators fixed
- Keep bootstrap 2000 and its scorer seed 20260925 fixed

## Planned transforms and checks

- Score the original alarm order, reverse order, lexicographic xyz order and independent per-patch permutations with seeds 0 through 19
- Score a lossless JSON roundtrip and an exact duplicate insertion
- Before each permutation score, prove equality of the point multiset, patch keys and no-verdict states against the original export
- Permutation seeds control only export ordering and are distinct from the scorer event-selection and bootstrap seed
- Do not alter official scoring or propose a replacement deduplication algorithm

## Outputs and interpretation

- Primary outputs are change in integer false-alarm count, rate per 100 mm, recall hit count, event count and coverage
- Any nonzero difference is numerical sensitivity and does not automatically establish practical significance
- A method ranking reversal is reported only if comparable evaluated rows exchange their metric ordering

## Bounded execution envelope

- One CPU worker with OMP_NUM_THREADS, OPENBLAS_NUM_THREADS, MKL_NUM_THREADS, VECLIB_MAXIMUM_THREADS and NUMEXPR_NUM_THREADS set to 1 or 2 as supported
- Retain raw immutable inputs and derived results within 200 MiB working data and 1 GiB total project data including an isolated environment
- Monitor children and terminate near 4 GiB RSS while recording the interruption
- No patch geometry download, dependency installation, detector run or scorer invocation occurs in Phase 0
