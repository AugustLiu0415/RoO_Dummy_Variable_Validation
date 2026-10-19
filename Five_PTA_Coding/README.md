# Five-PTA input–output coding (18–19 October 2026)

The conventions developed on ASEAN–Japan (PTA_1) were turned into one general coding workflow. Under that workflow
four more agreements were coded (Brunei–Japan, Australia–US, CAFTA, Bahrain–US), and ASEAN–Japan was recoded under
the same rules, so a pair has the same code in every agreement. The scope conventions were set by Professor Zhang on
19 October 2026. The result is version `2026_10_19_v2`.

This folder holds the workflow, the methodology and the aggregate results. The row-level coded files (one Stata file
per agreement) are kept locally and are not published here.

## Contents

| Path | Contents |
|---|---|
| [`workflow/RoO_coding_workflow_2026_10_19_v2.pdf`](workflow/RoO_coding_workflow_2026_10_19_v2.pdf) | General coding rules: steps 1–7, worked examples and a summary of the scope conventions (`.html` is the source) |
| [`methodology/AI_Coder_Codebook.md`](methodology/AI_Coder_Codebook.md) | Codebook given to both AI coders and to the auditors (steps 2–6, examples; section 10 lists the conventions) |
| [`methodology/prompts/`](methodology/prompts/) | Prompts for AI coder 2 (Codex): all batches, and the batches moved from the model bands. Also the prompt for the independent AI audit |
| [`methodology/scripts/`](methodology/scripts/) | Pipeline scripts (order below) |
| [`results/Results_5_PTAs_2026_10_19_v2.pdf`](results/Results_5_PTAs_2026_10_19_v2.pdf) | Result report: main results, uncertain pairs, coding methods, reliability, revisions |
| [`results/Variables_5_PTAs_2026_10_19_v2.pdf`](results/Variables_5_PTAs_2026_10_19_v2.pdf) | Variables of the coded files and the values of each categorical variable |
| [`results/summary/`](results/summary/) | Aggregate figures: `summary_by_pta.csv` and the JSON reports of the pipeline (coder agreement, model checks, textile rules, policies, AI audit) |

## Pipeline

1. `01_intake.py`: read the agreements’ pairs, check the HS vintage, and build the pair master list.
2. `02_exact_copy_and_ml.py`: copy pairs already coded in ASEAN–Japan, then score the rest with the model (confidence bands 0.9 / 0.1).
3. `03_textile_rules.py` with `textile.py`: explicit rules for chapters 50–63.
4. `05_build_coder_inputs.py`: build heading-pair units and a blind sample for the two AI coders (Claude and Codex).
5. `04_check_coder_files.py`: check the coders’ output files.
6. `08_build_reroute_units.py`: send non-textile pairs from the model bands to the coders.
7. `06_combine.py`: combine the two coders (agree → their code; disagree → 1 with uncertain), compute kappa, audit the model bands and the rules on the sample, and settle model–rule conflicts.
8. `09_apply_policy.py`: apply the scope conventions of 19 October to all five agreements. It also re-copies exact pairs from the revised ASEAN–Japan labels, checks that shared pairs have identical codes, and writes the final files.
9. `07_human_audit.py`: draw the stratified audit sample (295 pairs) and compare the independent AI auditors with the final codes.
10. `make_results_report.py`: build the result report from the final files.

The scripts need the local project layout: the original agreement files, the ASEAN–Japan labels, the model outputs and
the AI coders’ files. These are not in this repository.

## Main results

| Agreement | Rows | DV = 1 | Share | DV_strict = 1 | Uncertain | Uncertain / DV = 1 |
|---|---:|---:|---:|---:|---:|---:|
| ASEAN–Japan | 115,764 | 53,949 | 46.6% | 49,811 | 4,138 | 7.7% |
| Brunei–Japan | 83,491 | 36,117 | 43.3% | 32,929 | 3,188 | 8.8% |
| Australia–US | 333,324 | 222,942 | 66.9% | 195,187 | 27,755 | 12.4% |
| CAFTA | 321,967 | 215,947 | 67.1% | 193,088 | 22,859 | 10.6% |
| Bahrain–US | 244,786 | 185,904 | 75.9% | 165,928 | 19,976 | 10.7% |

- **Consistency.** 327,518 pairs appear in two or more agreements. DV, uncertain, route and uncertain reason are identical in every agreement for all of them.
- **Two AI coders.** Claude and Codex agreed on 70.9% of 56,616 pairs (kappa 0.39). This was before the scope conventions, which settle most of the disagreements.
- **Model.** On non-textile pairs the confidence bands were not reliable: the ≥ 0.9 band was right 89.6% of the time and the ≤ 0.1 band 80.8%. The bands were therefore used only for textile pairs confirmed by the rules.
- **Textile rules.** The rules agree with the ASEAN–Japan labels on 92.3% of shared textile pairs.
- **Independent AI audit.** 295 stratified pairs were coded by two new AI sessions and reviewed by a research assistant. Where the two auditors agree, the final code matches them on 89.6% of pairs before the corrections and 99.2% after. The after-correction figure is measured on the same sample, so it overstates accuracy.

All codes are AI-assisted. The audit is an independent AI check reviewed by a research assistant, not an expert
hand-coding.
