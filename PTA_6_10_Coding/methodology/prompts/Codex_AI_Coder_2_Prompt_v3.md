# Codex prompt v3 — AI coder 2 for PTA 6–10, following the Coding Workflow of 19 October 2026

> 中文说明（给 August）：
> - **规则来源：** 本 prompt 的编码规则完整照录 2026-10-19 与张教授确定的
>   *Coding Workflow for RoO Restricted-Input Pairs*（`PTA_2_5/to_professor_2026_10_19_v2/RoO_coding_workflow_2026_10_19_v2.pdf`）
>   的第 2–6 步、全部例子和“口径汇总”，以及 PTA 2–5 已经使用的路线定义和 unit 格式。没有加入任何未经教授确认的新口径
>   （codebook 第 11 节不在其中）。Codex 只读这份 prompt，不读 codebook。
> - **相对第一轮的改进（只改做法，不改规则）：** ① 输入用 `ai_coders/input_v2/`，只写着 “Other” 的子目附上它所排除的
>   内容；② 禁止派子代理或并行代理，每条都由会话本身判断；③ 每块更小（unit 15 个、pair 30 个）；④ 按工作流第 6 步
>   “record the route” 的要求，每个 1 都要在理由中写明路线；⑤ 每个文件写完后，对照工作流逐条自查所有的 1。
> - **输出：** 写到 `ai_coders/coder2_codex_v2/`（第一轮的 `coder2_codex/` 保留作记录，Codex 不得打开）。
>   本文件取代 `Codex_AI_Coder_2_Prompt_v2.md`。
> - **怎么跑（建议先试点）：** 先只开会话 A，跑完前 2–3 个文件后告诉我，我对比 Claude 和独立裁判，确认没问题再开 B、C、D。
>   每个会话都是新的 Codex 会话，工作目录 `/Users/augustliu/Desktop/RoO_Project/Dummy_Variable/PTA6_10/`，允许写文件和
>   运行命令；粘贴下面 PROMPT，把第一行改成对应的 SESSION。中断时开新会话、粘贴同一段 PROMPT（同一 SESSION）即可续跑。
>   不要同时开两个相同 SESSION 的会话。

---

## PROMPT

**SESSION = A**  ← change to A, B, C or D

You are **AI coder 2** in a two-coder design that codes input–output links in rules of origin for five preferential
trade agreements (PTA 6–10: Turkey–Singapore, Nicaragua–Taiwan, Chile–Korea, Oman–US, Canada–Chile). Another coder
(coder 1) codes the same items independently; neither sees the other's answers. An earlier run by another session was
discarded. You must not look for, open or use coder 1's answers, the discarded run, any machine-learning output, any
rule output or any report.

**The coding rules are Part I of this prompt** (the Coding Workflow of 19 October 2026 agreed with Prof. Zhang). Use no
other rule file. Part II says how to work.

**Working folder:** `/Users/augustliu/Desktop/RoO_Project/Dummy_Variable/PTA6_10/` (all paths are relative to it).

---

# Part I — Coding rules (Coding Workflow, 19 October 2026)

## I.1 The question

Pairs are written **input → output** (A → B): the restricted input A and the output B of a rule of origin. The definition
of an input–output link is **expansive**: every pair starts at **DV = 1**, and each step turns to 0 only the cases it
clearly excludes. Steps 3–6 can only turn a 1 into a 0; no step turns a 0 back into a 1. For each item decide whether
the pair should be turned from 1 to 0, and at which step, and return `dv`, `route`, `step` and a one-sentence `reason`.

| field | values |
|---|---|
| `dv` | `1` (stays 1) or `0` (turned to 0) |
| `route` | why a pair stays 1: `same_good`, `forward`, `ingredient`, `component`, `reconstitute`, `mixture`, `recycle_waste`, `recycle_direct`, `feed`, `sibling_intermediate`; `none` if turned to 0 |
| `step` | `2` if locked as the same good; `3`, `4`, `5` or `6` for the step that turned it to 0; blank if it stays 1 through a route |
| `reason` | one sentence, at most 30 words, naming both goods and the deciding fact |

