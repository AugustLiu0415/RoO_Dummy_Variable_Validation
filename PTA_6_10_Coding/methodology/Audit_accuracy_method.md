# Accuracy assessment of PTA 6–10: method of `07_audit.py` (2026-10-28)

## Sample and auditors

305 pairs drawn on 2026-10-26 (`07_audit.py build`), stratified by how the final code was reached: AI units by input
section (174), textile rules by rule (40), TUR_SGP HS2012 concordance pairs (30) and exact copies from PTA 2–5 and
ASEAN–Japan (61). Self-pairs, the textile pair sample and the 295 pairs of the PTA 2–5 audit are outside the frame.
The draw still matches the v2 final: the frame rebuilt from it gives the same 305 pairs and weights.

Two blind auditors code every pair with the 10-19 rules only (`Coding_Rules_2026_10_19.md`): Claude (8 blind agents,
done) and Codex (a new Codex chat, run by August). Bare "Other" subheadings carry their context, as in the Codex v2
inputs. August reviews every pair where the auditors disagree with each other or with the final DV.

## What is measured

- An item is correct when the final value equals the true value of the pair. The true value is August's mark (column
  `August_dv`: 1, 0 or unsure) where he gave one, and otherwise the final DV where both auditors agree with it.
- DV and DV_strict are both scored against the true DV. DV_strict therefore shows how often the certain-links-only
  variant is right; it is lower by design, because pairs left uncertain by rule (e.g. minor constituents of other
  fibres) are 0 in DV_strict and 1 under the rules.
- DV_excl_remelt is not scored: it differs from DV only on recycle_direct pairs, by definition. compare reports
  those items (20 in the sample) and how the auditors coded them.

## Weights

- Pairs: each stratum counts its pairs in the frame.
- Records: each record with an HS6 input counts once, split equally over the HS2002 pairs it maps to; TUR_SGP records
  coded on their HS2012 pair count for that pair. Own self-records (locked at 1) and the 2,273 TUR_SGP WO / any
  records are outside the frame. Within a stratum, sampled pairs are weighted by their records.
- The frame covers these shares of each agreement's HS6 records: TUR_SGP 85.7%, NIC_TWN 97.9%, CHL_KOR 98.3%,
  OMN_USA 99.6%, CAN_CHL 98.5%.
- By agreement, two figures:
  - `records_<PTA>` applies the stratum accuracies of all agreements to that agreement's records. It assumes a stratum
    is as accurate in every agreement.
  - `records_<PTA>_own_pairs` uses only the sampled pairs that occur in the agreement (TUR_SGP 58, NIC_TWN 109,
    CHL_KOR 167, OMN_USA 48, CAN_CHL 207 of 305). It is design-based and wider, and it drops strata with no such pair:
    for TUR_SGP the ASEAN–Japan copies (11% of its records) have none, and the PTA 2–5 copies (42%) have one.
- A record mapped to several pairs whose codes differ counts as the average of its pairs. This approximates its code,
  which is the maximum. It matters only for TUR_SGP, where 190 frame records are mixed (about 0.6 points).

## Intervals

95% Wilson interval with an effective sample size. The variance adds up the strata's variances, each computed from
the Jeffreys-smoothed share (x + 0.5) / (n + 1). A stratum where every sampled pair agrees, such as 38 of 38 PTA 2–5
copies (62% of the pair weight), therefore still carries uncertainty. The interval always contains the estimate.

In simulations on this sample, intervals were tested against a true value of 0.97–0.99 in the strata observed at
100%:
- Wilson intervals covered the true value in 94–99% of cases;
- per-stratum Jeffreys draws covered it in 93–97% of cases, but sometimes excluded the estimate;
- a plain bootstrap covered it in only 74–84% of cases.

## Review and scoring

- `compare` writes `audit/audit_review.xlsx`. Review items come first. The `August_dv` column accepts only 1, 0 or
  unsure. Marks are carried over by audit_id only when the row still holds the same pair.
- `score` refuses any other mark and warns when the sample's final codes changed since compare (`stale`).
- If review items are unsure or unmarked, score gives `complete: false` and a point estimate over the decided items,
  plus lower and upper bounds that count those items as wrong and as right.

## Review of the script (2026-10-28)

Three independent agents reviewed the code (statistics, record mapping, review workflow), and a skeptic checked each
finding. Fixed:
- intervals too narrow;
- record weights ignored within strata;
- agreement figures borrowed silently;
- unsure or unmarked items dropped, so that score gave 1.0 before any review;
- DV_excl_remelt scored against DV;
- marks on status-3 rows ignored;
- marks carried to another pair;
- mistyped marks accepted;
- stale check covered DV only;
- between-auditor figures unweighted and unlabelled.

Two findings were refuted: old-format marks, and auditor-file collisions; neither can occur here.
One reviewer wrote a scratch file (`pairw.pkl`) into the project folder; it was deleted.

