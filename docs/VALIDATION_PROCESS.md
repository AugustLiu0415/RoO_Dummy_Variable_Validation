# Three-stage dummy-variable review process

This document records how the RoO input→output (IO) dummy variable was screened and cross-checked in three AI-assisted stages: initial Codex screening, Claude re-review, and a Codex cross-check. It describes what each stage did, what it produced, and what has **not** been done yet. Steps 8–11 add an external benchmark against another RA's modular coding, the revised decision rule V3 adopted on 2026-10-10, and the plan for V3 Round 1 (status as of 2026-10-10).

**Guiding rule (Professor Hao Zhang):**
*If input A could be potentially used to produce output B, then we should keep 1 there. Only when A and B are totally irrelevant should we change 1 to 0.*

The first half of the rule is directional (A used to produce B). Stages 1–3 operationalized the threshold for 0 as "A and B are totally irrelevant", which is not directional: yarn and fabric are related in both directions, so fabric → yarn stayed at 1 just like yarn → fabric. Step 8 shows that this, together with an unreviewed block of Round 1 rows, explains most disagreements with the external benchmark. Step 9 and [`REVISED_METHOD_V3.md`](REVISED_METHOD_V3.md) give the fix, which the professor confirmed on 2026-10-10.

**Professor Zhang's reminder (2026-10-09):** *we still want to have an expansive definition of input-output relations.* V3 therefore sets only sibling and backward pairs to 0 in addition to totally unrelated pairs; every other real route, direct or indirect, still counts as 1.

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

**Limitation (identified 2026-10-08).** The 57,117 rows from the chapter-level templates were not judged pair by pair. For example, 721931 cold-rolled stainless steel → 720260 ferro-nickel and 620333 men's jackets → 620431 women's jackets were both retained at 1. The Round 1 task instructions prohibited "same-chapter automatic 1" and broad chapter or keyword rules. The script did not follow that instruction, and the deviation was not detected until the external comparison in Step 8. Stages 2 and 3 reviewed only the three selected queues, so these rows have never been reviewed individually. Treat their `dummy = 1` as unreviewed, not as a confirmed plausible use.

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

In `SIBLING_SPEC` and `REVERSE_STAGE` rows, Claude's own explanation usually states that A cannot be made into B. The rows stayed at 1 only because the pair was not "totally irrelevant". These are the rows the revised rule in Step 9 addresses.

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

The cross-check covered only the 56,689 selected-queue pairs. The 59,075 `KEEP_1_PLAUSIBLE` pairs from Step 2 were outside its scope.

The directory names `DV_Round_2`, `DV_Round_3` and `DV_Round_4` identify different source queues and processing folders; they do not imply four independent validation stages. `P` in `review_status` means potential use, not the Classification / Other source queue; `C` identifies a remaining code or classification issue.

## Step 6 – Automated consistency checks of the Claude-stage outputs (218 checks, all passed)

Run before the Claude-stage files were delivered; this historical 218-check result does not by itself validate the new `2.0` files:

- Source files (`Round_1–5` Review / Input / Manual, 20 files) unchanged (hash comparison).
- Target lists recomputed from the source files and compared with the frozen lists; no duplicate `sample_id` / `pair_id`; the two queues do not overlap; no original-0 or `KEEP_1_PLAUSIBLE` row is included.
- Every target has exactly one result; result status ↔ `review_dummy` consistent; every Z / P / U / C row has a specific reason field.
- Each workbook: header, row count, HS6 stored as text, no formulas or error values, yellow conditional format covering every data row down to the last row, 0/1 validation on `human_dummy`, frozen header and filter, neutral creator metadata, CSV mirror identical to the workbook.
- Totals: `T = H + R + N`, `R = Z + P + U + C`, `Q = Z + U + C` hold for every round and for the de-duplicated total.
- Rows with code 290400 keep their original code and are all classed C.

