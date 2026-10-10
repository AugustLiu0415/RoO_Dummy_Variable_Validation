# Decision rule V3

**Status:** adopted on 2026-10-10 after Professor Zhang's confirmation. First applied in V3 Round 1 with the [IO Pair Matching Prompt](../prompts/IO_Pair_Matching_Prompt.md). The Stage 1–3 values in this repository were produced under the earlier rule (`EXPANSIVE_EXCLUSION_V2`) and are not relabelled.

Confirmed decisions (2026-10-10):

1. Same-family sibling pairs (`SIBLING`) and reverse-stage pairs (`BACKWARD`) are set to 0.
2. Five policy routes count as input–output relations (1): same-polymer melt recycling, wool-yarn waste carding, flour → syrup, provisionally preserved → dried goods, and feed routes (Section 3).

Professor Zhang's reminder (2026-10-09): *we still want to have an expansive definition of input-output relations.* V3 narrows the 0 side only for siblings and backward pairs; every other real route still counts as 1.

The evidence for the change is the external benchmark in Step 8 of [`VALIDATION_PROCESS.md`](VALIDATION_PROCESS.md).

## 1. The question asked for each pair

Old threshold: *are A and B totally irrelevant?* This is not directional. Yarn and fabric are related, so both yarn → fabric (a real step) and fabric → yarn (impossible) stayed at 1.

V3 question, applied to the direction A → B only:

> **Would a producer of B, in normal commercial practice, use A as a material, component, ingredient, processing input, feed, or recycled or recovered feedstock to make B?**

- Direct and indirect uses both count, including minor uses and recycling routes, as long as they exist in real practice. When uncertain, keep 1 and flag the pair.
- Belonging to the same material family or production chain is not, by itself, a reason for 1.
- Chapter or heading membership is never a reason by itself, either for 1 or for 0.
- Hypothetical routes that no producer uses (burning anything for energy, dissolving anything into chemicals) do not count.

This keeps the professor's directional wording ("A could be potentially used to produce B") and applies it to the 0 side as well.

## 2. Decision order

Apply the classes in order and use the first that fits. Check classes 3–8 before assigning a 0 class. Each row records `relation_type`, the stage of each product where relevant, and a one-sentence reason naming both products. The dummy follows mechanically from `relation_type`.

| # | `relation_type` | Condition | `DV` | Uncertain |
|---:|---|---|:-:|:-:|
| 1 | `CODE_ISSUE` | Code not found or not a valid HS2002 subheading; the code is never replaced | 1 | yes |
| 2 | `SAME_GOOD` | Identical six-digit code | 1 | no |
| 3 | `RECYCLE` | B is a waste or scrap heading of A's material; or A is such a heading and B is a primary or semi-finished product of the same material; or same-polymer melt recycling (fabric, yarn or fibre → filament, staple or yarn of the same thermoplastic polymer) | 1 | no |
| 4 | `COMPONENT` | A is a part, component, refill, blank, sub-assembly, or an item of a set of B. Judge from the full heading text, not a short label | 1 | no |
| 5 | `FORWARD` | A is earlier than B on a production ladder, with compatible material or species, including processing steps within one heading | 1 | no |
| 6 | `INGREDIENT` | A is a normal ingredient of B, a processing input consumed in making B, or B is a mixture containing A | 1 | no |
| 7 | `FEED` | A is a recognized feed for the animal in B | 1 | no |
| 8 | `RECONSTITUTE` | Recognized reconstitution, e.g. milk powder or milk fat → recombined milk or cream | 1 | no |
| 9 | `BACKWARD` | A is later than B on the same ladder, and classes 3 and 8 do not apply | **0** | no |
| 10 | `SIBLING` | Mutually exclusive finished goods or same-stage specifications in one family, differing only in fixed attributes (material, gender, use, size, weave and the like), and classes 4–6 do not apply | **0** | no |
| 11 | `DIFFERENT_IDENTITY` | Totally unrelated: different species, fibre or material with no conversion route, or no plausible route of any kind | 0 | no |
| 12 | `UNRESOLVED` | Cannot be decided; the reason says why classes 3–11 do not fit | 1 | yes |

Compared with Stages 1–3, only classes 9 and 10 move from 1 to 0. Classes 3, 4, 6 and 8 make explicit the routes that must stay at 1.

When A or B is a residual "Other" subheading, establish its scope from the parent heading and sibling subheadings before classifying.

## 3. Policy flags

All five routes were decided on 2026-10-10 and are coded 1. Rows on these routes carry a `policy_flag`, so they can be counted and traced.

| Flag | Pairs | `relation_type` |
|---|---|---|
| `POLYMER_MELT_RECYCLING` | Same-polymer fabric, yarn or fibre → filament, staple or yarn | `RECYCLE` |
| `WOOL_WASTE_CARDING` | Wool or fine-hair yarn waste, opened and carded → 5105 | `RECYCLE` |
| `FLOUR_TO_SYRUP` | Starch-based flour, grits, flakes or root flour → glucose or fructose syrup | `FORWARD` |
| `PRESERVED_TO_DRIED` | Provisionally preserved goods → dried goods | `FORWARD` |
| `FEED_ROUTE` | Fish, crustaceans, molluscs or other recognized feedstuffs → the farmed animals they feed | `FEED` |

