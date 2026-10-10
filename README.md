# RoO_Dummy_Variable_Validation

This repository documents the AI-assisted validation of the rules-of-origin (RoO) input → output (IO) dummy variable in one PTA dataset (PTA_1, ASEAN–Japan, 115,764 HS2002 pairs) used for the ongoing paper *The Political Origins of Rules of Origin* by In Song Kim and Hao Zhang. It covers three completed review stages, a comparison with another RA's independent coding, the revised decision rule adopted on 2026-10-10, and the prompt for the next coding round. The `Round_1`–`Round_5` labels on the earlier workbooks refer to five fixed data batches, not validation stages.

## Current status (2026-10-10)

1. **Stages 1–3 are complete** under the original threshold ("only totally irrelevant pairs become 0"). Their workbooks are in this repository.
2. **External benchmark (2026-10-08).** A comparison with another RA's modular coding found two problems:
   - 57,117 initial "plausible" rows had been retained by chapter-level templates and never reviewed pair by pair.
   - The old threshold kept reverse-stage and same-family sibling pairs at 1.
3. **Revised rule V3 adopted (2026-10-10)** after Professor Zhang's confirmation. Sibling and backward pairs become 0; same-polymer melt recycling counts as a recycling route; the definition of input–output relations stays expansive.
4. **Next: V3 Round 1.** Codex (GPT-6 Sol Ultra) re-codes all 115,764 pairs with the [IO Pair Matching Prompt](prompts/IO_Pair_Matching_Prompt.md). Its output, `PTA_1_IO_DV_Uncertain_Validation_Round_1.xlsx`, is produced locally first and is not yet in this repository.

## Decision rule

Professor Zhang's rule:

> If input A could be potentially used to produce output B, then we should keep 1 there. Only when A and B are totally irrelevant should we change 1 to 0.

He added on 2026-10-09: *we still want to have an expansive definition of input-output relations.*

From V3 Round 1 onward, the rule is applied as a directional question ([full V3 rule](docs/REVISED_METHOD_V3.md)):

> Would a producer of B, in normal commercial practice, use A as a material, component, ingredient, processing input, feed, or recycled or recovered feedstock to make B?

- **Keep 1** for any such route, direct or indirect: `SAME_GOOD`, `RECYCLE` (including same-polymer melt recycling), `COMPONENT`, `FORWARD`, `INGREDIENT`, `FEED`, `RECONSTITUTE`.
- **Set 0** only for `SIBLING` (mutually exclusive goods in one family, e.g. men's suits → women's suits), `BACKWARD` (a later stage → an earlier stage, e.g. fabric → yarn) and `DIFFERENT_IDENTITY` (totally unrelated).
- **Keep 1 and flag** pairs that cannot be decided (`UNRESOLVED`) and code problems (`CODE_ISSUE`).
- Chapter or heading membership is never a reason by itself, either for 1 or for 0.

Stages 1–3 used the original threshold, under which reverse-stage and sibling pairs stayed at 1. Their results are kept as they are and are not relabelled.

All values here are **AI-assisted suggestions, not human confirmations**. A suggested `0` is a candidate for exclusion, not a confirmed deletion. A suggested `1` means only *not excluded*; it does not verify an actual production relationship. No final human 0/1 decisions or accuracy rate are recorded here.

## Workflow

| Stage | Model (reported setting) | Scope | Rule | Status |
|---|---|---:|---|---|
| 1. Initial screen | Codex, GPT-6.1 Sol, high reasoning | 115,764 | `EXPANSIVE_EXCLUSION_V2` | Done |
| 2. Re-review of selected queues | Claude Opus 5.5, Ultracode setting | 56,689 | Original threshold | Done |
| 3. Cross-check of Stage 2 | Codex, GPT-6.1 Sol, ultra reasoning | 56,689 | Original threshold | Done |
| External benchmark | Comparison with another RA's modular votes | 36,427 | — | Done (2026-10-08) |
| **V3 Round 1** | **Codex, GPT-6 Sol Ultra** | **115,764** | **V3** | **Next** |
| V3 checks | Comparison with previous values and the RA's modules; human check of a random sample | — | V3 | After Round 1 |

1. **Stage 1, Codex initial screen.** An automatic, repeatable rule-based screen of all 115,764 pairs in five fixed batches.
   - An initial `0` marks a candidate obvious mismatch.
   - An initial `1` means *not excluded*.
   - The 59,075 `KEEP_1_PLAUSIBLE` pairs were assigned by fixed templates: 57,117 by chapter-level templates, not pair by pair. Stages 2–3 did not re-review them (see the limitation in Step 2 of the [validation process](docs/VALIDATION_PROCESS.md)).