These checks verify file integrity and internal consistency. They do not test whether a reason is specific to its pair, so they could not detect the chapter-level templates in Step 2. The revised method adds a template audit (see [`REVISED_METHOD_V3.md`](REVISED_METHOD_V3.md)).

## Step 7 – Human review (in progress)

- Repository copies were marked as **preliminarily reviewed for workflow tracking**. This does not document an independent human 0/1 judgement for each row. The later orange flags remain to be adjudicated.
- In this repository the column `human_review_status` was set to **`REVIEWED`** for every row that was previously `PENDING` or `AWAITING_USER_ACCEPTANCE`. Rows marked `NOT_REQUIRED` (the 59,075 `KEEP_1_PLAUSIBLE` rows) were left as they are. `NOT_REQUIRED` means "outside the focused queue"; it does not mean the row was reviewed (see the limitation in Step 2).
- `human_dummy` (the final 0/1 human decision) and `human_notes` were **not** filled by anyone or anything in these files. **No row-level human 0/1 decisions are recorded yet.** `human_review_status = REVIEWED` alone must not be used as a ground-truth label or an accuracy denominator.
- The status change is applied to the copies in this repository only; the RA's local working files were not modified.

## Step 8 – External benchmark: comparison with another RA's modular votes (2026-10-08)

Professor Zhang shared a second coding of the same ASEAN–JPN pairs, made independently by another RA with a modular rule approach. Each module casts only one kind of vote (only 1 or only 0) when strict criteria are met, and most pairs receive no vote. When modules conflict, M6 overrides M0 and M4. The RA's file contains 36,427 voted pairs in HS2002. All of them matched our pairs on `input_hs6 + output_hs6`. **The RA's data are not included in this repository.**

On our side, the comparison uses Claude's proposed value (`round_3_DV`, which carries the Round 2 value forward) for the 56,689 re-reviewed pairs, and the Round 1 Codex value otherwise. Agreement here means agreement between two codings, not accuracy; neither side is a human label.

