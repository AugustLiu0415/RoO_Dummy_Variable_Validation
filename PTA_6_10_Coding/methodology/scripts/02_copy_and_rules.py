"""Workflow steps 2 and 7 for the PTA 6-10 master list: exact copies, self-pairs, textile rules, AI-coder queue.

For every unique HS2002 pair in intake/master_pairs.csv:
  7(a) the pair is already coded in PTA 1-5 (ASEAN-Japan labels of 2026-10-19 or the final PTA 2-5 master) -> copy
       DV, uncertain, uncertain_reason, route, step, locked, policy and the AI coders' codes; source = exact_copy.
  2    self-pair (same HS6) -> DV 1, locked, route same_good; source = rule.
  7(e) both codes in chapters 50-63 -> textile rules (PTA_2_5/_work/textile.py, the rules of 2026-10-19 v2);
       source = rule_textile. Rules in UNCERTAIN_RULES give DV 1 with uncertain 1.
  7(c) every other pair -> the two AI coders (queue ai_units). The ML bands are not used to code pairs: the PTA 2-5
       audit (workflow 7d) found them reliable only for textile pairs, where the rules decide anyway. The ML
       probability is computed for every new pair as information (ml_prob) and for the accuracy report.
Output: _work/coded/master_coded_stage2.csv, stage2.json.

Run: /usr/local/bin/python3 -I _work/02_copy_and_rules.py
"""
import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import CODED, INTAKE, ML, PTAS, load_coded_master  # noqa: E402
from textile import UNCERTAIN_RULES, attributes, code_pair, load_texts  # noqa: E402

sys.path.insert(0, str(ML))
sys.path.insert(0, str(ML / 'ml_v1'))
from common import code_levels  # noqa: E402
from features import CodeSpace, pair_features  # noqa: E402

LABELS_ML = ML / 'labels_2026_10_18/outputs/PTA_1_labels_2026_10_18.csv'    # training labels of models.pkl
MODELS = ML / 'ml_v1/outputs/models.pkl'
FROZEN = ML / 'PTA_1_2026_10_15.dta'


class _Rows:
    """dict-of-rows wrapper with the .loc[code].attr access code_pair uses"""
    def __init__(self, d):
        self.d = d
        self.loc = self

    def __getitem__(self, c):
        return pd.Series(self.d[c], name=c)


def ml_probability(df):
    """p_ens of the ML validator (ml_v1), as in PTA_2_5/_work/02_exact_copy_and_ml.py; information only"""
    L = pd.read_csv(LABELS_ML, dtype={'input_hs6': str, 'output_hs6': str}, keep_default_na=False)
    mod = pickle.load(open(MODELS, 'rb'))
    assert hashlib.sha256(open(LABELS_ML, 'rb').read()).hexdigest() == mod['labels_sha256']
    cs = CodeSpace()
    cs.add_codes(set(df.input_hs6) | set(df.output_hs6))
    X = pair_features(cs, df.input_hs6, df.output_hs6)[mod['features']]
    f64 = [c for c in X.columns if X[c].dtype == 'float64']
    X[f64] = X[f64].astype('float32')
    pb = mod['binary'].predict_proba(X)[:, 1]
    P = mod['class'].predict_proba(X)
    classes = list(mod['class'].classes_)
    frozen = pd.read_stata(FROZEN, convert_categoricals=False, columns=['input_hs6', 'output_hs6', 'input_stage',
                                                                         'output_stage'])
    LV = code_levels(frozen)
    E = np.hstack([cs.E, pd.get_dummies(pd.Categorical([c[:2] for c in cs.leaf],
                                                       categories=[f'{i:02d}' for i in range(1, 98)])).values])
    pF_model = dict(zip(cs.leaf, mod['level'].predict_proba(E)[:, 1]))
    pF = lambda c: 1.0 if LV.get(c) == 'F' else (0.0 if LV.get(c) in ('P', 'I') else pF_model[c])  # noqa: E731
    one = np.array([c in ('COMPONENT', 'FEED', 'FORWARD', 'INGREDIENT', 'RECONSTITUTE', 'RECYCLE', 'SAME_GOOD')
                    for c in classes])
    j = classes.index('SIBLING')
    p_in, p_out = df.input_hs6.map(pF).values, df.output_hs6.map(pF).values
    pc = P[:, one].sum(1) + P[:, j] * (1 - p_in * p_out)
    tr = L[L.train_eligible == 1]
    cp_n = tr.groupby([tr.input_hs6.str[:2], tr.output_hs6.str[:2]]).size()
    cpn = np.array([int(cp_n.get((a[:2], b[:2]), 0)) for a, b in zip(df.input_hs6, df.output_hs6)])
    return np.round((pb + pc) / 2, 4), np.array(classes)[P.argmax(1)], (cpn > 30).astype(int)


