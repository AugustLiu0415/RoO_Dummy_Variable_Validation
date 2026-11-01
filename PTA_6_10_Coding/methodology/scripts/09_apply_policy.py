"""Apply Prof. Zhang's coding decisions (2026-10-19) to the new PTA 6-10 pairs and write the final files.

The policies are the functions and the order of PTA_2_5/_work/09_apply_policy.py (imported, not copied), applied
only to pairs coded in this round (textile rules, AI units, AI pair sample). Exact copies keep the code of PTA 1-5,
so a pair has the same code in every PTA (asserted below).
  P_Q4    route recycle_direct -> DV 1
  P_Q1_2  textile pair coded by the AI pair sample, both fibres synthetic, coded 0, the textile rule finds a route
  P_Q1_1  AI coders disagree, one coded sibling_intermediate and the other did not call it backward -> DV 1
  P_AUD_C, P_AUD_D, P_AUD_A, P_OPT2   textile rules of the 2026-10-19 audit and option 2 override AI-sample zeros
  P_UNC   1 from an uncertain textile rule -> uncertain 1
  P_AUD_B same-material intermediates coded 0 by both AI coders -> DV 1, sibling_intermediate
  P_Q2_1  chemicals (ch. 28-38) -> wastes of heading 3825;  P_Q2_2  minerals of ch. 25 -> cement 2523
  P_FISH  seafood siblings of different species -> 0 unless the input can feed the output
Conventions of 28-30 October 2026 (Prof. Zhang's questionnaire answers; PTA_2_5/_work/conventions.py), new pairs only:
  P_Q3E_own / P_Q3E_other / P_Q3E_0   remelting: own upstream form 1; other primary or semi-finished form 1 +
          uncertain; finished product, vulcanised rubber, thermosets, other polymers 0
  P_Q2C   parts and metal articles of different headings, different compounds of one heading -> uncertain 1
  P_PROF0 pairs both auditors coded 0 where the professor said such pairs are 0 (questions 1, 2(c))
  P_RESCUE a P_Q3E_0 pair for which the rescue screen found another specific route -> 1 + uncertain
          (_work/coded/screen_rescue.csv)
  P_A1    one-sided 1s that both model families judged clearly invalid in the screen (_work/coded/screen_final.csv)
The one-sided 1s left after these are written to _work/coded/screen_pool.csv (the pool for the screen).

Record files. Each original record takes the code of its HS2002 pair. A record mapped to several HS2002 pairs
(TUR_SGP HS2012 codes that are not one-to-one; CHL_KOR invalid codes 610340/610344/610345) takes DV = max over its
pairs (broadest scope), the route and reasons of a certain DV-1 pair that is not an HS2002 self-pair where one exists,
and uncertain = 1 when its pairs differ (uncertain_reason "HS concordance: ..."). Only a record whose input and output
are the same code in its own vintage is locked at 1 (same good). A TUR_SGP record with two different HS2012 codes
whose HS2002 pairs include an HS2002 self-pair is coded on its HS2012 codes by both AI coders (concord_pairs.csv,
source ai_concord), because the self-pair only says that both goods share an HS2002 subheading. Records whose input
is not an HS6 code (TUR_SGP "WO", "any") are deleted (Prof. Zhang, 2026-10-28; until then their DV was missing).
Outputs: final/<PTA>_coded_<DATE>.dta and .csv, final/master_coded_final.csv, final/policy_report.json.

Run after 06_combine.py: /usr/local/bin/python3 _work/09_apply_policy.py
"""
import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CODED, FINAL, INTAKE, LABELS_PTA1, NAMES, PTAS, SEA, load_coded_master, REF  # noqa: E402
from textile import COMMON_RULES, UNCERTAIN_RULES, attributes, load_texts  # noqa: E402
import conventions as CV  # noqa: E402

P25 = importlib.import_module('09_apply_policy')         # PTA_2_5/_work/09_apply_policy.py (policy functions)
apply, fish_policy, family, synthetic, textile_rule = (P25.apply, P25.fish_policy, P25.family, P25.synthetic,
                                                       P25.textile_rule)
