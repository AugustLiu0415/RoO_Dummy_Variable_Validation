# AI Coder Codebook — RoO restricted-input pairs (PTA 2–5, middle band)

> 中文说明：本手册是两位 AI coder（Claude = coder 1，Codex = coder 2）共用的编码规则，内容来自教授的
> *Coding Workflow for RoO Restricted-Input Pairs*（2026-10-18）第 2–6 步及其例子，并补充了 PTA_1 已确定的惯例
> （标注"PTA_1 convention"）。两位 coder 独立作答，互不查看对方结果。

Version 2026-10-18. Shared by both coders. Each coder works **independently** and never looks at the other
coder's answers.

## 1. The task

Every pair is written **input → output** (A → B): the restricted input A and the output B of a rule of origin.
Each pair **starts at DV = 1**. The DV is 1 when A can plausibly be used to produce B under an **expansive**
definition of input–output links. Decide whether the pair should be **turned from 1 to 0**, and at which step.

For each pair return exactly one line:

| field | values |
|---|---|
| `dv` | `1` (stays 1) or `0` (turned to 0) |
| `route` | if dv = 1: `same_good`, `forward`, `ingredient`, `component`, `reconstitute`, `mixture`, `recycle_waste`, `feed`, `sibling_intermediate`, `recycle_direct`; if dv = 0: `none` |
| `step` | `2` if locked as the same good; `3`, `4`, `5` or `6` if turned to 0; blank if the pair stays 1 through a route at step 6 |
| `reason` | one sentence, specific to the two goods (name them), no more than 30 words |

Work through the steps in order. A step can only turn a 1 into a 0, and no step turns a 0 back into a 1.
**If you are in doubt, leave the pair at 1** and say why in the reason.

All codes are HS2002 six-digit subheadings. Use the official HS2002 description. Do not rely only on the code
digits, and do not rely on similar examples alone: the worked examples given with each pair are the 5 most similar
pairs already coded in ASEAN–Japan (PTA_1). They show how similar pairs were coded and do not decide the new pair.

## 2. Step 2 — lock identical or same-good pairs at 1 (`route = same_good`, `step = 2`)

Lock the pair when input and output are the **same good or very similar**:
- the same HS6 code; or
- the same species, material or variety, differing only in **processing stage, preservation state, packing or
  size of presentation**; or
- the same good plus a **treatment the producer can add**: roasting, decaffeinating, dyeing, printing, plying
  (folding single yarn into multiple yarn).

"Very similar" means that one good can be turned into the other, **in this direction**.

| Input → Output | DV | Why |
|---|---|---|
| 090111 coffee, not roasted → 090111 coffee, not roasted | 1, locked | Same HS6 code (self-pair) |
| 090111 coffee, not roasted → 090121 coffee, roasted | 1, locked | Same coffee, roasted |
| 090111 coffee, not roasted → 090112 coffee, decaffeinated | 1, locked | Same coffee, decaffeinated |
| 090210 green tea, packs ≤ 3 kg → 090220 green tea, packs > 3 kg | 1, locked | Same tea, different packing |
| 520811 unbleached cotton plain weave → 520831 dyed cotton plain weave | 1, locked | Same fabric, dyed |

**Boundary with siblings (step 4).** Goods that differ in a **fixed attribute** (fibre, species, gender cut,
base material) are siblings, not the same good: women's cotton jackets → women's synthetic jackets is not locked
and goes to 0 at step 4. The direction must be possible: dyed fabric → unbleached fabric is not locked and goes to
0 at step 5.

## 3. Step 3 — turn to 0: clearly irrelevant pairs (`route = none`, `step = 3`)

Turn to 0 **only when no route from step 6 could apply**: the input would have to change into a different
species, plant, fibre or substance, **and** it is not a constituent, feed, part or waste of the output. If in
doubt, leave the pair at 1 for step 6.

| Input → Output | DV | Why |
|---|---|---|
| 200941 pineapple juice → 200410 frozen prepared potatoes | 1 → 0 | Different plant; juice is not an ingredient of potatoes |
| 210500 ice cream → 210320 tomato ketchup | 1 → 0 | Unrelated food preparations |
| 151110 crude palm oil → 151491 crude rapeseed oil | 1 → 0 | Refining cannot change the oil's source |
| 710231 unworked diamonds → 711510 platinum catalysts | 1 → 0 | A stone does not become a metal |
| 730810 steel bridges → 730729 stainless tube fittings | 1 → 0 | Finished articles with unrelated uses |

