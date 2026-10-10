# IO Pair Matching Prompt: PTA_1, V3 Round 1

## 0. Task

Code every input → output HS6 pair in PTA_1 (ASEAN–Japan, 115,764 pairs, HS2002) with a dummy `DV`. `DV = 1` means input A can be used to produce output B; `DV = 0` means it cannot. Follow the V3 decision rule below. Review every pair individually. For each pair, record a relation type and a reason specific to that pair.

The work runs in **five fixed groups, one group per session** (Section 6). A final session combines the groups and writes the deliverables:

- one Excel workbook;
- a CSV mirror;
- a **bilingual (Chinese and English) report**.

This is the first validation round under the V3 rule. The results are AI-assisted suggestions: `DV = 1` is provisional retention, not a verified production relationship, and `DV = 0` is a candidate exclusion that still needs human confirmation.

## 1. Guiding principle

Professor Zhang's rule:

> If input A could be potentially used to produce output B, then we should keep 1 there. Only when A and B are totally irrelevant should we change 1 to 0.

His reminder of 2026-10-09: *we still want to have an expansive definition of input-output relations.*

Ask one directional question for each pair, A → B only:

> **Would a producer of B, in normal commercial practice, use A as a material, component, ingredient, processing input, feed, or recycled or recovered feedstock to make B?**

- **Be expansive.** Direct and indirect uses both count, including minor uses and recycling routes, as long as they exist in real practice. When you are uncertain, keep 1 and mark the pair uncertain.
- **Only three kinds of pairs get 0:** `SIBLING`, `BACKWARD` and `DIFFERENT_IDENTITY` (Section 3).
- **Do not invent routes.** Burning anything for energy, dissolving anything into chemicals, or unlimited disassembly is not a production route. The standard is normal, economically meaningful practice, not logical possibility.
- **Relatedness alone is not a reason for 1.** Two goods in the same family or the same production chain can still fail the directional test (fabric → yarn).
- **Classification position alone is never a reason.** Do not code "same chapter = 1", "cross-chapter = 0" or "cross-chapter = 1". Judge the two specific products.

## 2. Inputs (read-only)

The project root is the `RoO_Project` folder, which contains `Dummy_Variable/`, `Dummy Variable/`, `RoO_Step0/` and `outputs/`. Note the two similar folder names: write only into `Dummy_Variable/PTA_1/`. The older `Dummy Variable/` folder (with a space) is read-only.

| Role | Path (from project root) | Expected |
|---|---|---|
| Pairs and descriptions | `RoO_Step0/results_step1/pairs_with_descriptions_PROVISIONAL.csv` | SHA-256 `e2061e3fabdc885ea6fda401dfc60cf664c70bbcedf952c5611ec8df78f149b4`; 115,764 rows; 31 columns; `description_status`: 115,753 `BOTH_FOUND`, 11 `CODE_NOT_FOUND`; 2,701 distinct HS6 codes |
| Fixed record IDs and groups | `Dummy Variable/_control/split_manifest.csv` | SHA-256 `90a41ff4e727dfb17999f0bfd40b014dc503970ae01666b89bc5aa152b436d18`; maps every `pair_id` to one `sample_id` and one `round_id` (`Round_1`–`Round_5`) |
| Previous values (FINALIZE only) | `outputs/pta_1_summary_20261007_final/PTA_1_Summary.xlsx`, sheet `Review_Pairs` | SHA-256 `0184a77114ae43e56f829ecd5f95f392cbc1e62c8639b2887982d1d4e6528ee4` |
| RA module votes (FINALIZE only) | `Dummy_Variable/reference/all voted rows (M0_M6).xlsx` | SHA-256 `62d121cad9c681494987e2c40d0362a49362ee14955688471c89d143fc5e8723`; 36,427 voted pairs; columns `m0_depth` … `m7_vegetables`, `io_real` |

Handling rules:

- Read every HS6 code as a six-character string, keeping leading zeros. Keep the input → output direction. Do not drop, de-duplicate, swap or edit any row.
- Join to the manifest on `pair_id`. Join the previous values and RA votes on `input_hs6` + `output_hs6`.
- The manifest's `round_id` and the `sample_id` prefix (`R1`–`R5`) define the five groups (Section 6). They are data groups, not validation rounds: all five groups belong to V3 Round 1.
- If a checksum, row count or column count differs from the table, stop and report it. Do not adjust data to match the expected numbers.

