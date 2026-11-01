"""Apply Prof. Zhang's coding decisions of 2026-10-19 to all five PTAs and write the final files.

Decisions (PTA_2_5_coding_questions_2026_10_18_Hao.docx):
  1-1 A  intermediate goods of the same material at the same stage are linked (sibling_intermediate = 1);
         siblings of finished goods stay 0 (workflow step 4).
  1-2 A  different synthetic polymers count as one fibre (textile rules changed in textile.py; ASEAN-Japan labels
         aligned here).
  1-3 A  fabrics of the same fibre but different construction are linked (already in the textile rules).
  2-1 A  any chemical (chapters 28-38) is an input of the wastes of heading 3825.
  2-2 A  any mineral of chapter 25 is an input of cement (heading 2523).
  2-3 A  a technically possible use counts; where the two AI coders still disagree the pair stays 1, uncertain 1.
  3   D  minor fibre constituents of garments and made-ups: DV 1, uncertain 1 (unchanged).
  4      comment: direct remelting is 1 in the main DV and keeps route = recycle_direct (the box ticked was "0 in DV,
         1 in DV_max"; DV_excl_remelt below gives that version).
General principle: keep 1 wherever any production route is possible; AI-coder disagreement -> DV 1, uncertain 1.

Policies, applied in this order (each changed row records the policy id in `policy`):
  P_Q4    route recycle_direct -> DV 1                                   (ASEAN-Japan and PTA 2-5)
  P_Q1_2  textile pair, both fibres synthetic, labelled 0, the textile rule finds a route -> DV 1   (ASEAN-Japan,
          and PTA 2-5 pairs coded by the AI pair sample)
  P_Q1_1  AI coders disagree, one coded sibling_intermediate and the other did not call it backward -> DV 1
  P_CONF  textile ML-rule conflict where the textile rule finds a route -> rule's code, uncertain 0
  P_Q2_1  input in chapters 28-38, output in heading 3825 -> DV 1, recycle_waste
  P_Q2_2  input in chapter 25 (not 2523), output in heading 2523 -> DV 1, ingredient
  P_UNC   already 1 from the textile rules or the model, in an uncertain rule category -> uncertain 1
Corrections after the independent AI audit of 2026-10-19:
  P_AUD_A minor fibre, yarn or waste of another fibre in a yarn or fabric -> DV 1, uncertain 1
  P_AUD_B same-material intermediates coded 0 by both AI coders -> DV 1, sibling_intermediate
  P_AUD_C sewing thread <-> yarn and twine -> DV 1;  P_AUD_D clothing accessories -> garments -> DV 1, component
Prof. Zhang's replies of 2026-10-19 (afternoon):
  P_FISH  seafood siblings of different species -> 0 (step 3) unless the input can feed the output (feed, 1)
  P_OPT2  option 2: a cotton or man-made input as a minor constituent (garments, yarns, fabrics) -> DV 1, certain
          (the textile rules code these directly as T_CONSTITUENT_COMMON, T_FORWARD_COMMON_FIBRE,
          T_WASTE_COMMON_FIBRE; P_OPT2 marks labelled or AI-coded 0s that the rule turns to 1)
Exact copies in PTA 2-5 are re-copied from the new ASEAN-Japan labels, so a pair has the same code in every PTA.

Run after 06_combine.py (it reads the master list that 06 writes and overwrites it with the policy version).
Outputs: Data_Validation_Through_Machine_Learning/labels_2026_10_19/outputs/ (new dated ASEAN-Japan labels and their
change log; the frozen 10-15 file and the 10-18 labels are untouched); PTA_2_5/final/<PTA>_coded_2026_10_19.dta and
.csv for the five PTAs, master_coded_final.csv, policy_report.json and policy_report.md.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from dta_old import read_any_dta  # noqa: E402
from textile import COMMON_RULES, FAMILY, UNCERTAIN_RULES, attributes, code_pair, load_texts  # noqa: E402

ML = PROJECT / 'Data_Validation_Through_Machine_Learning'
LAB_IN = ML / 'labels_2026_10_18/outputs/PTA_1_labels_2026_10_18.csv'
LAB_DIR = ML / 'labels_2026_10_19/outputs'
FINAL = HERE.parent / 'final'
V2 = HERE.parent / 'final_v2_2026_10_18'
DATE = '2026_10_19'
PTAS = ['BRN_JPN', 'AUS_USA', 'CAFTA', 'BHR_USA']
CODE_COLS = ['DV', 'uncertain', 'route', 'step', 'locked']
UNC_A = {'T_FORWARD_OTHER_FIBRE', 'T_WASTE_OTHER_FIBRE_MINOR'}     # audit group A: minor constituents in yarn/fabric
RULE_C_D = {'T_THREAD_TO_YARN': 'P_AUD_C', 'T_ACCESSORY_TO_GARMENT': 'P_AUD_D'}
SEA = ('0301', '0302', '0303', '0304', '0305', '0306', '0307', '1604', '1605', '2301')   # fish and other seafood
FARMED_MAYBE = {'030611', '030621'}   # rock lobster: farmed on trash fish in parts of ASEAN, outside the feed convention


def fish_policy(df, mask, feed_in, farmed):
    """Prof. Zhang, 2026-10-19 (reply to point 3): different fish species are 0 unless the input could feed the
    output. Sibling pairs of seafood become feed (1) when the input is a feed-grade good and the output a farmed
    carnivore under the ASEAN-Japan feed convention, 1 with uncertain for rock lobster, and 0 (step 3) otherwise."""
    sea = mask & df.input_hs6.str[:4].isin(SEA) & df.output_hs6.str[:4].isin(SEA) & (df.route == 'sibling_intermediate')
    fin = df.input_hs6.isin(feed_in)
    out = {'P_FISH_feed': apply(df, sea & fin & df.output_hs6.isin(farmed), 'P_FISH', DV=1, uncertain=0, route='feed',
                                step=''),
           'P_FISH_maybe': apply(df, sea & fin & df.output_hs6.isin(FARMED_MAYBE), 'P_FISH', DV=1, uncertain=1,
                                 route='feed', step='')}
    out['P_FISH_0'] = apply(df, sea & (df.route == 'sibling_intermediate'), 'P_FISH', DV=0, uncertain=0, route='none',
                            step='3')
    return out


def family(code):
    """same-material families of intermediate goods (decision 1-1), used for audit group B"""
    x = code.str[:4].astype(int)
    ch = code.str[:2]
    glass = {7001, 7002, 7003, 7004, 7005, 7006, 7011, 7014, 7015, 7016, 7018, 7019}
    return np.select([x.between(4801, 4813), x.between(7206, 7229), x.isin(glass), x.between(2302, 2308),
                      ch.isin(['74', '75', '76', '78', '79', '80'])],
                     ['paper', 'steel', 'glass', 'feed residues', 'metal ch' + ch], '')


def synthetic(f):
    return f == 'syn' or FAMILY.get(f) == 'syn'


class _Rows:
    """dict-of-rows wrapper with the .loc[code].attr access code_pair uses (fast)"""
    def __init__(self, d):
        self.d = d
        self.loc = self

    def __getitem__(self, c):
        return pd.Series(self.d[c], name=c)


def textile_rule(pairs, A):
    """textile rule (dv, route, step, rule id) for (input, output) pairs with both codes in chapters 50-63"""
    out, R, idx = {}, _Rows(A.to_dict('index')), set(A.index)
    for a, b in pairs:
        if a in idx and b in idx and a != b and (a, b) not in out:
            r = code_pair(a, b, R)
            out[(a, b)] = (r[0], r[2], r[3], r[4])
    return out


def apply(df, mask, pid, **vals):
    """set values on rows in mask that change; record the policy id; return number of rows whose DV changed"""
    m = mask.copy()
    before = df.loc[m, 'DV'].copy()
    for k, v in vals.items():
        df.loc[m, k] = v if not isinstance(v, pd.Series) else v[m]
    df.loc[m, 'policy'] = np.where(df.loc[m, 'policy'] == '', pid, df.loc[m, 'policy'] + ';' + pid)
    return int((before != df.loc[m, 'DV']).sum()), int(m.sum())


def finish(df):
    df['DV'] = df.DV.astype(int)
    df['uncertain'] = df.uncertain.astype(int)
    df['DV_strict'] = df.DV * (1 - df.uncertain)
    df['DV_max'] = df.DV
    df['DV_excl_remelt'] = np.where(df.route == 'recycle_direct', 0, df.DV)
    return df


def main():
    T = load_texts()
    A = attributes([k for k in T if len(k) == 6 and k.isdigit()], T)
    rep = {'decisions_file': 'PTA_2_5_coding_questions_2026_10_18_Hao.docx', 'policies': {}}

    # ---------------- ASEAN-Japan (PTA_1) labels ----------------
    L = pd.read_csv(LAB_IN, dtype=str, keep_default_na=False)
    L['DV'] = L.DV.astype(float).astype(int)
    L['uncertain'] = L.uncertain.astype(float).astype(int)
    L['locked'] = L.locked.astype(float).astype(int)
    L['policy'] = ''
    L0 = L.copy()
    rules = textile_rule(zip(L.input_hs6, L.output_hs6), A)
    L['rule_dv'] = [rules.get((a, b), (None,))[0] for a, b in zip(L.input_hs6, L.output_hs6)]
    L['rule_route'] = [rules.get((a, b), (None, ''))[1] for a, b in zip(L.input_hs6, L.output_hs6)]
    fi, fo = L.input_hs6.map(A.fibre), L.output_hs6.map(A.fibre)
    pol = {}
    pol['P_Q4'] = apply(L, L.route == 'recycle_direct', 'P_Q4', DV=1)
    m = (fi.map(synthetic, na_action='ignore').fillna(False).astype(bool)
         & fo.map(synthetic, na_action='ignore').fillna(False).astype(bool)
         & (L.DV == 0) & (L.rule_dv == 1) & (L.relation_class != 'BACKWARD'))
    pol['P_Q1_2'] = apply(L, m, 'P_Q1_2', DV=1, uncertain=0, route=L.rule_route, step='')
    L['rule_id'] = [rules.get((a, b), (None, '', None, ''))[3] for a, b in zip(L.input_hs6, L.output_hs6)]
    for rid, pid in RULE_C_D.items():      # these rules replace the earlier "thread -> yarn is backward" labels too
        pol[pid] = apply(L, (L.DV == 0) & (L.rule_id == rid) & (L.rule_dv == 1), pid, DV=1, uncertain=0,
                         route=L.rule_route, step='')
    lab0 = (L.DV == 0) & (L.relation_class != 'BACKWARD')
    pol['P_AUD_A'] = apply(L, lab0 & L.rule_id.isin(UNC_A) & (L.rule_dv == 1), 'P_AUD_A', DV=1, uncertain=1,
                           route=L.rule_route, step='')
    pol['P_OPT2'] = apply(L, lab0 & L.rule_id.isin(COMMON_RULES) & (L.rule_dv == 1), 'P_OPT2', DV=1, uncertain=0,
                          route=L.rule_route, step='')
    # feed convention of the ASEAN-Japan labels: inputs and outputs of its seafood feed pairs
    sea_feed = (L.route == 'feed') & L.input_hs6.str[:4].isin(SEA) & L.output_hs6.str[:4].isin(SEA)
    FEED_IN, FARMED = set(L.input_hs6[sea_feed]), set(L.output_hs6[sea_feed])
    pol.update(fish_policy(L, L.input_hs6 != L.output_hs6, FEED_IN, FARMED))
    L['DV_strict'] = L.DV * (1 - L.uncertain)
    L['DV_max'] = L.DV
    L['DV_excl_remelt'] = np.where(L.route == 'recycle_direct', 0, L.DV)
    LAB_DIR.mkdir(parents=True, exist_ok=True)
    keep = [c for c in L0.columns if c not in ('rule_dv', 'rule_route', 'rule_id')] + ['DV_excl_remelt']
    L[keep].to_csv(LAB_DIR / 'PTA_1_labels_2026_10_19.csv', index=False)
    ch = L.DV != L0.DV
    L.loc[ch | (L.policy != ''), ['pair_id', 'input_hs6', 'output_hs6', 'relation_class', 'route', 'policy']].assign(
        DV_before=L0.DV[ch | (L.policy != '')], DV_after=L.DV[ch | (L.policy != '')]).to_csv(
        LAB_DIR / 'changes_2026_10_19.csv', index=False)
    rep['pta1'] = {'rows': len(L), 'DV1_before': int(L0.DV.sum()), 'DV1_after': int(L.DV.sum()),
                   'policies': {k: {'rows_matched': v[1], 'DV_changed': v[0]} for k, v in pol.items()},
                   'labels_sha256': hashlib.sha256(open(LAB_DIR / 'PTA_1_labels_2026_10_19.csv', 'rb').read()).hexdigest()}
    Li = L.set_index(['input_hs6', 'output_hs6'])

    # ---------------- PTA 2-5 master ----------------
    F = pd.read_csv(FINAL / 'master_coded_final.csv', dtype=str, keep_default_na=False)
    F0v2 = pd.read_csv(V2 / 'master_coded_final.csv', dtype=str, keep_default_na=False).set_index('master_id')
    for c in ['DV', 'uncertain', 'locked']:
        F[c] = F[c].astype(int)
    F['policy'] = ''
    pre = F.copy()                                            # after the textile-rule change, before policies
    # re-copy exact copies from the new labels
    ex = F.source == 'exact_copy'
    key = list(zip(F.input_hs6[ex], F.output_hs6[ex]))
    for c in ['DV', 'uncertain', 'route', 'step', 'locked']:
        F.loc[ex, c] = Li.loc[key, c].values
    F.loc[ex, 'policy'] = Li.loc[key, 'policy'].values
    F['DV'] = F.DV.astype(int)
    F['uncertain'] = F.uncertain.astype(int)
    pol2 = {'recopy_from_new_PTA1_labels': (int((pre.DV[ex] != F.DV[ex]).sum()), int(ex.sum()))}
    nc = ~ex & (F.input_hs6 != F.output_hs6) & (F.locked != 1)   # policies never touch copies, self-pairs, locked pairs
    pol2['P_Q4'] = apply(F, nc & (F.route == 'recycle_direct'), 'P_Q4', DV=1)
    rules2 = textile_rule(zip(F.input_hs6, F.output_hs6), A)
    rd = pd.Series([rules2.get((a, b), (None,))[0] for a, b in zip(F.input_hs6, F.output_hs6)], index=F.index)
    rr = pd.Series([rules2.get((a, b), (None, ''))[1] for a, b in zip(F.input_hs6, F.output_hs6)], index=F.index)
    rs = pd.Series([rules2.get((a, b), (None, '', None))[2] for a, b in zip(F.input_hs6, F.output_hs6)], index=F.index)
    rid = pd.Series([rules2.get((a, b), (None, '', None, ''))[3] for a, b in zip(F.input_hs6, F.output_hs6)],
                    index=F.index)
    fi2, fo2 = F.input_hs6.map(A.fibre), F.output_hs6.map(A.fibre)
    syn2 = (fi2.map(synthetic, na_action='ignore').fillna(False).astype(bool)
            & fo2.map(synthetic, na_action='ignore').fillna(False).astype(bool))
    m = nc & (F.source == 'ai_sample') & syn2 & (F.DV == 0) & (rd == 1)
    pol2['P_Q1_2'] = apply(F, m, 'P_Q1_2', DV=1, uncertain=0, route=rr, step='')
    both = (F.dv_ai1 != '') & (F.dv_ai2 != '')
    dis = nc & both & (F.dv_ai1 != F.dv_ai2)
    st1, st2 = pd.to_numeric(F.step_ai1, errors='coerce'), pd.to_numeric(F.step_ai2, errors='coerce')
    sib1 = (F.route_ai1 == 'sibling_intermediate') & (st2 != 5)
    sib2 = (F.route_ai2 == 'sibling_intermediate') & (st1 != 5)
    pol2['P_Q1_1'] = apply(F, dis & (sib1 | sib2), 'P_Q1_1', DV=1, uncertain=0, route='sibling_intermediate', step='')
    conf = nc & F.source.str.startswith('conflict') & (rd == 1)
    pol2['P_CONF'] = apply(F, conf, 'P_CONF', DV=1, uncertain=rid.isin(UNCERTAIN_RULES).astype(int), route=rr,
                           step='')
    for r_id, pid in RULE_C_D.items():
        pol2[pid] = apply(F, nc & (rid == r_id) & (rd == 1) & (F.DV == 0), pid, DV=1, uncertain=0, route=rr, step='')
    pol2['P_AUD_A'] = apply(F, nc & rid.isin(UNC_A) & (rd == 1) & (F.DV == 0), 'P_AUD_A', DV=1, uncertain=1,
                            route=rr, step='')
    pol2['P_OPT2'] = apply(F, nc & rid.isin(COMMON_RULES) & (rd == 1) & (F.DV == 0), 'P_OPT2', DV=1, uncertain=0,
                           route=rr, step='')
    # 1s that come from an uncertain rule (textile rules, model bands confirmed by the rule, settled conflicts)
    by_rule = nc & rid.isin(UNCERTAIN_RULES) & (F.DV == 1) & (F.uncertain == 0) & (
        F.source.isin(['rule_textile', 'ml']) | F.source.str.startswith('conflict'))
    pol2['uncertain_rule_category'] = apply(F, by_rule, 'P_UNC', uncertain=1)
    fi_, fo_ = family(F.input_hs6), family(F.output_hs6)
    agree0 = (F.dv_ai1 == '0') & (F.dv_ai2 == '0') & (F.DV == 0)
    bmask = nc & both & agree0 & (fi_ != '') & (fi_ == fo_) & (st1 != 5) & (st2 != 5)
    pol2['P_AUD_B'] = apply(F, bmask, 'P_AUD_B', DV=1, uncertain=0, route='sibling_intermediate', step='')
    chem = nc & F.input_hs6.str[:2].between('28', '38') & (F.output_hs6.str[:4] == '3825')
    pol2['P_Q2_1'] = apply(F, chem, 'P_Q2_1', DV=1, uncertain=0, route='recycle_waste', step='')
    mine = nc & (F.input_hs6.str[:2] == '25') & (F.input_hs6.str[:4] != '2523') & (F.output_hs6.str[:4] == '2523')
    pol2['P_Q2_2'] = apply(F, mine, 'P_Q2_2', DV=1, uncertain=0, route='ingredient', step='')
    pol2.update(fish_policy(F, nc, FEED_IN, FARMED))
    mlz = (F.source == 'ml') & (F.DV.astype(int) == 0)        # ML turn0 textile pairs: the rule's step
    F.loc[mlz, 'step'] = rs[mlz].map(lambda x: '' if x is None or pd.isna(x) else str(int(x)))
    F = finish(F)
    F.loc[F.DV == 1, 'step'] = np.where(F.loc[F.DV == 1, 'route'] == 'same_good', F.loc[F.DV == 1, 'step'], '')

    # uncertain by question
    dis = both & (F.dv_ai1 != F.dv_ai2)          # every AI disagreement, including locked pairs
    cat = np.select(
        [F.uncertain == 0,
         rid == 'T_CONSTITUENT',
         rid.isin(UNC_A),
         F.policy.str.contains('P_FISH'),
         dis & ((F.route_ai1 == 'sibling_intermediate') | (F.route_ai2 == 'sibling_intermediate')),
         dis | F.source.str.startswith('conflict'),
         F.route == 'unresolved'],
        ['', 'minor constituent of a garment or made-up: other fibre or construction',
         'minor constituent of a yarn or fabric: other fibre', 'possible feed (rock lobster)',
         'AI coders disagree: sibling or backward', 'AI coders, or the model and the textile rules, disagree',
         'open case in the ASEAN-Japan labels'], 'other')
    Lcat = np.where(L.uncertain == 1, np.where(L.route == 'unresolved', 'open case in the ASEAN-Japan labels',
                                               np.where(L.policy.str.contains('P_AUD_A'),
                                                        'minor constituent of a yarn or fabric: other fibre',
                                                        np.where(L.policy.str.contains('P_FISH'),
                                                                 'possible feed (rock lobster)', 'other'))), '')
    # exact copies keep the ASEAN-Japan reason, so a pair has one reason in every PTA
    Lr = pd.Series(Lcat, index=Li.index)
    F['uncertain_reason'] = np.where(ex, Lr.reindex(pd.MultiIndex.from_arrays([F.input_hs6, F.output_hs6])).values,
                                     cat)
    cat = F.uncertain_reason.values

    # ---------------- report: before (v2 as sent) -> after ----------------
    v2 = F0v2.reindex(F.master_id)
    rep['pta2_5_unique_pairs'] = {
        'pairs': len(F), 'DV1_v2': int(v2.DV.astype(int).sum()), 'DV1_after_textile_rule_change': int(pre.DV.sum()),
        'DV1_final': int(F.DV.sum()), 'DV_strict1_final': int(F.DV_strict.sum()),
        'uncertain_v2': int(v2.uncertain.astype(int).sum()), 'uncertain_final': int(F.uncertain.sum()),
        'textile_rule_change_Q1_2': {'DV_changed': int((v2.DV.astype(int).values != pre.DV.values).sum())},
        'policies': {k: {'rows_matched': v[1], 'DV_changed': v[0]} for k, v in pol2.items()},
        'uncertain_by_reason': pd.Series(cat)[cat != ''].value_counts().to_dict()}

    # ---------------- per-PTA files ----------------
    for f in FINAL.glob('*_coded_2026_10_18.*'):
        shutil.move(str(f), V2 / f.name) if not (V2 / f.name).exists() else f.unlink()
    F['why_ai1'], F['why_ai2'] = F.reason_ai1, F.reason_ai2
    keep = ['DV', 'DV_strict', 'DV_excl_remelt', 'DV_max', 'uncertain', 'uncertain_reason', 'locked', 'step', 'route',
            'source', 'policy', 'ml_prob', 'ml_supported', 'concord_flag', 'dv_ai1', 'dv_ai2', 'why_ai1', 'why_ai2',
            'master_id']
    desc = lambda c: f'{T.get(c[:4], "")} | {T.get(c, "")}'.strip(' |')
    labels = {'output_hs6': 'output: HS2002 6-digit code (original output_str)',
              'output_description': 'output: HS2002 heading | subheading text',
              'input_hs6': 'input: HS2002 6-digit code (original input_str)',
              'input_description': 'input: HS2002 heading | subheading text',
              'VA_Alternative': 'copied unchanged from the original file',
              'VA_Complement': 'copied unchanged from the original file',
              'pta': 'agreement', 'record_no': 'row number in the original file',
              'pair_id': 'unique row id (pta|input>output)', 'hs_vintage': 'HS vintage of the codes',
              'DV': '1 = input can be used to make output (main)',
              'DV_strict': 'DV x (1 - uncertain): certain links only',
              'DV_excl_remelt': 'like DV, but direct remelting (recycle_direct) = 0',
              'DV_max': 'same as DV since 2026-10-19 (kept for older code)',
              'uncertain': '1 = kept at 1 but uncertain (see uncertain_reason)',
              'uncertain_reason': 'why uncertain = 1',
              'locked': '1 = input and output are the same good (step 2)',
              'step': 'workflow step that set DV = 0 (2 = same good)',
              'route': 'why DV = 1 (forward, component, ...) or none',
              'source': 'how the code was reached (labels, copy, rule, ML, AI coders)',
              'policy': 'decision or audit fix of 2026-10-19 that changed the row',
              'ml_prob': 'ML probability that DV = 1 (information only)',
              'ml_supported': '1 = ML model had enough similar coded pairs',
              'concord_flag': '1 = a code is not a valid HS2002 code',
              'dv_ai1': 'DV of AI coder 1 (Claude), where coded', 'dv_ai2': 'DV of AI coder 2 (Codex), where coded',
              'why_ai1': 'reason of AI coder 1 (Claude)', 'why_ai2': 'reason of AI coder 2 (Codex)',
              'master_id': 'id of the input-output pair (same in every PTA)'}
    # one storage type per variable in every file, so the five files append in Stata
    BYTE = ['VA_Alternative', 'VA_Complement', 'DV', 'DV_strict', 'DV_excl_remelt', 'DV_max', 'uncertain', 'locked',
            'concord_flag']
    DOUBLE = ['step', 'ml_prob', 'ml_supported', 'dv_ai1', 'dv_ai2']
    NAMES = {'ASEAN_JPN': 'ASEAN-Japan', 'BRN_JPN': 'Brunei-Japan', 'AUS_USA': 'Australia-US', 'CAFTA': 'CAFTA',
             'BHR_USA': 'Bahrain-US'}
    Fi = F.set_index(['input_hs6', 'output_hs6'])[keep]
    pta_rep = {}

    def write(P, name):
        P.insert(P.columns.get_loc('pair_id') + 1, 'hs_vintage', 'HS2002')
        P.insert(P.columns.get_loc('input_hs6') + 1, 'input_description', P.input_hs6.map(desc))
        P.insert(P.columns.get_loc('output_hs6') + 1, 'output_description', P.output_hs6.map(desc))
        P.to_csv(FINAL / f'{name}_coded_{DATE}.csv', index=False)
        Pd = P.copy()
        for c in BYTE:
            v = pd.to_numeric(Pd[c], errors='raise')
            assert v.notna().all() and v.isin([0, 1]).all(), (name, c)
            Pd[c] = v.astype('int8')
        for c in DOUBLE:
            Pd[c] = pd.to_numeric(Pd[c].replace('', np.nan), errors='raise').astype('float64')
        Pd['record_no'] = Pd.record_no.astype('int32')
        assert set(Pd.columns) == set(labels), set(Pd.columns) ^ set(labels)
        Pd.to_stata(FINAL / f'{name}_coded_{DATE}.dta', write_index=False, version=118,
                    convert_strl=['input_description', 'output_description', 'why_ai1', 'why_ai2'],
                    variable_labels=labels, data_label=f'{NAMES[name]}: RoO input-output pairs coded {DATE}')
        pta_rep[name] = {'records': len(P), 'DV1': int(P.DV.sum()), 'DV1_share': round(float(P.DV.mean()), 4),
                         'DV_strict1': int(P.DV_strict.sum()), 'uncertain': int(P.uncertain.sum()),
                         'uncertain_by_reason': P.uncertain_reason[P.uncertain_reason != ''].value_counts().to_dict(),
                         'source': P.source.value_counts().to_dict()}

    for p in PTAS:
        R0 = pd.read_csv(HERE / 'intake' / f'pairs_{p}.csv', dtype={'input_hs6': str, 'output_hs6': str})
        P = R0.join(Fi, on=['input_hs6', 'output_hs6'])
        assert P.DV.notna().all(), p
        P['DV'] = P.DV.astype(int)
        write(P, p)
        old = pd.read_csv(V2 / f'{p}_coded_2026_10_18.csv', dtype={'input_hs6': str, 'output_hs6': str},
                          usecols=['DV', 'uncertain'])
        pta_rep[p]['DV1_v2'] = int(old.DV.sum())
        pta_rep[p]['uncertain_v2'] = int(old.uncertain.sum())
    # ASEAN-Japan in the same layout
    aj, _ = read_any_dta(PROJECT / 'Data_Validation_Through_Machine_Learning/reference_only/ASEAN_JPN.dta')
    aj = aj.rename(columns={'output_str': 'output_hs6', 'input_str': 'input_hs6'})
    aj['pta'] = 'ASEAN_JPN'
    aj['record_no'] = np.arange(1, len(aj) + 1)
    aj['pair_id'] = 'ASEAN_JPN|' + aj.input_hs6 + '>' + aj.output_hs6
    Lx = L.assign(uncertain_reason=Lcat, source='pta1_label', ml_prob='', ml_supported='', dv_ai1='', dv_ai2='',
                  why_ai1='', why_ai2='', master_id='M|' + L.input_hs6 + '>' + L.output_hs6)
    h2 = {k for k in T if len(k) == 6 and k.isdigit()}
    Lx['concord_flag'] = (~Lx.input_hs6.isin(h2) | ~Lx.output_hs6.isin(h2)).astype(int)
    Lx['step'] = Lx.step.replace({'<NA>': ''})
    P = aj.join(Lx.set_index(['input_hs6', 'output_hs6'])[keep], on=['input_hs6', 'output_hs6'])
    assert P.DV.notna().all() and len(P) == len(L)
    write(P, 'ASEAN_JPN')
    pta_rep['ASEAN_JPN']['DV1_v2'] = int(L0.DV.sum())
    pta_rep['ASEAN_JPN']['uncertain_v2'] = int(L0.uncertain.sum())
    rep['pta'] = pta_rep

    # consistency: a pair has one code in every PTA
    Fx = F.set_index(['input_hs6', 'output_hs6'])
    both_keys = Fx.index.intersection(Li.index)
    diff = int((Fx.loc[both_keys, 'DV'].values != Li.loc[both_keys, 'DV'].values).sum())
    udiff = int((Fx.loc[both_keys, 'uncertain'].astype(int).values != Li.loc[both_keys, 'uncertain'].astype(int).values).sum())
    rdiff = int((Fx.loc[both_keys, 'route'].values != Li.loc[both_keys, 'route'].values).sum())
    rep['consistency'] = {'pairs_in_ASEAN_JPN_and_PTA2_5': len(both_keys), 'DV_differs': diff,
                          'uncertain_differs': udiff, 'route_differs': rdiff}
    assert diff == 0 and udiff == 0 and rdiff == 0, rep['consistency']
    F.to_csv(FINAL / 'master_coded_final.csv', index=False)
    json.dump(rep, open(FINAL / 'policy_report.json', 'w'), indent=1, default=int)
    print(json.dumps(rep, indent=1, default=int))


if __name__ == '__main__':
    main()