def main():
    CODED.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INTAKE / 'master_pairs.csv', dtype=str, keep_default_na=False)
    M = load_coded_master().set_index(['input_hs6', 'output_hs6'])
    key = pd.MultiIndex.from_arrays([df.input_hs6, df.output_hs6])
    exact = key.isin(M.index)
    copy_cols = ['DV', 'uncertain', 'uncertain_reason', 'route', 'step', 'locked', 'policy', 'copy_from',
                 'copy_origin', 'dv_ai1', 'dv_ai2', 'why_ai1', 'why_ai2']
    C = M.reindex(key)[copy_cols]
    for c in copy_cols:
        df[c] = C[c].values
    for c in copy_cols:
        df[c] = df[c].where(exact, '')
    df['source'] = np.where(exact, 'exact_copy', '')
    df['rule_id'] = ''
    df['queue'] = ''

    selfp = ~exact & (df.input_hs6 == df.output_hs6)
    df.loc[selfp, ['DV', 'uncertain', 'route', 'step', 'locked', 'source']] = [1, 0, 'same_good', 2, 1, 'rule']

    T = load_texts()
    A = attributes([k for k in T if len(k) == 6 and k.isdigit()], T)
    tex = ~exact & ~selfp & df.input_hs6.isin(A.index) & df.output_hs6.isin(A.index)
    R = _Rows(A.to_dict('index'))
    res = [code_pair(a, b, R) for a, b in zip(df.input_hs6[tex], df.output_hs6[tex])]
    r = pd.DataFrame(res, columns=['dv', 'dv_strict', 'route', 'step', 'rule'], index=df.index[tex])
    unc = r.rule.isin(UNCERTAIN_RULES).astype(int)
    df.loc[tex, 'DV'] = r.dv.astype(int).values
    df.loc[tex, 'uncertain'] = (unc * r.dv.astype(int)).values
    df.loc[tex, 'route'] = r.route.values
    df.loc[tex, 'step'] = r.step.map(lambda x: '' if x is None or pd.isna(x) else int(x)).values
    df.loc[tex, 'locked'] = (r.route == 'same_good').astype(int).values
    df.loc[tex, 'rule_id'] = r.rule.values
    df.loc[tex, 'source'] = 'rule_textile'
    df.loc[df.source == '', 'queue'] = 'ai_units'

    new = df.source != 'exact_copy'
    df['ml_prob'], df['ml_class'], df['ml_supported'] = '', '', ''
    p, cl, sup = ml_probability(df[new])
    df.loc[new, 'ml_prob'] = p
    df.loc[new, 'ml_class'] = cl
    df.loc[new, 'ml_supported'] = sup
    df.to_csv(CODED / 'master_coded_stage2.csv', index=False)

    rt = df[df.source == 'rule_textile']
    q = df[df.queue == 'ai_units']
    rec = pd.read_csv(INTAKE / 'record_pairs.csv', dtype=str)
    src = rec.merge(df[['input_hs6', 'output_hs6', 'source']], on=['input_hs6', 'output_hs6'])
    summary = {
        'master_pairs': len(df),
        'source': df.source.replace('', 'ai_units (pending)').value_counts().to_dict(),
        'exact_copy_from': df.copy_from[exact].value_counts().to_dict(),
        'exact_copy_origin': df.copy_origin[exact].value_counts().to_dict(),
        'exact_copy_DV1_share': round(float(df.DV[exact].astype(int).mean()), 4),
        'textile_rules': {'pairs': len(rt), 'DV1': int(rt.DV.astype(int).sum()),
                          'uncertain': int(rt.uncertain.astype(int).sum()),
                          'by_rule': rt.rule_id.value_counts().to_dict()},
        'ai_units_queue': {'pairs': len(q), 'heading_pairs': int(q.groupby([q.input_hs6.str[:4],
                                                                          q.output_hs6.str[:4]]).ngroups)},
        'record_pairs_by_source': {p: src[src.pta == p].source.replace('', 'ai_units (pending)').value_counts()
                                   .to_dict() for p in PTAS},       # one count per (record, HS2002 pair)
    }
    json.dump(summary, open(CODED / 'stage2.json', 'w'), indent=1, default=int)
    print(json.dumps(summary, indent=1, default=int))


if __name__ == '__main__':
    main()