**General principle.** Use the broadest scope: keep 1 wherever any production route is technically possible, even if it
is uncommon. If in doubt, keep 1.

## I.2 Step 2 — Lock identical or same-good pairs at 1 (`route = same_good`, `step = 2`)

Rule: lock the pair when input and output are the same good or very similar: the same HS6 code, or the same species,
material or variety differing only in processing stage, preservation state, packing or size of presentation, or a
treatment the producer can add (roasting, decaffeinating, dyeing, printing, plying). Locked pairs skip steps 3–6.

| Input → Output | DV | Why |
|---|---|---|
| 090111 coffee, not roasted → 090111 coffee, not roasted | 1, locked | Same HS6 code (self-pair) |
| 090111 coffee, not roasted → 090121 coffee, roasted | 1, locked | Same coffee, roasted |
| 090111 coffee, not roasted → 090112 coffee, decaffeinated | 1, locked | Same coffee, decaffeinated |
| 090210 green tea, packs ≤ 3 kg → 090220 green tea, packs > 3 kg | 1, locked | Same tea, different packing |
| 520811 unbleached cotton plain weave → 520831 dyed cotton plain weave | 1, locked | Same fabric, dyed |

Boundary with siblings (step 4). "Very similar" means one can be turned into the other. Goods that differ in a fixed
attribute — fibre, species, gender cut, base material — are siblings, not the same good: women's cotton jackets →
women's synthetic jackets is not locked and goes to 0 at step 4. The direction must also be possible: dyed fabric →
unbleached fabric is not locked and goes to 0 at step 5.

## I.3 Step 3 — Turn to 0: clearly irrelevant pairs (`step = 3`)

Rule: turn to 0 only when no route from step 6 could apply: the input would have to change into a different species,
plant, fibre or substance, and it is not a constituent, feed, part or waste of the output. If in doubt, leave the pair
at 1 for step 6.

| Input → Output | DV | Why |
|---|---|---|
| 200941 pineapple juice → 200410 frozen prepared potatoes | 1→0 | Different plant; juice is not an ingredient of potatoes |
| 210500 ice cream → 210320 tomato ketchup | 1→0 | Unrelated food preparations |
| 151110 crude palm oil → 151491 crude rapeseed oil | 1→0 | Refining cannot change the oil's source |
| 710231 unworked diamonds → 711510 platinum catalysts | 1→0 | A stone does not become a metal |
| 730810 steel bridges → 730729 stainless tube fittings | 1→0 | Finished articles with unrelated uses |
| 030562 salted cod → 030344 frozen bigeye tuna | 1→0 | Different fish species, and salted cod is not feed |
| 030379 other frozen fish → 030332 frozen plaice | 1→0 | Different species; plaice is wild-caught, so no feed route |

Caution. Do not turn a pair to 0 at this step when the output is a mixture, a farmed animal or a waste product; leave
it at 1 for step 6. Example: chicken cuts → 160249 (prepared pork and mixtures) looks irrelevant but is a mixture pair.

Fibres. Different synthetic fibres — nylon, polyester, acrylic, polypropylene — count as one fibre: nylon yarn → acrylic
yarn is not a step-3 pair; it is an intermediate sibling (step 4) and stays 1. Different natural or artificial fibres
(cotton → polyester, flax → jute, viscose → polyester) remain different fibres.

Fish and other seafood. Different species are different goods: the pair is 0 at this step unless the input could feed
the output (step 6, feed). The intermediate-sibling rule of step 4 does not apply to different species.

Convention used in coding the earlier PTAs: intermediate goods of a different principal material or species (palm oil →
rapeseed oil) are step-3 pairs (0), not siblings; for textiles, minor constituents are handled in step 6.

## I.4 Step 4 — Turn to 0: downstream sibling products (`step = 4`)

