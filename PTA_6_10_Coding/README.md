# PTA 6–10 input–output coding (25 October – 1 November 2026)

Five more agreements were coded under the general coding workflow: Turkey–Singapore (HS2012), Nicaragua–Taiwan,
Chile–Korea, Oman–US and Canada–Chile. Pairs already coded in PTA 1–5 were copied, so a pair has the same code in
every agreement. The new pairs were coded by two AI coders, the textile rules and the conventions that Professor Zhang
set on 28–30 October 2026; he settled the remaining points on 1 November 2026. The result is version `2026_11_01`:
the codes of 31 October, without the variable DV_strict.

This folder holds the updated workflow, the methodology and the aggregate results. The row-level coded files (one
Stata file per agreement) are kept locally and are not published here.

## What changed in the workflow (28 October – 1 November 2026)

- **Decision rule.** DV is the main variable (Professor Zhang, 1 November). Following his overall principle, a known
  link is 1; a link that is technically possible but unconfirmed is 1 with `uncertain = 1`; a pair is 0 only on clear
  evidence (impossible, reverse direction, or no specific route). DV_strict is no longer computed and has been dropped
  from the files.
- **Scope.** The new conventions apply to the pairs newly coded in PTA 6–10 and to all later agreements. Codes
  delivered for PTA 1–5 are not re-judged, and pairs copied from them keep their codes. At the next reissue of the
  PTA 1–5 files, DV_strict is dropped from them and the blended fabrics that share a minor fibre get `uncertain = 1`.
- **Conventions** (Professor Zhang's questionnaire answers): process inputs; same-material intermediates (parts,
  metal articles, chemicals of one heading); direct remelting in three levels (own upstream form 1, another form of the
  same material 1 with uncertainty, a finished product 0; vulcanised rubber 0; plastics only the same polymer); complete
  machines inside other goods; waste routes; cut or refitted goods; minerals; food ingredients; size and direction;
  blended fabrics; chapter 59.
- **Meeting of 28 October.** One-sided 1s that both model families find clearly invalid are 0 (two-family screen);
  rows whose input is "WO" or "any" are deleted; the HS concordance will follow the project's conversion package.
- **Decisions of 1 November.** The convention on complete machines is not applied to pairs both coders coded 0 (no
  re-review). In the screen, a chemical stays 1 with uncertainty whenever a specific role can be named. Confirmed as
  coded: non-meltable plastics 0; rubbers in primary forms only the same polymer; "other plastics" a polymer of its own;
  no laminate route between different plastics; vulcanised rubber crumb as an ingredient 1 with uncertainty; for metal
  articles, the same-material rule takes precedence over the remelting levels.
- **AI coders.** From PTA 11 on, each coder also says whether a 1 is a *known* or only a *possible* link.

The full rules are in the workflow PDF and, as given to the coders, in
[`methodology/Coding_Rules_2026_10_30.md`](methodology/Coding_Rules_2026_10_30.md) (section I.9).

## Contents

| Path | Contents |
|---|---|
| [`workflow/RoO_coding_workflow_2026_11_01.pdf`](workflow/RoO_coding_workflow_2026_11_01.pdf) | General coding rules: decision rule, steps 1–7, worked examples and a summary of the conventions with the date each was set (`.html` is the source). Replaces the workflow of 19 October |
| [`methodology/Coding_Rules_2026_10_30.md`](methodology/Coding_Rules_2026_10_30.md) | Rules given to the AI coders, screeners and auditors (19 October rules plus section I.9, updated 1 November) |
| [`methodology/AI_Coder_Codebook.md`](methodology/AI_Coder_Codebook.md) | Codebook used by the AI coders for PTA 6–10 |
| [`methodology/Audit_accuracy_method.md`](methodology/Audit_accuracy_method.md) | How the audit sample is drawn and weighted, and how accuracy is estimated |
| [`methodology/prompts/`](methodology/prompts/) | Prompts for AI coder 2 (Codex), the independent AI audit, the screen of one-sided 1s and the rescue screen |
| [`methodology/scripts/`](methodology/scripts/) | Pipeline scripts (order below) |
| [`results/Results_PTA_6_10_2026_11_01.pdf`](results/Results_PTA_6_10_2026_11_01.pdf) | Result report: main results, uncertain pairs, coding methods, reliability, revisions, decisions of 1 November |
| [`results/Variables_PTA_6_10_2026_11_01.pdf`](results/Variables_PTA_6_10_2026_11_01.pdf) | Variables of the coded files and the values of each categorical variable |
| [`results/summary/`](results/summary/) | Aggregate figures: `summary_by_pta.csv` and the JSON reports of the pipeline (coder agreement, policies, screen, AI audit) |