**Descriptions.** Judge from `input_description` / `output_description` (heading text | subheading label), using the heading and chapter description columns as context. Never judge from the short subheading label alone: "Other", "Parts" or "Of cotton" means nothing without its heading. For a residual "Other" subheading, establish its scope from the parent heading and its sibling subheadings before classifying.

**Independence.** Do not open the previous values or the RA votes until FINALIZE, after every `DV` is frozen. Never change a frozen `DV` because of these comparisons; record the disagreement instead.

## 3. Decision order

Apply the classes in this order and use the first that fits. Before assigning any 0 class (9–11), check classes 3–8.

| # | `relation_type` | 中文 | Condition | `DV` | `uncertain_status` |
|---:|---|---|---|:-:|:-:|
| 1 | `CODE_ISSUE` | 编码问题 | `description_status` is not `BOTH_FOUND`, or the code is not a valid HS2002 subheading (e.g. 290400). Never replace a code. | 1 | 1 |
| 2 | `SAME_GOOD` | 同一商品 | Identical six-digit code. | 1 | 0 |
| 3 | `RECYCLE` | 回收 | (a) B is a waste, scrap or recovered-material heading of A's material (sink list, Section 4). (b) A is such a heading and B is a primary or semi-finished product of the same material. (c) Policy routes `POLYMER_MELT_RECYCLING` and `WOOL_WASTE_CARDING` (Section 3.1). | 1 | 0 |
| 4 | `COMPONENT` | 部件 | A is a part, component, refill, blank, sub-assembly, or an item of a set or assortment of B. Judge from the full heading text. Examples: 640699 parts of footwear → 6403 footwear; 960860 ball-point refills → 960810 ball-point pens; integrated circuits → smart cards. | 1 | 0 |
| 5 | `FORWARD` | 正向工序 | A precedes B on a production ladder (Section 4) with compatible material or species. Includes processing steps within one heading: greige → bleached → dyed or printed; hot-rolled → cold-rolled → coated; green → roasted; fresh → chilled, frozen, dried, salted or prepared; live animal → meat of the same species. Also the policy routes `FLOUR_TO_SYRUP` and `PRESERVED_TO_DRIED` (Section 3.1). | 1 | 0 |
| 6 | `INGREDIENT` | 配料或加工投入 | A is a normal ingredient of B, or a processing input consumed in making B, or B is a mixture or preparation containing A. Examples: spices → mixed spices or sauces; sugar → confectionery; tanning extracts → leather; dyes → dyed fabric. | 1 | 0 |
| 7 | `FEED` | 饲料 | A is a recognized feed for the animal in B, including the policy route `FEED_ROUTE` (Section 3.1). | 1 | 0 |
| 8 | `RECONSTITUTE` | 复原 | Recognized reconstitution or recombination: 0402 milk powder or 0405 milk fat → 0401 recombined milk or cream; concentrated juice → juice. | 1 | 0 |
| 9 | `BACKWARD` | 逆向 | A is a later stage than B on the same ladder, and classes 3 and 8 do not apply. Examples: fabric → yarn of a different polymer or of a natural fibre; rolled steel → pig iron or ferro-alloys; chocolate → cocoa paste; confectionery → sugar; cheese → milk; cigarettes → tobacco leaf. | **0** | 0 |
| 10 | `SIBLING` | 同族互斥 | A and B are mutually exclusive finished goods, or same-stage specifications, in one heading or material family. They differ only in fixed attributes (material, gender, species, use, size, weave, construction), and classes 4–6 do not apply. Examples: men's suits ↔ women's suits; leather-upper ↔ rubber footwear; wooden ↔ metal furniture; ball-point ↔ felt-tipped pens. | **0** | 0 |
| 11 | `DIFFERENT_IDENTITY` | 完全无关 | Totally unrelated: different species, fibre or material with no conversion route, or no plausible route of any kind after classes 3–8 have been checked. | **0** | 0 |
| 12 | `UNRESOLVED` | 无法判断 | Cannot be decided with confidence. The reason must name the classes considered and say why none fits. | 1 | 1 |

