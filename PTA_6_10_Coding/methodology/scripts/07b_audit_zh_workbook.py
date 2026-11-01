"""Chinese workbook of the audit review items, for reporting to Prof. Zhang.

Reads audit/audit_review.xlsx (August's marks), _work/coded/audit_review_zh.json (Chinese goods names and auditors'
reasons: translated by AI, checked against the English by a second AI), _work/coded/audit_key.csv and
final/ai_audit_report.json (07_audit.py score). Writes 不确定配对_中文对照_2026_10_28.xlsx in the PTA6_10 folder:
说明, 最终准确率, 不确定配对_判1, 不确定配对_判0, 黄色其余19对, 全部复核79对.

Run after 07_audit.py score: /usr/local/bin/python3 _work/07b_audit_zh_workbook.py
"""
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import BASE, CODED, FINAL, PTAS  # noqa: E402

OUT = BASE / '不确定配对_中文对照_2026_10_28.xlsx'
ROUTE = {'same_good': '同一商品', 'forward': '直接加工', 'ingredient': '原料/工艺投入', 'component': '零部件',
         'reconstitute': '还原', 'mixture': '混合物成分', 'recycle_waste': '废料回收', 'recycle_direct': '直接回熔',
         'feed': '饲料', 'sibling_intermediate': '中间品平行品', 'none': '—'}
SOURCE = {'ai_units': 'AI 编码', 'ai_concord': 'HS2012 对照', 'exact_copy': '直接复制 PTA 1–5', 'rule_textile': '纺织规则'}
GROUP = {('红', 1): '红一：coder 分歧（1 + uncertain），两位审核者都判 0',
         ('红', 2): '红二：纺织规则编 0，两位审核者都判 1',
         ('红', 3): '红三：纺织规则编 1 → 传动带 5910，两位审核者都判 0',
         ('红', 4): '红四：AI 或 HS2012 对照的确定编码，两位审核者都不同意',
         ('红', 5): '红五：直接复制的编码，两位审核者都不同意',
         ('黄', 1): '黄一：coder 分歧（1 + uncertain），两位审核者意见不同',
         ('黄', 2): '黄二：最终编码 1（确定），两位审核者意见不同',
         ('黄', 3): '黄三：最终编码 0，两位审核者意见不同'}
WIDTH = {'序号': 6, 'audit_id': 8, '复核类别': 26, '编码来源': 12, 'HS版本': 8, '投入 HS6': 9, '投入品': 32,
         '产出 HS6': 9, '产出品': 32, '最终 DV': 7, '最终路线': 12, 'uncertain': 9, 'Claude 判断': 8,
         'Claude 路线': 12, 'Claude 理由': 40, 'Codex 判断': 8, 'Codex 路线': 12, 'Codex 理由': 40,
         'August 判断': 9, 'August 备注': 24}
FILL = {'红': 'F8D7DA', '黄': 'FFF3CD'}
GROUP_NOTES = {'2026-10-28 不确定配对，判 1（报告教授）', '2026-10-28 August 判 1'}   # marks given to a whole group