Rule: both goods are finished products at the same stage, usually in the same heading or chapter, differing in a fixed
attribute (fibre, species, cut, material), and neither physically goes into the other.

| Input → Output | DV | Why |
|---|---|---|
| 620432 women's cotton jackets → 620433 women's synthetic jackets | 1→0 | Parallel finished garments |
| 620630 women's cotton blouses → 620640 women's man-made-fibre blouses | 1→0 | Parallel finished garments |
| 640192 waterproof boots → 640110 waterproof boots with metal toe-cap | 1→0 | Parallel footwear |
| 630622 synthetic-fibre tents → 630621 cotton tents | 1→0 | Parallel made-up articles |
| 960820 felt-tip pens → 960810 ballpoint pens | 1→0 | Parallel pens |

Exceptions that stay 1 (`route = component`), because one sibling is a part of the other:

| Input → Output | DV | Why |
|---|---|---|
| 640699 footwear parts → 640399 leather footwear | stays 1 | Parts (uppers, soles) go into footwear |
| 960891 nibs → 960839 fountain pens | stays 1 | Nib is a pen component |
| 960860 ballpoint refills → 960810 ballpoint pens | stays 1 | Refill is a pen component |
| 611780 knitted clothing accessories (trims, bows) → 610610 women's knitted cotton blouses | stays 1 | Trims are attached to garments |

Intermediate siblings stay 1. Step 4 applies only when both goods are finished. Two different intermediate goods of the
same material at the same stage stay 1 with `route = sibling_intermediate`. Intermediate goods are fibre, yarn (including
sewing thread), fabric, steel and other metal semi-finished products, paper and paperboard in rolls or sheets, glass in
the mass and semi-finished glass, feed residues, basic chemicals and parts. Fabrics of the same fibre but a different
construction (woven, knitted, pile, nonwoven) are intermediate siblings. Garments, made-up textile articles, footwear,
furniture, machines, vehicles, consumer articles and retail food preparations are finished.

| Input → Output | DV | Why |
|---|---|---|
| 720851 hot-rolled steel sheet → 721420 hot-rolled steel bars | stays 1 | Intermediate steel products |
| 480100 newsprint → 480411 kraft paper | stays 1 | Intermediate paper grades |
| 480591 other uncoated paper → 480512 straw fluting paper | stays 1 | Intermediate paper grades |
| 230230 wheat bran → 230400 soya-bean oil-cake | stays 1 | Parallel feed residues |
| 731815 screws and bolts → 731816 nuts | stays 1 | Steel fastener parts |
| 520811 cotton woven fabric → 600622 cotton knitted fabric | stays 1 | Same fibre, different construction |
| 540241 nylon filament yarn → 540243 polyester filament yarn | stays 1 | Synthetic fibres count as one fibre |
| 540110 synthetic sewing thread → 550959 synthetic staple yarn | stays 1 | Thread and yarn of one fibre |

## I.5 Step 5 — Turn to 0: inverse (backward) pairs (`step = 5`)

Rule: the input is downstream of the output in the same production chain, so the real relationship runs the other way.

| Input → Output | DV | Why |
|---|---|---|
| 721123 cold-rolled steel → 720229 ferro-silicon | 1→0 | Ferro-silicon goes into steel, not the reverse |
| 520811 cotton woven fabric → 520511 cotton yarn | 1→0 | Yarn is woven into fabric |
| 410791 finished leather → 410120 raw bovine hides | 1→0 | Hides are tanned into leather |

- Exception that stays 1: a reverse link through a waste or scrap code (step 6, `recycle_waste`).
- Exception that stays 1: direct remelting with no scrap code in between (step 6, `route = recycle_direct`).

## I.6 Step 6 — Turn to 0 only where the expansive definition finds no route (`step = 6`)

Rule: every pair still at 1 is checked against the expansive routes below. It stays 1 if any route plausibly applies
(**record the route**). It is turned to 0 only if you are sure no route exists — the cases listed in each table.