### 3.1 Policy routes (all decided on 2026-10-10: `DV = 1`)

These routes count as input–output relations. Code them with the class shown and set `policy_flag`, so that they can be counted and traced. Use only these values in `policy_flag`; leave it blank otherwise.

| `policy_flag` | Route | `relation_type` |
|---|---|---|
| `POLYMER_MELT_RECYCLING` | Fabric, yarn or fibre of one thermoplastic polymer (polyester, nylon/polyamide, polypropylene and similar) → filament, staple fibre or yarn of the same polymer | `RECYCLE` |
| `WOOL_WASTE_CARDING` | Wool or fine-hair yarn waste, opened and carded → carded or combed wool or hair (5105) | `RECYCLE` |
| `FLOUR_TO_SYRUP` | Starch-based flour, grits, flakes or root flour → glucose or fructose syrup (starch saccharification) | `FORWARD` |
| `PRESERVED_TO_DRIED` | Provisionally preserved goods → dried goods of the same product | `FORWARD` |
| `FEED_ROUTE` | Fish, crustaceans, molluscs, fish meal or other recognized feedstuffs → the farmed animals, or their products, that they feed | `FEED` |

## 4. Production ladders and recycling sinks (HS2002)

These lists cover the main chains but are not exhaustive. For chains not listed (chemicals, plastics, rubber, glass, paper products, machinery and others), apply the same logic from the HS descriptions and record the ladder you used in the rules log.

**Ladders**

- **Iron and steel:** 7201–7203, 7205 primary → 7206, 7207, 7218, 7224 semi-finished → 7208–7229 flat-rolled products, bars, rods, sections and wire → 7301–7326 articles. Hot-rolled → cold-rolled → plated or coated is forward, and so is slitting wide flat-rolled steel into narrow strip. Check subheading text for special cases, e.g. 721661 sections cold-formed from flat-rolled products.
- **Textiles:** fibres (5001–5003, 5101–5105, 5201–5203, 5301–5305, 5501–5507) → yarns (5004–5006, 5106–5110, 5204–5207, 5306–5308, 5401–5406, 5508–5511) → fabrics (5007, 5111–5113, 5208–5212, 5309–5311, 5407–5408, 5512–5516, chapters 56–60) → made-ups and garments (chapters 61–63, 65).
- **Leather:** 4101–4103 raw hides → 4104–4107 leather → chapter 42 and 64 articles.
- **Dairy:** 0401 → 0402–0406 (exception: class 8).
- **Cocoa, sugar, tobacco:** 1801 → 1803 → 1804, 1805 → 1806; 1212, 1701 → 1704, 1806; 2401 → 2402, 2403.
- **Wood and paper:** 4403 → 4407, 4408 → 4412 and other chapter 44 products → chapter 94; 4701–4706 → 4801–4811.
- **Non-ferrous metals:** unwrought (e.g. 7402–7406, 7502–7504, 7601–7603) → semi-finished (7407–7411, 7505–7507, 7604–7609) → articles.
- **Food and agriculture:** oilseeds 1201–1207 → oils 1507–1515; wheat 1001 and maize 1005 → flours, groats and meal 1101–1104; meat 0201–0210 → 1601–1602; fish 0301–0307 → 1604–1605; coffee 0901 → 2101.

**Recycling sinks** (class 3): 3915 plastics; 4004 rubber; 411520 leather parings and dust; 440130 sawdust and wood waste; 4707 recovered paper; 5003 silk waste; 5103, 5104 wool waste and garnetted stock; 5202 cotton waste; 5505 man-made fibre waste; 6309 worn clothing; 6310 rags; 7001 cullet; 7112 precious-metal waste; 7204 ferrous scrap; 7404, 7503, 7602, 7802, 7902, 8002 non-ferrous waste and scrap.

## 5. How to code each row

1. **Use the shared knowledge tables** built in SETUP (Section 6). For every HS6 code they record:
   - product identity, and material, species, fibre or polymer;
   - its stage on a ladder;
   - whether it is a part, refill, set or waste heading;
   - for residual "Other" subheadings, their scope.

   Use the same tables in every group.
