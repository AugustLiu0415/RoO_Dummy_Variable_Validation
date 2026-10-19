"""Workflow steps 2 and 7 for the PTA 2-5 master list: exact copies, rule locks, ML bands, worked examples.

For every unique pair in intake/master_pairs.csv (HS2002 codes; see intake.json for the vintage check):
  7(a) exact match with the coded PTA_1 pair list (labels 2026-10-18) -> copy DV, DV_max, route, step, locked,
       uncertain, class, open question; source = exact_copy.
  2    self-pair (same HS6) -> DV 1, locked, route same_good; source = rule.
  7(c) otherwise the ML validator (Data_Validation_Through_Machine_Learning/ml_v1/models.pkl):
       p_ens >= 0.9 -> DV 1, p_ens <= 0.1 -> DV 0 (source = ml); otherwise band = middle -> the two AI coders,
       with the 5 most similar coded PTA_1 pairs (cosine of the input and output text vectors) as worked examples.
Output: _work/ml/master_coded_stage1.csv, middle_band_for_coders.csv, ml_apply.json.

Run: /usr/local/bin/python3 -I _work/02_exact_copy_and_ml.py
"""
import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
ML = PROJECT / 'Data_Validation_Through_Machine_Learning'
sys.path.insert(0, str(ML))
sys.path.insert(0, str(ML / 'ml_v1'))
from common import code_levels  # noqa: E402
from features import CodeSpace, pair_features, pair_vectors  # noqa: E402

LABELS = ML / 'labels_2026_10_18/outputs/PTA_1_labels_2026_10_18.csv'
MODELS = ML / 'ml_v1/outputs/models.pkl'
FROZEN = ML / 'PTA_1_2026_10_15.dta'
OUT = HERE / 'ml'
K = 5


