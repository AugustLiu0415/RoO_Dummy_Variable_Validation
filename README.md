# RoO_Dummy_Variable_Validation

This repository records the validation of the RoO input→output (IO) dummy variable.

**Rule (Professor Hao Zhang):** *If input A could be potentially used to produce output B, then we should keep 1 there. Only when A and B are totally irrelevant should we change 1 to 0.*

> **AI-assisted review suggestions, not human confirmation.** A suggested 0 is a candidate for exclusion, not a confirmed deletion; a suggested 1 with a pathway is not "verified". No accuracy rate is claimed, and this is **not** a statement that the whole PTA data set has been cleaned.

The full step-by-step description is in [`docs/VALIDATION_PROCESS.md`](docs/VALIDATION_PROCESS.md).

## Status at a glance

- 115,764 HS6 input→output pairs, split into 5 fixed rounds (about 23,153 each) and screened by a loose-exclusion rule (`EXPANSIVE_EXCLUSION_V2`).
- 2,649 original candidate 0s were re-checked (AI-assisted): 2,603 still suggested 0, 34 suggested back to 1, 12 kept 1 as uncertain.
- 54,040 pairs from the "Uncertain" (52,419) and "Classification / Other" (1,621) queues received an AI-assisted suggestion:

| | Pairs | Z: suggest 0 | P: keep 1 (pathway) | U: keep 1 (uncertain) | C: code problem |
|---|---|---|---|---|---|
| Uncertain | 52,419 | 30,856 | 4,840 | 16,723 | 0 |
| Classification / Other | 1,621 | 1,598 | 6 | 6 | 11 |
| **Total** | **54,040** | **32,454** | **4,846** | **16,729** | **11** |

- 218 automated consistency checks passed.
- A preliminary manual review was done by the RA; `human_review_status` is set to `REVIEWED` in these copies. **`human_dummy` (the final 0/1 human decision) is still empty everywhere.**
- Open policy questions for the professor are listed in Step 7 of the process document (the biggest one: whether the 16,729 "same family, no direct route" U pairs should be flipped to 0 in bulk).

## Repository layout

| Path | Content |
|---|---|
| `DV_Round_1_Validation/` | `Round_1–5_Review.xlsx` – rule-based screening of every pair (23k rows per file). |
| `DV_Round_2_ZeroDV_Review/` | `Round_1–5_ZeroDV_Review.xlsx` – second-pass AI-assisted review of the 2,649 original candidate 0s (sheet `Zero_Review`). AI columns are prefixed `ai_`. |
| `DV_Round_3_Uncertain_Review/` | `Round_1–5_Uncertain_Review.xlsx` and `Round_k_Report.md` – AI-assisted review of the Uncertain queue. |
| `DV_Round_4_Other_Review/` | `Round_1–5_Other_Review.xlsx` and `Round_k_Report.md` – AI-assisted review of the Classification / Other queue. |
| `Summary/` | `Data_Cleaning_Summary.xlsx` / `.csv` (T, H, R, Z, P, U, C, N, Q per queue and round, with subtotals and de-duplicated total) and `Data_Cleaning_Report.md`. |
| `docs/VALIDATION_PROCESS.md` | The validation steps, results, checks, decisions needed and next steps. |

## How to read the workbooks

- **Review sheet, `review_dummy = 0` rows are highlighted yellow** (conditional formatting over the entire row): these are AI suggestions to exclude.
- Key columns: `sample_id`, `pair_id`, `input_hs6`, `output_hs6` (text, leading zeros kept), original descriptions and Chinese names, `original_status`, `review_dummy`, `review_status`, `review_reason`, `potential_pathway`, `zero_reason`, `remaining_issue`, `issue_class`, `knowledge_basis`, `reviewer_type = AI_ASSISTED`, `rule_version`, `human_review_status`, `human_dummy`, `human_notes`.
- `human_dummy` accepts only 0 or 1 (data validation). Fill it only with a human decision.

| `review_status` | Meaning |
|---|---|
| `EXCLUDE_0_PENDING_HUMAN` | AI suggests 0 (Z); needs human confirmation. |
| `KEEP_1_POTENTIAL_USE` | Keep 1; a concrete processing / ingredient / feed / recycling route exists (P). |
| `KEEP_1_UNCERTAIN_PENDING_HUMAN` | Keep 1; no direct route seen but not totally irrelevant (U). |
| `KEEP_1_CLASSIFICATION_PENDING_HUMAN` | Keep 1; code / classification problem (C). |

`human_review_status`: `REVIEWED` (preliminary manual review done), `NOT_REQUIRED` (original `KEEP_1_PLAUSIBLE` rows, not part of the human-review queue).

## Differences from the RA's local working files

The files in this repository are copies. Compared with the local working files:

1. `human_review_status`: `PENDING` / `AWAITING_USER_ACCEPTANCE` → `REVIEWED` (56,689 rows in the five validation workbooks, 45,335 rows in zero-review Round_2–5, and all 54,040 target rows in the two queue folders; `NOT_REQUIRED` unchanged). Round_1 of the zero-review folder has no such column and is unchanged.
2. `DV_Round_2_ZeroDV_Review/`: AI-related column names and a few text values were made neutral (prefix `ai_`, reviewer value `AI_ASSISTED`); no judgements were changed.
3. The folder `DV_Round_1_Valdiation` is spelled `DV_Round_1_Validation` here.
4. Nothing else was edited; no `human_dummy` value was written.

## Not included

CSV mirrors of the workbooks, the full audit trail (frozen target lists, source snapshots, per-batch result files, about 200 MB) and the scripts are kept locally and can be added on request.
