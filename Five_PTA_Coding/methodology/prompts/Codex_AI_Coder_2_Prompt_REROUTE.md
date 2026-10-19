# Codex prompt — AI coder 2, re-routed ML pairs (workflow 7d): units_batch_19 … units_batch_24

> 中文说明（给 August）：
> - 这是第二轮：审计发现 ML 概率带对非纺织 pair 不可靠，按流程 7d 把 8,516 个 pair（1,166 个 unit）交给两个
>   AI coder。Coder 1 已完成；请用和上次相同的方式运行 Codex：工作目录设为
>   `PTA_2_5/`，允许写文件和运行命令，粘贴下面 PROMPT。
> - 只处理 6 个文件（batch 19–24），已完成的 batch 01–18 和 sample 文件不会被改动。
> - 中途停止的话，开新会话再粘贴同一段 PROMPT 即可续跑。
> - 完成后告诉我，我会运行合并（06_combine.py）并更新报告。

---

## PROMPT

You are **AI coder 2** in a two-coder design for coding input–output links in rules of origin. Another coder
(coder 1) codes the same items independently. You must not look for, open or use coder 1's answers, any machine
learning output or any rule output.

**Working folder:** `PTA_2_5/` (all paths below are relative to it).

**FILES** (process in this order; each is `ai_coders/input/<FILE>.csv`; all are heading-pair unit files):
`units_batch_19`, `units_batch_20`, `units_batch_21`, `units_batch_22`, `units_batch_23`, `units_batch_24`.

Your output files for other batches already exist in `ai_coders/coder2_codex/`; do not change them.

### Allowed files and commands

- Read: `AI_Coder_Codebook.md`, this prompt (`Codex_AI_Coder_2_Prompt_REROUTE.md`), `ai_coders/input/*.csv`, and your own
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

When all 6 FILES pass, run the check once for the whole folder and report the table from `_progress.md`:

```bash
/usr/local/bin/python3 _work/04_check_coder_files.py coder2_codex
```
