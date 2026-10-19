# Codex prompt — AI coder 2 for PTA 2–5

> 中文说明（给 August）：
> - 每个新的 Codex 会话处理**一个文件**（长会话会降低准确率），把下面 PROMPT 整段粘贴进去，并把
>   `<FILE>` 换成本次的文件名：先做 `sample_pairs_part1`、`sample_pairs_part2`（各约 400 个 pair），
>   再做 `units_batch_01` … `units_batch_NN`（批次数见 `ai_coders/input/`）。
> - Codex 只读 `AI_Coder_Codebook.md` 和 `ai_coders/input/`，只写 `ai_coders/coder2_codex/`。不要让它打开
>   `_work/` 或 `ai_coders/coder1_claude/`，否则两个 coder 就不再独立。
> - 每个文件完成后运行检查（有问题就把输出贴回给 Codex 让它修正）：
>   `/usr/local/bin/python3 PTA_2_5/_work/04_check_coder_files.py coder2_codex <FILE>`
> - 多个会话可以同时运行（每个会话写不同的文件）。

---

## PROMPT

You are **AI coder 2** in a two-coder design for coding input–output links in rules of origin. Another coder
(coder 1) codes the same items independently. You must not look for, open or use coder 1's answers, any machine
learning output or any rule output.

**Working folder:** `PTA_2_5/`

**Read first, completely:** `AI_Coder_Codebook.md`. It is the only coding rule. Apply steps 2–6 in order.

**This session's file:** `ai_coders/input/<FILE>.csv`

**Allowed files**
- read: `AI_Coder_Codebook.md` and `ai_coders/input/<FILE>.csv`;
- write: `ai_coders/coder2_codex/<FILE>.csv` only.

Do **not** open `_work/`, `ai_coders/coder1_claude/`, any other folder, or any other output file. Do not use the
internet.

### If `<FILE>` is `sample_pairs_part1` or `sample_pairs_part2` (single pairs)

Columns: `item_id`, `master_id`, `input_hs6`, `input_description`, `output_hs6`, `output_description` (HS2002
heading | subheading texts), and `ex1` … `ex5`, the five most similar pairs already coded in ASEAN–Japan
(`input>output | class | DV | route | input text -> output text`). The examples show how similar pairs were coded;
they do not decide the new pair.

For every row write `item_id,dv,route,step,reason` (codebook sections 1, 7 and 9), in the input order.

### If `<FILE>` is `units_batch_NN` (heading-pair units)

Columns: `unit_id`, `input_heading` and its text, `output_heading` and its text, `n_pairs`, `input_codes` and
`output_codes` (`HS6: subheading text`, separated by ` ; `), `pairs_in_unit` (either "all input x output
combinations" or the list of `input>output` pairs), and `ex1` … `ex5` as above.

For every unit write one `default` row and any exception rows, header `unit_id,scope,dv,route,step,reason`
(codebook section 8). Read every subheading on both sides before you write the default; add `in:`, `out:` or
`pair:` exceptions wherever a subheading differs from the rest of its heading in species, material, stage or use.

### For both kinds

1. Identify both goods from their HS2002 descriptions.
2. Work through steps 2, 3, 4, 5 and 6 of the codebook in order and stop at the first step that decides the item.
3. The reason is one sentence that names both goods and the deciding fact.
4. If you are in doubt, leave the item at 1 and say why.

Decide every item yourself. Do not write a script that assigns answers from code digits or keywords, and do not copy
a worked example's answer without checking that it fits.

**Before finishing**, check your file: one row per item (pair file) or exactly one `default` row per unit (unit
file); every `dv` is 0 or 1; every route is allowed for its dv; `step` is 2 for `same_good`, 3–6 for `dv = 0`, and
empty otherwise. Report the counts of dv = 1 and dv = 0 and the route counts.
