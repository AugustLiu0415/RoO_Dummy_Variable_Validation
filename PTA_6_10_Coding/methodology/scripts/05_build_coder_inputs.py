"""Build the blind inputs for the two AI coders (coder 1 Claude, coder 2 Codex) for PTA 6-10.

1. Heading-pair units: every pair in the ai_units queue (02_copy_and_rules.py) is grouped by (input HS4, output HS4),
   exactly as in PTA_2_5/_work/05_build_coder_inputs.py. A coder gives each unit a default code and may add
   exceptions for single input codes, output codes or pairs. Units are batched by whole input headings (smaller
   files than the chapter batches of PTA 2-5, so each coder session stays short).
2. Pair sample: textile rule pairs, sampled by rule (sqrt-N allocation, floor 5, about 150 in all), coded pair by
   pair by both coders to audit the textile rules on the new pairs (workflow 7d). The two-coder result replaces the
   rule code for the sampled pairs (06_combine.py).
Worked examples (workflow 7c): the 5 most similar coded pairs. Units: the PTA 1-5 master list, i.e. the ASEAN-Japan
labels (training-eligible rows) and the certain (uncertain = 0) codes of PTA 2-5 that were not exact copies. Pair
sample: the ASEAN-Japan labels only, as in PTA 2-5, so the coders who audit the textile rules never see a textile-rule
code as an example (fixed 2026-10-25 after the script review, before any coder had coded the sample).
Neither file shows the pair's own rule decision, ML probability or the other coder's answer.
--sample-only rewrites sample_pairs.csv and sample_key.csv and leaves the unit files untouched.
Output: ai_coders/input/units_batch_NN.csv, ai_coders/input/sample_pairs.csv; _work/coded/unit_membership.csv,
sample_key.csv (stratum and rule decision; not for coders) and coder_inputs.json.

Run: /usr/local/bin/python3 _work/05_build_coder_inputs.py [--sample-only]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import AI, CODED, LABELS_PTA1, MASTER_P25, ML  # noqa: E402

sys.path.insert(0, str(ML / 'ml_v1'))
from features import CodeSpace, pair_vectors  # noqa: E402

SEED = 20261025
UNITS_PER_BATCH = 150         # batches hold whole input headings: at most 150 units and about 200 KB
BATCH_BYTES = 200_000
SAMPLE_N, SAMPLE_FLOOR = 150, 5
K = 5


def describe(cs, c):
    t = cs.text[c].split(' | ')
    return f'{t[1]} | {t[2]}' if len(t) == 3 else cs.text[c]


def reference(cs, pta1_only=False):
    """coded PTA 1-5 pairs used as worked examples, with their example text"""
    L = pd.read_csv(LABELS_PTA1, dtype=str, keep_default_na=False)
    L = L[L.train_eligible == '1'].assign(label=lambda x: x.relation_class, origin='ASEAN-Japan')
    F = pd.read_csv(MASTER_P25, dtype=str, keep_default_na=False)
    F = F[(F.source != 'exact_copy') & (F.source != 'rule') & (F.uncertain == '0') & (not pta1_only)]
    F = F.assign(label=F.source.map(lambda s: 'textile rule' if s == 'rule_textile' else 'AI coders'
                                    if s.startswith('ai_') else 'model or rule'), origin='PTA 2-5')
    R = pd.concat([L[['input_hs6', 'output_hs6', 'DV', 'route', 'label', 'origin']],
                   F[['input_hs6', 'output_hs6', 'DV', 'route', 'label', 'origin']]], ignore_index=True)
    R['DV'] = R.DV.astype(float).astype(int).astype(str)
    cs.add_codes(set(R.input_hs6) | set(R.output_hs6))
    txt = (R.input_hs6 + '>' + R.output_hs6 + ' | ' + R.origin + ': ' + R.label + ' | DV ' + R.DV + ' | ' + R.route
           + ' | ' + [cs.sub[c][:60] for c in R.input_hs6] + ' -> ' + [cs.sub[c][:60] for c in R.output_hs6]).values
    V = pair_vectors(cs, R.input_hs6, R.output_hs6).astype(np.float32)
    return V, txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sample-only', action='store_true')
    sample_only = ap.parse_args().sample_only
    (AI / 'input').mkdir(parents=True, exist_ok=True)
    for d in ('coder1_claude', 'coder2_codex'):
        (AI / d).mkdir(exist_ok=True)
    df = pd.read_csv(CODED / 'master_coded_stage2.csv', dtype=str, keep_default_na=False)
    cs = CodeSpace()
    cs.add_codes(set(df.input_hs6) | set(df.output_hs6))
    REF = {'units': reference(cs), 'sample': reference(cs, pta1_only=True)}

    def examples(V, ref='units'):
        Vr, ref_txt = REF[ref]
        out = []
        V = V.astype(np.float32)
        for s in range(0, len(V), 1000):
            S = V[s:s + 1000] @ Vr.T
            top = np.argpartition(-S, K, axis=1)[:, :K]
            top = np.take_along_axis(top, np.argsort(-np.take_along_axis(S, top, 1), axis=1), 1)
            out.extend([[ref_txt[j] for j in row] for row in top])
        return out

    # ---- 1. heading-pair units (unchanged by --sample-only) ----
    if not sample_only:
        q = df[df.queue == 'ai_units'].copy()
        q['in4'], q['out4'] = q.input_hs6.str[:4], q.output_hs6.str[:4]
        units = []
        for (a, b), g in q.groupby(['in4', 'out4'], sort=True):
            ins, outs = sorted(g.input_hs6.unique()), sorted(g.output_hs6.unique())
            full = len(g) == len(ins) * len(outs)
            units.append({'in4': a, 'out4': b, 'n_pairs': len(g), 'ins': ins, 'outs': outs, 'full': full,
                          'pairs': [] if full else sorted(g.input_hs6 + '>' + g.output_hs6)})
        U = pd.DataFrame(units)
        U['unit_id'] = 'U' + U.in4 + '_' + U.out4
        V = np.vstack([pair_vectors(cs, pd.Series(r.ins).repeat(len(r.outs)),
                                    pd.Series(r.outs * len(r.ins))).mean(0) for r in U.itertuples()])
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
        R['ch'] = R.input_heading.str[:2]
        R['bytes'] = R.drop(columns='ch').apply(lambda r: len(r.to_csv()), axis=1)
        b, n, nb, batch = 1, 0, 0, []
        for h, g in R.groupby('input_heading', sort=True):    # whole input headings; a new batch at a new chapter
            new_ch = batch and R.ch[len(batch) - 1] != h[:2]  # once the batch holds half its units
            if n and (n + len(g) > UNITS_PER_BATCH or nb + g.bytes.sum() > BATCH_BYTES
                      or (new_ch and n >= UNITS_PER_BATCH / 2)):
                b, n, nb = b + 1, 0, 0
            batch += [b] * len(g)
            n += len(g)
            nb += g.bytes.sum()
        R['batch'] = batch
        R = R.drop(columns='bytes')
        for f in (AI / 'input').glob('units_batch_*.csv'):
            f.unlink()
        for k, g in R.groupby('batch'):
            g.drop(columns=['ch', 'batch']).to_csv(AI / 'input' / f'units_batch_{k:02d}.csv', index=False)
        q = q.merge(U[['in4', 'out4', 'unit_id']], on=['in4', 'out4'])
        q[['master_id', 'input_hs6', 'output_hs6', 'unit_id', 'queue']].to_csv(CODED / 'unit_membership.csv', index=False)

    # ---- 2. pair sample of textile rule pairs ----
    rt = df[df.source == 'rule_textile']
    sizes = np.sqrt(rt.rule_id.value_counts())
    alloc = np.maximum(SAMPLE_FLOOR, np.round(SAMPLE_N * sizes / sizes.sum())).astype(int)
    parts = []
    for rule, k in alloc.items():
        g = rt[rt.rule_id == rule]
        s = g.sample(min(k, len(g)), random_state=SEED)
        parts.append(s.assign(stratum='rule:' + rule, weight=len(g) / len(s)))
    S = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
    S['item_id'] = [f'S{i + 1:04d}' for i in range(len(S))]
    exs = examples(pair_vectors(cs, S.input_hs6, S.output_hs6), ref='sample')
    P = pd.DataFrame({'item_id': S.item_id, 'master_id': S.master_id, 'input_hs6': S.input_hs6,
                      'input_description': [describe(cs, x) for x in S.input_hs6], 'output_hs6': S.output_hs6,
                      'output_description': [describe(cs, x) for x in S.output_hs6],
                      **{f'ex{j + 1}': [e[j] for e in exs] for j in range(K)}})
    P.to_csv(AI / 'input' / 'sample_pairs.csv', index=False)
    S[['item_id', 'master_id', 'input_hs6', 'output_hs6', 'stratum', 'weight', 'source', 'rule_id', 'DV',
       'uncertain', 'route']].to_csv(CODED / 'sample_key.csv', index=False)
    sz = {f.name: f.stat().st_size for f in sorted((AI / 'input').glob('*.csv'))}
    info = json.load(open(CODED / 'coder_inputs.json')) if sample_only else {
        'units': len(R), 'unit_pairs': int(R.n_pairs.sum()), 'batches': int(R.batch.max()),
        'units_per_batch': R.groupby('batch').size().to_dict(),
        'pairs_per_batch': R.groupby('batch').n_pairs.sum().to_dict(),
        'input_chapters_per_batch': R.groupby('batch').ch.agg(lambda s: f'{s.min()}-{s.max()}').to_dict(),
        'unit_size': R.n_pairs.describe().round(1).to_dict()}
    info.update({'sample_items': len(S), 'sample_strata': S.stratum.value_counts().to_dict(),
                 'reference_pairs_for_examples': {k: len(v[1]) for k, v in REF.items()},
                 'file_bytes': sz, 'total_bytes': sum(sz.values())})
    json.dump(info, open(CODED / 'coder_inputs.json', 'w'), indent=1, default=int)
    print(json.dumps(info, indent=1, default=int))


if __name__ == '__main__':
    main()