Route meanings (as used in coding PTA 1–5):
- `forward`: the input is processed into the output (slaughtering, cutting, spinning, weaving, rolling, refining,
  assembling the input as the main material).
- `ingredient`: the input is one of several materials of the output, including process inputs such as solvents,
  catalysts and reagents that are used up in making it.
- `component`: the input is a part, sub-assembly or accessory of the output.
- `reconstitute`: the output is the input brought back to an earlier form (dried → liquid).
- `mixture`: the output is a mixture and the input is one of its constituents.
- `recycle_waste`: the output is a waste or scrap code produced when making or using the input, or the input is a waste
  that is reprocessed into the output.
- `recycle_direct`: direct remelting or re-processing with no scrap code in between (the step-5 exception).
- `feed`: see the feed rules below.
- `sibling_intermediate`: see step 4.

**Mixtures (`route = mixture`)**

| Input → Output | DV | Why |
|---|---|---|
| 020714 frozen chicken cuts → 160249 prepared pork and mixtures | stays 1 | Another meat in a meat mixture |
| 070310 onions → 200570 prepared olives | stays 1 | Flavouring or stuffing |
| 070960 capsicum → 200570 prepared olives | stays 1 | Pimento-stuffed olives |
| 551219 polyester woven fabric → 551693 rayon woven fabric | 1→0 | "Mixed" refers to fibre content; fabric → fabric of another fibre has no route |

**Minor constituents of textile goods (`route = ingredient` or `mixture`).** A garment, made-up article, yarn or fabric
is classified by its main fibre, but it can contain other fibres: lining, pocketing, trim or blend. A fibre, yarn, fabric
or waste of another fibre going into it stays 1: certain 1 when the input is cotton or a man-made fibre (synthetic or
artificial); 1 with uncertainty when the input is another fibre (wool, silk, flax, ramie, coarse animal hair, other
textile materials), and when fabric of the same fibre but another construction goes into a garment (woven fabric →
knitted garment and the reverse). (The uncertainty flag is set by rule; you code these pairs `dv = 1`.)

| Input → Output | DV | Why |
|---|---|---|
| 540231 nylon filament yarn → 620342 men's cotton trousers | stays 1 | Man-made yarn as minor constituent |
| 540752 dyed polyester woven fabric → 620311 men's wool suits | stays 1 | Lining or blend |
| 520821 cotton fabric → 630253 table linen of man-made fibres | stays 1 | Cotton as blend or trim |
| 540231 nylon filament yarn → 520851 printed cotton fabric | stays 1 | Minor yarn in a fabric |
| 510710 wool yarn → 610463 women's knitted synthetic trousers | 1 (uncertain) | Wool blend: possible, less common |
| 500720 silk woven fabric → 570110 wool carpets | 1 (uncertain) | Silk as minor constituent |
| 520811 cotton woven fabric → 610610 women's knitted cotton blouses | 1 (uncertain) | Same fibre, other construction (woven trim) |

**Recycling (`route = recycle_waste`; `recycle_direct`)**

| Input → Output | DV | Why |
|---|---|---|
| 551431 synthetic woven fabric → 550510 synthetic fibre waste | stays 1 | Cutting waste |
| 411200 finished sheep leather → 411520 leather parings and dust | stays 1 | Shaving and buffing waste |
| 510310 wool noils → 510521 combed wool in fragments | stays 1 | Waste reprocessed into fibre |
| 721320 hot-rolled rod → 720610 non-alloy ingots | stays 1 (recycle_direct) | Direct remelting with no scrap code in between |
| 761010 aluminium doors and windows → 760110 unwrought aluminium | stays 1 (recycle_direct) | Direct remelting |
| 780500 lead pipes → 780110 refined lead | stays 1 (recycle_direct) | Direct remelting |
| 540752 dyed polyester woven fabric → 540233 textured polyester yarn | stays 1 (recycle_direct) | Polyester can be melted and spun again |

**Broad scope: wastes, raw materials and uncommon uses**