## Results before August's review (compare, 2026-10-28 11:5x)

Auditors: Claude (8 blind agents) and Codex (new chat, 11:02–11:27). The Codex process was compliant:
- it read only the rules file, the pairs and its own file;
- it displayed every 20-row chunk before writing it;
- it re-displayed all dv = 1 rows in a self-review.

During that self-review Codex changed 4 rows from 0 to 1 (A011, A053, A077, A177) and reworded others. Both auditor
files pass the checker.

| | Claude | Codex |
|---|---|---|
| dv = 1 / dv = 0 | 165 / 140 | 196 / 109 |
| agrees with final DV, pair-weighted | 94.8% [90.9, 97.1] | 91.4% [84.9, 95.3] |
| agrees with final DV, record-weighted | 96.9% [92.1, 98.9] | 93.9% [87.1, 97.2] |

Between the auditors: 87.2% agree, κ 0.74 (unweighted). Weighted agreement is 92.4% by pairs and 95.0% by records.
In the PTA 2–5 audit the figures were 78% and κ 0.53.

**Final code vs the auditors, where the two auditors agree (266 of 305 items)**

| | DV | DV_strict |
|---|---|---|
| pair-weighted | 96.2% [91.8, 98.3] | 87.2% [78.2, 92.9] |
| record-weighted | 97.6% [92.1, 99.3] | 88.1% [77.8, 94.0] |
| TUR_SGP | 92.0% [85.3, 95.8] | 78.3% [69.5, 85.1] |
| TUR_SGP, own pairs only | 94.1% [44.0, 99.7], covers 88% | 81.5% [38.1, 96.9] |
| NIC_TWN | 97.2% [90.9, 99.2] | 89.4% |
| CHL_KOR | 97.5% [92.1, 99.2] | 88.2% |
| OMN_USA | 99.0% [92.4, 99.9] | 88.5% |
| CAN_CHL | 97.2% [92.0, 99.1] | 87.6% |

By family (DV, pair-weighted, consensus items):
- exact copies: 98.7% (57 items);
- AI units: 81.6% (143);
- textile rules: 77.6% (40);
- HS2012 concordance pairs: 88.5% (26).

**Review items for August: 79**

- 40 where both auditors agree but the final DV differs:
  - 21 are DV = 1 with uncertain = 1, where the two coders disagreed; both auditors say 0;
  - 9 are textile-rule 0s where both auditors say 1: worn clothing 6309 (5), rags 6310 (3), coated fabric 5901 → tyre cord fabric 5902 (1);
  - 2 are textile intermediate-sibling 1s → belting 5910;
  - 8 are other cases.
- 39 where the auditors disagree; in 35 of them Codex says 1 and Claude says 0.

Recycle_direct items in the sample: 20. Claude coded 10 of them as 1 and Codex 13.

## August's review, part 1: the 40 red items (2026-10-28 12:09)

The marks are backed up in `_work/coded/audit_review_August_marks_red_2026_10_28.xlsx`. August agreed with the two
auditors on 37 of the 40 items and with the final DV on 3 (A076, A215, A033, all final 0, auditors 1).

| group | n | August |
|---|---|---|
| AI units, DV = 1 with uncertain (coders disagreed) | 21 | all 0 |
| textile rules 0: yarn/fabric → worn clothing 6309 (5), fibre → rags 6310 (3), 5901 → tyre cord 5902 (1) | 9 | all 1 |
| textile intermediate sibling 1 → belting 5910 | 2 | both 0 |
| AI units / concordance, certain codes | 7 | 4 × 0, 3 kept final |
| exact copy A243 (polyester blend fabric → printed rayon fabric, sibling 1) | 1 | 0 |

Interim accuracy, from `07 score` with the 39 yellow items still unmarked (`complete: false`):

| | point estimate [95% interval] | lower – upper (yellow counted wrong – right) |
|---|---|---|
| DV, pair-weighted | 96.4% [91.9, 98.4] | 89.4 – 97.0 |
| DV, record-weighted | 97.7% [92.2, 99.4] | 93.0 – 98.0 |
| DV_strict, pair-weighted | 87.4% [78.3, 93.0] | 81.0 – 88.5 |
| DV_strict, record-weighted | 88.3% [77.9, 94.1] | 83.9 – 88.9 |
| DV by agreement (records) | TUR_SGP 93.6, NIC_TWN 97.5, CHL_KOR 97.6, OMN_USA 99.0, CAN_CHL 97.3 | TUR_SGP 85.3 – 94.7 |

What the review shows so far.
- Two coders that agree are almost always right: of the AI pairs coded with certainty, 48 of 48 final 0 and 53 of 56
  final 1 are correct. HS2012 concordance pairs: 7 of 7 and 15 of 16.
- Two coders that disagree are a coin flip: of the AI pairs left at 1 with uncertain = 1, 21 are truly 0, 18 truly 1,
  and 18 still have to be reviewed (yellow). DV counts the first group as errors and DV_strict counts the second.
  This is why DV and DV_strict bracket the truth.
