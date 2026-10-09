# Three-stage dummy-variable review process

This document records how the RoO input→output (IO) dummy variable was screened and cross-checked in three AI-assisted stages: initial Codex screening, Claude re-review, and a Codex cross-check. It describes what each stage did, what it produced, and what has **not** been done yet.

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

## Step 2 – Codex initial rule-based screening of every pair (`Round_k_Review`)

Rule set `EXPANSIVE_EXCLUSION_V2`, implemented as a script (`v2_screen.py`, kept locally). It assigned each pair one status:

1. **Candidate 0 (`EXCLUDE_0_PENDING_HUMAN`):** a narrow list of identity contradictions, for example two different named raw fruits, grains, oilseeds, spices, pure plant oils or log species, or a different-species herbivore meat. Entries whose classification involves an "Other" residual subheading were not excluded automatically.
2. **`KEEP_1_PLAUSIBLE`:** the pair matched one of the script's fixed templates (the ten that produced rows are listed below).
3. **`KEEP_1_UNCERTAIN_PENDING_HUMAN` / `KEEP_1_CLASSIFICATION_PENDING_HUMAN`:** every other pair, or a pair with a missing description or a boundary-affecting residual subheading.

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

### How the 59,075 `KEEP_1_PLAUSIBLE` rows were assigned

Two templates are pair-specific. The other eight are **chapter-level templates**: every pair whose input and output chapters fall in the listed block received the same retention sentence, whatever the specific products.

| Template (input → output) | Retention sentence (paraphrased) | Pairs |
|---|---|---:|
| Identical six-digit code | Same good; can be further processed, repacked or remade | 1,830 |
| Live animal (ch. 01) → meat of the same species (ch. 02) | Rearing and slaughter | 128 |
| Ch. 50–60, 62–63 → ch. 56–60, 62–63 | Textile, cutting, coating, recycling or garment-remaking material | 29,489 |
| Ch. 72–73 → ch. 72–73 | Can be smelted, rolled, processed or used as a component | 21,208 |
| Food chapters → ch. 16, 19, 20, 21, 22 (subset) | Seasoning, ingredient or reprocessing input | 4,038 |
| Ch. 71 → ch. 71 | Precious-metal recovery, processing or assembly | 832 |
| Ch. 64 → ch. 64 | Footwear part, repair or remaking material | 812 |
| Ch. 44 → ch. 44, 46, 94 | Wood-processing, furniture or plaiting material | 400 |
| Ch. 94 → ch. 94 | Dismantling, refurbishing or remaking | 286 |
| Ch. 91 → ch. 91 | Clock-part remaking or assembly | 52 |
| **Total** | | **59,075** |

**Limitation (identified 2026-10-08).** The 57,117 rows from the chapter-level templates were not judged pair by pair. For example, 721931 cold-rolled stainless steel → 720260 ferro-nickel and 620333 men's jackets → 620431 women's jackets were both retained at 1. The Round 1 task instructions prohibited "same-chapter automatic 1" and broad chapter or keyword rules. The script did not follow that instruction, and the deviation was not detected at the time. Stages 2 and 3 reviewed only the three selected queues, so these rows have never been reviewed individually. Treat their `dummy = 1` as unreviewed, not as a confirmed plausible use.

## Step 3 – Claude re-review of the 2,649 candidate 0s (`DV_Round_2_ZeroDV_Review/`)

Every original candidate 0 was re-checked against both product definitions and against possible ingredient / component / feed / recycling routes. Claude recorded a proposed value and explanation without overwriting the initial dummy. Column names that identify the AI-assisted columns use the prefix `ai_` in the earlier repository copies; the later `2.0` snapshots preserve their original Claude-named columns.

| Result | Pairs |
|---|---|
| Still suggested 0 (`SUPPORTS_0_PENDING_HUMAN`) | 2,603 |
| Suggested back to 1 – potential use (`RESTORE_1_POTENTIAL_USE`) | 34 |
| Kept 1 – uncertain (`KEEP_1_UNCERTAIN_PENDING_HUMAN`) | 12 |

## Step 4 – Claude re-review of the two human-review queues (`DV_Round_3_Uncertain_Review/`, `DV_Round_4_Other_Review/`)

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

## Step 5 – Codex cross-check of Claude's proposals (third AI-assisted stage)

Codex re-examined Claude's proposed values and explanations in all three selected queues. It marked questionable rows orange and wrote a specific `second_round_reason` for each orange row in fifteen `2.0` workbooks (five for initial zeros, five for Uncertain and five for Classification / Other). The cross-check did **not** change the initial dummy or Claude's proposed 0/1 value or status. An orange flag is a question for manual adjudication, not a confirmed wrong dummy value.

