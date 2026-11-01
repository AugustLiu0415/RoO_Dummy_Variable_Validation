# Coding rules — Coding Workflow of 19 October 2026, with the conventions of 28–30 October 2026

> 中文说明：本文件 = `Coding_Rules_2026_10_19.md` 的规则 I.1–I.8（除 2026-11-01 对 I.3、I.6 的更正外逐字照录）+ 第 I.9 节（10-28 会议、10-30 张教授问卷答复
> 和 August 的 DV 规则）。I.9 与前文不同之处，以 I.9 为准。用于 PTA 6–10 终稿的 A1 筛查和 PTA 11 起的 AI coder、审核者。
> 10-19 版本保留不动，供 PTA 6–10 审核样本的复核使用（审核者当时按 10-19 规则判）。
> 2026-11-01 更正（两轮独立核对后）：I.3 删去与 I.9 第 2 条冲突的例子（钢桥 → 不锈钢管件）；I.6 换掉与 I.9 第 10 条冲突的混合物例子，
> 并写明布 → 另一纤维的布不算次要成分；I.9 第 2、3、8、9 条按教授答卷改正或注明待确认。
> 2026-11-01 会议后：原注明待确认的各点均已由教授确认（DV 为主变量、不再计算 DV_strict；整机对子不重审；化学品维持现行标准；其余按目前做法），I.9 已相应改写。备份：`_work/Coding_Rules_2026_10_30_before_1101_fix.md`。

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
| `basis` | for `dv = 1` only: `known` (a known production route or standard industrial practice) or `possible` (technically possible but no known route confirms it); see I.9 |

**General principle.** Use the broadest scope: keep 1 wherever any production route is technically possible, even if it
is uncommon. If in doubt, keep 1.