| Module | Rule (RA's description, abridged) | Vote | Pairs voted | Our value differs | Share |
|---|---|:-:|---:|---:|---:|
| M0 depth | Pair spans two chapters, or is the identical code | 1 | 15,651 | 4,209 | 26.9% |
| M1 parts | Input described as a part of the output | 1 | 126 | 5 | 4.0% |
| M2 siblings | Two mutually exclusive, relatively finished goods with the same substantive description | 0 | 1,344 | 1,199 | 89.2% |
| M3 raw to processed | Raw input and processed output of the same product within one heading | 1 | 3 | 0 | 0% |
| M4 forward chains | Pre-set list of production steps | 1 | 4,272 | 1,076 | 25.2% |
| M5 backward chains | Output is an earlier stage of an M4 chain (correcting for recycling) | 0 | 5,244 | 4,087 | 77.9% |
| M6 animals | Different specific animals, none in common | 0 | 10,778 | 622 | 5.8% |
| M7 vegetables | Not in the RA's documentation; by its name, different specific vegetables | 0 | 2,386 | 210 | 8.8% |

Overall agreement with the RA's final vote is **76.4%** (27,830 / 36,427).

- **RA 0, ours 1 (6,118 pairs):** M2 and M5 account for 5,286 (86%).
- **RA 1, ours 0 (2,479 pairs):** 2,427 are cross-chapter pairs, which M0 votes 1 automatically (2,184 rest on M0 alone). M0 is itself a blanket rule, comparable to the chapter-level templates in Step 2.

### Why M2 and M5 disagree with us

| Cause | M2 | M5 | Total |
|---|---:|---:|---:|
| A. Step 2 chapter-level template, never reviewed | 1,137 | 3,243 | 4,380 (83%) |
| B. Claude tagged `SIBLING_SPEC` / `REVERSE_STAGE` but kept 1 under the "totally irrelevant" threshold | 59 | 706 | 765 (14%) |
| C. Claude recorded a concrete route (same-polymer melt recycling, milk reconstitution, yarn waste → garnetted stock, refill → pen) | 3 | 138 | 141 (3%) |
| **Total** | **1,199** | **4,087** | **5,286** |

Cause A comes from the textile template (610), the footwear template (434) and the furniture template (93) for M2. For M5, all 3,243 come from the steel template, for example flat-rolled or bar steel → ferro-alloys, pig iron or iron powders. In cause B, Claude's explanation agrees with the RA in substance (A cannot be made into B); only the threshold differs. Example: 540720 woven synthetic filament fabric → 540261 nylon filament yarn.

Causes A and B need different fixes, and neither works alone. Re-reviewing the template rows under the old threshold would not change agreement, because Claude would tag them `SIBLING_SPEC` / `REVERSE_STAGE` and keep 1. Estimated on the 36,427 benchmark pairs:

| Change | Agreement |
|---|---:|
| None | 76.4% |
| Re-review template rows only | 76.4% |
| Change the threshold only (reviewed `SIBLING_SPEC` / `REVERSE_STAGE` → 0) | 78.5% |
| Both (parts → product kept at 1) | about 90.5% |

The last row assumes re-reviewed template rows in M2/M5 become 0 except for documented exceptions. It is an estimate, not the result of a re-run.

The problem is larger than the benchmark shows. The RA voted on only 17,475 of the 59,075 `KEEP_1_PLAUSIBLE` pairs. For example, chapter 62 → chapter 62 has 12,980 template rows, of which M2 voted on 486.

### Possible false 0s in the RA's modules

These are our judgements and need checking. They show that the modules should be used as a regression test, not as a gold standard.

- **M2:** 640699 parts of footwear → footwear (17 pairs). The UN short description "Footwear; of materials n.e.s. in heading no. 6406" omits "parts".
- **M2:** 960860 ball-point refills and 960891 nibs → pens (6 pairs).
- **M5:** 0402 milk powder and 0405 milk fat → 0401 recombined milk or cream (24 pairs).
- **M5:** wool yarn → 510400 garnetted stock, which is a recovered-fibre heading (6 pairs).
- **Policy questions:** same-polymer melt recycling, fabric or yarn → filament or staple fibre (111 benchmark pairs); carding of wool-yarn waste → 5105 (6 pairs).

The comparison also exposed an inconsistency in Claude's review: 0402 → 0401 was classed as potential use (reconstitution), but 0405 → 0401 as `REVERSE_STAGE`. The revised method treats both as reconstitution.

## Step 9 – Revised decision rule (V3, adopted 2026-10-10)

Full text: [`REVISED_METHOD_V3.md`](REVISED_METHOD_V3.md). Prompt for applying it: [`IO_Pair_Matching_Prompt.md`](../prompts/IO_Pair_Matching_Prompt.md). In short:

1. Replace the relevance test with a directional input test: *would a producer of B, in normal commercial practice, use A as a material, component, ingredient, processing input, feed, or recycled or recovered feedstock to make B?* Direct and indirect uses both count.
2. Two explicit 0 classes are added: `SIBLING` (mutually exclusive finished goods or same-stage specifications in one family) and `BACKWARD` (A is a later stage than B on the same production chain). Totally unrelated pairs (`DIFFERENT_IDENTITY`) remain 0.
3. Routes that keep 1 are listed explicitly: `SAME_GOOD`, `RECYCLE` (including same-polymer melt recycling), `COMPONENT`, `FORWARD`, `INGREDIENT`, `FEED`, `RECONSTITUTE`. Undecidable pairs stay at 1 as `UNRESOLVED`.
4. Every row carries a `relation_type`; the dummy follows mechanically from it. Rows that depend on a policy decision carry a `policy_flag`.
5. The prompt provides stage ladders and a recycling-sink list, extending the RA's 36 pre-set linkages.
6. Chapter-level templates are forbidden and audited for.

## Step 10 – Decisions

**Confirmed on 2026-10-10:**

1. **Directional test (Step 9):** `SIBLING` and `BACKWARD` pairs are set to 0, with components, recycling routes and reconstitution kept at 1. This affects the 16,729 U rows (12,606 `SIBLING_SPEC`, 4,123 `REVERSE_STAGE`) and part of the 57,117 template rows. U rows are re-mapped one by one through the exceptions, not flipped to 0 as a class.
2. **Fibre recycling of the same meltable polymer** (polyester, nylon, polypropylene; 199 rows in the full table, 111 in the benchmark) counts as a recycling route (`RECYCLE`, `policy_flag = POLYMER_MELT_RECYCLING`).

**Still open.** Items 3 and 5–7 keep 1 under the expansive definition and carry a `policy_flag` in V3 Round 1, so they can be recoded if the professor rules otherwise.

3. **Carding of wool-yarn waste → carded wool (5105)** (6 benchmark pairs): accept as a recycling route? (`WOOL_WASTE_CARDING`)
4. **Manual review scope:** the professor asked for manual checks of remaining uncertain and excluded pairs and an accuracy rate. Determine whether to review all candidate exclusions and unresolved cases or adjudicate a defined set of flags plus an approved stratified sample of unflagged cases. A flag-only review cannot estimate overall accuracy.
5. **Flour / grits / flakes / root flour → glucose or fructose syrup** (68 rows): accept as a potential use? Currently P; germ, gluten, malt, legume flour and fruit flour are Z. (`FLOUR_TO_SYRUP`)
6. **Feed route** (about 600 rows): fish, crustaceans and molluscs as feed for farmed carnivorous fish / shrimp / crab – accept as potential use? Currently P. (`FEED_ROUTE`)
7. **Provisionally preserved goods → dried goods** (35 rows): currently U. (`PRESERVED_TO_DRIED`)
8. **Code problems** (11 rows, e.g. 290400): someone must confirm the real code.

## Step 11 – Next steps

1. **Done (2026-10-10):** professor's decisions on items 1–2 of Step 10; V3 prompt written ([`IO_Pair_Matching_Prompt.md`](../prompts/IO_Pair_Matching_Prompt.md)).
2. **V3 Round 1:** Codex, now using **GPT-6 Sol Ultra** (Stages 1 and 3 used GPT-6.1 Sol), re-codes all 115,764 PTA_1 pairs under V3 so that every row carries a `relation_type`. Particular attention goes to the 57,117 template rows and the 16,729 U rows. Codex sees the previous values and the RA's votes only after all V3 values are frozen. Output: `PTA_1_IO_DV_Uncertain_Validation_Round_1.xlsx`, with a CSV mirror and a report, produced locally in `Dummy_Variable/PTA_1/`.
3. Write a new report for the professor and compare the new values with the previous values and with the RA's modules, module by module. Proceed only if both acceptance checks hold:
   - (a) every remaining M2/M5 disagreement falls in a documented exception (`COMPONENT`, `RECYCLE`, `RECONSTITUTE`);
   - (b) a human-checked random sample of 100 remaining disagreements (seed 20261010) shows no systematic error.

   Report the RA module blind spots back to the RA.
4. If both conditions hold, freeze the procedure and apply it to the remaining data.
5. Human adjudication: the Stage 3 orange flags refer to the old-threshold proposals. After the V3 re-run, re-derive the human-review queue rather than reusing the flags directly. If sampling is used, define the random or stratified population and denominator before reporting an accuracy estimate.
6. Record final human decisions in `human_dummy`, then compute confirmation or disagreement rates separately for proposed 0 and retained 1 on the human-reviewed population. Do not call the AI proposals final dummy values before adjudication.

## Not included in this repository

CSV mirrors of the workbooks, the full audit trail (frozen target lists, source snapshots, per-batch result files, about 200 MB) and the scripts are kept locally and can be added on request. The other RA's modular votes and the row-level comparison workbook are kept locally and are not published here.