2. **Classify every pair.** You may draft rows with narrow rules if each rule meets all of these conditions:
   - It tests a product relationship (for example "same garment type, different gender"), not chapter or heading membership.
   - It has a `rule_id`.
   - Its conditions and exceptions are written in the shared rules log.
   - Its condition has been checked for each row it covers.

   Every row's reason must name both products and both HS6 codes.
3. **Work in batches** of at most 200 rows, ordered by `(input_hs6, output_hs6)` within the group. Read every row of a batch before saving it. Save each batch to `_work/batches/Group_k/`, then update `_work/progress.json`. Never overwrite a completed batch.
4. **Knowledge basis.** Use `COMMON_KNOWLEDGE` by default. If you actually consult a web page, use `BASIC_WEB_CHECK` or `MIXED` and record the real URL in `source_url`. If knowledge is insufficient, use `UNRESOLVED`. Never invent sources.

**Not allowed:**

- Setting default values in a loop and calling the rows reviewed.
- Chapter-level or keyword templates.
- String similarity used in place of judgement.
- Skipping or thinning rows to finish a group faster.
- Uploading the data to external services.

## 6. Run plan: five groups, one group per session

**Why groups.** Coding 115,764 rows in one session risks losing earlier standards when the working context fills up, and invites shortcuts such as templates. It also means a wrong rule is found only at the end. Each group is a fixed random fifth of the data (about 3,800 of the 5,076 distinct four-digit heading pairs appear in every group). Group 1 therefore tests most rules early, and the groups give regular checkpoints.

**Groups.** Group k is every row whose manifest `round_id` is `Round_k` (`sample_id` prefix `Rk`): 23,153 rows in Groups 1–4 and 23,152 in Group 5. Never change group membership.

**Units, in order.** At the start of every session, read `_work/progress.json` and continue with the first unfinished unit:

| Unit | Work | Session |
|---|---|---|
| `SETUP` | Verify inputs (Section 2); build the knowledge tables for all 2,701 codes; start the rules log. | Same session as `GROUP_1` |
| `GROUP_1` … `GROUP_5` | Code the group (Section 5), run the group checks (Section 7.1), export the group files (Section 8.1). | One group per session |
| `FINALIZE` | Combine, check, freeze, compare, export the final files and the bilingual report (Sections 7.2–7.4, 8.2, 9). | Its own session |

Session rules:

- When a group is complete and its checks pass, **stop**. Do not start the next unit in the same session.
- If a session ends partway through a group, the next session resumes from the next unsaved batch.
- When the user sends this prompt again, or writes "continue" / "继续", run the next unit.

**Consistency across groups.**

- The knowledge tables and the rules log are shared and versioned. Record every change with its date and the group in which it was made.
- If you change or fix a rule in Group k, re-check every row the rule already covered in earlier groups and update those rows. Log the number of changed rows per group in `_work/rule_fixes.csv`, and re-export the affected group files with a revision note.

## 7. Checks

### 7.1 Group checks (end of every group)

- **Coverage:** every manifest row of the group appears exactly once.
- **Consistency:** every row has exactly one `relation_type`, and `DV` and `uncertain_status` match Section 3. Every `reason` is non-empty and contains both HS6 codes. `policy_flag` uses only the allowed values. HS6 codes are stored as text.
- **Template audit:** for each `rule_id`, count the distinct four-digit heading pairs it covers in the group. If a rule covers more than 50, list it in `Template_Audit` with its conditions and the result of a 20-row spot check. Apart from the codes, no two reasons should be identical.
- **Spot-check sample:** draw 30 random rows of the group with seed `20261010 + k` for optional human review.

### 7.2 FINALIZE: combined checks, then freeze

- **Coverage:** 115,764 rows; `pair_id` and `sample_id` are unique; every manifest row appears exactly once.
- **Group checks:** repeat the 7.1 checks on the combined table.
- **Rule consistency:** rows covered by the same `rule_id` have the same `relation_type` in every group.
- **Cross-group stability:** the groups are random fifths, so the share of `DV = 1` within a heading pair should be similar across groups. List in `Consistency` every four-digit heading pair with at least 5 rows in two or more groups whose `DV = 1` share is 100% in one group and 0% in another. Re-check those rows and record the outcome.
- **Counts reconcile:** overall, by group and by `relation_type`.
- **Inputs unchanged:** recompute the input checksums.

