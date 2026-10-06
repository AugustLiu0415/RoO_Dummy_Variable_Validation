# RoO_Dummy_Variable_Validation

This repository records three AI-assisted review stages for the RoO input→output (IO) dummy variable across one PTA.

**Rule (Professor Hao Zhang):** *If input A could be potentially used to produce output B, then we should keep 1 there. Only when A and B are totally irrelevant should we change 1 to 0.*

> **AI-assisted review suggestions, not human confirmation.** A suggested 0 is a candidate for exclusion, not a confirmed deletion; a suggested 1 with a pathway is not "verified". No accuracy rate is claimed, and this is **not** a statement that the whole PTA data set has been cleaned.

The full method and results are in [`docs/VALIDATION_PROCESS.md`](docs/VALIDATION_PROCESS.md). The latest cross-check counts are also in [`Summary/Third_Pass_Review_Report.md`](Summary/Third_Pass_Review_Report.md).

## Three review stages

1. **Codex initial screen:** Apply the expansive rule to all 115,764 pairs in five fixed batches. `1` means *not excluded*, including uncertain pairs; `0` means a candidate obvious mismatch awaiting human confirmation.
2. **Claude re-review:** Review every initial candidate-0, Uncertain, and Classification / Other pair. Record a proposed 0/1 value and an explanation for each pair in separate review columns; preserve the initial dummy value.
3. **Codex cross-check:** Reassess Claude's proposed values and explanations. Mark questionable rows orange and add `second_round_reason`. This stage did not change Claude's proposed 0/1 values.

The directory names `DV_Round_2_ZeroDV_Review`, `DV_Round_3_Uncertain_Review`, and `DV_Round_4_Other_Review` distinguish **source queues**. They are not the number of independent validation stages.

## Status at a glance

- 115,764 HS6 input→output pairs, split into 5 fixed rounds (about 23,153 each) and screened by a loose-exclusion rule (`EXPANSIVE_EXCLUSION_V2`).
- The first screen produced 2,649 candidate 0s, 52,419 Uncertain cases and 1,621 Classification / Other cases. The other 59,075 pairs were provisionally retained as plausible 1s and were outside the focused re-review.
- Claude's re-review and Codex's cross-check produced the following **provisional** results. Orange is a question for human adjudication, not a confirmed error:

| Original queue | Pairs | Claude suggests 0 | Claude retains 1 | Codex orange flags |
|---|---:|---:|---:|---:|
| Initial candidate 0 | 2,649 | 2,603 | 46 | 69 (all suggested 0) |
| Uncertain | 52,419 | 30,856 | 21,563 | 3,327 (3,086 suggested 0; 241 retained 1) |
| Classification / Other | 1,621 | 1,598 | 23 | 86 (all suggested 0) |
| **Reviewed queues** | **56,689** | **35,057** | **21,632** | **3,482** |

- The 218 automated consistency checks documented in the earlier process applied to the Claude-stage files. The third-stage file and count checks are documented in the current report.
- `human_review_status = REVIEWED` in repository copies records preliminary workflow review. **`human_dummy` (the final human 0/1 decision) remains empty.** Neither the orange counts nor this status measures accuracy.
- The remaining decisions and manual review scope are listed in the process document.

## Repository layout

| Path | Content |
|---|---|
| `DV_Round_1_Validation/` | `Round_1–5_Review.xlsx` – rule-based screening of every pair (23k rows per file). |
| `DV_Round_2_ZeroDV_Review/` | `Round_1–5_ZeroDV_Review.xlsx` – Claude-stage review of initial 0s; `Round_1–5_ZeroDV_Review2.0.xlsx` – Codex cross-check with orange flags. |
| `DV_Round_3_Uncertain_Review/` | `Round_1–5_Uncertain_Review.xlsx` and `Round_k_Report.md` – Claude-stage Uncertain review; `Round_1–5_Uncertain_Review2.0.xlsx` – Codex cross-check. |
| `DV_Round_4_Other_Review/` | `Round_1–5_Other_Review.xlsx` and `Round_k_Report.md` – Claude-stage Classification / Other review; `Round_1–5_Other_Review_2.0.xlsx` – Codex cross-check. |
| `Summary/` | `Data_Cleaning_Summary.xlsx` / `.csv` and `Data_Cleaning_Report.md` describe Claude-stage U/Other results; `Third_Pass_Review_Report.md` summarizes Codex flags. |
| `docs/VALIDATION_PROCESS.md` | The validation steps, results, checks, decisions needed and next steps. |

## How to read the workbooks

- **Yellow** in the Claude-stage review marks a suggested 0. **Orange** in a `2.0` workbook marks a Codex concern; its explanation is in `second_round_reason`. An orange row can currently be either 0 or 1.
- Use `sample_id` and `pair_id` to match records between stages. HS6 codes are text, so leading zeros are preserved. The original value, Claude's proposed value and the Codex flag are separate fields/formatting.
- `human_dummy` accepts only 0 or 1 (data validation). Fill it only with a human decision.

| `review_status` | Meaning |
|---|---|
| `EXCLUDE_0_PENDING_HUMAN` | AI suggests 0 (Z); needs human confirmation. |
| `KEEP_1_POTENTIAL_USE` | Keep 1; a concrete processing / ingredient / feed / recycling route exists (P). |
| `KEEP_1_UNCERTAIN_PENDING_HUMAN` | Keep 1; no direct route seen but not totally irrelevant (U). |
| `KEEP_1_CLASSIFICATION_PENDING_HUMAN` | Keep 1; code / classification problem (C). |

`P` in `review_status` means **potential use**; it is not shorthand for the Classification / Other source queue. `C` marks a remaining classification issue. `human_review_status = REVIEWED` is preliminary workflow metadata, not a final manual label; `NOT_REQUIRED` applies to original `KEEP_1_PLAUSIBLE` rows outside the focused queue.

## Copies and provenance

The earlier-stage files in this repository are copies. Compared with the local working files:

1. `human_review_status`: `PENDING` / `AWAITING_USER_ACCEPTANCE` → `REVIEWED` (56,689 rows in the five validation workbooks, 45,335 rows in zero-review Round_2–5, and all 54,040 target rows in the two queue folders; `NOT_REQUIRED` unchanged). Round_1 of the zero-review folder has no such column and is unchanged.
2. `DV_Round_2_ZeroDV_Review/`: AI-related column names and a few text values were made neutral (prefix `ai_`, reviewer value `AI_ASSISTED`); no judgements were changed.
3. The folder `DV_Round_1_Valdiation` is spelled `DV_Round_1_Validation` here.
4. No `human_dummy` value was written.

The `2.0` files preserve the local Codex cross-check snapshots. In particular, the Zero `2.0` files retain the original Claude-named review columns, whereas the earlier Zero repository copies use neutral `ai_` column names. This naming difference does not indicate a change in the proposed decisions.

## Not included

CSV mirrors of the workbooks, the full audit trail (frozen target lists, source snapshots, per-batch result files, about 200 MB) and the scripts are kept locally and can be added on request.