def dv_prob_from_classes(P, classes, p_inF, p_outF):
    one = np.array([c in ('COMPONENT', 'FEED', 'FORWARD', 'INGREDIENT', 'RECONSTITUTE', 'RECYCLE', 'SAME_GOOD')
                    for c in classes])
    j = list(classes).index('SIBLING')
    return P[:, one].sum(1) + P[:, j] * (1 - p_inF * p_outF)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    M = pd.read_csv(HERE / 'intake/master_pairs.csv', dtype=str, keep_default_na=False)
    L = pd.read_csv(LABELS, dtype={'input_hs6': str, 'output_hs6': str}, keep_default_na=False)
    mod = pickle.load(open(MODELS, 'rb'))
    lab_sha = hashlib.sha256(open(LABELS, 'rb').read()).hexdigest()
    assert lab_sha == mod['labels_sha256'], 'models were trained on a different label file'
    LO, HI = mod['bands']

    cs = CodeSpace()
    nonleaf = cs.missing(set(M.input_hs6) | set(M.output_hs6) | set(L.input_hs6) | set(L.output_hs6))
    cs.add_codes(nonleaf)

    keep = ['relation_class', 'DV', 'DV_max', 'uncertain', 'DV_strict', 'locked', 'step', 'route', 'open_question']
    lab = L.set_index(['input_hs6', 'output_hs6'])[keep + ['pair_id']].rename(columns={'pair_id': 'pta1_pair_id'})
    df = M.join(lab, on=['input_hs6', 'output_hs6'])
    exact = df.DV.notna()
    df['source'] = np.where(exact, 'exact_copy', '')
    selfp = ~exact & (df.input_hs6 == df.output_hs6)
    df.loc[selfp, ['relation_class', 'DV', 'DV_max', 'uncertain', 'DV_strict', 'locked', 'step', 'route', 'source']] = \
        ['SAME_GOOD', 1, 1, 0, 1, 1, 2, 'same_good', 'rule']

    # ML on every pair (also on exact copies, as a consistency check)
    X = pair_features(cs, df.input_hs6, df.output_hs6)[mod['features']]
    X[[c for c in X.columns if X[c].dtype == 'float64']] = X[[c for c in X.columns if X[c].dtype == 'float64']].astype('float32')
    df['p_binary'] = mod['binary'].predict_proba(X)[:, 1]
    P = mod['class'].predict_proba(X)
    classes = list(mod['class'].classes_)
    frozen = pd.read_stata(FROZEN, convert_categoricals=False, columns=['input_hs6', 'output_hs6', 'input_stage',
                                                                         'output_stage'])
    LV = code_levels(frozen)
    E = np.hstack([cs.E, pd.get_dummies(pd.Categorical([c[:2] for c in cs.leaf],
                                                       categories=[f'{i:02d}' for i in range(1, 98)])).values])
    pF_model = dict(zip(cs.leaf, mod['level'].predict_proba(E)[:, 1]))
    pF = lambda c: 1.0 if LV.get(c) == 'F' else (0.0 if LV.get(c) in ('P', 'I') else pF_model[c])  # noqa: E731
    df['level_known'] = [int(a in LV and b in LV) for a, b in zip(df.input_hs6, df.output_hs6)]
    df['p_class_rule'] = dv_prob_from_classes(P, classes, df.input_hs6.map(pF).values, df.output_hs6.map(pF).values)
    df['p_ens'] = (df.p_binary + df.p_class_rule) / 2
    df['ml_class'] = np.array(classes)[P.argmax(1)]
    df['ml_class_prob'] = P.max(1)
    for c in ('p_binary', 'p_class_rule', 'p_ens', 'ml_class_prob'):
        df[c] = df[c].round(4)

    # support condition: ML bands only where the chapter pair has > 30 coded PTA_1 training pairs. Grouped CV by
    # chapter pair (unseen chapter pairs) gave only 88% agreement in the 0.9/0.1 bands, against 96.7% when only the
    # input heading is unseen (ml_v1/outputs/metrics.json); unseen chapter pairs go to textile rules / AI coders.
    tr = L[L.train_eligible == 1]
    cp_n = tr.groupby([tr.input_hs6.str[:2], tr.output_hs6.str[:2]]).size()
    df['cp_n_pta1'] = [int(cp_n.get((a[:2], b[:2]), 0)) for a, b in zip(df.input_hs6, df.output_hs6)]
    tex = df.input_hs6.str[:2].astype(int).between(50, 63) & df.output_hs6.str[:2].astype(int).between(50, 63)
    df['segment'] = np.select([exact, selfp, df.cp_n_pta1 > 30, tex], ['exact_copy', 'self_pair', 'ml_supported',
                              'unseen_textile'], 'unseen_other')
    todo = (df.source == '') & (df.segment == 'ml_supported')
    df['band'] = ''
    df.loc[todo & (df.p_ens >= HI), 'band'] = 'keep1'
    df.loc[todo & (df.p_ens <= LO), 'band'] = 'turn0'
    df.loc[todo & (df.p_ens > LO) & (df.p_ens < HI), 'band'] = 'middle'
    hi, lo = df.band == 'keep1', df.band == 'turn0'
    df.loc[hi, ['DV', 'source']] = [1, 'ml']
    df.loc[lo, ['DV', 'source']] = [0, 'ml']
    df.loc[hi | lo, 'uncertain'] = 0
    df.loc[hi | lo, 'route'] = np.where(df.loc[hi | lo, 'DV'] == 1, 'ml_' + df.loc[hi | lo, 'ml_class'].str.lower(), 'none')
    df['ml_prob'] = np.where(df.source == 'ml', df.p_ens, np.nan)

    # 5 most similar coded PTA_1 pairs for the middle band (training-eligible, coded pairs only)
    ref = L[(L.train_eligible == 1)].reset_index(drop=True)
    Vr = pair_vectors(cs, ref.input_hs6, ref.output_hs6)
    mid = df[df.band == 'middle'].copy()
    Vm = pair_vectors(cs, mid.input_hs6, mid.output_hs6)
    ex_cols = []
    for start in range(0, len(mid), 2000):
        S = Vm[start:start + 2000] @ Vr.T
        top = np.argsort(-S, axis=1)[:, :K]
        for j in range(K):
            r = ref.iloc[top[:, j]]
            idx = mid.index[start:start + 2000]
            mid.loc[idx, f'ex{j + 1}'] = (r.input_hs6 + '>' + r.output_hs6 + ' | ' + r.relation_class + ' | DV '
                                          + r.DV.astype(str) + ' | ' + r.route).values
            mid.loc[idx, f'ex{j + 1}_sim'] = S[np.arange(len(idx)), top[:, j]].round(3)
    ex_cols = [c for j in range(1, K + 1) for c in (f'ex{j}', f'ex{j}_sim')]

    df.to_csv(OUT / 'master_coded_stage1.csv', index=False)
    mid[['master_id', 'input_hs6', 'output_hs6', 'ptas', 'p_ens', 'ml_class'] + ex_cols].to_csv(
        OUT / 'middle_band_for_coders.csv', index=False)
    ex = df[exact]
    summary = {
        'labels_sha256': lab_sha, 'bands': {'keep1': HI, 'turn0': LO},
        'master_pairs': len(df), 'non_leaf_codes_given_parent_text': cs.added,
        'source': df.source.replace('', 'pending_ai').value_counts().to_dict(),
        'band': df.band.replace('', 'n/a').value_counts().to_dict(),
        'segment': df.segment.value_counts().to_dict(),
        'exact_copy': {'pairs': int(exact.sum()), 'DV1': int((ex.DV == 1).sum()),
                       'with_open_question': int((ex.open_question != '').sum()),
                       'ml_agrees_with_copied_DV': round(float(((ex.p_ens >= 0.5).astype(int) == ex.DV).mean()), 4)
                       if len(ex) else None},
        'pairs_with_both_codes_in_pta1': int(df.level_known.sum()),
        'by_pta': {},
    }
    for pta in ['BRN_JPN', 'AUS_USA', 'CAFTA', 'BHR_USA']:
        s = df[df.ptas.str.contains(pta)]
        summary['by_pta'][pta] = {'pairs': len(s), **s.segment.value_counts().to_dict(),
                                  **{f'band_{k}': v for k, v in s.band[s.band != ''].value_counts().to_dict().items()}}
    json.dump(summary, open(OUT / 'ml_apply.json', 'w'), indent=1, default=int)
    print(json.dumps(summary, indent=1, default=int))


if __name__ == '__main__':
    main()