## 4. Stage ladders and recycling sinks

These extend the other RA's 36 pre-set linkages (HS2002) and are not exhaustive. For other chains, the same logic is applied from the HS descriptions and recorded in the rules log.

- **Iron and steel:** 7201–7203, 7205 primary → 7206, 7207, 7218, 7224 semi-finished → 7208–7229 flat-rolled products, bars, rods, sections and wire → 7301–7326 articles. Hot-rolled → cold-rolled → plated or coated is forward.
- **Textiles:** fibres (5001–5003, 5101–5105, 5201–5203, 5301–5305, 5501–5507) → yarns (5004–5006, 5106–5110, 5204–5207, 5306–5308, 5401–5406, 5508–5511) → fabrics (5007, 5111–5113, 5208–5212, 5309–5311, 5407–5408, 5512–5516, chapters 56–60) → made-ups and garments (chapters 61–63, 65). Within fabrics, greige → bleached → dyed, yarn-dyed or printed is forward.
- **Leather:** 4101–4103 raw hides → 4104–4107 leather → chapter 42 and 64 articles.
- **Dairy:** 0401 → 0402–0406. Exception: 0402 and 0405 → 0401 is `RECONSTITUTE`.
- **Cocoa, sugar, tobacco:** 1801 → 1803 → 1804, 1805 → 1806; 1212, 1701 → 1704, 1806; 2401 → 2402, 2403.
- **Wood and paper:** 4403 → 4407, 4408 → 4412 and other chapter 44 products → chapter 94; 4701–4706 → 4801–4811.
- **Non-ferrous metals:** unwrought → semi-finished → articles.
- **Food and agriculture:** oilseeds → oils; wheat and maize → flours and meal; meat → 1601–1602; fish → 1604–1605; coffee → 2101.
- **Recycling sinks:** 3915, 4004, 411520, 440130, 4707, 5003, 5103, 5104, 5202, 5505, 6309, 6310, 7001, 7112, 7204, 7404, 7503, 7602, 7802, 7902, 8002.

## 5. Examples (real PTA_1 pairs)

| A → B | `relation_type` | `DV` |
|---|---|:-:|
| 620333 men's synthetic-fibre jackets → 620431 women's wool jackets | `SIBLING` | 0 |
| 6403 leather-upper footwear → 6402 rubber or plastic footwear | `SIBLING` | 0 |
| 960810 ball-point pens → 960820 felt-tipped pens | `SIBLING` | 0 |
| 721931 cold-rolled stainless steel → 720260 ferro-nickel | `BACKWARD` | 0 |
| 540720 woven synthetic filament fabric → 540261 nylon filament yarn (different polymer) | `BACKWARD` | 0 |
| 540741 nylon filament fabric → 540210 nylon high-tenacity yarn (same polymer) | `RECYCLE` | 1 |
| 170410 chewing gum → 170111 raw cane sugar | `BACKWARD` | 0 |
| 640699 parts of footwear → 6403 footwear | `COMPONENT` | 1 |
| 960860 ball-point refills → 960810 ball-point pens | `COMPONENT` | 1 |
| 040210 skimmed milk powder → 0401 recombined milk | `RECONSTITUTE` | 1 |
| 510610 carded wool yarn → 510400 garnetted stock | `RECYCLE` | 1 |
| 7208 hot-rolled flat steel → 7209 cold-rolled flat steel | `FORWARD` | 1 |

## 6. Scope of V3 Round 1

- All 115,764 PTA_1 pairs are coded again, so that every row carries a `relation_type`.
- Particular attention goes to the 57,117 rows that Stage 1 retained by chapter-level templates, and to the 16,729 Stage 2 U rows (12,606 `SIBLING_SPEC`, 4,123 `REVERSE_STAGE`). U rows are checked one by one against classes 3–8, not flipped as a class.
- The run is split into the five fixed groups of the split manifest, one group per session, with shared knowledge tables and rules and a final combining session (see the prompt, Section 6).
- Earlier values are kept. V3 results are written to a new workbook, `PTA_1_IO_DV_Uncertain_Validation_Round_1.xlsx`, with a report in Chinese and English.

## 7. Checks

In addition to the integrity checks in Step 6 of `VALIDATION_PROCESS.md`:

- Every row has exactly one `relation_type`, and `DV` matches the class mapping.
- Every reason names both products and both codes; apart from the codes, no two reasons are identical.
- **Template audit:** any rule covering more than 50 distinct four-digit heading pairs is listed with its conditions and a 20-row spot check.
- Counts by `relation_type` reconcile with the `DV` counts, overall and per data batch.

## 8. Benchmark and acceptance

The other RA's modules are a regression test, not a gold standard (Step 8 of `VALIDATION_PROCESS.md` lists their likely false 0s). The comparison is made only after all V3 values are frozen.

1. Report agreement with each module.
2. **Acceptance check (a):** every remaining M2 or M5 disagreement should be `COMPONENT`, `RECYCLE` or `RECONSTITUTE`. Any that is not is listed and re-examined.
3. **Acceptance check (b):** a human checks a random sample of 100 remaining disagreements (seed 20261010) and finds no systematic error.
4. If both hold, the procedure is frozen and applied to the remaining data.

Agreement with the RA is not accuracy. An accuracy rate still requires human labels in `human_dummy`.