| Input → Output | DV | Rule |
|---|---|---|
| 292212 diethanolamine → 382520 sewage sludge | stays 1 | Any chemical (ch. 28–38) → wastes of heading 3825 (recycle_waste) |
| 290322 trichloroethylene → 382541 halogenated waste solvents | stays 1 | As above |
| 252400 asbestos → 252330 aluminous cement | stays 1 | Any mineral of ch. 25 → cement (ingredient) |
| 251200 diatomite → 252329 Portland cement | stays 1 | As above |
| 480451 kraft paper → 482320 filter paper | stays 1 | Technically possible further use (forward) |
| 910811 watch movements → 910599 other clocks | stays 1 | Technically possible further use (component) |

**Feed (`route = feed`).** The input must be a feed-grade good — whole low-value fish (herring, sardines, mackerel,
other fish), fish meat and meal, crustaceans and their meal (krill), molluscs — and the output a farmed carnivorous
fish or crustacean (trout, salmon, eels, sea bass, flatfish, bluefin tuna, shrimps and prawns, crabs) or a product made
from it. Wild-caught outputs (other tunas, skipjack, cod, herring, plaice) and grazers or filter feeders are 0. Where a
feed use is possible but not established, the pair is 1 (with uncertainty).

| Input → Output | DV | Why |
|---|---|---|
| 030264 fresh mackerel → 160411 prepared salmon | stays 1 | Feed fish → farmed salmon |
| 030371 frozen sardines → 030191 live trout | stays 1 | Feed fish → farmed carnivore |
| 030629 other crustaceans and crustacean meal → 030621 rock lobster | 1 (uncertain) | Rock lobster is farmed on such feed in parts of Asia |
| 030410 fresh fish fillets → 030613 frozen shrimp | 1→0 | Fillets are a human-food form, not feed |
| 030350 frozen herring → 160414 canned tuna | 1→0 | Canned tuna is wild-caught |
| 030710 oysters → 030332 frozen plaice | 1→0 | Oysters are high-value food, not feed |
| any fish → abalone, oysters or mussels | 1→0 | Grazers and filter feeders do not eat fish feed |

**Other routes**

| Input → Output | DV | Route |
|---|---|---|
| 010639 live birds → 020890 other meat | stays 1 | forward |
| 120400 linseed → 200811 peanut butter | stays 1 | ingredient |
| 350211 dried egg albumin → 350219 liquid egg albumin | stays 1 | reconstitute |
| 290220 benzene → 290611 menthol (process solvent) | stays 1 | ingredient (process) |

## I.7 Reading "of other textile materials"

In the HS this means every fibre that is not named in the same group of subheadings. 610990 T-shirts "of other textile
materials" include synthetic T-shirts, because only cotton has its own subheading (610910), so 540231 nylon yarn →
610990 is a main-fibre (forward) pair. 620449 dresses of other textile materials exclude wool, cotton, synthetic and
artificial fibres, which have their own subheadings.

## I.8 Summary of scope conventions (19 October 2026)

| Question | Convention |
|---|---|
| Different intermediate goods of the same material at the same stage | 1, route sibling_intermediate; finished siblings stay 0 (step 4) |
| Different synthetic fibres (nylon, polyester, acrylic, polypropylene) | One fibre |
| Fabrics of the same fibre, different construction | 1 (sibling_intermediate) |
| Sewing thread ↔ yarn of the same fibre | 1 (sibling_intermediate; thread → twine forward) |
| Clothing accessories (trims, bows) → garments | 1 (component) |
| Any chemical (ch. 28–38) → wastes of heading 3825 | 1 (recycle_waste) |
| Any mineral of ch. 25 → cement (2523) | 1 (ingredient) |
| Technically possible but uncommon further use | 1 |
| Minor constituent of another fibre in a garment, made-up, yarn or fabric | Cotton or man-made input: 1. Other fibres, or the same fibre in another construction (fabric → garment): 1 with uncertainty |
| Direct remelting with no scrap code in between | 1, route recycle_direct |
| Fish and other seafood of different species | 0 (step 3), unless the input could feed the output: feed (1); possible but unestablished feed: 1 with uncertainty |
| "Of other textile materials" | Every fibre not named in the same group of subheadings |
| The two AI coders disagree and no convention settles it | 1 with uncertainty (set when the two coders are combined; code your own view) |

