# Third-party notices and provenance

## Scope of this notice

The MIT license in [LICENSE](LICENSE) applies only to original implementation code authored for this project, including the local scripts and tests

It does not claim ownership of or relicense upstream source, scan data, annotations, alarm exports, transformed copies of upstream inputs, derived results that contain upstream material or separately acquired dependencies

[manifests/deliverables.json](manifests/deliverables.json) is a report-file inventory, not a complete inventory of the repository

The review inventory contains the case-study documents, static figure, local renderer, checkpoint and these licensing notices

Read-only `git ls-files` confirms that the tracked repository also includes `results/baseline/comparison.json`, `results/baseline/score.json`, 24 transformed files in `results/invariance/inputs/`, 26 worker-result files in `results/invariance/`, `results/invariance/summary.json`, `results/invariance/validation.json`, `results/invariance/variants.json` and `results/invariance/selected_real_patch_example.json`

The virtual environment and cache were acquired separately for local execution and are not included in the review inventory

## Upstream software

The local provenance records identify `lightsgoblack/scroll-audits` at commit [`d7401a7087710875e8e168e6d30410919d1739b9`](https://github.com/lightsgoblack/scroll-audits/tree/d7401a7087710875e8e168e6d30410919d1739b9)

Its [pyproject.toml](https://github.com/lightsgoblack/scroll-audits/blob/d7401a7087710875e8e168e6d30410919d1739b9/pyproject.toml) declares `license = { text = "MIT" }` and its [README](https://github.com/lightsgoblack/scroll-audits/blob/d7401a7087710875e8e168e6d30410919d1739b9/README.md) states `Code: MIT`

The upstream [LICENSE](https://github.com/lightsgoblack/scroll-audits/blob/d7401a7087710875e8e168e6d30410919d1739b9/LICENSE) is MIT, copyright (c) 2026 Colin Mark Robinson (lightsgoblack)

The locally acquired `tools/switchbench_kit` source and related package files are recorded in [manifests/acquired-files.tsv](manifests/acquired-files.tsv) and [manifests/phase1-acquired-files.tsv](manifests/phase1-acquired-files.tsv)

If that source is redistributed, retain its upstream attribution and applicable MIT notice

## Upstream data and annotations

The upstream [README](https://github.com/lightsgoblack/scroll-audits/blob/d7401a7087710875e8e168e6d30410919d1739b9/README.md) identifies the source scans as *Vesuvius Challenge – CT Scans of Herculaneum Papyri* for PHercParis4, 2026 ESRF scan 20260411134726 and asks users to cite Giorgio Angelotti, Stephen Parsons, Sean Johnson, Elian Rafael Dal Prà, Johannes Rudolph, Paul Tafforeau, Alessandro Mirone, Paul Henderson, Hendrik Schilling, Forrest McDonald, David Josey, Youssef Nader, C. Seth Parker, W. Brent Seales

That README declares the source scans CC BY-NC 4.0 and derived label files CC BY-NC 4.0 under Vesuvius Challenge data terms

The local geometry patches in `data/patches/` were separately acquired from the documented `scrollprize/datasets` bucket and are not in the report-file inventory

The locally acquired corpus events and leaderboard metadata are listed as upstream `v1_metadata` records in [manifests/acquired-files.tsv](manifests/acquired-files.tsv)

The reviewed declarations do not establish that every JSON metadata or result artifact is a derived label file, so this notice does not assign CC BY-NC 4.0 to all such artifacts

## Alarm export and transformed inputs

The shipped `tifxyz-doctor_coherent-normal-step__default.json` alarm export is recorded as `v1_alarm_export` in [manifests/acquired-files.tsv](manifests/acquired-files.tsv)

The upstream repository provides an MIT license and separately identifies scans and derived label files as CC BY-NC 4.0

The reviewed declarations do not explicitly classify detector alarm exports between these categories

This project does not assign its own MIT license to the alarm export or the tracked transformed copies in `results/invariance/inputs/`

This wording does not resolve the classification question

## Derived local results

The tracked baseline outputs, transformed inputs, worker results, summary, validation, variants and selected-patch evidence are local study artifacts derived using upstream corpus, geometry and alarm inputs

This notice does not assign those artifacts a blanket third-party license where they contain upstream material
