# Independent AI audit of the 295-pair sample

> 中文说明（给 August）：
> - **为什么做：** 用一个全新的、看不到任何答案的 AI 会话，按教授口径独立判断这 295 对，用来检验最终数据。建议做两次：
>   一次用新的 Claude 会话（`<CODER>` 填 `claude`），一次用新的 Codex 会话（`<CODER>` 填 `codex`），两次互不相干。
> - **工作目录：** 新会话的工作目录请设为 `PTA_2_5/`（不要设为 `RoO_Step0`，
>   否则新的 Claude 会自动读到本项目的记忆，其中有之前的编码结论）。允许它写文件和运行命令，然后粘贴下面 PROMPT，并把
>   `<CODER>` 换成 claude 或 codex。
> - **完成后检查格式：**
>   `/usr/local/bin/python3 PTA_2_5/_work/07_human_audit.py check human_audit/audit_<CODER>.csv`
> - **两个都完成后**告诉我，我运行比较脚本并生成复核表 `human_audit/audit_review.xlsx`，你只需浏览其中有分歧的对子。

---

## PROMPT

You are an **independent auditor** of input–output codes for rules of origin. Other coders have coded these pairs;
you must not look for, open or use their answers, any model output, any rule output or any report.

**Working folder:** `PTA_2_5/`

**Read first, completely:** `AI_Coder_Codebook.md`. It is the only coding rule. Section 10 (decisions of 19 October
2026) overrides anything above it that reads differently. Apply steps 2–6 in order.

**Your file:** `human_audit/human_audit_pairs.csv`, 295 rows. Columns: `audit_id`, `input_hs6`,
`input_description`, `output_hs6`, `output_description` (HS2002 heading | subheading texts); the columns `dv`,
`route`, `step` and `reason` are empty.

**Allowed files**
- read: `AI_Coder_Codebook.md`, this prompt (`human_audit/AI_Audit_Prompt.md`) and `human_audit/human_audit_pairs.csv`;
- write: `human_audit/audit_<CODER>.csv` only.

Do **not** open `_work/`, `ai_coders/`, `final/`, `final_v1_2026_10_18/`, `final_v2_2026_10_18/`, any folder whose
name starts with `to_professor`, any `Report*`, `Email*` or `Progress*` file, or any other file. Do not use the
internet.

**Task.** For every row decide one question: can this input be used to make this output? Write
`audit_id,dv,route,step,reason` in the input order:
- `dv`: 1 or 0;
- `route`: if dv = 1, one of `same_good`, `forward`, `ingredient`, `component`, `reconstitute`, `mixture`,
  `recycle_waste`, `recycle_direct`, `feed`, `sibling_intermediate`; if dv = 0, `none`;
- `step`: `2` for `same_good`; `3`, `4`, `5` or `6` when dv = 0; empty otherwise;
- `reason`: one sentence that names both goods and the deciding fact; no commas or double quotes.

Use the broadest scope: keep 1 wherever any production route is possible, and keep 1 when in doubt.

Work in chunks of about 40 rows:
1. Display a chunk with
   `/usr/local/bin/python3 -c "import pandas as pd; d=pd.read_csv('human_audit/human_audit_pairs.csv',dtype=str,keep_default_na=False); print(d.iloc[<A>:<B>,:5].to_csv(index=False))"`.
2. Decide every row yourself.
3. Append the rows to `human_audit/audit_<CODER>.csv`, creating the file with its header line first.

Do not write a script that assigns answers from code digits or keywords.

**Before finishing**, run
`/usr/local/bin/python3 _work/07_human_audit.py check human_audit/audit_<CODER>.csv`. It must print `OK`; fix any
problems it reports. Then report your counts of dv = 1 and dv = 0.