---

# Part II — How to work

## II.1 Files of each SESSION (process in this order; inputs are `ai_coders/input_v2/<FILE>.csv`)

- A: `sample_pairs`, `concord_pairs`, `units_batch_01` … `units_batch_10`
- B: `units_batch_11` … `units_batch_21`
- C: `units_batch_22` … `units_batch_32`
- D: `units_batch_33` … `units_batch_42`

## II.2 Allowed and forbidden

- **Work alone.** Do not spawn, assign, message or wait for sub-agents or parallel agents, and do not split a file
  between workers. You read and decide every item yourself, in this one session.
- Read: this prompt (`Codex_AI_Coder_2_Prompt_v3.md`), `ai_coders/input_v2/*.csv` and your own files in
  `ai_coders/coder2_codex_v2/`.
- Write: `ai_coders/coder2_codex_v2/<FILE>.csv` and `ai_coders/coder2_codex_v2/_progress_<SESSION>.md` only.
- Run: the display, append and check commands below. You may run `_work/04_check_coder_files.py` but must not open it
  or any other file in `_work/`.
- Do **not** open `_work/`, `ai_coders/input/`, `ai_coders/coder1_claude/`, `ai_coders/coder2_codex/` (discarded run),
  `adjudication/`, `audit/`, `final/`, any other prompt or codebook file, any folder outside the working folder, or any
  other file. Do not use the internet.

## II.3 Input files

- All codes are HS2002 six-digit subheadings, except in `concord_pairs`, which uses **HS2012** codes and texts (pairs of
  the Turkey–Singapore agreement whose two codes fall in the same HS2002 subheading).
- A subheading whose HS text is only "Other" is described by what it excludes, in square brackets, e.g.
  `284169: Other [Salts of oxometallic or peroxometallic acids, group 2841.6x, other than: Potassium permanganate]`.
  Two different "Other" subheadings are different goods.
- `ex1` … `ex5` are the five most similar pairs already coded in PTA 1–5
  (`input>output | origin: how it was coded | DV | route | input text -> output text`). They show how similar pairs were
  coded; they do not decide the new pair.

**Pair files** (`sample_pairs`, `concord_pairs`): columns `item_id`, (`master_id` in `sample_pairs` only), `input_hs6`,
`input_description`, `output_hs6`, `output_description` (heading | subheading texts) and `ex1` … `ex5`. Write one row per
item, in input order, with the header `item_id,dv,route,step,reason`.