## Pipeline

1. `01_intake.py`: read the agreements, map HS2012 to HS2002 (UN correlation table), build the pair master list.
2. `02_copy_and_rules.py` with `textile.py`: copy pairs already coded in PTA 1–5, lock self-pairs, apply the textile rules.
3. `05_build_coder_inputs.py`, `05b_build_concord_pairs.py`, `05c_enrich_other_texts.py`: build heading-pair units, the blind textile sample and the HS2012 pairs for the two AI coders.
4. `04_check_coder_files.py`: check the coders' output files.
5. `06_combine.py`: combine the two coders (agree → their code; disagree → 1 with uncertain), compute kappa, audit the textile rules on the sample.
6. `09_apply_policy.py` with `conventions.py`: apply the conventions of 19 October (to copies, as in PTA 1–5) and of 28–30 October (to new pairs), the screen and the rescue screen; check that copies equal the PTA 1–5 codes; write the final files (without DV_strict from 1 November).
7. `11_screen.py`: build, check and combine the two-family screen of one-sided 1s and the rescue screen.
8. `07_audit.py`, `07b_audit_zh_workbook.py`: draw the stratified audit sample (305 pairs), compare the independent AI auditors with the final codes, and score the accuracy of DV after review.
9. `10_question_pairs.py`: list the pairs each questionnaire question affects.
10. `make_results_report.py`: build the result report and the variable file from the final files.

The scripts need the local project layout (the original agreement files, the PTA 1–5 codes and the AI coders' files),
which is not in this repository. `09_apply_policy_PTA_2_5.py` is the PTA 1–5 script whose functions the PTA 6–10
script reuses.

## Main results

| Agreement | Rows | DV = 1 | Share | Uncertain | Uncertain / DV = 1 |
|---|---:|---:|---:|---:|---:|
| Turkey–Singapore | 21,873 | 14,559 | 66.6% | 5,541 | 38.1% |
| Nicaragua–Taiwan | 211,027 | 139,179 | 66.0% | 18,458 | 13.3% |
| Chile–Korea | 313,785 | 209,686 | 66.8% | 33,833 | 16.1% |
| Oman–US | 249,838 | 189,946 | 76.0% | 20,656 | 10.9% |
| Canada–Chile | 374,528 | 252,172 | 67.3% | 43,566 | 17.3% |
| **Total** | **1,171,051** | **805,542** | **68.8%** | **122,054** | **15.2%** |

- **Coverage.** 405,004 unique HS2002 pairs; 349,143 (86.2%) were copied from PTA 1–5 with identical codes. 92.6% of
  the rows are copies; the conventions of 30 October change only the other 7.4%.
- **Consistency.** 342,891 pairs (master_id) appear in two or more of the five agreements; DV is identical in all of
  them.
- **Two AI coders.** Claude and Codex agreed on 57.7% of 53,696 new pairs (kappa 0.28); Codex coded 1 far more often.
  Disagreements stay 1 with uncertainty unless a convention settles them.
- **Screen of one-sided 1s.** Of 16,508 one-sided 1s, Claude found 7,683 clearly invalid and Codex, blind, agreed on
  210 (mainly tobacco → garments); only those became 0.
- **Independent AI audit.** 305 stratified pairs, coded by two new AI sessions and reviewed by a research assistant.
  DV accuracy is 96.5% by pairs and 98.8% by rows (95.1% and 98.0% for the draft of 28 October on the same true values).

All codes are AI-assisted. The audit is an independent AI check reviewed by a research assistant, not an expert
hand-coding.