When all checks pass, freeze the `DV` values.

### 7.3 FINALIZE: compare with the previous values

Define `previous_DV` as `round_3_DV` where present, otherwise `round_1_DV`. Report the cross-tabulation of `previous_DV` × `DV`, the 0 → 1 and 1 → 0 transitions by `relation_type`, and the most frequent heading pairs in each direction.

### 7.4 FINALIZE: compare with the RA's modules

The RA's modules are a regression test, not a gold standard. Any agreement rate you report is agreement between two codings, not accuracy.

- For each module M0–M7, report the pairs voted, the pairs where our `DV` equals the vote, and the pairs where it differs.
- **Acceptance check (a):** every remaining M2 (siblings) or M5 (backward chain) disagreement should be `COMPONENT`, `RECYCLE` or `RECONSTITUTE`. List every disagreement that is not.
- Also report pairs where the RA votes 1 and we code 0, by module. M0 votes 1 for every cross-chapter pair, so an M0 vote is not evidence by itself.
- **Human-check sample:** draw a random sample of 100 remaining RA disagreements (all modules) with seed `20261010`, or all of them if there are fewer than 100. Leave `human_dummy` and `human_notes` blank. The human check is acceptance check (b) and will be done by a person.

## 8. Deliverables (in `Dummy_Variable/PTA_1/`)

```
PTA_1/
  PTA_1_IO_DV_Uncertain_Validation_Round_1.xlsx          (FINALIZE)
  PTA_1_IO_DV_Uncertain_Validation_Round_1.csv           (FINALIZE; mirror of Review)
  PTA_1_IO_DV_Uncertain_Validation_Round_1_Report.md     (FINALIZE; bilingual)
  groups/Group_k/                                        (k = 1–5)
    PTA_1_IO_DV_Uncertain_Validation_Round_1_Group_k.xlsx
    PTA_1_IO_DV_Uncertain_Validation_Round_1_Group_k.csv
    Group_k_Report.md                                    (bilingual)
  _work/   knowledge tables, batches, rules log, rule fixes, progress, audits, scripts
```

**`Review` columns**, in this order:

1. `sample_id`
2. `data_group` (`Group_1`–`Group_5`)
3. `pair_id`
4. `input_hs6`
5. `input_description`
6. `output_hs6`
7. `output_description`
8. `input_product` (short English name)
9. `output_product`
10. `relation_type`
11. `input_stage`
12. `output_stage`
13. `DV`
14. `uncertain_status`
15. `policy_flag`
16. `reason`
17. `rule_id`
18. `knowledge_basis`
19. `source_url`
20. `human_dummy`
21. `human_notes`

Columns added in FINALIZE, final workbook only:

22. `previous_DV`
23. `change_vs_previous` (`SAME`, `0_TO_1`, `1_TO_0`)
24. `RA_io_real` (blank if the RA did not vote)
25. `RA_modules_voted` (e.g. `m2_siblings=0; m5_backward=0`)
26. `agree_with_RA` (blank if the RA did not vote)

### 8.1 Group workbook

| Sheet | Content |
|---|---|
| `README` | Bilingual (中文 / English): rule summary, class table with Chinese names, column definitions, colour legend, and the statement "DV = 1 为暂时保留，不代表已核实；DV = 0 为候选排除，须人工确认 / DV = 1 is provisional retention, not verified; DV = 0 is a candidate exclusion pending human review." |
| `Summary` | Group totals; `DV` = 0 / 1; counts by `relation_type`, by `uncertain_status` and by `policy_flag`; completion status; revision note if re-exported. |
| `Review` | The group's rows, columns 1–21. |
| `Rules_Used` | Rules applied in the group, with rows covered. |
| `Template_Audit` | Output of the template audit in 7.1. |
| `Spot_Check` | The 30-row sample, with blank `human_dummy` and `human_notes`. |

### 8.2 Final workbook