DATE = '2026_11_01'                                       # DV_strict dropped (Prof. Zhang, 2026-11-01)
CONCORD_REASON = 'HS concordance: the HS2002 pairs of this record differ'
SCREEN = CODED / 'screen_final.csv'                      # A1 screen: pairs both families judged clearly invalid
RESCUE = CODED / 'screen_rescue.csv'                     # P_Q3E_0 pairs with another specific route (rescue screen)


def policies(F, A, L, T, vintage='HS2002'):
    """the PTA 2-5 policies, in their order, then the conventions of 28-30 October and the A1 screen, on the pairs
    coded in this round; returns {policy: (DV changed, rows)}"""
    sea_feed = (L.route == 'feed') & L.input_hs6.str[:4].isin(SEA) & L.output_hs6.str[:4].isin(SEA)
    FEED_IN, FARMED = set(L.input_hs6[sea_feed]), set(L.output_hs6[sea_feed])
    nc = (F.source != 'exact_copy') & (F.input_hs6 != F.output_hs6) & (F.locked != 1)
    pol = {'P_Q4': apply(F, nc & (F.route == 'recycle_direct'), 'P_Q4', DV=1)}
    new = F.source != 'exact_copy'                       # rule ids for every new pair (reasons); masks use nc
    rules = textile_rule(zip(F.input_hs6[new], F.output_hs6[new]), A)
    get = lambda i, d: pd.Series([rules.get((a, b), (None, '', None, ''))[i] if n else d  # noqa: E731
                                  for a, b, n in zip(F.input_hs6, F.output_hs6, new)], index=F.index)
    rd, rr, rid = get(0, None), get(1, ''), get(3, '')
    F['rule_id_now'] = rid
    fi, fo = F.input_hs6.map(A.fibre), F.output_hs6.map(A.fibre)
    syn = (fi.map(synthetic, na_action='ignore').eq(True) & fo.map(synthetic, na_action='ignore').eq(True))
    pol['P_Q1_2'] = apply(F, nc & (F.source == 'ai_sample') & syn & (F.DV == 0) & (rd == 1), 'P_Q1_2', DV=1,
                          uncertain=0, route=rr, step='')
    both = (F.dv_ai1 != '') & (F.dv_ai2 != '')
    dis = nc & both & (F.dv_ai1 != F.dv_ai2)
    st1, st2 = pd.to_numeric(F.step_ai1, errors='coerce'), pd.to_numeric(F.step_ai2, errors='coerce')
    sib1 = (F.route_ai1 == 'sibling_intermediate') & (st2 != 5)
    sib2 = (F.route_ai2 == 'sibling_intermediate') & (st1 != 5)
    pol['P_Q1_1'] = apply(F, dis & (sib1 | sib2), 'P_Q1_1', DV=1, uncertain=0, route='sibling_intermediate', step='')
    for r_id, pid in P25.RULE_C_D.items():
        pol[pid] = apply(F, nc & (rid == r_id) & (rd == 1) & (F.DV == 0), pid, DV=1, uncertain=0, route=rr, step='')
    pol['P_AUD_A'] = apply(F, nc & rid.isin(P25.UNC_A) & (rd == 1) & (F.DV == 0), 'P_AUD_A', DV=1, uncertain=1,
                           route=rr, step='')
    pol['P_OPT2'] = apply(F, nc & rid.isin(COMMON_RULES) & (rd == 1) & (F.DV == 0), 'P_OPT2', DV=1, uncertain=0,
                          route=rr, step='')
    by_rule = nc & rid.isin(UNCERTAIN_RULES) & (F.DV == 1) & (F.uncertain == 0) & (F.source == 'rule_textile')
    pol['uncertain_rule_category'] = apply(F, by_rule, 'P_UNC', uncertain=1)
    fi_, fo_ = family(F.input_hs6), family(F.output_hs6)
    agree0 = (F.dv_ai1 == '0') & (F.dv_ai2 == '0') & (F.DV == 0)
    bmask = nc & both & agree0 & (fi_ != '') & (fi_ == fo_) & (st1 != 5) & (st2 != 5)
    pol['P_AUD_B'] = apply(F, bmask, 'P_AUD_B', DV=1, uncertain=0, route='sibling_intermediate', step='')
    chem = nc & F.input_hs6.str[:2].between('28', '38') & (F.output_hs6.str[:4] == '3825')
    pol['P_Q2_1'] = apply(F, chem, 'P_Q2_1', DV=1, uncertain=0, route='recycle_waste', step='')
    mine = nc & (F.input_hs6.str[:2] == '25') & (F.input_hs6.str[:4] != '2523') & (F.output_hs6.str[:4] == '2523')
    pol['P_Q2_2'] = apply(F, mine, 'P_Q2_2', DV=1, uncertain=0, route='ingredient', step='')
    pol.update(fish_policy(F, nc, FEED_IN, FARMED))
    pol.update(CV.apply_conventions(F, nc, T, A, apply, vintage))
    R = pd.read_csv(RESCUE, dtype=str, keep_default_na=False) if RESCUE.exists() else None
    pol.update(CV.apply_rescue(F, nc, R, apply, vintage))
    pool = CV.screen_pool(F, nc)
    F['screen_pool'] = pool.astype(int)
    S = pd.read_csv(SCREEN, dtype=str, keep_default_na=False) if SCREEN.exists() else None
    pol.update(CV.apply_screen(F, pool, S, apply, vintage))
    # uncertain_reason of the new pairs, with the categories of PTA_2_5/_work/09 (every AI disagreement counts,
    # including locked pairs)
    dis = new & both & (F.dv_ai1 != F.dv_ai2)
    cat = np.select(
        [F.uncertain == 0, rid == 'T_CONSTITUENT', rid.isin(P25.UNC_A), F.policy.str.contains('P_FISH'),
         F.policy.str.contains('P_Q3E_other'), F.policy.str.contains('P_Q2C') | F.policy.str.contains('P_2CFLAG'),
         F.policy.str.contains('P_RESCUE'),
         dis & ((F.route_ai1 == 'sibling_intermediate') | (F.route_ai2 == 'sibling_intermediate')), dis],
        ['', 'minor constituent of a garment or made-up: other fibre or construction',
         'minor constituent of a yarn or fabric: other fibre', 'possible feed (rock lobster)',
         'remelting into another primary or semi-finished form (convention of 2026-10-30)',
         'same-material intermediate of another heading, or another compound (convention of 2026-10-30)',
         'remelting excluded (convention of 2026-10-30), another route possible',
         'AI coders disagree: sibling or backward', 'AI coders, or the model and the textile rules, disagree'],
        'other')
    F['uncertain_reason'] = np.where(new, cat, F.uncertain_reason)
    return pol