**Caution.** Do not turn a pair to 0 at this step when the output is a **mixture**, a **farmed animal** or a
**waste product**; leave it at 1 for step 6. Example: chicken cuts → 160249 (prepared pork *and mixtures*) looks
irrelevant but is a mixture pair.

PTA_1 convention: intermediate goods of a **different principal fibre, material or species** (cotton yarn →
polyester yarn, palm oil → rapeseed oil) are step 3 pairs (0), not siblings.

## 4. Step 4 — turn to 0: downstream (finished) sibling products (`route = none`, `step = 4`)

Both goods are **finished products at the same stage**, usually in the same heading or chapter, differing in a
fixed attribute (fibre, species, cut, material), and **neither physically goes into the other**.

| Input → Output | DV | Why |
|---|---|---|
| 620432 women's cotton jackets → 620433 women's synthetic jackets | 1 → 0 | Parallel finished garments |
| 640192 waterproof boots → 640110 waterproof boots with metal toe-cap | 1 → 0 | Parallel footwear |
| 630622 synthetic-fibre tents → 630621 cotton tents | 1 → 0 | Parallel made-up articles |
| 960820 felt-tip pens → 960810 ballpoint pens | 1 → 0 | Parallel pens |

Exceptions that stay 1 (`route = component`), because one sibling is a part of the other:

| Input → Output | DV | Why |
|---|---|---|
| 640699 footwear parts → 640399 leather footwear | stays 1 | Parts (uppers, soles) go into footwear |
| 960891 nibs → 960839 fountain pens | stays 1 | Nib is a pen component |
| 960860 ballpoint refills → 960810 ballpoint pens | stays 1 | Refill is a pen component |

PTA_1 convention (decided with the professor on 2026-10-15): step 4 applies **only when both goods are finished
(final) goods**. Siblings of the **same material or fibre** where at least one side is a primary or intermediate
good (steel bars of different sections, flat-rolled steel of different widths, yarns of different counts, fabrics
of different weaves) are **not** turned to 0 at step 4: code them `dv = 1, route = sibling_intermediate`.
Fabric, yarn, fibre, steel products (chapter 72), plastics in primary forms, basic chemicals and parts are
intermediate; garments, made-up textile articles, footwear, furniture, machines, vehicles, consumer articles and
retail food preparations are finished.

## 5. Step 5 — turn to 0: inverse (backward) pairs (`route = none`, `step = 5`)

The input is **downstream** of the output in the same production chain, so the real relationship runs the other way.

| Input → Output | DV | Why |
|---|---|---|
| 721123 cold-rolled steel → 720229 ferro-silicon | 1 → 0 | Ferro-silicon goes into steel, not the reverse |
| 540752 dyed polyester woven fabric → 540233 textured polyester yarn | 1 → 0 | Yarn is woven into fabric |
| 410791 finished leather → 410120 raw bovine hides | 1 → 0 | Hides are tanned into leather |

- Exception that stays 1: a reverse link **through a waste or scrap code** (output is a waste, scrap, parings,
  noils or similar code) → step 6, `route = recycle_waste`.
- A reverse link by **direct remelting or re-processing with no scrap code in between** (steel rod → ingots, polyester
  fabric → polyester yarn or staple fibre) is `dv = 1, route = recycle_direct`, step blank (decision of 2026-10-19,
  section 10). The route flag lets a robustness version set these pairs to 0.

## 6. Step 6 — every pair still at 1 is checked against the expansive routes

It **stays 1** if any route plausibly applies (record the route). It is **turned to 0** (`step = 6`) only if you
are sure no route exists.

**Mixtures (`route = mixture`)**

| Input → Output | DV | Why |
|---|---|---|
| 020714 frozen chicken cuts → 160249 prepared pork and mixtures | stays 1 | Another meat in a meat mixture |
| 070310 onions → 200570 prepared olives | stays 1 | Flavouring or stuffing |
| 070960 capsicum → 200570 prepared olives | stays 1 | Pimento-stuffed olives |
| 551219 polyester woven fabric → 551693 rayon woven fabric | 1 → 0 | "Mixed" refers to fibre content; fabric → fabric has no route |