| Sheet | Content |
|---|---|
| `README` | As in the group workbook, for all groups. |
| `Summary` | Totals; `DV` = 0 / 1; counts by `relation_type`, by `uncertain_status`, by `policy_flag` and by group; completion status and timestamp. |
| `Review` | All 115,764 rows, columns 1–26. |
| `Rules_Log` | `rule_id`, condition, exceptions, `relation_type`, rows covered, distinct heading pairs, version history and fixes. |
| `Template_Audit` | The combined template audit. |
| `Consistency` | Output of the cross-group stability check in 7.2. |
| `Compare_Previous` | Output of 7.3. |
| `Compare_RA_Modules` | Output of 7.4, including the full list for acceptance check (a). |
| `Human_Check_Sample` | The 100-row sample from 7.4. |

**Format (all workbooks)**

- Store HS6 codes as text. Store `DV`, `uncertain_status` and `previous_DV` as numbers.
- Bold header, frozen header row, filters, wrapped text for descriptions and reasons.
- Fill the whole row yellow (`#FFFF00`) where `DV = 0`, and light blue (`#DDEBF7`) where `uncertain_status = 1`, using conditional formatting over the full range down to the last data row.
- Data validation on `human_dummy`: blank, 0 or 1 only. Leave `human_dummy` and `human_notes` empty.
- No formulas or error values.
- The CSV mirrors are identical to the `Review` sheets.

**If a unit is incomplete**, name its files with a `_PARTIAL` suffix, mark `Summary` as `IN_PROGRESS`, and report the reviewed count and the next batch. Do not present default values as reviewed rows.

## 9. Bilingual reports (中英双语)

Both the final report and the group reports are written in **Simplified Chinese and English**.

**Format**

- Give every section heading in both languages, e.g. `## 3. 结果 / Results`.
- Under each heading, write the Chinese text first, marked **中文**, then the English text, marked **English**. The two versions must say the same thing and use the same numbers. Write natural Chinese, not word-for-word translation.
- Show each table once, with bilingual column headers (e.g. `类别 / Class`, `行数 / Rows`).
- Keep HS codes, `relation_type` codes, `policy_flag` values, column names and file names unchanged in both languages. At first use in the Chinese text, give the Chinese name from Section 3 in brackets, e.g. `SIBLING`（同族互斥）.

**Final report**, `PTA_1_IO_DV_Uncertain_Validation_Round_1_Report.md`:

1. 摘要 / Summary: half a page with the key numbers and the acceptance results.
2. 范围与数据 / Scope and inputs: the files, checksums and five groups.
3. 判定规则 / Decision rule: the V3 rule, the expansive principle, the class table with Chinese names, and the decisions of 2026-10-10 (`SIBLING` and `BACKWARD` → 0; all five policy routes → 1).
4. 结果 / Results: `DV` counts; counts by `relation_type`, by `policy_flag` and by group; the number of uncertain rows.
5. 与旧结果对比 / Changes against the previous values, and their main drivers.
6. 与 RA 模块对比 / RA module comparison, and the result of acceptance check (a).
7. 检查与规则修订 / Checks and rule fixes: the template audit, cross-group stability and rule fixes.
8. 局限 / Limitations: no human labels, so no accuracy rate; the knowledge basis; anything not completed.
9. 下一步 / Next steps: the human check of the 100-row sample (acceptance check b), and any open questions.

**Group report**, `Group_k_Report.md`, one to two pages:

- rows coded and checks passed;
- counts by `DV`, `relation_type` and `policy_flag`;
- rules added or changed, and the rows re-checked in earlier groups;
- the template audit result;
- the location of the spot-check sample;
- the next unit.

## 10. Reply at the end of each session

- **After a group**, title the reply "PTA_1 V3 Round 1 – Group k: reviewed x / n". Give the `DV` and `relation_type` counts, the checks passed, any rule changes and the rows re-checked, the file paths, and the next unit.
- **After FINALIZE**, title the reply "PTA_1 V3 Round 1: reviewed x / 115,764". Give the `DV` and `relation_type` counts, the result of acceptance check (a), the number of rows changed against the previous values, and the file paths.

Do not start any further validation round.
