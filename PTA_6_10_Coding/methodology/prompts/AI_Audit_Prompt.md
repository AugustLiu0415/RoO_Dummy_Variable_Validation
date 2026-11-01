# Independent AI audit of the PTA 6–10 sample (305 pairs)

> 中文说明（给 August）：
> - **什么时候用：** 第 7 步。第 6 步（09）已写出第二轮草稿；`audit/audit_pairs.csv`（305 对，2026-10-26 抽样）已就绪，
>   2026-10-28 给其中 96 对只写着 “Other” 的描述补上了它所排除的内容（`07_audit.py enrich`，与 Codex 第二轮输入相同）。
> - **为什么做：** 用全新的、看不到任何答案的 AI 会话，按 10-19 规则独立判断这 305 对，用来估计最终数据的准确率。
>   做两次，互不相干：Codex 一次（`<CODER>` 填 `codex`，由你在**新的** Codex 会话里跑，不要用编码时那个会话），
>   Claude 一次（由 Claude 用独立的盲审代理跑，同样的规则和要求；结果先单独存放，等 Codex 跑完再一起比较）。
> - **规则：** 只读 `Coding_Rules_2026_10_19.md`（逐字照录 `Codex_AI_Coder_2_Prompt_v3.md` 的 Part I，即 10-19 规则）。
>   不读 codebook，因此不含第 11 节（教授未确认）。
> - **工作目录：** 新会话的工作目录设为 `/Users/augustliu/Desktop/RoO_Project/Dummy_Variable/PTA6_10/`，允许写文件和运行命令，
>   粘贴下面 PROMPT，并把 `<CODER>` 换成 codex。
> - **完成后**告诉我，我运行比较脚本生成复核表 `audit/audit_review.xlsx`，你只需浏览其中有分歧的对子
>   在 August_dv 列填你判断的真实值（1 / 0 / unsure），再次运行比较时你的标注会自动保留。

---

## PROMPT

You are an **independent auditor** of input–output codes for rules of origin. Other coders have coded these pairs;
you must not look for, open or use their answers, any model output, any rule output or any report.

**Working folder:** `/Users/augustliu/Desktop/RoO_Project/Dummy_Variable/PTA6_10/` (all paths are relative to it).

**Read first, completely:** `Coding_Rules_2026_10_19.md`. It is the only coding rule (the Coding Workflow of 19 October
2026). Apply steps 2–6 in order.

**Your file:** `audit/audit_pairs.csv`, 305 rows. Columns: `audit_id`, `hs_vintage`, `input_hs6`, `input_description`,
`output_hs6`, `output_description` (heading | subheading texts).
- Most rows are HS2002 codes. Rows with `hs_vintage = HS2012` use HS2012 codes and texts; code them with the same rules.
- A subheading whose HS text is only "Other" is described by what it excludes, e.g.
  `Other [Other vessels ..., other than: Warships]`. Two different "Other" subheadings are different goods.

**Allowed files**
- read: `Coding_Rules_2026_10_19.md`, this prompt (`AI_Audit_Prompt.md`) and `audit/audit_pairs.csv`;
- write: `audit/audit_<CODER>.csv` only.

Do **not** open `_work/` (except running the checker below), `ai_coders/`, `adjudication/`, `final/`, any other file in
`audit/`, `AI_Coder_Codebook.md`, any `Codex_*` file, any `README*`, `Report*` or `Email*` file, any folder outside this
working folder, or any other file. Do not use the internet. Do not start sub-agents or parallel agents: decide every row
yourself.

**Task.** For every row decide one question: can this input be used to make this output? Write
`audit_id,dv,route,step,reason` in the input order:
- `dv`: 1 or 0;
- `route`: if dv = 1, one of `same_good`, `forward`, `ingredient`, `component`, `reconstitute`, `mixture`,
  `recycle_waste`, `recycle_direct`, `feed`, `sibling_intermediate`; if dv = 0, `none`;
- `step`: `2` for `same_good`; `3`, `4`, `5` or `6` when dv = 0; empty otherwise;
- `reason`: one sentence of at most 30 words that names both goods and the deciding fact; for a 1 it states the route
  (what is done to the input to make the output, or how it enters the output); no commas or double quotes.

Work in chunks of 20 rows:
1. Display a chunk with
   `/usr/local/bin/python3 -c "import pandas as pd; d=pd.read_csv('audit/audit_pairs.csv',dtype=str,keep_default_na=False); print(d.iloc[<A>:<B>].to_csv(index=False))"`.
2. Decide every row of the chunk yourself against the rules.
3. Append the rows to `audit/audit_<CODER>.csv`, creating the file with its header line first.

Do not write a script that assigns answers from code digits or keywords.

**Self-review.** When all 305 rows are written, display your dv = 1 rows again and check each against the rules: is
the route real for these two goods, and is it the route named? Correct any row in place.

**Before finishing**, run
`/usr/local/bin/python3 _work/07_audit.py check audit/audit_<CODER>.csv`. It must print `OK`; fix any problems it
reports. Then report your counts of dv = 1 and dv = 0.
