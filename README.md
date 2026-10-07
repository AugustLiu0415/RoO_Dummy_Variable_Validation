# RoO_Dummy_Variable_Validation

This repository documents three AI-assisted validation stages for the rules-of-origin (RoO) input → output (IO) dummy variable in one PTA dataset used for the ongoing paper *The Political Origins of Rules of Origin* by In Song Kim and Hao Zhang. The `Round_1`–`Round_5` labels refer to five fixed data batches, not five validation stages.

## Validation rule

> If input A could be potentially used to produce output B, then we should keep 1 there. Only when A and B are totally irrelevant should we change 1 to 0.

These are **AI-assisted suggestions, not human confirmations**. A suggested `0` is a candidate for exclusion, not a confirmed deletion. A suggested `1`, even with a plausible pathway, means only *not excluded*; it does not verify an actual production relationship. No final human 0/1 decisions or accuracy rate are recorded here.

The [validation process](docs/VALIDATION_PROCESS.md) gives the full method and results. The [third-pass review report](Summary/Third_Pass_Review_Report.md) gives the latest cross-check counts.

## Three review stages

1. **Codex initial screen (Stage 1; GPT-6.1 Sol, high reasoning):** Apply an automatic, repeatable rule-based screen to all 115,764 pairs in five fixed batches. An initial `1` means *not excluded*, including uncertain and classification-related pairs. An initial `0` marks a candidate obvious mismatch awaiting human confirmation.
2. **Claude first re-review (Stage 2; Claude Opus 5.5, Ultracode setting):** Review all 56,689 pairs from the initial candidate-0, Uncertain, and Classification / Other queues. Record a proposed dummy value and pair-specific explanation in separate review columns while preserving the initial dummy value. In the Claude review workbooks, yellow marks a proposed `0` requiring human confirmation; unresolved Uncertain or Classification cases can remain at `1` with a pending-review status.
3. **Codex second re-review (Stage 3; GPT-6.1 Sol, ultra reasoning):** Reassess Claude's proposed values and explanations. Mark questionable rows orange in the `2.0` workbooks and explain each concern in `second_round_reason`. An orange flag is a question for human adjudication, not a confirmed error. This stage did not overwrite the initial dummy or Claude's proposed 0/1 value.

The model labels and reasoning settings above are reported workflow settings; the workbook metadata does not independently record model versions.

The directory names `DV_Round_2_ZeroDV_Review`, `DV_Round_3_Uncertain_Review`, and `DV_Round_4_Other_Review` distinguish **source queues**. They are not the number of independent validation stages.

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
