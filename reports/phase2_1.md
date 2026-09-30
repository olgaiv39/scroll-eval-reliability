# Phase 2.1 evidence hardening

## VERIFIED SAVED EVIDENCE

- Validation checked all 16 Phase 0 records, all 1186 Phase 1 records and all 25 saved point-estimate variants without invoking scoring or bootstrap
- The 26 validation checks passed, including the saved permutation_15 bootstrap 2000 run against its bootstrap 0 point-estimate counterpart
- Bootstrap is intentionally 2000 in the selected-extreme run and 0 in the point-estimate run while their hits, events, false alarms, denominator, rate, coverage and per-patch false-alarm counts match
- Every saved variant has the expected name, transformation and seed, pinned input hashes, fixed settings, matching geometry fingerprint, 24 of 213 recall counts, 237 of 237 coverage, denominator, per-patch sum and rate
- Derived variants metadata now reports equal point multisets only for order variants and roundtrip
- Duplicate insertion reports equal unique support, exactly doubled multiplicity and an adjacent copy after each original point while its point-multiset check is null because it is inapplicable
- Raw worker files and saved inputs were not rewritten
- Validation now reconstructs each declared saved transformation from the pinned original and requires complete parsed JSON equality including non-alarm metadata
- Every saved denominator is compared with results/baseline/score.json using absolute tolerance 1e-12 and zero relative tolerance and original point metrics must match that baseline
- Normal validate never repairs derived artifacts

## SAVED-EVIDENCE FINALIZATION

- Added finalize-saved, a no-scoring and no-bootstrap path that validates before any artifact write, uses the existing bootstrap records and normalizes historical equivalence metadata only in memory
- The path verifies the expanded selected patch explanation remains byte-identical and never writes variants, inputs or worker results
- This phase tested finalization only on temporary copies and did not run it on the real evidence

## NEW LOCAL SELECTED-PATCH COMPUTATION

- The preselected patch auto_grown_20260420125348089_region_000 was reconstructed from the pinned local corpus, alarm inputs, geometry, dedup and proximity primitives without invoking the full scorer
- Thresholds were 1 mm matching and 0.5 mm deduplication or 104.16666666666667 and 52.083333333333336 voxels
- Original order retained 8 alarms and contributed 1 false alarm through input index 7 at coordinate 3786.31298828125, 5091.5684814453125, 16288.715576171875 against confirmed negative run index 1297
- Permutation_15 retained 6 alarms and contributed 0 false alarms after event exclusion
- This explanation was selected after the experiment and is descriptive only

## LIMITS

- Validation confirms internal consistency of saved artifacts and does not independently reproduce the 25 score computations
- The active RSS watchdog uses macOS ru_maxrss bytes and its units are platform-specific

## EXECUTED CHECKS

- Eight focused unittest cases passed including wrong transformation rejection, changed denominator rejection, historical in-memory finalization, pre-write rejection and patch explanation preservation
- Normal saved-evidence validation passed 26 checks with scoring_invoked false and bootstrap_invoked false

## GATE

EVIDENCE_READY
