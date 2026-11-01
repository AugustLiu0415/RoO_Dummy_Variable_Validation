# A1 screen — clearly invalid one-sided 1s (PTA 6–10)

> 中文说明：10-28 会议决定"明显不成立的单方 1 直接筛掉"（补充规则 A1）。本 prompt 供 Claude 和 Codex 使用，两边规则相同。
> Claude 筛全部 45 个文件；Codex 只筛 Claude 判为 invalid 的对子（`input_codex/`），看不到 Claude 的判断。
> 两家都判 invalid 的对子才改为 0，其余保持 1 + uncertain（以 DV 为准，10-30）。
> Codex 用法：把下面的 `<CODER>` 换成 `codex`，输入文件夹用 `ai_coders/screen_a1/input_codex/`；在新的 Codex 会话中运行，
> 工作目录为 `Dummy_Variable/PTA6_10`。

You are `<CODER>`. Your working directory is `Dummy_Variable/PTA6_10`.

## 1. Rules

Read `Coding_Rules_2026_10_30.md` in full before you start. Section I.9 takes precedence over I.1–I.8. Do not open any other
project file except your input files and your own output files. In particular, do not open `ai_coders/coder1_claude/`,
`ai_coders/coder2_codex*/`, `audit/`, `final/`, `adjudication/`, `_work/` (except running the checker below), or any other
coder's screen output.

## 2. The task

Each input row is an input → output pair of HS6 codes. One AI coder coded it 1 and gave `claim_route` and `claim_reason`;
the other coded it 0 and gave `counter_reason`. The pair is now DV 1 + uncertain. Decide whether the 1 is **clearly invalid**.

**`invalid`** only when there is clear evidence that the input cannot be used to make the output, and you cannot name a
specific valid route yourself. That means one of these:

| | case | step |
|---|---|---|
| a | Step 3: the input is a different material, plant, animal or substance, and it is not a constituent, ingredient (including a specific process input), feed, part or waste of the output. Example: unmanufactured tobacco → garments "as an extracted dye". | 3 |
| b | The claimed route is generic, with no specific role, reaction or process: "can serve as a reagent", "may supply ingredients with uncertainty", "compatibility uncertain". You also cannot name a specific route (I.9 convention 1). | 3 |
| c | Physically or chemically impossible: remelting vulcanised rubber or a thermoset; turning developed film back into unexposed film. | 6 |
| d | Reverse direction: the output is upstream of the input and no waste, remelting or other route applies. | 5 |
| e | A parallel by-product of the same source, not a waste of making or using the input (frozen pork → pig bristles; I.9 convention 5). | 3 |
| f | Two finished goods, neither of which goes into the other (I.4). | 4 |

**`valid`** in every other case, including these:
- any specific, technically possible route, even an uncommon one;
- the conventions that give 1 or 1 + uncertain (I.9):
  - a complete machine as a component, if the combination is conceivable (4);
  - refitting (6), associated minerals (7a), crushed filler (7b);
  - food ingredients that are technically possible (8);
  - waste of a component (5c);
  - blends sharing a minor fibre (10);
  - same-material intermediates (2).

Judge the pair, not only the wording of the claim. If the claim is weak but you can name a specific valid route, the pair is
valid: say which route.

**When in doubt, valid.** DV is the variable that counts, and an uncertain pair stays 1. Mark `invalid` only when another
careful reader would agree that the link is impossible or irrelevant.

## 3. Output

- Write `ai_coders/screen_a1/<CODER>/<same file name as the input>`.
- Use the header `item_id,verdict,step,reason`: one row per input row, in the same order.
- `verdict` is `valid` or `invalid`.
- `step` is empty for `valid`, and 3, 4, 5 or 6 for `invalid` (see the table).
- `reason` is one sentence of at most 30 words, naming the deciding fact. For a valid pair whose claim was weak, name the route
  you found.
- Write a correct CSV: quote fields that contain commas.

## 4. Process

1. Work on one input file at a time.
2. Read the rows in groups of about 50; rows of the same `unit` (input heading > output heading) usually share a decision,
   but check each pair's subheadings.
3. After each group, append your rows to the output file, so that progress is saved.
4. When the file is done, re-read every row you marked `invalid` and confirm it meets one of cases a–f with clear evidence;
   change it to `valid` if not.
5. Run `/usr/local/bin/python3 _work/11_screen.py check <CODER> <file stem>` (for example `screen_batch_07`); it must print
   `OK`. Fix any problem it reports.
6. Do not use scripts, keyword lists or rules of thumb to decide verdicts. Read each pair. You may use a script only to write
   your decided rows to the CSV.