| Original source queue | Pairs checked | Claude suggests 0 | Claude retains 1 | Orange flags | Orange among 0 | Orange among 1 |
|---|---:|---:|---:|---:|---:|---:|
| Initial candidate 0 | 2,649 | 2,603 | 46 | 69 | 69 | 0 |
| Uncertain | 52,419 | 30,856 | 21,563 | 3,327 | 3,086 | 241 |
| Classification / Other | 1,621 | 1,598 | 23 | 86 | 86 | 0 |
| **All selected queues** | **56,689** | **35,057** | **21,632** | **3,482** | **3,241** | **241** |

Thus the two original Uncertain / Other queues account for **3,413** orange rows. Their original `dummy = 1` remains in the source workbooks. Claude proposed 32,454 candidate zeros in those queues, so these decisions could materially change the final dataset if a human confirms them under the professor's rule. The separate [`Third_Pass_Review_Report.md`](../Summary/Third_Pass_Review_Report.md) gives round-level counts and workbook locations.

The directory names `DV_Round_2`, `DV_Round_3` and `DV_Round_4` identify different source queues and processing folders; they do not imply four independent validation stages. `P` in `review_status` means potential use, not the Classification / Other source queue; `C` identifies a remaining code or classification issue.

## Step 6 – Automated consistency checks of the Claude-stage outputs (218 checks, all passed)

Run before the Claude-stage files were delivered; this historical 218-check result does not by itself validate the new `2.0` files:

- Source files (`Round_1–5` Review / Input / Manual, 20 files) unchanged (hash comparison).
- Target lists recomputed from the source files and compared with the frozen lists; no duplicate `sample_id` / `pair_id`; the two queues do not overlap; no original-0 or `KEEP_1_PLAUSIBLE` row is included.
- Every target has exactly one result; result status ↔ `review_dummy` consistent; every Z / P / U / C row has a specific reason field.
- Each workbook: header, row count, HS6 stored as text, no formulas or error values, yellow conditional format covering every data row down to the last row, 0/1 validation on `human_dummy`, frozen header and filter, neutral creator metadata, CSV mirror identical to the workbook.
- Totals: `T = H + R + N`, `R = Z + P + U + C`, `Q = Z + U + C` hold for every round and for the de-duplicated total.
- Rows with code 290400 keep their original code and are all classed C.

## Step 7 – Human review (in progress)

- Repository copies were marked as **preliminarily reviewed for workflow tracking**. This does not document an independent human 0/1 judgement for each row. The later orange flags remain to be adjudicated.
- In this repository the column `human_review_status` was set to **`REVIEWED`** for every row that was previously `PENDING` or `AWAITING_USER_ACCEPTANCE`. Rows marked `NOT_REQUIRED` (the 59,075 `KEEP_1_PLAUSIBLE` rows) were left as they are.
- `human_dummy` (the final 0/1 human decision) and `human_notes` were **not** filled by anyone or anything in these files. **No row-level human 0/1 decisions are recorded yet.** `human_review_status = REVIEWED` alone must not be used as a ground-truth label or an accuracy denominator.
- The status change is applied to the copies in this repository only; the RA's local working files were not modified.

## Step 8 – Decisions needed from the professor

1. **Manual review scope:** the professor asked for manual checks of remaining uncertain and excluded pairs and an accuracy rate. Given the 3,482 orange flags and larger unflagged population, determine whether to review all candidate exclusions and unresolved cases or adjudicate every orange flag plus an approved stratified sample of unflagged cases. An orange-only review cannot estimate overall accuracy.
2. **U rows (16,729):** these remain at 1 under the expansive rule unless a pair is shown to be totally unrelated. Do not flip a whole issue class to 0 solely because no direct route was found.
3. **Flour / grits / flakes / root flour → glucose or fructose syrup** (68 rows): accept as a potential use? Currently P; germ, gluten, malt, legume flour and fruit flour are Z.
4. **Feed route** (about 600 rows): fish, crustaceans and molluscs as feed for farmed carnivorous fish / shrimp / crab – accept as potential use? Currently P.
5. **Fibre recycling of the same meltable polymer** (polyester, nylon, polypropylene; 199 rows): accept as a recycling route? Currently P.
6. **Provisionally preserved goods → dried goods** (35 rows): currently U; review under the expansive rule.
7. **Code problems** (11 rows, e.g. 290400): someone must confirm the real code.

## Step 9 – Proposed next steps

- Prioritize manual adjudication of the 69 flagged initial-zero pairs and 3,413 flagged Uncertain / Other pairs, especially proposed zeros with a possible indirect production or feed route and Classification / Other boundary cases.
- Agree with the professor on the remaining manual review coverage. If sampling is used, define the random/stratified population and denominator before reporting an accuracy estimate; do not infer whole-dataset accuracy from targeted orange flags alone.
- Record final human decisions in `human_dummy`, then compute confirmation or disagreement rates separately for proposed 0 and retained 1 on the human-reviewed population. Do not call the AI proposals final dummy values before adjudication.

## Not included in this repository

CSV mirrors of the workbooks, the full audit trail (frozen target lists, source snapshots, per-batch result files, about 200 MB) and the scripts are kept locally and can be added on request.