def aggregate(R):
    """one row per record from its HS2002 pairs (R: record_pairs joined with the pair codes)"""
    R = R.assign(self_pair=(R.input_hs6 == R.output_hs6).astype(int))
    R = R.sort_values(['record_no', 'DV', 'uncertain', 'self_pair', 'master_id'],
                      ascending=[True, False, True, True, True])
    g = R.groupby('record_no', sort=False)
    out = g.head(1).set_index('record_no').copy()            # a certain DV-1 pair, not an HS2002 self-pair, first
    hs_self = out.self_pair == 1                             # own codes differ (own self-records are locked later)
    out.loc[hs_self, 'locked'] = 0
    out.loc[hs_self, 'step'] = ''
    out['n_pairs'] = g.size()
    out['mapped_DV1_share'] = g.DV.mean().round(4)
    out['DV_excl_remelt'] = g.DV_excl_remelt.max()
    mixed = g.DV.nunique() > 1
    out['mixed'] = mixed
    out.loc[mixed[mixed].index, 'uncertain'] = 1
    out.loc[mixed[mixed].index, 'uncertain_reason'] = CONCORD_REASON
    return out


def concord_codes(A, L, T):
    """two-coder codes of the TUR_SGP concordance pairs (HS2012), with the policies applied; indexed by record_no"""
    f = CODED / 'concord_coded.csv'
    if not f.exists():
        return None, {}
    C = pd.read_csv(f, dtype=str, keep_default_na=False)
    C['DV'], C['uncertain'] = C.DV.astype(int), C.uncertain.astype(int)
    C['locked'] = ((C.route == 'same_good') & (C.uncertain == 0)).astype(int)
    C['policy'], C['uncertain_reason'] = '', ''
    pol = policies(C, A, L, T, 'HS2012')
    C = P25.finish(C).drop(columns='DV_strict')            # DV only (Prof. Zhang, 2026-11-01)
    C.loc[C.DV == 1, 'step'] = np.where(C.loc[C.DV == 1, 'route'] == 'same_good', C.loc[C.DV == 1, 'step'], '')
    C.loc[C.uncertain == 0, 'uncertain_reason'] = ''
    C['why_ai1'], C['why_ai2'] = C.reason_ai1, C.reason_ai2
    C['copy_from'], C['ml_prob'], C['ml_supported'] = '', '', ''
    C['master_id'] = 'HS2012|' + C.input_hs6 + '>' + C.output_hs6
    C.drop(columns=['reason_ai1', 'reason_ai2']).to_csv(FINAL / 'concord_coded_final.csv', index=False)
    rep = {'pairs': len(C), 'records': int(C.n_records.astype(int).sum()), 'DV1': int(C.DV.sum()),
           'uncertain': int(C.uncertain.sum()),
           'policies': {k: {'rows_matched': v[1], 'DV_changed': v[0]} for k, v in pol.items() if v[1]}}
    C['record_no'] = C.record_nos.str.split(';')
    C = C.explode('record_no')
    C['record_no'] = C.record_no.astype(int)
    return C.set_index('record_no'), rep