2. **Stage 2, Claude re-review.** Reviewed the 56,689 pairs in the initial candidate-0, Uncertain and Classification / Other queues. Proposed values and pair-specific explanations are in separate columns; the initial dummy is preserved.
3. **Stage 3, Codex cross-check.** Reassessed Claude's proposals and marked questionable rows orange in the `2.0` workbooks, with the concern in `second_round_reason`. It did not overwrite any value. An orange flag is a question for human adjudication, not a confirmed error.
4. **External benchmark.** Agreement with the other RA's final vote was 76.4%. Most disagreements came from M2 siblings (our value differed on 89% of its votes) and M5 backward chains (78%). Of those 5,286 disagreements:
   - 83% were never-reviewed template rows;
   - 14% were rows Claude tagged `SIBLING_SPEC` or `REVERSE_STAGE` but kept at 1 under the old threshold;
   - 3% had a concrete recycling, reconstitution or component route.

   The RA's modules also contain likely false 0s, so they serve as a regression test, not a gold standard. Agreement is not accuracy.
5. **V3 Round 1.** Codex, now using GPT-6 Sol Ultra, re-codes every pair under V3 and gives each row a `relation_type`. It does not see the previous values or the RA's votes until all values are frozen.
6. **V3 checks.** Proceed to the remaining data only if two conditions hold:
   - every remaining M2/M5 disagreement is a documented exception (`COMPONENT`, `RECYCLE` or `RECONSTITUTE`);
   - a human check of a random sample of the remaining disagreements finds no systematic error.

The model labels and reasoning settings are reported workflow settings; the workbook metadata does not independently record model versions. Full details: [validation process](docs/VALIDATION_PROCESS.md) and the [third-pass review report](Summary/Third_Pass_Review_Report.md).

## Repository layout

| Path | Content |
|---|---|
| `DV_Round_1_Validation/` | Stage 1 workbooks, one per data batch |
| `DV_Round_2_ZeroDV_Review/` | Stages 2–3 for the initial candidate-0 queue |
| `DV_Round_3_Uncertain_Review/` | Stages 2–3 for the Uncertain queue |
| `DV_Round_4_Other_Review/` | Stages 2–3 for the Classification / Other queue |
| `Summary/` | Stage 2 and Stage 3 summary reports |
| `docs/VALIDATION_PROCESS.md` | Full method, results, benchmark and next steps |
| `docs/REVISED_METHOD_V3.md` | The V3 decision rule |
| `prompts/IO_Pair_Matching_Prompt.md` | Prompt for V3 Round 1 |

The `DV_Round_2`–`DV_Round_4` directory names distinguish **source queues**, not independent validation stages.

## How to read the workbooks

**Stages 1–3**

- **Yellow** in the Claude-stage review marks a suggested 0. **Orange** in a `2.0` workbook marks a Codex concern, explained in `second_round_reason`; an orange row can be either 0 or 1.
- Use `sample_id` and `pair_id` to match records between stages. HS6 codes are text, so leading zeros are preserved.
- `human_dummy` accepts only 0 or 1. Fill it only with a human decision.

| `review_status` | Meaning |
|---|---|
| `EXCLUDE_0_PENDING_HUMAN` | AI suggests 0 (Z); needs human confirmation. |
| `KEEP_1_POTENTIAL_USE` | Keep 1; a concrete processing / ingredient / feed / recycling route exists (P). |
| `KEEP_1_UNCERTAIN_PENDING_HUMAN` | Keep 1; no direct route seen but not totally irrelevant (U). |
| `KEEP_1_CLASSIFICATION_PENDING_HUMAN` | Keep 1; code / classification problem (C). |

`P` means **potential use**, not the Classification / Other source queue; `C` marks a remaining classification issue. `human_review_status = REVIEWED` is preliminary workflow metadata, not a final manual label. `NOT_REQUIRED` applies to original `KEEP_1_PLAUSIBLE` rows outside the focused queue; it does not mean those rows were reviewed.

**V3 Round 1 workbook (once produced)**

- Every row has a `relation_type`, a `DV`, an `uncertain_status` and a pair-specific `reason`.
- Yellow rows are `DV = 0`; light-blue rows have `uncertain_status = 1`.
- `policy_flag` marks rows that depend on a policy decision, e.g. `POLYMER_MELT_RECYCLING` or the pending `FEED_ROUTE`.

## Copies and provenance

The earlier-stage files in this repository are copies. Compared with the local working files:

1. `human_review_status`: `PENDING` / `AWAITING_USER_ACCEPTANCE` → `REVIEWED` (56,689 rows in the five validation workbooks, 45,335 rows in zero-review Round_2–5, and all 54,040 target rows in the two queue folders; `NOT_REQUIRED` unchanged). Round_1 of the zero-review folder has no such column and is unchanged.
2. `DV_Round_2_ZeroDV_Review/`: AI-related column names and a few text values were made neutral (prefix `ai_`, reviewer value `AI_ASSISTED`); no judgements were changed.
3. The folder `DV_Round_1_Valdiation` is spelled `DV_Round_1_Validation` here.
4. No `human_dummy` value was written.

The `2.0` files preserve the local Codex cross-check snapshots. In particular, the Zero `2.0` files retain the original Claude-named review columns, whereas the earlier Zero repository copies use neutral `ai_` column names. This naming difference does not indicate a change in the proposed decisions.

## Not included

CSV mirrors of the workbooks, the full audit trail (frozen target lists, source snapshots, per-batch result files, about 200 MB) and the scripts are kept locally and can be added on request. The other RA's modular votes and the row-level comparison workbook are kept locally and are not published here. V3 Round 1 outputs are produced locally first.
