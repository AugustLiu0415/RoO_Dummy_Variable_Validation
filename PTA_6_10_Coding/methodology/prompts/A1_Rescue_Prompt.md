# Rescue screen — pairs set to 0 by the remelting convention (PTA 6–10)

> 中文说明：按教授问题 3-1 的答案（I.9 第 3 条），"回熔做成成品"、硫化橡胶、热固性塑料或不同聚合物的回熔都记 0。
> 但这些对子可能还有别的具体路线（例如审核项 A284：金属软管灌入焊剂、拉成药芯焊丝）。按"只有明确证据才记 0"，
> 本筛查让 Claude 逐对判断是否存在别的具体路线：有 → 恢复为 1 + uncertain；没有 → 维持 0。
> 两位 coder 中声称 1 的一方只给了回熔路线，所以 Claude 找不到别的路线时，两家模型都已无路线可举。

You are `claude`. Your working directory is `Dummy_Variable/PTA6_10`.

## 1. Rules

Read `Coding_Rules_2026_10_30.md` in full; section I.9 takes precedence. Open no other project file except your input file
and your own output file (no `ai_coders/coder*`, `audit/`, `final/`, `adjudication/`, other screen outputs; `_work/` only to run
the checker).

## 2. The task

Each row is an input → output pair. A coder coded it 1 through direct remelting or re-processing (`claim_reason`), but
I.9 convention 3 excludes that route (`excluded_because`): remelting into a finished product, vulcanised rubber,
thermoset or cellulose plastics, a different polymer, or film. The pair is now 0. `counter_reason` is the other coder's view
(empty when both coders claimed remelting).

Decide whether the input can be used to make the output by **another specific route**, other than remelting or
re-processing into the output. The routes that count are:
- `forward` processing of the input itself (e.g. flexible metal tubing filled with flux and drawn into cored brazing wire);
- `ingredient`, `mixture` or `component` (a specific role in the output);
- `recycle_waste`, when the output is a waste of making or using the input;
- `sibling_intermediate`, for same-material intermediates (I.4, I.9 convention 2);
- `feed`, `reconstitute` or `same_good` where the rules allow them.

| verdict | when | route |
|---|---|---|
| `valid` | you can name a specific, technically possible route of this kind, even if uncommon | the route you name |
| `invalid` | no such route: the only link is remelting or re-processing, or the link is reversed, unrelated or impossible | `none` |

Do not count remelting, melting down, repulping or re-processing the input into the output: convention 3 has settled those.
Do not count generic claims ("can supply material", "may be used with uncertainty") either.

## 3. Output

- Write `ai_coders/screen_a1/claude/<same file name as the input>`.
- Use the header `item_id,verdict,route,reason`: one row per input row, in the same order.
- `reason` is one sentence of at most 30 words. For `valid`, name the route concretely; for `invalid`, give the deciding
  fact.
- Write a correct CSV: quote fields that contain commas.

## 4. Process

1. Read the rows in groups of about 50; rows of the same `unit` usually share a decision, but check each pair.
2. After each group, append your rows to the output file.
3. At the end, re-read every `valid` row and confirm that the route you named is specific and is not remelting.
4. Run `/usr/local/bin/python3 _work/11_screen.py rescue_check <file stem>`; it must print `OK`.
5. Decide each pair yourself: no keyword scripts for verdicts. A script may only write your decided rows.
