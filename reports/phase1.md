# Phase 1 baseline reproduction

## SOURCE_REPORTED

- Pinned commit d7401a7087710875e8e168e6d30410919d1739b9 reports 24 hits from 213 counted events, 70 false alarms, 0.42646495768486786 false alarms per 100 mm and 237 of 237 patches with a verdict for tifxyz-doctor coherent-normal-step default
- Published scorer settings are 1 mm matching, 0.5 mm false-alarm deduplication, per-patch cap 3, bootstrap 2000 and seed 20260925

## LOCALLY_MEASURED

- Existing Phase 0 acquisitions were rehashed and all 16 records matched their manifest
- Added four pinned source files needed for execution and all 1186 Phase 1 records in manifests/phase1-acquired-files.tsv passed byte and SHA-256 verification
- Bucket preflight selected 1185 geometry or metadata files for 237 patches and reported 31708812 bytes before transfer
- Local data directory occupies 33904 KiB including the pinned fetch manifest and project disk use is 391132 KiB, below the 1 GiB project limit
- The unmodified scorer matched corpus geometry fingerprint e6115ded16ad4c1e87d863014b2bc086009640bb8c74b79b5a10151aabaedffa and reported geometry_check match
- Baseline result was 24 of 213 hits, 70 false alarms, 0.42646495768486786 false alarms per 100 mm and 237 of 237 coverage
- All requested settings matched exactly and the displayed rate rounded to 0.43
- Final bootstrap 2000 run took 8.382670513994526 seconds with 242675712 bytes macOS peak RSS, below the 900 second and 2 GiB limits

## INFERRED

- This Mac can reproduce the pinned primary baseline within the stated disk, CPU and memory limits
- This result establishes only the original-order baseline and does not evaluate transformed alarm exports

## Commands

- /usr/local/bin/python3.12 -m venv .venv
- PIP_CACHE_DIR=/Users/olga/Documents/scroll-eval-reliability/cache/pip .venv/bin/python -m pip install --only-binary=:all: numpy scipy tifffile imagecodecs huggingface_hub
- OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 .venv/bin/python -u scripts/baseline.py acquire
- OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 .venv/bin/python -u scripts/baseline.py score

## Gate

BASELINE_REPRODUCED
