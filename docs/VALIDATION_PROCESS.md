# Data validation process

This document records, step by step, how the RoO input→output (IO) dummy variable was validated. It describes what each stage did, what it produced, and what has **not** been done yet.

**Guiding rule (Professor Hao Zhang):**
*If input A could be potentially used to produce output B, then we should keep 1 there. Only when A and B are totally irrelevant should we change 1 to 0.*

**Important framing.** Everything labelled "AI-assisted" below is a *suggestion*, not a human confirmation. Suggested 0s are candidates for exclusion, not confirmed deletions. No accuracy rate is claimed anywhere in this repository, because no independent human labels exist yet.

---

## Step 0 – Source data

- File: `pairs_with_descriptions_PROVISIONAL.csv` – **115,764** input→output HS6 pairs with HS2002 product descriptions (`hs_version = UNCONFIRMED_ASEAN_JPN`, descriptions looked up in HS2002).
- Every pair starts with `dummy = 1` (keep) and is only changed to 0 when the rule above allows it.
- HS6 codes are always handled as 6-character text (leading zeros preserved).

## Step 1 – Fixed split into five rounds

- Pairs sorted by `pair_id`, shuffled with `random.Random(20260930)`, and cut into five equal parts: 23,153 / 23,153 / 23,153 / 23,153 / 23,152.
- A fixed `split_manifest.csv` is the only grouping used afterwards (no re-sampling). Sample IDs look like `R1-000001`.

## Step 2 – Rule-based loose-exclusion screening of every pair (`Round_k_Review`)

Rule set `EXPANSIVE_EXCLUSION_V2`: only very clear identity contradictions (for example two different named raw fruits, grains, oilseeds, plant oils, wood species) become *candidate* 0; anything with a plausible ingredient, component, feed, recycling or reprocessing route stays 1. Entries whose classification involves an "Other" residual subheading are not excluded automatically.

Result per round (status of the original screening; the workbooks are in `DV_Round_1_Validation/`):

| Round | Pairs | EXCLUDE_0_PENDING_HUMAN | KEEP_1_PLAUSIBLE | KEEP_1_UNCERTAIN_PENDING_HUMAN | KEEP_1_CLASSIFICATION_PENDING_HUMAN |
|---|---|---|---|---|---|
| 1 | 23,153 | 564 | 11,799 | 10,481 | 309 |
| 2 | 23,153 | 532 | 11,844 | 10,467 | 310 |
| 3 | 23,153 | 482 | 11,882 | 10,439 | 350 |
| 4 | 23,153 | 522 | 11,687 | 10,582 | 362 |
| 5 | 23,152 | 549 | 11,863 | 10,450 | 290 |
| **Total** | **115,764** | **2,649** | **59,075** | **52,419** | **1,621** |

This stage was an automatic, repeatable rule screen, not a row-by-row review.

## Step 3 – Second-pass AI-assisted review of the 2,649 candidate 0s (`DV_Round_2_ZeroDV_Review/`)

Every original candidate 0 was re-checked against both product definitions and against possible ingredient / component / feed / recycling routes. Column names that identify the AI-assisted columns use the prefix `ai_` in this repository.

| Result | Pairs |
|---|---|
| Still suggested 0 (`SUPPORTS_0_PENDING_HUMAN`) | 2,603 |
| Suggested back to 1 – potential use (`RESTORE_1_POTENTIAL_USE`) | 34 |
| Kept 1 – uncertain (`KEEP_1_UNCERTAIN_PENDING_HUMAN`) | 12 |

## Step 4 – AI-assisted review of the two human-review queues (`DV_Round_3_Uncertain_Review/`, `DV_Round_4_Other_Review/`)

Scope (frozen lists, no overlap, not re-sampled):

- **Uncertain queue:** original `dummy = 1` and `KEEP_1_UNCERTAIN_PENDING_HUMAN` – 52,419 pairs.
- **Classification / description / Other queue:** original `dummy = 1` and `KEEP_1_CLASSIFICATION_PENDING_HUMAN` – 1,621 pairs.
- Original 0s and `KEEP_1_PLAUSIBLE` rows were not touched in this step.

Method:

1. Read the real source files, verified them by SHA-256, and froze the target lists from the files themselves (counts recomputed, not copied from earlier notes).
2. Built code-level knowledge tables from the HS2002 working dictionary and general knowledge (species, fibres, materials, production stages, feed / recycling routes, "Other" residual subheadings with their sibling scope).
3. Generated a draft verdict per pair, in batches ordered by `(input_hs6, output_hs6, sample_id)`; **every batch was read row by row before being saved.**
4. During reading, three rule weaknesses were found and fixed (starch-saccharification route for flours, same-polymer filament yarns wrongly treated as different fibres, provisionally preserved goods → dried goods). All rows read before each fix were re-checked afterwards (63 rows changed).
5. Exported one workbook per stream per round, with a one-page Summary sheet and a notes sheet.

Verdict meaning (columns `review_dummy`, `review_status`, `issue_class`):