**Recycling (`route = recycle_waste`)**

| Input → Output | DV | Why |
|---|---|---|
| 551431 synthetic woven fabric → 550510 synthetic fibre waste | stays 1 | Cutting waste |
| 411200 finished sheep leather → 411520 leather parings and dust | stays 1 | Shaving and buffing waste |
| 510310 wool noils → 510521 combed wool in fragments | stays 1 | Waste reprocessed into fibre |
| 721320 hot-rolled rod → 720610 non-alloy ingots | stays 1 (`recycle_direct`) | Direct remelting with no scrap code in between (2026-10-19) |

**Feed (`route = feed`)**

| Input → Output | DV | Why |
|---|---|---|
| 030264 fresh mackerel → 160411 prepared salmon | stays 1 | Feed fish → farmed salmon |
| 030371 frozen sardines → 030191 live trout | stays 1 | Feed fish → farmed carnivore |
| 030410 fresh fish fillets → 030613 frozen shrimp | 1 → 0 | Fillets are a human-food form, not feed |
| 030350 frozen herring → 160414 canned tuna | 1 → 0 | Canned tuna is wild-caught |
| 030710 oysters → 030332 frozen plaice | 1 → 0 | Oysters are high-value food, not feed |
| any fish → abalone, oysters or mussels | 1 → 0 | Grazers and filter feeders do not eat fish feed |

PTA_1 convention for feed: the input must be a feed-grade form (whole low-value fish, fish or crustacean meal,
flours and pellets, krill); the output must be a farmed carnivorous fish or crustacean (trout, salmon, eel, sea bass,
sea bream, bluefin tuna (ranched), shrimps and prawns) or a product made from it. Wild-caught outputs (canned
tunas, skipjack, bonito; cod) are 0. Feed crops, oil-cakes or fish meal → land animals or their meat are not
covered by PTA_1 or the examples: decide each such pair on its own merits and explain the decision in the reason.

**Other routes**

| Input → Output | DV | Route |
|---|---|---|
| 010639 live birds → 020890 other meat | stays 1 | forward |
| 120400 linseed → 200811 peanut butter | stays 1 | ingredient |
| 350211 dried egg albumin → 350219 liquid egg albumin | stays 1 | reconstitute |
| 290220 benzene → 290611 menthol (process solvent) | stays 1 | ingredient (process) |

Route meanings:
- `forward`: the input is processed into the output (slaughtering, cutting, spinning, weaving, rolling, refining,
  assembling the input as the main material).
- `ingredient`: the input is one of several materials of the output, including process inputs such as solvents,
  catalysts and reagents that are used up in making it.
- `component`: the input is a part, sub-assembly or accessory of the output.
- `reconstitute`: the output is the input brought back to an earlier form (dried → liquid).
- `mixture`: the output is a mixture and the input is one of its constituents.
- `recycle_waste`: the output is a waste or scrap code produced when making or using the input, or the input is
  a waste that is reprocessed into the output.
- `feed`: see the feed rules above.

## 7. Output format

Write one CSV row per pair, in the same order as the input file, with the header

```
master_id,dv,route,step,reason
```

Use only the values listed in section 1. Leave `step` empty when the pair stays 1 through a step 6 route. Quote
the reason if it contains a comma.

## 8. Heading-pair units

Most open pairs come in **units**: all pairs between one input heading (HS4) and one output heading (HS4). A unit
row lists the input subheadings, the output subheadings and which combinations are pairs (usually all of them).

For each unit write **one `default` row** that applies to every pair of the unit, and add **exception rows** only
where a subheading or a pair is coded differently:

| scope | applies to |
|---|---|
| `default` | every pair of the unit |
| `in:<HS6>` | every pair whose input is that subheading |
| `out:<HS6>` | every pair whose output is that subheading |
| `pair:<HS6>><HS6>` | that single pair (input>output) |

Precedence: `pair` > `in` > `out` > `default`. If an `in:` and an `out:` exception would give one pair different
answers, add a `pair:` row for it. Read every subheading on both sides before you write the default: an exception
is needed wherever one subheading differs in species, material, stage or use from the rest of its heading.

