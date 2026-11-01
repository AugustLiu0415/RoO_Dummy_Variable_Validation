"""Build the concordance pair file for the two AI coders: TUR_SGP pairs that HS2002 cannot code.

A TUR_SGP record (HS2012) whose input and output are different HS2012 codes but whose HS2002 mapping contains an
HS2002 self-pair (both codes fall, wholly or partly, in the same HS2002 subheading) cannot be coded from HS2002: the
self-pair only says that both goods share a subheading (e.g. 200591 bamboo shoots -> 200599 other vegetables, both
in 200590). Such records are coded directly on their HS2012 codes and texts by both coders, pair by pair (found in
the script review of 2026-10-25). 09_apply_policy.py gives these records the two-coder code (source ai_concord).
Worked examples: the 5 most similar ASEAN-Japan labels (training-eligible rows), with the HS2012 texts embedded in
the same text space as the HS2002 codes.
Output: ai_coders/input/concord_pairs.csv (item ids C0001 ...), _work/coded/concord_key.csv.

Run: /usr/local/bin/python3 _work/05b_build_concord_pairs.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import AI, CODED, INTAKE, LABELS_PTA1, ML, REF  # noqa: E402

sys.path.insert(0, str(ML / 'ml_v1'))
from features import CodeSpace, pair_vectors  # noqa: E402

K = 5


def concord_records():
    """TUR_SGP hs6 records with different own codes whose HS2002 pairs include an HS2002 self-pair"""
    r = pd.read_csv(INTAKE / 'records_TUR_SGP.csv', dtype=str, keep_default_na=False)
    rp = pd.read_csv(INTAKE / 'record_pairs.csv', dtype=str)
    rp = rp[rp.pta == 'TUR_SGP']
    selfrec = set(rp.record_no[rp.input_hs6 == rp.output_hs6])
    return r[(r.input_type == 'hs6') & (r.input_hs6 != r.output_hs6) & r.record_no.isin(selfrec)]


def main():
    H4 = {x['id']: x['text'] for x in json.load(open(REF / 'H4.json'))['results']}
    clean = lambda t: t.split(' - ', 1)[-1].lstrip('- ').strip() if ' - ' in t else t  # noqa: E731
    r = concord_records()
    P = (r.groupby(['input_hs6', 'output_hs6'])
         .agg(n_records=('record_no', 'size'), record_nos=('record_no', ';'.join),
              input_hs2002=('input_hs2002', 'first'), output_hs2002=('output_hs2002', 'first'))
         .reset_index().sort_values(['input_hs6', 'output_hs6']).reset_index(drop=True))
    P['item_id'] = [f'C{i + 1:04d}' for i in range(len(P))]
    cs = CodeSpace()
    L = pd.read_csv(LABELS_PTA1, dtype=str, keep_default_na=False)
    L = L[L.train_eligible == '1'].reset_index(drop=True)
    cs.add_codes(set(L.input_hs6) | set(L.output_hs6))
    Vr = pair_vectors(cs, L.input_hs6, L.output_hs6).astype(np.float32)
    ref_txt = (L.input_hs6 + '>' + L.output_hs6 + ' | ASEAN-Japan: ' + L.relation_class + ' | DV '
               + L.DV.astype(float).astype(int).astype(str) + ' | ' + L.route + ' | '
               + [cs.sub[c][:60] for c in L.input_hs6] + ' -> ' + [cs.sub[c][:60] for c in L.output_hs6]).values
    doc = lambda c: f'{clean(H4.get(c[:2], ""))} | {clean(H4.get(c[:4], ""))} | {clean(H4[c])}'  # noqa: E731
    emb = lambda codes: normalize(cs.svd.transform(cs.tfidf.transform([doc(c) for c in codes])))  # noqa: E731
    V = normalize(np.hstack([emb(P.input_hs6), emb(P.output_hs6)])).astype(np.float32)
    S = V @ Vr.T
    top = np.argsort(-S, axis=1)[:, :K]
    desc = lambda c: f'{clean(H4.get(c[:4], ""))} | {clean(H4[c])}'  # noqa: E731
    out = pd.DataFrame({'item_id': P.item_id, 'input_hs6': P.input_hs6,
                        'input_description': P.input_hs6.map(desc), 'output_hs6': P.output_hs6,
                        'output_description': P.output_hs6.map(desc),
                        **{f'ex{j + 1}': [ref_txt[t[j]] for t in top] for j in range(K)}})
    out.to_csv(AI / 'input' / 'concord_pairs.csv', index=False)
    P.to_csv(CODED / 'concord_key.csv', index=False)
    info = {'records': len(r), 'pairs': len(P), 'by_input_chapter': P.input_hs6.str[:2].value_counts().to_dict()}
    print(json.dumps(info, indent=1))


if __name__ == '__main__':
    main()
