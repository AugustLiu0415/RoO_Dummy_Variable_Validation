# Uncertain 与 分类/Other 队列 AI 辅助复核总报告（EXPANSIVE_EXCLUSION_V2）

> **AI辅助复核建议，非人工确认。** Z 是候选排除建议，不是确认删除；P 不是已核实；R 不是人工完成；本报告不含任何准确率，也不代表整个 PTA 数据已清洗完成。

## 1. 范围

- 两个互不重叠的冻结队列，来自正式 Round_1–5 Review 文件（只读，源文件哈希已核对，未被改动）：
  - Uncertain：原 dummy=1 且 screening_status=KEEP_1_UNCERTAIN_PENDING_HUMAN；
  - 分类/描述/Other：原 dummy=1 且 screening_status=KEEP_1_CLASSIFICATION_PENDING_HUMAN。
- 不含原 dummy=0 与 KEEP_1_PLAUSIBLE；目标中没有已有人工结论的行，故无跳过（H=0）。
- 教授规则：If input A could be potentially used to produce output B, then we should keep 1 there. Only when A and B are totally irrelevant should we change 1 to 0.

## 2. 汇总表

| 复核队列 | 来源Round | T | H | R | Z | P | U | C | N | Q |
|---|---|---|---|---|---|---|---|---|---|---|
| Uncertain | Round_1 | 10481 | 0 | 10481 | 6201 | 964 | 3316 | 0 | 0 | 9517 |
| Uncertain | Round_2 | 10467 | 0 | 10467 | 6173 | 949 | 3345 | 0 | 0 | 9518 |
| Uncertain | Round_3 | 10439 | 0 | 10439 | 6177 | 976 | 3286 | 0 | 0 | 9463 |
| Uncertain | Round_4 | 10582 | 0 | 10582 | 6240 | 984 | 3358 | 0 | 0 | 9598 |
| Uncertain | Round_5 | 10450 | 0 | 10450 | 6065 | 967 | 3418 | 0 | 0 | 9483 |
| Uncertain | 小计 | 52419 | 0 | 52419 | 30856 | 4840 | 16723 | 0 | 0 | 47579 |
| 分类/描述/Other | Round_1 | 309 | 0 | 309 | 305 | 0 | 1 | 3 | 0 | 309 |
| 分类/描述/Other | Round_2 | 310 | 0 | 310 | 308 | 0 | 1 | 1 | 0 | 310 |
| 分类/描述/Other | Round_3 | 350 | 0 | 350 | 345 | 3 | 1 | 1 | 0 | 347 |
| 分类/描述/Other | Round_4 | 362 | 0 | 362 | 353 | 3 | 3 | 3 | 0 | 359 |
| 分类/描述/Other | Round_5 | 290 | 0 | 290 | 287 | 0 | 0 | 3 | 0 | 290 |
| 分类/描述/Other | 小计 | 1621 | 0 | 1621 | 1598 | 6 | 6 | 11 | 0 | 1615 |
| 合计(去重) | Round_1–5 | 54040 | 0 | 54040 | 32454 | 4846 | 16729 | 11 | 0 | 49194 |

检查：T=H+R+N、R=Z+P+U+C、Q=Z+U+C 在每一行及合计均成立；去重按 sample_id（重复 0）与 pair_id（跨队列重复 0）核对。

## 3. 按 issue_class 统计（Z/U/C）

| 类别 | issue_class | 数量 |
|---|---|---|
| Z | DIFF_SPECIES | 23179 |
| Z | DIFF_FIBRE | 6374 |
| Z | DIFF_MATERIAL | 2901 |
| C | CODE_ISSUE | 11 |
| U | SIBLING_SPEC | 12606 |
| U | REVERSE_STAGE | 4123 |

- Z：DIFF_SPECIES / DIFF_FIBRE / DIFF_MATERIAL（物种、纤维、材料不同）。
- U：SIBLING_SPEC（同一材料族内规格不同）、REVERSE_STAGE（同一生产链方向相反）；按“可能就保留”的字面规则暂留 1，等待一次统一裁定。
- C：CODE_ISSUE（代码在字典中不存在或含义不明，如 290400），不擅自替换。

## 4. 方法与局限

- 以 HS2002 工作字典和 AI 通用知识建立编码级知识表，逐批生成逐对草稿；每批全部行阅读后才写入结果库；运行中发现并修正的规则问题（面粉→糖浆路径、同聚合物纱线被误判、暂时保藏品→干制品）已对受影响的 63 条重读更新。
- `knowledge_basis=COMMON_KNOWLEDGE`，未联网核实，`source_url` 为空。
- 没有任何人工标签，因此不计算准确率或一致率；只有收到人工标签后才能计算已复核子集的一致率。

## 5. 待人工回答的问题

1. U 类（16729 条）是否统一改 0？
2. 面粉/粗粒/片/薯粉 → 葡萄糖及果糖糖浆是否接受为潜在用途（AI 判 P）？
3. 饲料路径（仅养殖肉食鱼虾蟹用饲料鱼/虾蟹/软体动物为投入）是否接受？
4. 11 条代码/分类问题（如 290400）需人工确认真实代码。

## 6. 文件

- `DV_Round_3_Uncertain_Review/` 与 `DV_Round_4_Other_Review/`：各 5 个 Excel、5 个 CSV、5 份 Round 报告和 `_audit/`。
- `Data_Cleaning_Summary.xlsx` / `.csv`：上表。
- `Updated_Pending_Review_Queue.csv`：Z/U/C 共 49194 条（去重），含轮次、队列、pair_id、两端商品、新建议和具体理由。

<!--CHECKS-->
## 9. 交付前自检（2026-10-05）

自动校验共 218 项，失败 0 项，结果：**PASS**。覆盖：源文件哈希未变、目标清单与源文件重新计数一致、无重复/无重叠、Excel 与 CSV 一致、HS6 保留前导零、review_dummy 与状态一致、human 字段为空、黄色条件格式覆盖到末行、human_dummy 仅允许 0/1、无公式、xlsx 内无品牌字符串、T/H/R/Z/P/U/C/N/Q 关系成立。
详细结果见 `_review_tools/validation_result.json`。

<!--/CHECKS-->