| Code | review_status | review_dummy | Meaning |
|---|---|---|---|
| Z | `EXCLUDE_0_PENDING_HUMAN` | 0 | Different species / fibre / material, no production route (`DIFF_SPECIES`, `DIFF_FIBRE`, `DIFF_MATERIAL`). Row is highlighted yellow. |
| P | `KEEP_1_POTENTIAL_USE` | 1 | A concrete processing / ingredient / feed / recycling route exists. |
| U | `KEEP_1_UNCERTAIN_PENDING_HUMAN` | 1 | Same material family but no direct route seen (`SIBLING_SPEC`) or opposite direction in the same production chain (`REVERSE_STAGE`); kept at 1 under the literal rule, awaiting one batch policy decision. |
| C | `KEEP_1_CLASSIFICATION_PENDING_HUMAN` | 1 | Code / classification problem (for example code 290400, which is not a valid HS2002 subheading); the code was not replaced. |

Results (all 54,040 targets reviewed; none skipped, none left unreviewed):

| Queue | Pairs | Z (0) | P | U | C |
|---|---|---|---|---|---|
| Uncertain | 52,419 | 30,856 | 4,840 | 16,723 | 0 |
| Classification / Other | 1,621 | 1,598 | 6 | 6 | 11 |
| **Total** | **54,040** | **32,454 (60%)** | **4,846 (9%)** | **16,729 (31%)** | **11** |

Per-round tables and examples: `Summary/Data_Cleaning_Summary.xlsx`, `Summary/Data_Cleaning_Report.md` and the `Round_k_Report.md` files.
Of the Z rows: 23,179 `DIFF_SPECIES`, 6,374 `DIFF_FIBRE`, 2,901 `DIFF_MATERIAL`. Of the U rows: 12,606 `SIBLING_SPEC`, 4,123 `REVERSE_STAGE`.

Knowledge basis is the HS2002 working dictionary plus general knowledge (`knowledge_basis = COMMON_KNOWLEDGE`); nothing was verified online (`source_url` is empty).

## Step 5 – Automated consistency checks (218 checks, all passed)

Run before the files were delivered:

- Source files (`Round_1–5` Review / Input / Manual, 20 files) unchanged (hash comparison).
- Target lists recomputed from the source files and compared with the frozen lists; no duplicate `sample_id` / `pair_id`; the two queues do not overlap; no original-0 or `KEEP_1_PLAUSIBLE` row is included.
- Every target has exactly one result; result status ↔ `review_dummy` consistent; every Z / P / U / C row has a specific reason field.
- Each workbook: header, row count, HS6 stored as text, no formulas or error values, yellow conditional format covering every data row down to the last row, 0/1 validation on `human_dummy`, frozen header and filter, neutral creator metadata, CSV mirror identical to the workbook.
- Totals: `T = H + R + N`, `R = Z + P + U + C`, `Q = Z + U + C` hold for every round and for the de-duplicated total.
- Rows with code 290400 keep their original code and are all classed C.

## Step 6 – Human review (in progress)

- The RA (August Liu) carried out a **preliminary manual review** of these workbooks.
- In this repository the column `human_review_status` was set to **`REVIEWED`** for every row that was previously `PENDING` or `AWAITING_USER_ACCEPTANCE`. Rows marked `NOT_REQUIRED` (the 59,075 `KEEP_1_PLAUSIBLE` rows) were left as they are.
- `human_dummy` (the final 0/1 human decision) and `human_notes` were **not** filled by anyone or anything in these files. **No row-level human 0/1 decisions are recorded yet.**
- The status change is applied to the copies in this repository only; the RA's local working files were not modified.

## Step 7 – Decisions needed from the professor

1. **U rows (16,729):** flip all `SIBLING_SPEC` / `REVERSE_STAGE` rows to 0 in bulk? Kept at 1 for now under the literal rule. If yes, only about 4,857 rows (P + C) would remain at 1 in these two queues; if no, 21,586 rows (40%) remain at 1.
2. **Flour / grits / flakes / root flour → glucose or fructose syrup** (68 rows): accept as a potential use? Currently P; germ, gluten, malt, legume flour and fruit flour are Z.
3. **Feed route** (about 600 rows): fish, crustaceans and molluscs as feed for farmed carnivorous fish / shrimp / crab – accept as potential use? Currently P.
4. **Fibre recycling of the same meltable polymer** (polyester, nylon, polypropylene; 199 rows): accept as a recycling route? Currently P.
5. **Provisionally preserved goods → dried goods** (35 rows): currently U; can be folded into decision 1.
6. **Code problems** (11 rows, e.g. 290400): someone must confirm the real code.

## Step 8 – Proposed next steps

- Draw a stratified random audit sample (about 100 Z, 50 P, 50 U, stratified by round and `issue_class`) and have it labelled by a human, to estimate how often the AI suggestions would be overturned; fix rule weaknesses found per rule tag.
- Apply the professor's policy decisions in bulk by `issue_class` / rule tag.
- Fill `human_dummy` (0/1) for the final dataset; only then compute agreement on the human-reviewed subset (this must not be called accuracy of all pairs).

## Not included in this repository

CSV mirrors of the workbooks, the full audit trail (frozen target lists, source snapshots, per-batch result files, about 200 MB) and the scripts are kept locally and can be added on request.
