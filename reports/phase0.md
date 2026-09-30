# Phase 0 feasibility and gate

## SOURCE_REPORTED

- The pinned upstream commit is d7401a7087710875e8e168e6d30410919d1739b9
- The published primary row is tifxyz-doctor coherent-normal-step default with 24 hits from 213 counted events, 70 false alarms, 0.42646495768486786 false alarms per 100 mm and 237 of 237 patch verdict coverage
- The v1 corpus specifies 1 mm matching, 0.5 mm false-alarm deduplication, per-patch cap 3, bootstrap 2000 and seed 20260925
- The source describes v1 geometry acquisition from Hugging Face bucket scrollprize/datasets at spiral/PHercParis4/unverified_patches and estimates about 30 MB of patch files
- Upstream declares code under MIT and derived label files and the cited scan data under CC BY-NC 4.0
- Upstream declares Python 3.10 or later plus numpy, scipy and tifffile for scoring and imagecodecs for LZW tifxyz geometry

## LOCALLY_MEASURED

- Host is macOS 12.7.6 on Intel x86_64 with 30 GiB free disk
- The project currently occupies 2288 KiB and immutable acquired inputs are 2.2 MiB
- The shipped primary alarm export has 237 patch keys and 6825 points
- The v1 corpus metadata has 237 scored patches, 294 confirmed source events and 1261 confirmed negative runs before the cap
- Python 3.12.8 is available at /usr/local/bin/python3.12 and its environment lacks numpy, scipy, tifffile, imagecodecs and huggingface_hub
- Python 3.8.15 and Python 3.9.6 are also present and do not meet the declared Python floor
- No scorer, detector, geometry fetch, dependency installation or transformed-alarm score ran

## INFERRED

- The reported roughly 30 MB geometry transfer fits the 200 MiB working-data budget when accepted as a source estimate, but the exact remote file list and bytes have not been acquired or verified
- The primary score and sensitivity audit appear computationally bounded because they reuse shipped alarms and score 237 patches on CPU, but this has not been benchmarked locally

## Gate

PHASE0_BLOCKED

The current rules permit GitHub acquisition only while the required immutable geometry lives in a Hugging Face bucket, and no compatible local dependency environment exists

Smallest next action is to explicitly authorize a bounded read-only acquisition from the exact Hugging Face prefix with a preflight byte cap and provide or authorize an isolated Python 3.10 or later environment containing the declared binary dependencies
