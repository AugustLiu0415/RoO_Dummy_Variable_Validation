"""Build the blind inputs for the two AI coders (coder 1 Claude, coder 2 Codex).

1. Heading-pair units: every pair still open after stages 1-2 (non-textile ML middle band and non-textile pairs in
   chapter pairs PTA_1 never coded) is grouped by (input HS4, output HS4). A coder gives each unit a default code and
   may add exceptions for single input codes, output codes or pairs. Units are batched by input chapter.
2. Pair sample: a stratified sample coded pair by pair by both coders, to measure the textile rules and the ML
   bands: textile rule pairs (sqrt-N allocation by rule, floor 10, 400 in all), 100 ML keep1 and 100 ML turn0 pairs,
   and 150 of the textile pairs where the ML band and the textile rule disagree (sqrt-N by rule, floor 5).
Each item carries the 5 most similar coded PTA_1 pairs as worked examples (workflow step 7c). Neither file shows the
ML probability, the rule decision or the other coder's answer.
Output: ai_coders/input/units_batch_NN.csv, ai_coders/input/sample_pairs.csv; _work/coded/coder_inputs.json and
_work/coded/sample_key.csv (stratum and the rule / ML decision; not for coders).
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
SEED = 20261018
UNITS_PER_BATCH = 250
K = 5


def describe(cs, c):
    t = cs.text[c].split(' | ')
    return f'{t[1]} | {t[2]}' if len(t) == 3 else cs.text[c]


def main():
    AI.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(HERE / 'coded/master_coded_stage2.csv', dtype={'input_hs6': str, 'output_hs6': str},
                     keep_default_na=False)
    L = pd.read_csv(LABELS, dtype={'input_hs6': str, 'output_hs6': str}, keep_default_na=False)
    cs = CodeSpace()
    cs.add_codes(set(df.input_hs6) | set(df.output_hs6) | set(L.input_hs6) | set(L.output_hs6))
    ref = L[L.train_eligible == 1].reset_index(drop=True)
    Vr = pair_vectors(cs, ref.input_hs6, ref.output_hs6)
    ref_txt = (ref.input_hs6 + '>' + ref.output_hs6 + ' | ' + ref.relation_class + ' | DV ' + ref.DV.astype(str)
               + ' | ' + ref.route + ' | ' + [cs.sub[c][:60] for c in ref.input_hs6] + ' -> '
               + [cs.sub[c][:60] for c in ref.output_hs6]).values

    def examples(V):
        out = []
        for s in range(0, len(V), 2000):
            S = V[s:s + 2000] @ Vr.T
            top = np.argsort(-S, axis=1)[:, :K]
            out.extend([[ref_txt[j] for j in row] for row in top])
        return out

    rng = np.random.default_rng(SEED)
    # ---- 1. heading-pair units ----
    q = df[df.queue.isin(['ml_middle', 'unseen_other'])].copy()
    q['in4'], q['out4'] = q.input_hs6.str[:4], q.output_hs6.str[:4]
    units = []
    for (a, b), g in q.groupby(['in4', 'out4'], sort=True):
        ins, outs = sorted(g.input_hs6.unique()), sorted(g.output_hs6.unique())
        full = len(g) == len(ins) * len(outs)
        units.append({'in4': a, 'out4': b, 'n_pairs': len(g), 'ins': ins, 'outs': outs, 'full': full,
                      'pairs': [] if full else sorted(g.input_hs6 + '>' + g.output_hs6)})
    U = pd.DataFrame(units)
    U['unit_id'] = 'U' + U.in4 + '_' + U.out4          # stable id: the heading pair itself
    V = np.vstack([pair_vectors(cs, pd.Series(r.ins).repeat(len(r.outs)), pd.Series(r.outs * len(r.ins))).mean(0)
                   for r in U.itertuples()])
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    ex = examples(V)
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
    # batches: whole input chapters, about UNITS_PER_BATCH units each
    R['ch'] = R.input_heading.str[:2]
    b, n, batch = 1, 0, []
    for ch, g in R.groupby('ch', sort=True):
        if n and n + len(g) > UNITS_PER_BATCH:
            b, n = b + 1, 0
        batch += [b] * len(g)
        n += len(g)
    R['batch'] = batch
    for k, g in R.groupby('batch'):
        g.drop(columns=['ch', 'batch']).to_csv(AI / f'units_batch_{k:02d}.csv', index=False)
    q = q.merge(U[['in4', 'out4', 'unit_id']], on=['in4', 'out4'])
    q[['master_id', 'input_hs6', 'output_hs6', 'unit_id', 'queue']].to_csv(HERE / 'coded/unit_membership.csv', index=False)

    # ---- 2. pair sample ----
    parts = []
    rt = df[df.source == 'rule_textile']
    sizes = np.sqrt(rt.rule_id.value_counts())
    alloc = np.maximum(10, np.round(400 * sizes / sizes.sum())).astype(int)
    for rule, n in alloc.items():
        g = rt[rt.rule_id == rule]
        s = g.sample(min(n, len(g)), random_state=SEED)
        parts.append(s.assign(stratum='rule:' + rule, weight=len(g) / len(s)))
    mlp = df[df.source == 'ml']
    for band in ('keep1', 'turn0'):
        g = mlp[mlp.band == band]
        s = g.sample(min(100, len(g)), random_state=SEED)
        parts.append(s.assign(stratum='ml:' + band, weight=len(g) / len(s)))
    # ML band vs textile rule conflicts: 150 sampled by rule (sqrt-N, floor 5); the sample decides, per rule,
    # whether the ML band or the rule is applied to the remaining conflicts
    c = df[df.queue == 'ml_rule_conflict']
    sz = np.sqrt(c.rule_id.value_counts())
    al = np.maximum(5, np.round(150 * sz / sz.sum())).astype(int)
    for rule, n in al.items():
        g = c[c.rule_id == rule]
        s = g.sample(min(n, len(g)), random_state=SEED)
        parts.append(s.assign(stratum='conflict:' + rule, weight=len(g) / len(s)))
    S = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
    S['item_id'] = [f'S{i + 1:04d}' for i in range(len(S))]
    exs = examples(pair_vectors(cs, S.input_hs6, S.output_hs6))
    P = pd.DataFrame({'item_id': S.item_id, 'master_id': S.master_id, 'input_hs6': S.input_hs6,
                      'input_description': [describe(cs, x) for x in S.input_hs6], 'output_hs6': S.output_hs6,
                      'output_description': [describe(cs, x) for x in S.output_hs6],
                      **{f'ex{j + 1}': [e[j] for e in exs] for j in range(K)}})
    half = (len(P) + 1) // 2                     # two files, one Codex session each
    P.iloc[:half].to_csv(AI / 'sample_pairs_part1.csv', index=False)
    P.iloc[half:].to_csv(AI / 'sample_pairs_part2.csv', index=False)
    S[['item_id', 'master_id', 'input_hs6', 'output_hs6', 'stratum', 'weight', 'source', 'rule_id', 'DV', 'p_ens',
       'band']].to_csv(HERE / 'coded/sample_key.csv', index=False)
    info = {'units': len(R), 'unit_pairs': int(R.n_pairs.sum()), 'batches': int(R.batch.max()),
            'units_per_batch': R.groupby('batch').size().to_dict(),
            'pairs_per_batch': R.groupby('batch').n_pairs.sum().to_dict(),
            'sample_items': len(S), 'sample_strata': S.stratum.value_counts().to_dict()}
    json.dump(info, open(HERE / 'coded/coder_inputs.json', 'w'), indent=1, default=int)
    print(json.dumps(info, indent=1, default=int))


if __name__ == '__main__':
    main()
