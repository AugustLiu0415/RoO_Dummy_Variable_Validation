"""Code the textile pairs of PTA 2-5 by rule (workflow steps 2-6 applied by rule; textile.py).

Scope: pairs with both codes in chapters 50-63 that stage 1 left open (segment unseen_textile, and textile pairs in
the ML middle band). T_CONSTITUENT pairs (another fibre or construction as a minor constituent of a garment or
made-up) get DV = 1, uncertain = 1, so DV_strict = 0 (decided by August, 2026-10-18).
Checks, not changes: the rule is also computed on textile pairs that were copied from PTA_1 or accepted by the ML
bands; ML-accepted textile pairs where the rule disagrees are sent to the AI coders (queue = ml_rule_conflict).
Output: _work/coded/master_coded_stage2.csv, textile_rules.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from textile import UNCERTAIN_RULES, attributes, code_pair, load_texts  # noqa: E402

OUT = HERE / 'coded'


class _Rows:
    """dict-of-rows wrapper with the .loc[code].attr access code_pair uses"""
    def __init__(self, d):
        self.d = d
        self.loc = self

    def __getitem__(self, c):
        return pd.Series(self.d[c], name=c)


def main():
    OUT.mkdir(exist_ok=True)
    df = pd.read_csv(HERE / 'ml/master_coded_stage1.csv', dtype={'input_hs6': str, 'output_hs6': str},
                     keep_default_na=False)
    T = load_texts()
    A = attributes([k for k in T if len(k) == 6 and k.isdigit()], T)
    tex = df.input_hs6.isin(A.index) & df.output_hs6.isin(A.index) & (df.input_hs6 != df.output_hs6)
    Ad = A.to_dict('index')                                   # fast row access for code_pair
    cache = {}
    res = []
    for a, b in zip(df.input_hs6[tex], df.output_hs6[tex]):
        if (a, b) not in cache:
            cache[(a, b)] = code_pair(a, b, _Rows(Ad))
        res.append(cache[(a, b)])
    R = pd.DataFrame(res, columns=['r_dv', 'r_dv_strict', 'r_route', 'r_step', 'r_rule'], index=df.index[tex])
    df['rule_id'] = R.r_rule.reindex(df.index).fillna('')
    df['rule_dv'] = R.r_dv.reindex(df.index).astype('Int64').astype(str).replace('<NA>', '')
    df['queue'] = ''
    todo = tex & (df.source == '')
    r = R.loc[df.index[todo]]
    unc = r.r_rule.isin(UNCERTAIN_RULES).astype(int)
    df.loc[todo, 'DV'] = r.r_dv.values
    df.loc[todo, 'DV_max'] = np.where(r.r_route == 'recycle_direct', 1, r.r_dv)
    df.loc[todo, 'uncertain'] = unc.values
    df.loc[todo, 'DV_strict'] = (r.r_dv * (1 - unc)).values
    df.loc[todo, 'locked'] = (r.r_route == 'same_good').astype(int).values
    df.loc[todo, 'step'] = r.r_step.map(lambda x: '' if x is None or pd.isna(x) else int(x)).values
    df.loc[todo, 'route'] = r.r_route.values
    df.loc[todo, 'source'] = 'rule_textile'
    conflict = tex & (df.source == 'ml') & (df.rule_dv.astype(str) != df.DV.astype(str).str.replace('.0', '', regex=False))
    df.loc[conflict, 'queue'] = 'ml_rule_conflict'
    df.loc[conflict, ['DV', 'source', 'route', 'ml_prob']] = ['', '', '', '']
    pending = df.source == ''
    df.loc[pending & (df.queue == ''), 'queue'] = np.where(df.band[pending & (df.queue == '')] == 'middle',
                                                           'ml_middle', 'unseen_other')
    ex = tex & (df.segment == 'exact_copy')
    agree_copy = (df.rule_dv[ex].astype(int) == df.DV[ex].astype(float).astype(int)).mean()
    df.to_csv(OUT / 'master_coded_stage2.csv', index=False)
    rt = df[df.source == 'rule_textile']
    summary = {
        'textile_pairs_coded_by_rule': len(rt),
        'by_rule': rt.rule_id.value_counts().to_dict(),
        'DV1_main': int((rt.DV.astype(int) == 1).sum()), 'DV1_strict': int(rt.DV_strict.astype(int).sum()),
        'uncertain_constituent': int(rt.uncertain.astype(int).sum()),
        'rule_vs_copied_PTA1_DV_agreement': round(float(agree_copy), 4), 'copied_textile_pairs': int(ex.sum()),
        'ml_textile_pairs_rule_conflict': int(conflict.sum()),
        'source': df.source.replace('', 'pending').value_counts().to_dict(),
        'queue': df.queue[df.queue != ''].value_counts().to_dict(),
    }
    json.dump(summary, open(OUT / 'textile_rules.json', 'w'), indent=1, default=int)
    print(json.dumps(summary, indent=1, default=int))


if __name__ == '__main__':
    main()