def main():
    T = load_texts()
    A = attributes([k for k in T if len(k) == 6 and k.isdigit()], T)
    L = pd.read_csv(LABELS_PTA1, dtype=str, keep_default_na=False)
    F = pd.read_csv(CODED / 'master_coded_combined.csv', dtype=str, keep_default_na=False)
    for c in ('DV', 'uncertain', 'locked'):
        F[c] = F[c].astype(int)
    before = F[['DV', 'uncertain']].copy()
    pol = policies(F, A, L, T)
    F = P25.finish(F).drop(columns='DV_strict')            # DV only (Prof. Zhang, 2026-11-01)
    F.loc[F.DV == 1, 'step'] = np.where(F.loc[F.DV == 1, 'route'] == 'same_good', F.loc[F.DV == 1, 'step'], '')
    new = F.source != 'exact_copy'
    F.loc[new & (F.DV == 0), 'uncertain'] = 0
    F.loc[new & (F.uncertain == 0), 'uncertain_reason'] = ''
    F['why_ai1'], F['why_ai2'] = F.reason_ai1, F.reason_ai2

    # a pair has the same code in every PTA
    M = load_coded_master().set_index(['input_hs6', 'output_hs6'])
    ex = F[F.source == 'exact_copy']
    m = M.loc[list(zip(ex.input_hs6, ex.output_hs6))]
    consistency = {'exact_copies': len(ex),
                   'DV_differs': int((ex.DV.values != m.DV.values).sum()),
                   'uncertain_differs': int((ex.uncertain.values != m.uncertain.values).sum()),
                   'route_differs': int((ex.route.values != m.route.values).sum())}
    assert consistency['DV_differs'] == consistency['uncertain_differs'] == consistency['route_differs'] == 0, \
        consistency
    FINAL.mkdir(parents=True, exist_ok=True)
    F.drop(columns=['reason_ai1', 'reason_ai2']).to_csv(FINAL / 'master_coded_final.csv', index=False)

    rep = {'decisions': 'Prof. Zhang 2026-10-19 (PTA_2_5_coding_questions_2026_10_18_Hao.docx and replies); conventions '
                        'of 2026-10-30 (PTA_6_10_coding_questions_2026_10_28_answered.docx, Coding_Rules_2026_10_30.md I.9); '
                        'A1 screen (_work/coded/screen_final.csv) and rescue screen (screen_rescue.csv); '
                        'meeting of 2026-11-01: DV is the main variable, DV_strict is no longer computed',
           'policies_on_new_pairs': {k: {'rows_matched': v[1], 'DV_changed': v[0]} for k, v in pol.items()},
           'new_pairs': {'pairs': int(new.sum()), 'DV1_before_policies': int(before.DV[new].sum()),
                         'DV1': int(F.DV[new].sum()), 'uncertain': int(F.uncertain[new].sum()),
                         'by_source': F[new].groupby('source').DV.agg(['size', 'sum']).rename(
                             columns={'size': 'pairs', 'sum': 'DV1'}).to_dict('index'),
                         'uncertain_by_reason': F.uncertain_reason[new & (F.uncertain == 1)].value_counts().to_dict()},
           'consistency_with_PTA_1_5': consistency}

    # ---- per-PTA record files
    H4 = {x['id']: x['text'] for x in json.load(open(REF / 'H4.json'))['results']}
    clean = lambda t: t.split(' - ', 1)[-1].lstrip('- ').strip() if ' - ' in t else t  # noqa: E731
    desc2 = lambda c: f'{T.get(c[:4], "")} | {T.get(c, T.get(c[:5], ""))}'.strip(' |')  # noqa: E731
    desc4 = lambda c: f'{clean(H4.get(c[:4], ""))} | {clean(H4.get(c, ""))}'.strip(' |')  # noqa: E731
    pv = ['DV', 'DV_excl_remelt', 'DV_max', 'uncertain', 'uncertain_reason', 'locked', 'step', 'route',
          'source', 'copy_from', 'policy', 'ml_prob', 'ml_supported', 'dv_ai1', 'dv_ai2', 'why_ai1', 'why_ai2',
          'master_id']
    Fi = F.set_index(['input_hs6', 'output_hs6'])[pv]
    CC, rep['concord_pairs'] = concord_codes(A, L, T)
    # the one-sided 1s that no rule or convention settled: the pool for the A1 screen
    PC = ['input_hs6', 'output_hs6', 'DV', 'uncertain', 'route', 'policy', 'source', 'n_records', 'dv_ai1', 'route_ai1',
          'why_ai1', 'dv_ai2', 'route_ai2', 'why_ai2']
    # and the pairs convention 3 set to 0 (the pool for the rescue screen: is there another specific route?)
    Cp = pd.read_csv(FINAL / 'concord_coded_final.csv', dtype=str, keep_default_na=False) if CC is not None else None
    pool = [F.loc[F.screen_pool == 1, PC].assign(vintage='HS2002')]
    rpool = [F.loc[F.policy.str.contains('P_Q3E_0'), PC].assign(vintage='HS2002')]
    if Cp is not None:
        pool.append(Cp.loc[Cp.screen_pool == '1', PC].assign(vintage='HS2012'))
        rpool.append(Cp.loc[Cp.policy.str.contains('P_Q3E_0'), PC].assign(vintage='HS2012'))
    pool = pd.concat(pool, ignore_index=True)
    pool.to_csv(CODED / 'screen_pool.csv', index=False)
    pd.concat(rpool, ignore_index=True).to_csv(CODED / 'rescue_pool.csv', index=False)
    rep['screen_pool'] = {'pairs': len(pool), 'set_to_0_by_screen': int(pool.policy.str.contains('P_A1').sum()),
                          'screen_file': str(SCREEN) if SCREEN.exists() else 'none yet'}
    rp = pd.read_csv(INTAKE / 'record_pairs.csv', dtype=str)
    rp['record_no'] = rp.record_no.astype(int)
    labels = {'output_hs6': 'output: HS6 code in the agreement\'s HS vintage (original output_str)',
              'output_description': 'output: heading | subheading text (HS vintage of the agreement)',
              'input_hs6': 'input: HS6 code in the agreement\'s HS vintage (original input_str)',
              'input_description': 'input: heading | subheading text (HS vintage of the agreement)',
              'VA_Alternative': 'copied unchanged from the original file',
              'VA_Complement': 'copied unchanged from the original file',
              'special_rule': 'copied unchanged from the original file',
              'pta': 'agreement', 'record_no': 'row number in the original file',
              'pair_id': 'unique row id (pta|input>output|record_no)', 'hs_vintage': 'HS vintage of the codes',
              'input_type': 'hs6 (records whose input is WO / any were deleted, 2026-10-28)',
              'input_hs2002': 'input mapped to HS2002 (; separates several codes)',
              'output_hs2002': 'output mapped to HS2002 (; separates several codes)',
              'n_mapped_pairs': 'number of HS2002 pairs the record maps to',
              'mapped_DV1_share': 'share of those HS2002 pairs with DV = 1',
              'concord_flag': '1 = code not one-to-one with HS2002 or not a valid code',
              'concord_note': 'type of the HS concordance link',
              'DV': '1 = input can be used to make output (main)',
              'DV_excl_remelt': 'like DV, but direct remelting (recycle_direct) = 0',
              'DV_max': 'same as DV (kept for older code)',
              'uncertain': '1 = kept at 1 but uncertain (see uncertain_reason)',
              'uncertain_reason': 'why uncertain = 1',
              'locked': '1 = input and output are the same good (step 2)',
              'step': 'workflow step that set DV = 0 (2 = same good)',
              'route': 'why DV = 1 (forward, component, ...) or none',
              'source': 'how the code was reached (copy, rule, AI coders)',
              'copy_from': 'coded list an exact copy comes from (ASEAN_JPN or PTA_2_5)',
              'policy': 'decision, convention (2026-10-19, 2026-10-30) or A1 screen that changed the pair',
              'ml_prob': 'ML probability that DV = 1 (information only)',
              'ml_supported': '1 = ML model had enough similar coded pairs',
              'dv_ai1': 'DV of AI coder 1 (Claude), where coded', 'dv_ai2': 'DV of AI coder 2 (Codex), where coded',
              'why_ai1': 'reason of AI coder 1 (Claude)', 'why_ai2': 'reason of AI coder 2 (Codex)',
              'master_id': 'id of the HS2002 input-output pair (same in every PTA)'}
    BYTE = ['VA_Alternative', 'VA_Complement', 'special_rule', 'DV', 'DV_excl_remelt', 'DV_max',
            'uncertain', 'locked', 'concord_flag']
    DOUBLE = ['step', 'ml_prob', 'ml_supported', 'dv_ai1', 'dv_ai2', 'mapped_DV1_share']
    order = ['output_hs6', 'output_description', 'input_hs6', 'input_description', 'VA_Alternative', 'VA_Complement',
             'special_rule', 'pta', 'record_no', 'pair_id', 'hs_vintage', 'input_type', 'input_hs2002',
             'output_hs2002', 'n_mapped_pairs', 'mapped_DV1_share', 'concord_flag', 'concord_note'] + pv
    rep['pta'] = {}
    for p in PTAS:
        R0 = pd.read_csv(INTAKE / f'records_{p}.csv', dtype=str, keep_default_na=False)
        R0['record_no'] = R0.record_no.astype(int)
        J = rp[rp.pta == p].join(Fi, on=['input_hs6', 'output_hs6'])
        assert J.DV.notna().all(), p
        Ag = aggregate(J)
        P = R0.drop(columns=['input_str', 'output_str']).join(Ag[pv + ['mapped_DV1_share', 'mixed']], on='record_no')
        nh = P.input_type != 'hs6'                           # TUR_SGP "WO" / "any": deleted (Prof. Zhang, 2026-10-28)
        assert P.DV[nh].isna().all() and P.DV[~nh].notna().all(), p
        P = P[~nh].copy()
        conc =P.record_no.isin(CC.index) if (p == 'TUR_SGP' and CC is not None) else pd.Series(False, index=P.index)
        if p == 'TUR_SGP':
            assert CC is not None, 'concord_coded.csv missing: run 06_combine.py after both coders coded concord_pairs'
            for c in pv:
                P.loc[conc, c] = P.loc[conc, 'record_no'].map(CC[c]).values
            P.loc[conc, 'mixed'] = False
        selfp = (P.input_type == 'hs6') & (P.input_hs6 == P.output_hs6)
        P.loc[selfp, 'mixed'] = False
        P.loc[selfp, ['DV', 'DV_excl_remelt', 'DV_max', 'uncertain', 'uncertain_reason', 'locked',
                      'step', 'route']] = [1, 1, 1, 0, '', 1, '2', 'same_good']
        multi = P.n_mapped_pairs.astype(int) > 1
        vint = P.hs_vintage.iloc[0]
        dfun = desc4 if vint == 'HS2012' else desc2
        P['output_description'] = P.output_hs6.map(dfun)
        P['input_description'] = P.input_hs6.map(dfun)
        mixed = P.mixed.fillna(False).astype(bool)
        P = P[[c for c in order if c in P.columns and not (c == 'special_rule' and p != 'TUR_SGP')]]
        Pd = P.copy()
        for c in BYTE:
            if c in Pd:
                v = pd.to_numeric(Pd[c].replace('', np.nan).infer_objects(), errors='raise')
                assert v.dropna().isin([0, 1]).all(), (p, c)
                assert v.notna().all() or c not in ('VA_Alternative', 'VA_Complement', 'concord_flag'), (p, c)
                Pd[c] = v.astype('Int8')
        for c in DOUBLE:
            Pd[c] = pd.to_numeric(Pd[c].replace('', np.nan).infer_objects(), errors='raise').astype('float64')
        Pd['record_no'] = Pd.record_no.astype('int32')
        Pd['n_mapped_pairs'] = Pd.n_mapped_pairs.astype('int16')
        for c in Pd.columns:
            if Pd[c].dtype == object:
                Pd[c] = Pd[c].fillna('').astype(str)
        Pd.to_csv(FINAL / f'{p}_coded_{DATE}.csv', index=False)
        Pd.to_stata(FINAL / f'{p}_coded_{DATE}.dta', write_index=False, version=118,
                    convert_strl=['input_description', 'output_description', 'why_ai1', 'why_ai2', 'concord_note',
                                  'uncertain_reason', 'policy'],
                    variable_labels={c: labels[c] for c in Pd.columns},
                    data_label=f'{NAMES[p]}: RoO input-output pairs coded {DATE}')
        rep['pta'][p] = {
            'records_in_original_file': len(R0), 'records': len(P), 'hs_vintage': vint,
            'records_deleted_not_hs6_input': int(nh.sum()),
            'DV1': int(P.DV.sum()), 'DV1_share': round(float(P.DV.mean()), 4),
            'uncertain': int(P.uncertain.sum()),
            'uncertain_share_of_DV1': round(float(P.uncertain.sum() / max(P.DV.sum(), 1)), 4),
            'records_mapped_to_several_pairs': int(multi.sum()),
            'records_concordance_mixed': int(mixed.sum()),
            'records_coded_on_HS2012_codes': int(conc.sum()),
            'source': P.source.value_counts().to_dict(),
            'copy_from': P.copy_from[P.copy_from != ''].value_counts().to_dict(),
            'uncertain_by_reason': P.uncertain_reason[P.uncertain == 1].value_counts().to_dict()}
    json.dump(rep, open(FINAL / 'policy_report.json', 'w'), indent=1, default=int)
    print(json.dumps(rep, indent=1, default=int))


if __name__ == '__main__':
    main()