Output header for units: `unit_id,scope,dv,route,step,reason`. The rules for `dv`, `route`, `step` and `reason` are
those of section 1. Every unit has exactly one `default` row.

## 9. Pair sample

`sample_pairs_part1.csv` and `sample_pairs_part2.csv` list single pairs (item ids `S0001` …). Code each pair on its own, as in section 7, with the
header `item_id,dv,route,step,reason`.

## 10. Decisions of Prof. Zhang, 2026-10-19 (apply to every PTA)

These answers settle the questions on which the two AI coders disagreed most. They override anything above that
reads differently.

**General principle.** Keep 1 wherever any production route is possible. If you are in doubt, keep 1 and say why.
When the two coders disagree, the combined code is 1 with `uncertain = 1`.

| # | Question | Decision | Example |
|---|---|---|---|
| 1-1 | Two different intermediate goods of the same material at the same stage | `dv = 1`, `sibling_intermediate`. Finished goods that are siblings stay 0 at step 4 | steel sheet → steel bars; newsprint → kraft paper; bran → oil-cake; screws → nuts; float glass → lamp envelopes = 1. Cotton blouse → synthetic blouse = 0 |
| 1-2 | Different synthetic fibres (nylon, polyester, acrylic, polypropylene) | one fibre | nylon yarn → acrylic yarn = 1 (sibling); nylon yarn → polyester fabric = 1 (forward) |
| 1-3 | Fabrics of the same fibre, different construction (woven, knitted, pile, nonwoven) | `dv = 1`, `sibling_intermediate` | cotton woven fabric → cotton knitted fabric = 1 |
| 2-1 | Any chemical (chapters 28–38) → wastes of heading 3825 | `dv = 1`, `recycle_waste` | diethanolamine → sewage sludge = 1 |
| 2-2 | Any mineral of chapter 25 → cement (2523) | `dv = 1`, `ingredient` | asbestos → aluminous cement = 1 |
| 2-3 | A technically possible but uncommon further use | `dv = 1` | kraft paper → filter paper; watch movements → other clocks = 1 |
| 3 | Yarn or fabric of another fibre or construction in a garment or made-up (minor constituent) | `dv = 1`. Certain when the input is cotton or man-made (decision 6); otherwise `uncertain = 1` (set by rule) | nylon yarn → cotton trousers = 1; silk yarn → cotton shirts = 1, uncertain |
| 4 | Direct remelting with no scrap code in between | `dv = 1`, `route = recycle_direct` (kept so a robustness version can set it to 0) | steel rod → steel ingots; aluminium windows → unwrought aluminium |
| A | Fibre, yarn or waste of another fibre as a minor blend component of a yarn or fabric (audit, 19 Oct) | as decision 3 | nylon yarn → printed cotton fabric = 1; flax yarn → wool fabric = 1, uncertain |
| C | Sewing thread ↔ yarn of the same fibre (audit, 19 Oct) | `dv = 1`, `sibling_intermediate` (thread → twine: `forward`) | synthetic sewing thread → synthetic staple yarn = 1 |
| D | Clothing accessories (trims, bows; 611780, 621710) → garments (audit, 19 Oct) | `dv = 1`, `component` | knitted trims → cotton blouses = 1 |
| 5 | Fish and other seafood of different species (reply of 19 Oct) | `dv = 0` (step 3), unless the input could feed the output: then `feed` under the feed convention of section 6; 1 with `uncertain = 1` for feed fish → rock lobster | frozen cod → frozen bigeye tuna = 0; frozen sardines → live trout = 1 (feed) |
| 6 | Option 2 (reply of 19 Oct) | a **cotton or man-made** fibre, yarn, fabric or waste as a minor constituent of a good of another fibre is a certain 1; other fibres (wool, silk, flax, ramie, coarse hair, other) stay 1 with `uncertain = 1`; the same fibre in another construction (woven fabric → knitted garment) stays 1 with `uncertain = 1` | polyester fabric → wool suits = 1 |

**Reading "of other textile materials".** In the HS this means every fibre that is not named in the same group of
subheadings. 610990 T-shirts "of other textile materials" include synthetic T-shirts, because only cotton has its own
subheading (610910); 620449 dresses of other textile materials exclude wool, cotton, synthetic and artificial fibres.