def load_audit():
    spec = importlib.util.spec_from_file_location('audit07', Path(__file__).with_name('07_audit.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pct(e):
    return f"{e['est'] * 100:.1f}%（{e['ci95'][0] * 100:.1f}–{e['ci95'][1] * 100:.1f}）" if e else ''


def table_sheet(wb, name, d):
    s = wb.create_sheet(name)
    cols = list(d.columns)
    s.append(cols)
    for _, x in d.iterrows():
        s.append([x[c] for c in cols])
    for i, c in enumerate(cols, 1):
        s.column_dimensions[s.cell(1, i).column_letter].width = WIDTH[c]
        s.cell(1, i).font = Font(bold=True)
        s.cell(1, i).fill = PatternFill('solid', fgColor='D9E2F3')
        s.cell(1, i).alignment = Alignment(wrap_text=True, vertical='center', horizontal='center')
    for row in s.iter_rows(min_row=2):
        f = PatternFill('solid', fgColor=FILL[str(row[2].value)[0]])
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.fill = f
    s.freeze_panes = 'C2'
    s.auto_filter.ref = s.dimensions


def main():
    m = load_audit()
    zh = json.load(open(CODED / 'audit_review_zh.json'))
    r = pd.read_excel(BASE / 'audit/audit_review.xlsx', dtype=str).fillna('')
    key = pd.read_csv(CODED / 'audit_key.csv', dtype=str)
    r = r.merge(key[['audit_id', 'master_id', 'stratum']], on='audit_id')
    rep = json.load(open(FINAL / 'ai_audit_report.json'))
    res = rep['after_August_review']

    rows = []
    for a, z in sorted(zh.items(), key=lambda t: (t[1]['color'] != '红', t[1]['order'])):
        x = r.set_index('audit_id').loc[a]
        rows.append({'序号': 0, 'audit_id': a, '复核类别': GROUP[(z['color'], z['grp'])], '编码来源': SOURCE[x.family],
                     'HS版本': x.hs_vintage, '投入 HS6': x.input_hs6, '投入品': z['input_zh'], '产出 HS6': x.output_hs6,
                     '产出品': z['output_zh'], '最终 DV': int(x.final_DV), '最终路线': ROUTE.get(x.final_route, ''),
                     'uncertain': int(x.final_uncertain), 'Claude 判断': int(x.claude_dv),
                     'Claude 路线': ROUTE.get(x.claude_route, ''), 'Claude 理由': z['claude_zh'],
                     'Codex 判断': int(x.codex_dv), 'Codex 路线': ROUTE.get(x.codex_route, ''),
                     'Codex 理由': z['codex_zh'], 'August 判断': x.August_dv, 'August 备注': x.August_note})
    A = pd.DataFrame(rows)
    A['序号'] = range(1, len(A) + 1)
    sheets = {'不确定配对_判1': A[A.复核类别.str.startswith('黄一')], '不确定配对_判0': A[A.复核类别.str.startswith('红一')],
              '黄色其余19对': A[A.复核类别.str.startswith(('黄二', '黄三'))], '全部复核79对': A}

    # true value of every sample item, as in 07_audit.py score
    W, _ = m.weights(key)
    mark = r.August_dv.map(m.read_mark).astype(float)
    review = ~r.status.str.startswith('3')
    truth = mark.where(mark.notna(), r.final_DV.astype(float).where(~review))
    ok = (r.final_DV.astype(float) == truth).astype(float).where(truth.notna())
    ua = r[(r.final_uncertain == '1') & r.family.isin(['ai_units', 'ai_concord'])]
    t = truth[ua.index]
    # the yellow items (auditors disagree) were marked 1 as a group on 2026-10-28, not judged one by one; an item
    # leaves the group once August marks it again with another note
    tb = ua.August_note.isin(GROUP_NOTES)
    judged = mark[ua.index].notna() & ~tb

    info = [
        ['PTA 6–10 准确率审核：复核对子中文对照（2026-10-28）'], [''],
        ['内容', '本文件把准确率审核中由 August 复核的 79 对翻译成中文，并列出最终准确率，供向张教授报告。'],
        ['审核方法', '从第二轮草稿的最终编码中分层抽取 305 对；Claude 与 Codex 两个全新的 AI 会话按 2026-10-19 规则独立盲审；'
                 '两位审核者与最终编码不一致（红色 40 对）、或两位审核者意见不同（黄色 39 对）的对子由 August 判断真实值；'
                 '其余 226 对两位审核者都与最终编码一致，视为正确。'],
        ['不确定配对', '两位 AI coder 意见不同时，按 10-19 规则编为 DV = 1、uncertain = 1（DV_strict = 0）。'],
        ['样本中的不确定配对', f'样本中由 AI 编码（含 HS2012 对照）的不确定配对共 {len(ua)} 对：August 逐对复核，判为 0 的 '
                      f'{int((judged & (t == 0)).sum())} 对' + (f'、判为 1 的 {n1} 对' if (n1 := int((judged & (t == 1)).sum())) else '') + '；两位审核者都同意'
                      f'最终编码 1、未经复核的 {int((~judged & ~tb & (t == 1)).sum())} 对；另有 {int(tb.sum())} 对两位审核者'
                      '意见不同，按 August 的指示统一判为 1，没有逐对判断，教授答复问卷后按新口径重判。'
                      'DV 把真实值为 0 的算错，DV_strict 把真实值为 1 的算错，两者夹住真实值。'],
        ['最终准确率', f"复核{'已完成' if res['complete'] else '未完成'}。DV：按 pair {pct(res['DV']['pair_weighted'])}，"
                  f"按记录 {pct(res['DV']['record_weighted'])}；DV_strict：按 pair {pct(res['DV_strict']['pair_weighted'])}，"
                  f"按记录 {pct(res['DV_strict']['record_weighted'])}。括号内为 95% 区间。详见“最终准确率”。"],
        ['翻译', '商品名称与两位审核者的理由由 AI 翻译，并由另一个 AI 对照英文原文核对；如有出入以英文原文'
               '（audit/audit_review.xlsx）为准。'],
        ['工作表', '最终准确率；不确定配对_判1（黄一 20 对）；不确定配对_判0（红一 21 对）；黄色其余19对（黄二、黄三）；'
                '全部复核79对（红 40 + 黄 39）。'],
    ]
    wb = Workbook()
    ws = wb.active
    ws.title = '说明'
    for row in info:
        ws.append(row)
    ws['A1'].font = Font(bold=True, size=13)
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['B'].width = 110
    for row in ws.iter_rows(min_row=3):
        row[0].font = Font(bold=True)
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')

    acc = wb.create_sheet('最终准确率')
    acc.append(['指标', '按 pair', '按记录'] + PTAS)
    for v in ('DV', 'DV_strict'):
        e = res[v]
        acc.append([v, pct(e['pair_weighted']), pct(e['record_weighted'])] + [pct(e.get(f'records_{p}')) for p in PTAS])
    acc.append([])
    acc.append(['按编码来源（DV，按 pair）', '样本对数', '其中错误', '准确率（95% 区间）'])
    for fam in ('exact_copy', 'ai_units', 'ai_concord', 'rule_textile'):
        sel = r.family == fam
        acc.append([SOURCE[fam], int(sel.sum()), int((ok[sel] == 0).sum()),
                    pct(m.estimate(ok.where(sel), r, W, by_pta=False)['pair_weighted'])])
    acc.append([])
    acc.append(['说明', '按记录：每条记录计一次；各协定按自身记录构成加权（借用同一来源层在各协定的准确率）。'
                      'TUR_SGP 另有 2,273 条 WO/any 记录未编码，不在审核范围内（10-28 会议决定删除）。'])
    for i, w in enumerate([26, 22, 22] + [20] * len(PTAS), 1):
        acc.column_dimensions[acc.cell(1, i).column_letter].width = w
    for c in acc[1]:
        c.font = Font(bold=True)
    for row in acc.iter_rows():
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
    for c in acc[5]:
        c.font = Font(bold=True)

    for name, d in sheets.items():
        d = d.copy()
        d['序号'] = range(1, len(d) + 1)
        table_sheet(wb, name, d)
    wb.save(OUT)
    print(f'{OUT.name}: ' + ', '.join(f'{k} {len(v)}' for k, v in sheets.items()))


if __name__ == '__main__':
    main()
