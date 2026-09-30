# Scroll Evaluation Reliability Study

This independent local case study audits one fixed SwitchBench detector export on an Intel Mac

## Finding

Reordering the same alarm points changed the false-alarm result from 56 to 70 across 23 tested order variants while recall stayed 24/213 and coverage stayed 237/237

The lowest observed count, 56 for `permutation_15`, was 20% below the original count of 70

This measures sensitivity of this scorer and export to alarm order, not a detector improvement or a global minimum

## Scope and evidence

The audit fixes `tifxyz-doctor coherent-normal-step default`, the SwitchBench v1 corpus snapshot, shipped alarm export, matching radius, false-alarm deduplication radius, per-patch cap and scorer seed

Read the [case study](reports/STUDY.md), [claim check](reports/CLAIM_CHECK.md), [order-variant figure](reports/study.svg), [summary](results/invariance/summary.json), [saved variants](results/invariance/variants.json), [validation](results/invariance/validation.json) and [selected-patch explanation](results/invariance/selected_real_patch_example.json)

The 25 bootstrap-zero point-estimate workers summed to 259.0369584389846 seconds and their largest measured peak RSS was 257171456 bytes

The experiment covers one export and one corpus snapshot, does not test ranking changes, annotation validity or generalization, and treats selected-extreme bootstrap intervals as descriptive

## Local commands

Reading saved results needs no scorer execution

```sh
python3 -m json.tool results/invariance/summary.json
```

Validating existing local evidence needs the acquired inputs, pinned source files and the existing virtual environment, but does not invoke scoring or bootstrap

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  .venv/bin/python -u scripts/experiment.py validate
```

Saved-evidence finalization uses existing bootstrap records and validates before writing its derived validation record

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  .venv/bin/python -u scripts/experiment.py finalize-saved
```

Do not use the legacy `finalize` command on preserved artifacts because it can invoke workers and rewrite derived results

Reproducing the baseline score computation requires the acquired geometry, pinned upstream source and local dependencies

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
  .venv/bin/python -u scripts/baseline.py score
```

A fresh clone is not self-contained because it does not include the acquired data, virtual environment or cache

## Attribution and licenses

The pinned upstream source is [lightsgoblack/scroll-audits at d7401a7087710875e8e168e6d30410919d1739b9](https://github.com/lightsgoblack/scroll-audits/tree/d7401a7087710875e8e168e6d30410919d1739b9)

Upstream code is MIT and upstream derived labels and scan data are CC BY-NC 4.0 under the upstream terms

This study is independent work and does not imply acceptance or endorsement by ScrollPrize or upstream maintainers