**Unit files** (`units_batch_NN`): each row is a heading-pair unit: all pairs between one input heading (HS4) and one
output heading (HS4). Columns `unit_id`, `input_heading` and its text, `output_heading` and its text, `n_pairs`,
`input_codes` and `output_codes` (`HS6: subheading text`, separated by ` ; `), `pairs_in_unit` (either "all input x
output combinations" or the list of `input>output` pairs) and `ex1` … `ex5`. For each unit write **one `default` row**
that applies to every pair of the unit, and **exception rows** only where a subheading or a pair is coded differently,
with the header `unit_id,scope,dv,route,step,reason`:

| scope | applies to |
|---|---|
| `default` | every pair of the unit |
| `in:<HS6>` | every pair whose input is that subheading |
| `out:<HS6>` | every pair whose output is that subheading |
| `pair:<HS6>><HS6>` | that single pair (input>output) |

Precedence: `pair` > `in` > `out` > `default`. If an `in:` and an `out:` exception would give one pair different answers,
add a `pair:` row for it. Read every subheading on both sides before you write the default: an exception is needed
wherever one subheading differs in species, material, stage or use from the rest of its heading. Write all rows of a
unit together, default row first.

## II.4 Step 0 — resume (at the start and after any context reset)

1. Read `ai_coders/coder2_codex_v2/_progress_<SESSION>.md` if it exists.
2. For each FILE of your SESSION in order, run the check (II.8). Skip every FILE that already passes ("OK"). The first
   FILE that is missing or fails is the current FILE.
3. If the current FILE's output exists but is incomplete, continue after the last `item_id` / `unit_id` already in it
   (input order). Do not rewrite rows that are already there unless the check reports a problem with them.

## II.5 Code each FILE in small chunks

Before each FILE, re-read Part I of this prompt completely. Then display one chunk at a time (pair files: 30 rows; unit
files: 15 rows):

```bash
/usr/local/bin/python3 -c "import pandas as pd; d=pd.read_csv('ai_coders/input_v2/<FILE>.csv',dtype=str,keep_default_na=False); print(len(d)); print(d.iloc[<A>:<B>].to_csv(index=False))"
```

For every item:
1. Identify both goods from their descriptions.
2. Work through steps 2, 3, 4, 5 and 6 of Part I in order and stop at the first step that decides the item.
3. If the item stays 1, record the route (step 6): in the reason, say which route applies and how — what is done to
   the input to make the output, or how it enters the output — in terms of the route meanings of I.6 and the examples
   of Part I. If the item is turned to 0, say which step and the deciding fact.
4. The reason is one sentence of at most 30 words that names both goods. **Do not use commas or double quotes in the
   reason** (the files are plain CSV).
5. If you are in doubt, keep 1 and say why.

After deciding a chunk, append its rows at once (create the file with its header line first):

```bash
cat >> ai_coders/coder2_codex_v2/<FILE>.csv <<'EOF'
<your rows for this chunk>
EOF
```

Decide every item yourself. Do not write a script that assigns answers from code digits, keywords or the worked
examples; do not give a whole chunk the same answer without reading each item; do not copy a worked example's answer
without checking that it fits. Scripts may only display input rows, append the rows you decided, and run the check.

## II.6 Self-review of each FILE before the check

When the FILE is fully written, display your own output and re-read **every row with dv = 1** against Part I:
- the reason records a route that plausibly applies to these two goods (I.6);
- `same_good` meets step 2 (same good or very similar; the direction is possible);
- a pair of two finished goods is not kept 1 unless one is a part of the other (step 4) or another route of step 6
  applies;
- a backward pair is kept 1 only through a waste or scrap code (`recycle_waste`) or direct remelting with no scrap code
  in between (`recycle_direct`), as in step 5;
- `component` is a part, sub-assembly or accessory of the output; `ingredient` is one of the materials of the output or
  a process input used up in making it; `feed` meets the feed rule.
Correct the rows that do not meet Part I by rewriting those rows in the file. Do not change rows that do.

## II.7 Keep going

Do not stop to ask the user anything and do not summarise between chunks. Continue chunk after chunk, FILE after FILE,
until every FILE of your SESSION passes the check.

## II.8 Check each FILE

```bash
/usr/local/bin/python3 _work/04_check_coder_files.py coder2_codex_v2 <FILE>
```

It must print `OK`. If it reports problems, fix those rows (one row per item and the same order as the input for pair
files; exactly one `default` row per unit for unit files; every `dv` is 0 or 1; every route is allowed for its dv;
`step` is 2 for `same_good`, 3–6 for `dv = 0`, and empty otherwise; reasons of at least 15 characters; scopes name codes
of that unit) and check again. Then append one line to `ai_coders/coder2_codex_v2/_progress_<SESSION>.md`:
`<FILE> | OK | rows <n> | dv1 <n> | dv0 <n> | rows changed in self-review <n> | routes <route counts>`.

## II.9 Finish

When every FILE of your SESSION passes, run the check once for those files and report the table from
`_progress_<SESSION>.md`.
