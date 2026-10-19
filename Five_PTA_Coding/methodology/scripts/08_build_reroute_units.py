"""Workflow 7d: narrow the ML bands. The audit (combine_report.json, 2026-10-18) found the ML bands accurate for
textile pairs, where the textile rule confirms them, but not for other pairs (keep1 39%, turn0 77% against the two
coders' agreed codes). So every non-textile pair accepted by an ML band (source = ml, no textile rule) is sent to
the two AI coders as heading-pair units, built exactly as in 05_build_coder_inputs.py.

Excluded: pairs already in the AI pair sample (both coders coded them pair by pair).
Unit ids start with R (re-routed) so they never clash with the U units of the same heading pair.
Output: ai_coders/input/units_batch_19.csv …; rows appended to _work/coded/unit_membership.csv with
queue = ml_reroute (re-running replaces them); _work/coded/reroute_inputs.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
ML = PROJECT / 'Data_Validation_Through_Machine_Learning'
sys.path.insert(0, str(ML / 'ml_v1'))
from features import CodeSpace, pair_vectors  # noqa: E402

LABELS = ML / 'labels_2026_10_18/outputs/PTA_1_labels_2026_10_18.csv'
AI = HERE.parent / 'ai_coders/input'
FIRST_BATCH = 19
UNITS_PER_BATCH = 250
K = 5


def main():
    df = pd.read_csv(HERE / 'coded/master_coded_stage2.csv', dtype={'input_hs6': str, 'output_hs6': str},
                     keep_default_na=False)
    key = pd.read_csv(HERE / 'coded/sample_key.csv', dtype=str)
    L = pd.read_csv(LABELS, dtype={'input_hs6': str, 'output_hs6': str}, keep_default_na=False)
    cs = CodeSpace()
    cs.add_codes(set(df.input_hs6) | set(df.output_hs6) | set(L.input_hs6) | set(L.output_hs6))
    ref = L[L.train_eligible == 1].reset_index(drop=True)
    Vr = pair_vectors(cs, ref.input_hs6, ref.output_hs6)
    ref_txt = (ref.input_hs6 + '>' + ref.output_hs6 + ' | ' + ref.relation_class + ' | DV ' + ref.DV.astype(str)
               + ' | ' + ref.route + ' | ' + [cs.sub[c][:60] for c in ref.input_hs6] + ' -> '
               + [cs.sub[c][:60] for c in ref.output_hs6]).values

    q = df[(df.source == 'ml') & (df.rule_id == '') & ~df.master_id.isin(key.master_id)].copy()
    q['in4'], q['out4'] = q.input_hs6.str[:4], q.output_hs6.str[:4]
    units = []
    for (a, b), g in q.groupby(['in4', 'out4'], sort=True):
        ins, outs = sorted(g.input_hs6.unique()), sorted(g.output_hs6.unique())
        full = len(g) == len(ins) * len(outs)
        units.append({'in4': a, 'out4': b, 'n_pairs': len(g), 'ins': ins, 'outs': outs, 'full': full,
                      'pairs': [] if full else sorted(g.input_hs6 + '>' + g.output_hs6)})
    U = pd.DataFrame(units)
    U['unit_id'] = 'R' + U.in4 + '_' + U.out4
    V = np.vstack([pair_vectors(cs, pd.Series(r.ins).repeat(len(r.outs)), pd.Series(r.outs * len(r.ins))).mean(0)
                   for r in U.itertuples()])
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    ex = []
    for s in range(0, len(V), 2000):
        top = np.argsort(-(V[s:s + 2000] @ Vr.T), axis=1)[:, :K]
        ex.extend([[ref_txt[j] for j in row] for row in top])
    rows = []
    for r, e in zip(U.itertuples(), ex):
        rows.append({
            'unit_id': r.unit_id, 'input_heading': r.in4, 'input_heading_text': cs._t.get(r.in4, ''),
            'output_heading': r.out4, 'output_heading_text': cs._t.get(r.out4, ''), 'n_pairs': r.n_pairs,
            'input_codes': ' ; '.join(f'{c}: {cs.sub[c]}' for c in r.ins),
            'output_codes': ' ; '.join(f'{c}: {cs.sub[c]}' for c in r.outs),
            'pairs_in_unit': 'all input x output combinations' if r.full else ' '.join(r.pairs),
            **{f'ex{j + 1}': e[j] for j in range(K)}})
    R = pd.DataFrame(rows)
    R['ch'] = R.input_heading.str[:2]
    b, n, batch = FIRST_BATCH, 0, []
    for ch, g in R.groupby('ch', sort=True):
        if n and n + len(g) > UNITS_PER_BATCH:
            b, n = b + 1, 0
        batch += [b] * len(g)
        n += len(g)
    R['batch'] = batch
    for f in AI.glob('units_batch_*.csv'):                     # re-running replaces earlier re-route batches
        if int(f.stem[-2:]) >= FIRST_BATCH:
            f.unlink()
    for k, g in R.groupby('batch'):
        g.drop(columns=['ch', 'batch']).to_csv(AI / f'units_batch_{k:02d}.csv', index=False)
    q = q.merge(U[['in4', 'out4', 'unit_id']], on=['in4', 'out4'])
    q['queue'] = 'ml_reroute'
    mem = pd.read_csv(HERE / 'coded/unit_membership.csv', dtype=str, keep_default_na=False)
    mem = pd.concat([mem[mem.queue != 'ml_reroute'], q[['master_id', 'input_hs6', 'output_hs6', 'unit_id', 'queue']]])
    mem.to_csv(HERE / 'coded/unit_membership.csv', index=False)
    info = {'pairs': len(q), 'excluded_in_pair_sample': int(((df.source == 'ml') & (df.rule_id == '')
                                                             & df.master_id.isin(key.master_id)).sum()),
            'band': q.band.value_counts().to_dict(), 'units': len(R),
            'batches': sorted(R.batch.unique().tolist()), 'units_per_batch': R.groupby('batch').size().to_dict(),
            'pairs_per_batch': R.groupby('batch').n_pairs.sum().to_dict()}
    json.dump(info, open(HERE / 'coded/reroute_inputs.json', 'w'), indent=1, default=int)
    print(json.dumps(info, indent=1, default=int))


if __name__ == '__main__':
    main()