- DV_strict errors also include pairs that are uncertain by rule but truly 1: 7 minor constituents of other fibres.
  This is the definition of DV_strict, not a coding error.
- The textile rules for worn clothing (6309) and rags (6310) set 0 where the auditors and August say 1. Two
  intermediate-sibling rule pairs into belting (5910) are 1 where they say 0. Both points go to the professor.

The A175 cell codex_reason in the review sheet was overwritten with "0" by hand (scoring unaffected; the next compare restores it from audit/audit_codex.csv). Chinese reading copy of the 40 red items: `_work/coded/audit_red40_zh.md`.

Correction (2026-10-28, on August's instruction): A076 and A215 changed from 0 to 1, to agree with both auditors
(backup before the change: `_work/coded/audit_review_before_A076_A215_fix_2026_10_28.xlsx`). The A175 codex_reason
cell was restored from audit/audit_codex.csv. August now agrees with the auditors on 39 of the 40 red items (A033
kept at the final 0). Interim score after the correction: DV 96.4% pair [91.9, 98.4], 97.7% record; TUR_SGP 93.3%;
DV_strict 87.4% / 88.3%; the other agreements are unchanged (both pairs are TUR_SGP concordance pairs).

## August's review, part 2: the yellow uncertain items (2026-10-28)

The 20 yellow items that are DV 1 with uncertain = 1, where the auditors disagree, were all marked 1 on August's
instruction. The note reads "不确定配对，判 1（报告教授）". A backup was taken first:
`_work/coded/audit_review_before_yellow_uncertain_2026_10_28.xlsx`. The other 19 yellow items are still unmarked.

The sample holds 62 uncertain pairs coded by the AI coders, including the HS2012 concordance pairs. Their true values
now stand at:
- 21 pairs are 0: both auditors said 0 and August marked 0 (red);
- 20 pairs are 1: the auditors disagree and August marked 1 (yellow);
- 21 pairs are 1: both auditors said 1.

Interim score, 19 items unmarked:

| | pair-weighted | record-weighted | TUR_SGP | bounds |
|---|---|---|---|---|
| DV | 96.7% [92.2, 98.6] | 97.8% | 94.3% | 91.1 – 97.0 (pair) |
| DV_strict | 86.2% [77.3, 92.0] | 87.7% | 76.1% | |

The Chinese workbook for the professor report is `不确定配对_中文对照_2026_10_28.xlsx` in the PTA6_10 folder. It has
four sheets:
- 说明 (notes);
- 不确定配对_判1 (20 pairs);
- 不确定配对_判0 (21 pairs);
- 全部复核79对 (all 79 review pairs).

## Final score (2026-10-28, review complete)

On August's instruction the remaining 19 yellow items (黄二 and 黄三) were all marked 1. A backup was taken first:
`_work/coded/audit_review_before_yellow_rest_2026_10_28.xlsx`. All 79 review items are now marked: 50 as 1 and 29
as 0. The report is `final/ai_audit_report.json`, with a copy at `_work/coded/ai_audit_report_final_2026_10_28.json`.

| | pair-weighted | record-weighted | TUR_SGP | NIC_TWN | CHL_KOR | OMN_USA | CAN_CHL |
|---|---|---|---|---|---|---|---|
| DV | 92.8% [86.5, 96.3] | 95.6% [89.1, 98.3] | 93.0 | 94.8 | 95.5 | 97.1 | 95.2 |
| DV_strict | 82.7% [73.4, 89.2] | 85.7% [75.2, 92.2] | 75.3 | 86.7 | 85.7 | 86.6 | 84.9 |

DV by source, pair-weighted:

| source | items | wrong | accuracy |
|---|---|---|---|
| exact copies | 61 | 4 | 94.5% |
| AI units | 174 | 29 | 82.9% |
| HS2012 concordance pairs | 30 | 5 | 83.3% |
| textile rules | 40 | 11 | 77.6% |

Sensitivity of the headline. Of the 19 items, 10 are 黄三: the final code is 0, Claude said 0, Codex said 1, and
August marked 1. Three of them are exact copies of PTA 1–5 codes: A064 and A201 from ASEAN–Japan, A285 from PTA 2–5.
Each copy carries a large stratum weight. With those 10 items:
- marked 1 (current): DV is 92.8% pair-weighted and 95.6% record-weighted;
- marked unsure: DV would be 96.8% and 98.0%;
- left at the final 0: DV would be 97.0% and 98.0%.

Chinese workbook: `不确定配对_中文对照_2026_10_28.xlsx`, built by `_work/07b_audit_zh_workbook.py` from
`_work/coded/audit_review_zh.json`. Its sheets are 说明, 最终准确率, 不确定配对_判1, 不确定配对_判0, 黄色其余19对 and
全部复核79对.
