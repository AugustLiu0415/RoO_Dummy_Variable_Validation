# Codex prompt — AI coder 2, all 20 files in one session

> 中文说明（给 August）：
> - 在 Codex 中把工作目录设为 `PTA_2_5/`，允许它在该文件夹内
>   写文件和运行命令（workspace-write / auto 模式，避免每一步都要确认），然后把下面 PROMPT 整段粘贴进去。
> - 总输入约 3,559 个 unit + 788 个 pair（约 5 MB），一个会话里 Codex 一定会多次压缩上下文，甚至可能中途停止。
>   这个 prompt 已按"断点续跑"设计：所有结果都按块写到磁盘，进度记在 `ai_coders/coder2_codex/_progress.md`。
>   **如果会话停止或卡住，开一个新会话，再粘贴同一段 PROMPT 即可**，它会跳过已通过检查的文件，从未完成的位置继续。
> - 不要同时开两个会话跑同一组文件（会写坏同一个输出文件）。如果想并行，可以把 PROMPT 里的 `FILES` 改成不同的
>   子集，每个会话一组，例如会话 A 跑 sample 两个文件和 batch 01–09，会话 B 跑 batch 10–18。
> - 和逐个文件运行相比，长会话的风险是后期准确率下降；所以 prompt 要求它每个文件开始前重读 codebook，每块只处理
>   少量条目。跑完后我会按文件检查两个 coder 的一致率，如果某些批次明显异常，再单独重跑这些批次。

---

## PROMPT

You are **AI coder 2** in a two-coder design for coding input–output links in rules of origin. Another coder
(coder 1) codes the same items independently. You must not look for, open or use coder 1's answers, any machine
learning output or any rule output.

**Working folder:** `PTA_2_5/` (all paths below are relative to it).

**FILES** (process in this order; each is `ai_coders/input/<FILE>.csv`):
`sample_pairs_part1`, `sample_pairs_part2`, `units_batch_01`, `units_batch_02`, `units_batch_03`, `units_batch_04`,
`units_batch_05`, `units_batch_06`, `units_batch_07`, `units_batch_08`, `units_batch_09`, `units_batch_10`,
`units_batch_11`, `units_batch_12`, `units_batch_13`, `units_batch_14`, `units_batch_15`, `units_batch_16`,
`units_batch_17`, `units_batch_18`.

### Allowed files and commands

- Read: `AI_Coder_Codebook.md`, this prompt (`Codex_AI_Coder_2_Prompt_ALL.md`), `ai_coders/input/*.csv`, and your own
  files in `ai_coders/coder2_codex/`.
- Write: `ai_coders/coder2_codex/<FILE>.csv` and `ai_coders/coder2_codex/_progress.md` only.
- Run: the display, append and check commands below. You may run `_work/04_check_coder_files.py` but must not open
  it or any other file in `_work/`.
- Do **not** open `_work/`, `ai_coders/coder1_claude/`, `final/`, `human_audit/` or any other folder. Do not use the
  internet.

### Step 0 — resume (do this at the start and after any context reset)

1. Read `ai_coders/coder2_codex/_progress.md` if it exists.
2. For each FILE in order, run the check (step 4 below). Skip every FILE whose output already passes ("OK"). The first
   FILE that is missing or fails is the current FILE.
3. If the current FILE's output exists but is incomplete, continue after the last `item_id` / `unit_id` already in it
   (input order). Do not rewrite rows that are already there unless the check reports a problem with them.

### Step 1 — before each FILE

Re-read `AI_Coder_Codebook.md` completely (every FILE, not only the first). It is the only coding rule. Apply steps
2–6 in order.

### Step 2 — code the FILE in small chunks

Display one chunk at a time (pairs: 40 rows; units: 20 rows) with:

```bash
/usr/local/bin/python3 -c "import pandas as pd; d=pd.read_csv('ai_coders/input/<FILE>.csv',dtype=str,keep_default_na=False); print(len(d)); print(d.iloc[<A>:<B>].to_csv(index=False))"
```

**Pair files** (`sample_pairs_part1`, `sample_pairs_part2`): columns `item_id`, `master_id`, `input_hs6`,
`input_description`, `output_hs6`, `output_description` (HS2002 heading | subheading texts) and `ex1` … `ex5`, the
five most similar pairs already coded in ASEAN–Japan (`input>output | class | DV | route | input text -> output
text`). The examples show how similar pairs were coded; they do not decide the new pair. Write one row per item:
header `item_id,dv,route,step,reason` (codebook sections 1, 7 and 9), in input order.

**Unit files** (`units_batch_NN`): columns `unit_id`, `input_heading` and its text, `output_heading` and its text,
`n_pairs`, `input_codes` and `output_codes` (`HS6: subheading text`, separated by ` ; `), `pairs_in_unit` (either
"all input x output combinations" or the list of `input>output` pairs) and `ex1` … `ex5` as above. For every unit
write one `default` row and any exception rows: header `unit_id,scope,dv,route,step,reason` (codebook section 8).
Read every subheading on both sides before you write the default; add `in:<HS6>`, `out:<HS6>` or
`pair:<HS6>><HS6>` exceptions wherever a subheading differs from the rest of its heading in species, material,
stage or use. Write all rows of a unit together, default row first.

For every item:
1. Identify both goods from their HS2002 descriptions.
2. Work through steps 2, 3, 4, 5 and 6 of the codebook in order and stop at the first step that decides the item.
3. The reason is one sentence (at most 30 words) that names both goods and the deciding fact. **Do not use commas or
   double quotes in the reason** (the files are plain CSV).
4. If you are in doubt, leave the item at 1 and say why.

After deciding a chunk, append its rows to `ai_coders/coder2_codex/<FILE>.csv` at once (create the file with its
header line first). For example:

```bash
cat >> ai_coders/coder2_codex/<FILE>.csv <<'EOF'
<your rows for this chunk>
EOF
```

Decide every item yourself. Do not write a script that assigns answers from code digits, keywords or the worked
examples; do not give a whole chunk the same answer without reading each item; and do not copy a worked example's
answer without checking that it fits. Scripts may only display input rows, append the rows you decided, and run the
check.

### Step 3 — keep going

Do not stop to ask the user anything and do not summarise between chunks. Continue chunk after chunk, FILE after
FILE, until every FILE passes the check.

### Step 4 — check each FILE when it is complete

```bash
/usr/local/bin/python3 _work/04_check_coder_files.py coder2_codex <FILE>
```

It must print `OK`. If it reports problems, fix those rows (one row per item and the same order as the input for
pair files; exactly one `default` row per unit for unit files; every `dv` is 0 or 1; every route is allowed for its
dv; `step` is 2 for `same_good`, 3–6 for `dv = 0`, and empty otherwise; scopes name codes of that unit) and check
again. Then append one line to `ai_coders/coder2_codex/_progress.md`:
`<FILE> | OK | rows <n> | dv1 <n> | dv0 <n> | routes <route counts>`.

### Finish

When all 20 FILES pass, run the check once for the whole folder and report the table from `_progress.md`:

```bash
/usr/local/bin/python3 _work/04_check_coder_files.py coder2_codex
```