**Refined on 30 October 2026 (I.9 takes precedence).** A pair stays 1 unless there is clear evidence that the input cannot
be used to make the output. A pair that stays 1 is `basis = known` when a known route or standard practice uses the input,
and `basis = possible` when the link is technically possible but unconfirmed (the pair is then marked uncertain).

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
| 520811 unbleached cotton plain weave → 540752 dyed polyester filament woven fabric | 1→0 | "Mixed" refers to fibre content; a fabric → a fabric of another fibre, with no fibre in common, has no route (blends that share a fibre: I.9 #10) |

**Minor constituents of textile goods (`route = ingredient` or `mixture`).** A garment, made-up article, yarn or fabric
is classified by its main fibre, but it can contain other fibres: lining, pocketing, trim or blend. A fibre, yarn or
waste of another fibre going into a yarn, fabric, garment or made-up article, or a fabric of another fibre going into a
garment or made-up article, stays 1 (a fabric → a fabric of another fibre is not such a pair; see the mixtures table and
I.9 #10): certain 1 when the input is cotton or a man-made fibre (synthetic or
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

## I.9 Conventions of 28–30 October 2026 (take precedence over I.1–I.8)

Source: the meeting with Prof. Zhang on 28 October and his answers to the questionnaire of 28 October (received 30 October).

**Decision rule.** DV is the variable that counts (confirmed by Prof. Zhang on 2026-11-01; DV_strict is no longer computed). Every pair starts at DV = 1. It is turned to 0 only on clear evidence
that the link is invalid: a rule or convention below says 0, the direction is reversed, the claimed route is physically or
chemically impossible, or the only route that can be named is generic. A pair you cannot settle stays 1 with
`basis = possible`; it is never turned to 0 for being uncertain.

**Three levels (overall principle).**

| level | what it means | code |
|---|---|---|
| known | the input is used in a known production route of the output (or of the same kind of product), or in standard industrial practice | `dv = 1`, `basis = known` |
| possible | technically possible, but no known route confirms it | `dv = 1`, `basis = possible` (combined into DV 1 + uncertain) |
| invalid | physically or chemically impossible, reverse direction, or no specific route can be named | `dv = 0` |

**Conventions.**

| # | Case | Code |
|---|---|---|
| 1 | Process inputs: reagent, solvent, catalyst, binder, fuel, reductant, flux | Used in a known production route of the output → 1 (known). A specific role can be named (a named reaction or function), but no known route uses it → 1 (possible). Only a generic claim ("can act as a reagent", "fuel for process heat") → 0, step 3. Example: 292214 dextropropoxyphene → 293712 insulin = 0. In the screen of one-sided 1s, a 1 stays whenever a specific role can be named (Prof. Zhang, 2026-11-01). |
| 2 | Same-material intermediates and metal articles (I.4) | Parts of machines or vehicles, and metal articles: same heading and same material → 1 (known), `sibling_intermediate`; different heading, linked only by the same base material, or same heading but a different material (road wheels → seat belts) → 1 (possible). Semi-finished forms of one material (plates, bars, rods, wire, sections, sheet piling, rails, tubes, sheet glass, base paper, plastic sheets) → 1 (known), as in I.4. Chemicals of one heading: the same compound in another grade or form → 1 (known); a different compound → 1 (possible). Metal articles of the same metal are not step-4 siblings, even when both are finished: same heading → 1 (known), e.g. 730810 bridges → 730840 scaffolding; another heading → 1 (possible), e.g. 732410 stainless-steel sinks → 730723 stainless-steel butt-welding fittings. |
| 3 | Direct remelting or re-processing (`recycle_direct`) | Back to the input's own upstream form (ingots or unwrought metal, glass in the mass, pulp, primary plastics of the same polymer, the semi-finished form the article is made from, yarn or fibre of the same fibre) → 1 (known). Another primary or semi-finished form of the same material → 1 (possible). Made into a finished product (passenger car → truck body; grinding wheels → abrasive paper) → 0, step 6. Steel stove → sheet piling is 1 (possible), because sheet piling is a semi-finished form. Vulcanised rubber (4007–4017) cannot be remelted → 0, except reclaimed rubber 4003 and rubber waste 4004. Glass (cullet) and paper (repulping) qualify. Thermoplastics: only the same polymer; different polymers (polyethylene → polycarbonate) → 0 (his answer 3-2). Confirmed by Prof. Zhang on 2026-11-01: rubbers in primary forms also only the same polymer (natural rubber → butyl rubber → 0); thermosets and cellulose plastics → 0; a code "of other plastics" is a polymer of its own; no laminate route between different plastics; vulcanised rubber ground into crumb as an ingredient of 4005/4006 is not remelting → 1 (possible). Metal articles of the same metal are decided by convention 2, whatever route is claimed (steel wire netting → cast-iron tube fittings: 1, possible); where conventions 2 and 3 overlap, convention 2 takes precedence (Prof. Zhang, 2026-11-01). DV_excl_remelt still sets every `recycle_direct` pair to 0. |
| 4 | A complete machine or appliance as a component of another finished good | A real product combining them exists (data module in mobile phones) → 1 (known); only conceivable (desk lamp → upholstered seat) → 1 (possible). Parts going into their own machine stay `component` 1 (known). Not applied to pairs that both coders of earlier PTAs coded 0; those are not re-reviewed (Prof. Zhang, 2026-11-01). |
| 5 | Waste routes | Waste of goods made from the input: yarn, fabric or fibre → worn clothing 6309, fibre → rags 6310 → 1 (`recycle_waste`). A parallel by-product of the same source (frozen pork → pig bristles) → 0, step 3. Waste of a component of the input (resistance furnace → spent batteries) → 1 (possible). A waste input reprocessed into the output stays 1 (I.6). |
| 6 | A finished good cut or refitted into another good (fishing vessel → patrol vessel) | 1 (possible). Dismantling a finished good for its parts stays 0 (I.5). |
| 7 | Minerals and stone | Recovering an associated mineral from an ore (marble containing talc → talc) → 1 (possible). A finished stone, concrete or ceramic good crushed into filler or aggregate (concrete → bituminous articles) → 1 (known). |
| 8 | Food ingredients | Unchanged (I.6, answer A): technically possible even if uncommon → 1 (`known`); obviously never added → 0. (Corrected 2026-11-01: an earlier version coded unusual ingredients `possible`, which was option C, not his answer.) |
| 9 | The same good in another size or format | Lock only the feasible direction (wide → narrow, long → short). The reverse direction (narrow → wide film, a short roll of film → a long roll) → 0, step 5. Intermediate goods such as paper and paperboard in rolls or sheets are not affected: they stay 1 as intermediate siblings (I.4). Endless belts of another circumference, or belts that differ in reinforcement, are different goods → 0. |
| 10 | Fabrics of different main fibres | Sharing a minor fibre, or the input's main fibre is the output's minor fibre (polyester/cotton → viscose/cotton) → 1 (possible). Otherwise I.6 (different fibres → 0). |
| 11 | Chapter 59 (textile rules) | Wicks 5908, hosepiping 5909 → belting 5910 = 0; coated or rubberised fabric (5901, 5903, 5906, 5907) → 5910 = 1; 5901 → tyre cord fabric 5902 = 1. |
| 12 | Feed for farmed animals other than fish and seafood | The I.6 feed conditions (a feed-grade fish or crustacean input, a farmed carnivorous fish or crustacean output) apply only when the output is a fish or other seafood. For other farmed animals and their products (meat, eggs, milk), the overall principle applies: a standard feed → 1 (known); a feed use that is possible but not established → 1 (possible). (Added 2026-11-01 to match the workflow document.) |

**Two coders.** Both 0 → 0. Both 1 → 1; uncertain if either gave `basis = possible`. One 1 and one 0 → 1 with uncertain,
unless a blind screen by both model families finds the 1 clearly invalid (then 0).
