# Third-pass Codex cross-check of Claude's dummy-variable review

Status as of 2026-10-05. This report covers the selected review queues across all five batches of the 115,764-pair PTA. The first Codex screen and Claude re-review are described in [`docs/VALIDATION_PROCESS.md`](../docs/VALIDATION_PROCESS.md).

## What the third pass did

Codex checked Claude's proposed dummy values and explanations for the original candidate-zero, Uncertain, and Classification / Other queues. Each questionable row is highlighted orange in the corresponding `2.0` workbook and has a `second_round_reason`. The third pass **did not change** the original dummy values or Claude's `review_dummy` / `review_status` proposals. Unflagged rows have no new reason in this column.

| Original source queue | Pairs checked | Claude suggests 0 | Claude retains 1 | Orange among suggested 0 | Orange among retained 1 | All orange |
|---|---:|---:|---:|---:|---:|---:|
| Initial candidate 0 | 2,649 | 2,603 | 46 | 69 | 0 | 69 |
| Uncertain | 52,419 | 30,856 | 21,563 | 3,086 | 241 | 3,327 |
| Classification / Other | 1,621 | 1,598 | 23 | 86 | 0 | 86 |
| **All selected queues** | **56,689** | **35,057** | **21,632** | **3,241** | **241** | **3,482** |

The Uncertain and Classification / Other queues together have **3,413** orange flags: 3,172 among proposed zeros and 241 among retained ones. Their queue names describe why the first screen set them aside, not their current proposed dummy values. All 54,040 of these pairs started with `dummy = 1`; Claude subsequently proposed 32,454 candidate zeros, pending human adjudication.

| Batch | Initial-zero orange | Uncertain orange | Classification / Other orange |
|---|---:|---:|---:|
| Round 1 | 14 | 668 | 19 |
| Round 2 | 17 | 639 | 15 |
| Round 3 | 17 | 671 | 20 |
| Round 4 | 11 | 685 | 17 |
| Round 5 | 10 | 664 | 15 |
| **Total** | **69** | **3,327** | **86** |

## File and count checks

All fifteen `2.0` workbooks passed ZIP integrity checks. The row counts and proposed 0/1 counts in the first table were recomputed from their review sheets. In every workbook, `second_round_reason` is populated exactly where the row has the orange fill. For the ten Uncertain / Other workbooks, every prior cell value matches its corresponding Claude-stage workbook; only the new reason column and formatting differ. For the five initial-zero workbooks, all 2,649 `sample_id`, `pair_id`, proposed-value and status combinations match the earlier repository copies. The Zero `2.0` files retain Claude-named headers and local snapshot metadata, while the earlier repository copies use neutral `ai_` headers.

## Interpretation and next step

Under Professor Zhang's expansive criterion, a plausible direct or indirect input-to-output use is enough to retain `1`; only a totally unrelated pair qualifies for final `0`. The orange flags identify decisions or explanations that need closer examination. They are **not** 3,482 confirmed errors and do not establish an accuracy rate. The 35,057 suggested zeros are provisional; they must not be reported as final exclusions.

The 69 initial-zero flags and 3,413 Uncertain/Other flags should be prioritized for human adjudication. The professor's guidance also calls for checking remaining uncertain and excluded pairs. Because the unflagged population is much larger, the scope of full manual review versus an approved stratified audit should be settled before calculating an overall accuracy estimate. Record final human decisions in `human_dummy` and retain the sampling denominator if an audit is used. Currently `human_dummy` is blank, so no human-confirmed accuracy rate is available.

## Workbook locations

- `DV_Round_2_ZeroDV_Review/Round_1–5_ZeroDV_Review2.0.xlsx`
- `DV_Round_3_Uncertain_Review/Round_1–5_Uncertain_Review2.0.xlsx`
- `DV_Round_4_Other_Review/Round_1–5_Other_Review_2.0.xlsx`

The earlier-stage workbooks remain in the same directories without the `2.0` suffix. `P` in Claude's `review_status` means potential use, not the Classification / Other source queue; `C` means a remaining classification issue.
