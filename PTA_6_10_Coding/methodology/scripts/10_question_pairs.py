"""Pairs that each question of the 2026-10-28 questionnaire touches, over every coded pair of PTA 1-10. Preparation for
re-coding after Prof. Zhang answers (Workflow_补充规则_2026_10_28.md, part D): the answers apply to all agreements.

Universe: the ASEAN-Japan labels of 2026-10-19, the PTA 2-5 master (pairs not in the labels), the new HS2002 pairs of
PTA 6-10 and the TUR_SGP HS2012 concordance pairs. One row per coded pair: a pair copied into later agreements is listed
once, where it was coded, with its record counts in PTA 2-5 and PTA 6-10.

Question tags (QUESTIONS) take the route of a coder who coded 1, or the final route (a 0-voter's route does not count),
plus chapters and headings; a few are keyword screens on the 1-voter's reason (KEYWORD_TAGS), which see only AI-coded
pairs and are screens: re-judging decides membership. A pair can carry several tags; `primary` gives the first in
QUESTIONS, route tags before keyword tags, as the questionnaire assigns overlapping pairs by the AI's route.
Scope tags (SCOPE_TAGS) list pairs now coded 0 that a broad answer would also reach; they are not question members.
Information tags:
  Q2b_semi        semi-finished metal on both sides: the rules' own example (steel plate -> steel bar = 1), not 2(b)
  Q3_chem         chemical recycle_direct pairs: conversions, left to question 1 (the 3-1 options do not fit them)
  Q3_vulcanised   vulcanised rubber (4007-4017) remelted into chapter 40 other than 4003/4004 (no rule codes it yet)
  Q3_0vote        recycle_direct named only by a coder who coded 0 (PTA 2-5): relevant only to a broad answer
  Q4_parts        component pairs whose input is a part: settled by the rules, not question 4
  Q5a_rags_ctx    yarn or fabric -> rags 6310 (coded 1 by T_RAGS); question 5(a) names only -> 6309 and fibre -> 6310
  Q5b, Q5c        screens for by-products (animal and food residues, slag) and component waste (8548)
  Q10_knit_pile   knitted and pile fabrics of different main fibres within one heading (same rule as question 10)
  B3              chapter-59 pairs corrected in textile.py on 2026-10-29
  ASEAN_open      open cases of the ASEAN-Japan labels (route unresolved, DV 1 + uncertain); textile ones get the
                  current textile rule in rule_dv_now / rule_id_now
  A1_pool         AI disagreements that no question covers and no policy settled: the pool for screening obviously
                  invalid one-sided 1s (decision A1)
  audit_flagged   exact copies the audit marked wrong; only A243 rests on a judgment (A064, A201, A285: group marks)
Remelting columns for question 3: material and level (0 primary, 1 semi-finished, 2 article) of input and output;
q3_A (output is a primary form of the input's material: option 3-1 A), q3_B (a primary or semi-finished form: B) and
q3_C (same material: C) say which pairs each option codes 1.
Outputs: _work/coded/question_pairs_2026_10_29.csv and .json.

Run: /usr/local/bin/python3 _work/10_question_pairs.py
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CODED, FINAL, LABELS_PTA1, MASTER_P25, P25, REF, pta1_uncertain_reason  # noqa: E402
from textile import COATED, FIBRE, attributes, code_pair, fibre_compatible, load_texts  # noqa: E402

OUT = CODED / 'question_pairs_2026_10_29'
P25_PTAS = ['BRN_JPN', 'AUS_USA', 'CAFTA', 'BHR_USA']
AI_COLS = ['dv_ai1', 'route_ai1', 'why_ai1', 'dv_ai2', 'route_ai2', 'why_ai2']
COLS = ['input_hs6', 'output_hs6', 'DV', 'uncertain', 'uncertain_reason', 'route', 'policy', 'source', 'rule_id'] + AI_COLS
KW = {'Q1_other': r'consum(?:ed|es|ption|able)|used up|\bfuel\b|reductant|reducing agent|\breduc(?:e|es|ing)\b[^.;]{0,40}'
                  r'(?:metal|oxide|ore|compound)|reagent|catalys|solvent|\bflux(?:es|ing)?\b|dopant|mineralis|mineraliz'
                  r'|as (?:an )?abrasive|leach|binding agent|as (?:a )?binder',
      'Q6': r'refit|refashion|recut|re-?shap|rebuil|repurpos|salvag|adapted (?:into|as)|fitted (?:out|with)'
            r'|cut (?:up|down|into)|converted (?:into|to)',
      'Q7a': r'contain|associated|accessory mineral|impurit|recover|by-?product|concentrat|separa|beneficiat',
      'Q7b': r'crush|rubble|broken|ground (?:up|into)|grind(?:ing)? (?:up|down|into)|recover|reclaim|scrap'}
KEYWORD_TAGS = ['Q7a', 'Q7b', 'Q1_other', 'Q6']
QUESTIONS = ['Q10', 'Q5a', 'Q9', 'Q3_2_glass', 'Q3_2_paper', 'Q3_2_plastics', 'Q3_1', 'Q2c', 'Q1_chem', 'Q2a', 'Q2b',
             'Q4', 'Q5', 'Q8', 'Q7a', 'Q7b', 'Q1_other', 'Q6', 'Q2_PQ11']           # order = priority for `primary`
SCOPE_TAGS = ['Q2b_scope0', 'Q3_scope0', 'Q8_scope0']
SETTLED = r'P_Q2_1|P_Q2_2|P_Q1_1|P_FISH'                 # policies of 2026-10-19 that decide a pair
AUDIT_FLAGGED = ['A243', 'A064', 'A201', 'A285']
FAB_S, FAB_A = {'5512', '5513', '5514', '5515', '5407'}, {'5516', '5408'}   # synthetic / artificial woven fabrics
KNIT_PILE = {'5801', '6001', '6002', '6003', '6004', '6005', '6006'}
FILM = {'3701', '3702', '3703', '3704', '3705', '3706', '3919', '4010', '8523', '8524'}   # goods sold by size (Q9)
SIZE = r'width|length|circumference|exceeding|\bmm\b|\bcm\b'      # subheadings that differ by size (Q9)
FOOD_OUT = {'0403', '0405', '0406', '0901', '0902', '0910', '1517'}     # prepared foods outside chapters 16-24
BYPRODUCT = {'0502', '0503', '0504', '0505', '0506', '0507', '0510', '0511', '1522', '2301', '2302', '2303', '2304',
             '2305', '2306', '2307', '2308', '2618', '2619', '2620', '2621'}
ARTICLE_HEADINGS = {'7411', '7412', '7413', '7414', '7415', '7416', '7417', '7418', '7419', '7507', '7508', '7805',
                    '7806', '7906', '7907', '8006', '8007'} | {str(h) for h in range(7608, 7617)}
# remelting levels by heading: unwrought or primary forms, semi-finished forms (incl. tubes, as in option 3-1 B)
PRIMARY = ({'7201', '7202', '7203', '7205', '7206', '7207', '7401', '7402', '7403', '7405', '7501', '7502', '7601', '7801',
            '7901', '8001', '7001', '4001', '4002', '4003', '4005'} | {str(h) for h in range(3901, 3915)}
           | {str(h) for h in range(4701, 4707)})
SEMI = ({str(h) for h in range(7207, 7230)} | {str(h) for h in range(7303, 7307)}
        | {'7406', '7407', '7408', '7409', '7410', '7411', '7504', '7505', '7506', '7507', '7603', '7604', '7605',
           '7606', '7607', '7608', '7804', '7903', '7904', '7905', '8003', '8004', '8005', '8006', '7002', '7003',
           '7004', '7005', '7006', '7019', '3916', '3917', '3919', '3920', '3921', '4006', '4007', '4008'}
        | {str(h) for h in range(4801, 4812)})
NOT_THERMOPLASTIC = {'391710', '392063', '392071', '392072', '392079', '392093', '392094', '392113', '392114'}


def metal_article(h):
    """heading of a metal article (chapters 73, 82, 83 and the articles of chapters 74-80), not a semi-finished form"""
    return h.str[:2].isin(['73', '82', '83']) | h.isin(ARTICLE_HEADINGS)


def material(c):
    """base material of a good for remelting: iron and steel, a non-ferrous metal, glass, plastics, paper, rubber"""
    ch, h = c[:2], c[:4]
    if ch in ('72', '73'):
        return 'iron_steel'
    if ch in ('74', '75', '76', '78', '79', '80'):
        return 'metal' + ch
    if ch == '81':
        return 'metal' + h
    return {'70': 'glass', '39': 'plastics', '47': 'paper', '48': 'paper', '49': 'paper', '40': 'rubber'}.get(ch, '')


def level(c, T):
    """0 primary form (ingots, semi-finished steel cast from the melt, unwrought metal, pulp, primary plastics, glass in
    the mass), 1 semi-finished form (bars, wire, plates, tubes, base paper, sheet glass, plastic sheets), 2 article"""
    h = c[:4]
    if h in PRIMARY or c in ('721810', '721891', '721899', '722410', '722490') or (h[:2] == '81' and 'unwrought' in T.get(c, '').lower()):
        return 0
    return 1 if h in SEMI else 2


def universe():
    L = pd.read_csv(LABELS_PTA1, dtype=str, keep_default_na=False)
    L['uncertain'] = L.uncertain.astype(float).astype(int)
    L['uncertain_reason'] = pta1_uncertain_reason(L)
    L['uncertain'] = L.uncertain.astype(str)
    L['DV'] = L.DV.astype(float).astype(int).astype(str)
    L['source'], L['rule_id'] = 'pta1_label', ''
    for c in AI_COLS:
        L[c] = ''
    L = L[COLS].assign(origin='ASEAN_JPN', vintage='HS2002')
    F = pd.read_csv(MASTER_P25, dtype=str, keep_default_na=False)
    lk = pd.MultiIndex.from_frame(L[['input_hs6', 'output_hs6']])
    F = F[~pd.MultiIndex.from_frame(F[['input_hs6', 'output_hs6']]).isin(lk)][COLS].assign(origin='PTA_2_5',
                                                                                          vintage='HS2002')
    Q = pd.read_csv(FINAL / 'master_coded_final.csv', dtype=str, keep_default_na=False)
    Qn = Q[Q.source != 'exact_copy'][COLS].assign(origin='PTA_6_10', vintage='HS2002')
    U = pd.concat([L, F, Qn], ignore_index=True)

    # where each pair occurs: ASEAN-Japan (one record per label), PTA 2-5 records, PTA 6-10 records
    R = pd.concat([pd.read_csv(P25 / f'_work/intake/pairs_{p}.csv', dtype=str, usecols=['input_hs6', 'output_hs6', 'pta'])
                   for p in P25_PTAS])
    g = R.groupby(['input_hs6', 'output_hs6'])
    r25 = pd.DataFrame({'n_rec_2_5': g.size(), 'ptas_2_5': g.pta.agg(lambda s: ';'.join(sorted(set(s))))})
    q = Q.set_index(['input_hs6', 'output_hs6'])[['n_records', 'ptas']].rename(
        columns={'n_records': 'n_rec_6_10', 'ptas': 'ptas_6_10'})
    U = U.join(r25, on=['input_hs6', 'output_hs6']).join(q, on=['input_hs6', 'output_hs6'])
    C = pd.read_csv(FINAL / 'concord_coded_final.csv', dtype=str, keep_default_na=False)
    C['rule_id'] = C.rule_id_now
    C = C[COLS + ['n_records']].rename(columns={'n_records': 'n_rec_6_10'}).assign(
        origin='PTA_6_10', vintage='HS2012', ptas_6_10='TUR_SGP')
    U = pd.concat([U, C], ignore_index=True)
    assert not U.duplicated(['vintage', 'input_hs6', 'output_hs6']).any()
    U['in_ASEAN'] = (U.origin == 'ASEAN_JPN').astype(int)
    for c in ('n_rec_2_5', 'n_rec_6_10'):
        U[c] = pd.to_numeric(U[c]).fillna(0).astype(int)
    for c in ('ptas_2_5', 'ptas_6_10'):
        U[c] = U[c].fillna('')
    return U


def tag(U, T, A):
    ic, oc = U.input_hs6.str[:2].astype(int), U.output_hs6.str[:2].astype(int)
    ih, oh = U.input_hs6.str[:4], U.output_hs6.str[:4]
    has1 = lambda r: (((U.dv_ai1 == '1') & (U.route_ai1 == r)) | ((U.dv_ai2 == '1') & (U.route_ai2 == r))  # noqa: E731
                      | (U.route == r))
    has0 = lambda r: ((U.dv_ai1 == '0') & (U.route_ai1 == r)) | ((U.dv_ai2 == '0') & (U.route_ai2 == r))  # noqa: E731
    U['split'] = ((U.dv_ai1 != '') & (U.dv_ai2 != '') & (U.dv_ai1 != U.dv_ai2)).astype(int)
    why1 = (np.where(U.dv_ai1 == '1', U.why_ai1, '') + ' | ' + np.where(U.dv_ai2 == '1', U.why_ai2, ''))
    why1 = pd.Series(why1, index=U.index).str.lower()
    kw = {k: why1.str.contains(p) for k, p in KW.items()}
    diff = U.input_hs6 != U.output_hs6
    film37 = (ic == 37) & (oc == 37)
    chem = ic.between(28, 38) & oc.between(28, 38) & diff & ~film37
    sib, rd = has1('sibling_intermediate'), has1('recycle_direct')
    codes = pd.unique(pd.concat([U.input_hs6, U.output_hs6]))
    mat = {c: material(c) for c in codes}
    lev = {c: level(c, T) for c in codes}
    U['mat_in'], U['mat_out'] = U.input_hs6.map(mat), U.output_hs6.map(mat)
    U['lev_in'], U['lev_out'] = U.input_hs6.map(lev), U.output_hs6.map(lev)
    same_mat = (U.mat_in != '') & (U.mat_in == U.mat_out)
    U['q3_A'] = (same_mat & (U.lev_out == 0) & (U.lev_in > 0)).astype(int)
    U['q3_B'] = (same_mat & (U.lev_out <= 1)).astype(int)
    U['q3_C'] = same_mat.astype(int)
    art_i, art_o = metal_article(ih), metal_article(oh)
    metals = ic.between(72, 83) & oc.between(72, 83)
    text = lambda c: (T.get(c[:4], '') + ' | ' + T.get(c, '')).lower()  # noqa: E731
    parts = U.input_hs6.map({c: bool(re.search(r'\bparts?\b|accessor', text(c))) for c in codes})
    fib = A.fibre.to_dict()
    tex = U.input_hs6.isin(A.index) & U.output_hs6.isin(A.index)
    G = pd.DataFrame(index=U.index)
    G['Q1_chem'] = chem & (oh != '3825')
    G['Q1_other'] = ~chem & kw['Q1_other']
    G['Q2a'] = sib & ic.between(84, 90) & oc.between(84, 90)
    G['Q2b_semi'] = sib & metals & ~art_i & ~art_o
    G['Q2b'] = sib & metals & ~G.Q2b_semi
    G['Q2c'] = sib & chem & (ih == oh)
    G['Q2_PQ11'] = U.policy.str.contains('P_Q1_1')
    G['Q3_chem'] = rd & chem
    G['Q3_1'] = rd & ~G.Q3_chem
    G['Q3_2_glass'] = G.Q3_1 & (ic == 70) & (oc == 70)
    G['Q3_2_paper'] = G.Q3_1 & ic.between(47, 49) & oc.between(47, 49)
    G['Q3_2_plastics'] = G.Q3_1 & (ic == 39) & (oc == 39)
    G['Q3_vulcanised'] = G.Q3_1 & ih.between('4007', '4017') & (oc == 40) & ~oh.isin(['4003', '4004'])
    G['Q3_0vote'] = has0('recycle_direct') & ~rd
    U['not_thermoplastic'] = (G.Q3_2_plastics & (U.input_hs6.isin(NOT_THERMOPLASTIC)
                                                 | U.output_hs6.isin(NOT_THERMOPLASTIC))).astype(int)
    comp = has1('component') & ic.between(84, 96) & oc.between(84, 96)
    G['Q4_parts'] = comp & parts
    G['Q4'] = comp & ~parts
    G['Q5a'] = ((oh == '6309') & ic.between(50, 60)) | ((oh == '6310') & ih.isin(FIBRE))
    G['Q5a_rags_ctx'] = (oh == '6310') & ic.between(50, 60) & ~ih.isin(FIBRE)
    waste = has1('recycle_waste') & ~(ic.between(28, 38) & (oh == '3825')) & ~G.Q5a & ~G.Q5a_rags_ctx
    G['Q5'] = waste
    G['Q5b'] = waste & oh.isin(BYPRODUCT) & ic.between(1, 27)
    G['Q5c'] = waste & (oh == '8548') & ~ih.isin(['8506', '8507'])
    raw = ic.between(1, 40) | ic.isin([47, 48, 68, 72]) | ic.between(50, 60) | ic.between(74, 81)
    G['Q6'] = kw['Q6'] & ~raw
    G['Q7a'] = (ic.between(25, 26) & oc.between(25, 26) & ((ih != oh) | ih.isin(['2612', '2616', '2617', '2530']))
                & kw['Q7a'])
    G['Q7b'] = ic.between(68, 69) & kw['Q7b']
    food = ic.between(1, 24) & (oc.between(16, 24) | oh.isin(FOOD_OUT))
    G['Q8'] = food & (has1('ingredient') | has1('mixture'))
    sized = U.input_hs6.map({c: bool(re.search(SIZE, T.get(c, '').lower())) for c in codes})
    sized_o = U.output_hs6.map({c: bool(re.search(SIZE, T.get(c, '').lower())) for c in codes})
    G['Q9'] = ih.isin(FILM) & (ih == oh) & diff & ((sized & sized_o) | (U.input_hs6.str[:5] == U.output_hs6.str[:5]))
    G['Q10'] = (ih.isin(FAB_S) & oh.isin(FAB_A)) | (ih.isin(FAB_A) & oh.isin(FAB_S))
    G['Q10_knit_pile'] = tex & ih.isin(KNIT_PILE) & (ih == oh) & pd.Series(
        [not fibre_compatible(fib[a], fib[b]) if t else False
         for a, b, t in zip(U.input_hs6, U.output_hs6, tex)], index=U.index)
    dv0 = U.DV == '0'
    G['Q2b_scope0'] = dv0 & art_i & art_o & (U.mat_in == U.mat_out) & (U.mat_in != '') & ~G.Q2b
    G['Q3_scope0'] = dv0 & same_mat & (U.lev_out <= 1) & ~G.Q3_1 & ~G.Q3_0vote
    G['Q8_scope0'] = dv0 & food & ~G.Q8
    G['B3'] = (U.vintage == 'HS2002') & ((ih.isin(['5908', '5909']) & (oh == '5910')) | (ih.isin(COATED) & (oh == '5910'))
                                         | ((ih == '5901') & (oh == '5902')))
    G['ASEAN_open'] = (U.origin == 'ASEAN_JPN') & (U.route == 'unresolved')
    G['A1_pool'] = (U.split == 1) & ~G[QUESTIONS].any(axis=1) & ~U.policy.str.contains(SETTLED)
    key = pd.read_csv(CODED / 'audit_key.csv', dtype=str)
    ids = set(key[key.audit_id.isin(AUDIT_FLAGGED)].master_id.str.split('|').str[-1])
    G['audit_flagged'] = (U.vintage == 'HS2002') & (U.input_hs6 + '>' + U.output_hs6).isin(ids)
    assert G.audit_flagged.sum() == len(AUDIT_FLAGGED), G.audit_flagged.sum()

    # the textile rule of today for open textile labels (mechanical resolution candidates)
    U['rule_dv_now'], U['rule_id_now'] = '', ''
    ot = G.ASEAN_open & tex & diff
    rows = _Rows(A.to_dict('index'))
    r = [code_pair(a, b, rows) for a, b in zip(U.input_hs6[ot], U.output_hs6[ot])]
    U.loc[ot, 'rule_dv_now'] = [str(x[0]) for x in r]
    U.loc[ot, 'rule_id_now'] = [x[4] for x in r]
    U['tags'] = G.apply(lambda x: ';'.join(G.columns[x.values]), axis=1)
    first = G[QUESTIONS].values.argmax(axis=1)
    U['primary'] = np.where(G[QUESTIONS].any(axis=1), np.array(QUESTIONS)[first], '')
    return U, G


class _Rows:
    """dict-of-rows wrapper with the .loc[code].attr access code_pair uses"""
    def __init__(self, d):
        self.d = d
        self.loc = self

    def __getitem__(self, c):
        return pd.Series(self.d[c], name=c)


def main():
    T = load_texts()
    A = attributes([k for k in T if len(k) == 6 and k.isdigit()], T)
    U, G = tag(universe(), T, A)
    keep = G.any(axis=1)
    H4 = {x['id']: x['text'] for x in json.load(open(REF / 'H4.json'))['results']}
    clean = lambda t: t.split(' - ', 1)[-1].lstrip('- ').strip() if ' - ' in t else t  # noqa: E731
    d2 = lambda c: f'{T.get(c[:4], "")} | {T.get(c, "")}'.strip(' |')  # noqa: E731
    d4 = lambda c: f'{clean(H4.get(c[:4], ""))} | {clean(H4.get(c, ""))}'.strip(' |')  # noqa: E731
    X = U[keep].copy()
    h12 = X.vintage == 'HS2012'
    for s in ('input', 'output'):
        X[f'{s}_description'] = np.where(h12, X[f'{s}_hs6'].map(d4), X[f'{s}_hs6'].map(d2))
    cols = ['primary', 'tags', 'origin', 'vintage', 'input_hs6', 'input_description', 'output_hs6',
            'output_description', 'DV', 'uncertain', 'route', 'policy', 'source', 'rule_id',
            'uncertain_reason', 'split'] + AI_COLS + ['mat_in', 'lev_in', 'mat_out', 'lev_out', 'q3_A', 'q3_B',
                                                      'q3_C', 'not_thermoplastic', 'rule_dv_now', 'rule_id_now',
                                                      'in_ASEAN', 'ptas_2_5', 'n_rec_2_5', 'ptas_6_10', 'n_rec_6_10']
    X[cols].sort_values(['primary', 'origin', 'input_hs6', 'output_hs6']).to_csv(f'{OUT}.csv', index=False)

    def count(t):
        m, x = G[t], U[G[t]]
        by = {o: {'pairs': int((x.origin == o).sum()), 'split': int(x.split[x.origin == o].sum()),
                  'DV1': int((x.DV[x.origin == o] == '1').sum()),
                  'uncertain': int((x.uncertain[x.origin == o] == '1').sum())}
              for o in ('ASEAN_JPN', 'PTA_2_5', 'PTA_6_10')}
        return {'pairs': int(m.sum()), 'by_origin': by, 'records_PTA_6_10': int(x.n_rec_6_10.sum()),
                'records_PTA_2_5': int(x.n_rec_2_5.sum()), 'ASEAN_records': int(x.in_ASEAN.sum()),
                'primary': int((U.primary[m] == t).sum()) if t in QUESTIONS else None}
    # the questionnaire's own counts (new AI-unit pairs of PTA 6-10, routes of either AI coder), and corrected ones
    a = (U.origin == 'PTA_6_10') & (U.source == 'ai_units')
    ai = lambda r: (U.route_ai1 == r) | (U.route_ai2 == r)  # noqa: E731
    ic, oc = U.input_hs6.str[:2].astype(int), U.output_hs6.str[:2].astype(int)
    ih, oh = U.input_hs6.str[:4], U.output_hs6.str[:4]
    chem_any = ic.between(28, 38) & oc.between(28, 38)
    rd_any = a & ai('recycle_direct')
    stated = {'Q1_chem': a & chem_any & (oh != '3825'),
              'Q2a': a & ai('sibling_intermediate') & ic.between(84, 90) & oc.between(84, 90),
              'Q2b': a & ai('sibling_intermediate') & ic.between(72, 83) & oc.between(72, 83),
              'Q2c': a & ai('sibling_intermediate') & chem_any & (ih == oh),
              'Q3_1': rd_any, 'Q3_1_not_upstream_same_chapter_test': rd_any & ~((ic == oc) & (oh < ih)),
              'Q4': a & ai('component') & ic.between(84, 96) & oc.between(84, 96), 'Q5': a & ai('recycle_waste'),
              'Q8': a & ic.between(1, 24) & oc.between(16, 24),
              'Q10_ASEAN_DV1_5516_2x_4x': G.Q10 & (U.origin == 'ASEAN_JPN') & (U.DV == '1') & (
                  U.input_hs6.str[:5].isin(['55162', '55164']) | U.output_hs6.str[:5].isin(['55162', '55164']))}
    corrected = {'Q2b_metal_articles': a & G.Q2b, 'Q3_1_not_upstream_material_test': rd_any & (U.q3_A == 0),
                 'Q3_vulcanised': a & G.Q3_vulcanised, 'Q4_complete_machines': a & G.Q4,
                 'Q8_ingredient_route': a & G.Q8, 'Q9_size_family_all_origins': G.Q9,
                 'Q10_ASEAN_DV1_all': G.Q10 & (U.origin == 'ASEAN_JPN') & (U.DV == '1'),
                 'Q10_knit_pile_ASEAN_DV1': G.Q10_knit_pile & (U.origin == 'ASEAN_JPN') & (U.DV == '1'),
                 'Q1_chem_DV0_ASEAN': G.Q1_chem & (U.origin == 'ASEAN_JPN') & (U.DV == '0'),
                 'Q1_chem_both_coders_0_PTA_2_5': G.Q1_chem & (U.origin == 'PTA_2_5') & (U.dv_ai1 == '0')
                 & (U.dv_ai2 == '0'),
                 'P_Q1_1_outside_Q2': G.Q2_PQ11 & ~(G.Q2a | G.Q2b | G.Q2b_semi | G.Q2c)}
    n = lambda d: {k: {'pairs': int(m.sum()), 'split': int(U.split[m].sum()), 'DV1': int((U.DV[m] == '1').sum())}  # noqa
                   for k, m in d.items()}
    rep = {'universe': {'pairs': len(U), 'by_origin': U.origin.value_counts().to_dict(),
                        'split': int(U.split.sum())},
           'keyword_tags': KEYWORD_TAGS, 'scope_tags': SCOPE_TAGS,
           'tags': {t: count(t) for t in G.columns},
           'questionnaire_definition_as_stated': n(stated), 'corrected_counts': n(corrected),
           'pairs_with_any_question': int(G[QUESTIONS].any(axis=1).sum()),
           'split_pairs_covered_by_a_question': int((G[QUESTIONS].any(axis=1) & (U.split == 1)).sum())}
    json.dump(rep, open(f'{OUT}.json', 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
