"""Combine the two AI coders for PTA 6-10 and audit the textile rules with the pair sample
(same rules as PTA_2_5/_work/06_combine.py; there are no ML bands or ML-rule conflicts in this round).

1. Units -> pairs. Each coder's unit rows are resolved to pairs with the codebook precedence pair > in > out >
   default (codebook section 8).
2. Combining rule (workflow, "Two AI coders"): both 0 -> DV 0; both 1 -> DV 1; they disagree -> DV 1, uncertain 1.
3. Agreement: Cohen's kappa between the coders, pair-weighted over unit pairs, over unit default rows, by input
   chapter group, and over the pair sample.
4. Audit (workflow 7d): on the textile pair sample, the share of textile-rule codes that match the coders where the
   coders agree, by rule, plus the weighted total (weights = rule population / sample size).
5. Sampled pairs take the two-coder result (source = ai_sample); the rule's value is kept in dv_auto.
6. TUR_SGP concordance pairs (HS2012 codes, 05b_build_concord_pairs.py) are combined with the same rule into
   _work/coded/concord_coded.csv; 09 gives their records this code (source ai_concord).
Outputs: _work/coded/master_coded_combined.csv (one row per unique HS2002 pair, both coders' codes and reasons),
_work/coded/concord_coded.csv, _work/coded/sample_audit.csv, final/combine_report.json.

Run after both coders finished: /usr/local/bin/python3 _work/06_combine.py (coder 2 defaults to the Codex v2 run)
     --draft   use coder 1 alone where coder 2 has no file yet (source ai1_only); for progress notes only
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import AI, CODED, FINAL  # noqa: E402

DEC = ['dv', 'route', 'step', 'reason']
GROUPS = [(1, 5, '01-05 animal'), (6, 15, '06-15 plant/fats'), (16, 24, '16-24 food'), (25, 27, '25-27 mineral'),
          (28, 38, '28-38 chemical'), (39, 40, '39-40 plastic/rubber'), (41, 43, '41-43 leather'),
          (44, 49, '44-49 wood/paper'), (50, 67, '50-67 textile/footwear'), (68, 71, '68-71 stone/glass/jewel'),
          (72, 83, '72-83 metals'), (84, 85, '84-85 machinery'), (86, 89, '86-89 transport'), (90, 97, '90-97 other')]


def group(ch):
    return next((g for a, b, g in GROUPS if a <= ch <= b), 'other')


def kappa(a, b):
    a, b = np.asarray(a, int), np.asarray(b, int)
    if len(a) == 0:
        return None
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return round(float((po - pe) / (1 - pe)), 4) if pe < 1 else 1.0


def read_units(folder):
    fs = sorted(folder.glob('units_batch_*.csv'))
    if not fs:
        return pd.DataFrame(columns=['unit_id', 'scope'] + DEC)
    return pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in fs], ignore_index=True)


def resolve(mem, dec):
    """pair-level decision of one coder; later layers override earlier ones: default < out < in < pair"""
    res = mem[['master_id', 'unit_id', 'input_hs6', 'output_hs6']].copy()
    for c in DEC + ['scope']:
        res[c] = pd.Series(np.nan, index=res.index, dtype=object)
    sc = dec.scope
    lay = [(dec[sc == 'default'], ['unit_id'])]
    o = dec[sc.str.startswith('out:')].assign(output_hs6=lambda x: x.scope.str[4:])
    lay.append((o, ['unit_id', 'output_hs6']))
    i = dec[sc.str.startswith('in:')].assign(input_hs6=lambda x: x.scope.str[3:])
    lay.append((i, ['unit_id', 'input_hs6']))
    p = dec[sc.str.startswith('pair:')]
    p = p.assign(input_hs6=p.scope.str[5:11], output_hs6=p.scope.str[12:18])
    lay.append((p, ['unit_id', 'input_hs6', 'output_hs6']))
    for L, keys in lay:
        L = L.drop_duplicates(keys, keep='last')[keys + DEC + ['scope']]
        m = res[keys].merge(L, on=keys, how='left')
        hit = m.dv.notna().values
        for c in DEC + ['scope']:
            res.loc[hit, c] = m.loc[hit, c].values
    return res


def combine(d1, d2, r1, r2, s1, s2):
    """two-coder rule; returns DV, uncertain, route, step arrays"""
    d1, d2 = np.asarray(d1).astype(int), np.asarray(d2).astype(int)
    r1, r2 = np.asarray(r1), np.asarray(r2)
    agree = d1 == d2
    dv = np.where(agree, d1, 1)
    unc = (~agree).astype(int)
    route = np.where(agree, r1, np.where(d1 == 1, r1, r2))
    st1 = pd.to_numeric(pd.Series(np.asarray(s1)), errors='coerce').values
    st2 = pd.to_numeric(pd.Series(np.asarray(s2)), errors='coerce').values
    step = np.where(dv == 0, np.fmin(st1, st2), np.where(agree & (route == 'same_good'), 2, np.nan))
    return dv, unc, route, step


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--coder1', default='coder1_claude')
    ap.add_argument('--coder2', default='coder2_codex_v2')     # coder2_codex = Codex round 1, discarded 2026-10-27
    ap.add_argument('--draft', action='store_true')
    args = ap.parse_args()
    FINAL.mkdir(parents=True, exist_ok=True)
    c1, c2 = AI / args.coder1, AI / args.coder2
    rep = {'run': datetime.datetime.now().isoformat(timespec='seconds'), 'coder1': str(c1), 'coder2': str(c2),
           'draft': args.draft}
    df = pd.read_csv(CODED / 'master_coded_stage2.csv', dtype=str, keep_default_na=False)
    mem = pd.read_csv(CODED / 'unit_membership.csv', dtype=str, keep_default_na=False)
    key = pd.read_csv(CODED / 'sample_key.csv', dtype=str, keep_default_na=False)

    # ---- 1-3. units -> pairs, combine, kappa
    u1, u2 = read_units(c1), read_units(c2)
    p1, p2 = resolve(mem, u1), resolve(mem, u2)
    have1, have2 = p1.dv.notna(), p2.dv.notna()
    rep['unit_pairs'] = len(mem)
    rep['unit_pairs_coded'] = {'coder1': int(have1.sum()), 'coder2': int(have2.sum())}
    if not have1.all():
        sys.exit(f'coder 1 has no decision for {int((~have1).sum())} unit pairs')
    if not have2.all() and not args.draft:
        sys.exit(f'coder 2 has no decision for {int((~have2).sum())} unit pairs; run with --draft for a preview')
    both = (have1 & have2).values
    U = mem[['master_id', 'unit_id']].copy()
    for c in DEC + ['scope']:
        U[c + '_ai1'] = p1[c].values
        U[c + '_ai2'] = p2[c].values
    dv, unc, route, step = combine(p1.dv[both], p2.dv[both], p1.route[both], p2.route[both], p1.step[both],
                                   p2.step[both])
    U['DV'], U['uncertain'], U['route'], U['step'] = np.nan, np.nan, '', np.nan
    U.loc[both, 'DV'], U.loc[both, 'uncertain'], U.loc[both, 'route'], U.loc[both, 'step'] = dv, unc, route, step
    U['source'] = np.where(both, 'ai_units', 'ai1_only')
    one = ~both                                              # draft only: coder 1 alone
    U.loc[one, 'DV'] = p1.dv[one].astype(int).values
    U.loc[one, 'uncertain'] = 0
    U.loc[one, 'route'] = p1.route[one].values
    U.loc[one, 'step'] = pd.to_numeric(p1.step[one], errors='coerce').values
    dflt1 = u1[u1.scope == 'default'].set_index('unit_id').dv
    dflt2 = u2[u2.scope == 'default'].set_index('unit_id').dv
    ud = pd.concat([dflt1.rename('a'), dflt2.rename('b')], axis=1).dropna()
    b1, b2 = p1.dv[both].astype(int), p2.dv[both].astype(int)
    rep['units'] = {
        'pairs_both_coders': int(both.sum()), 'kappa_pairs': kappa(b1, b2),
        'agreement_pairs': round(float((b1.values == b2.values).mean()), 4) if both.any() else None,
        'kappa_unit_defaults': kappa(ud.a, ud.b), 'units_both_coders': len(ud),
        'DV1_coder1': int(p1.dv[have1].astype(int).sum()), 'DV1_coder2': int(p2.dv[have2].astype(int).sum()),
        'coder1_1_coder2_0': int(((b1 == 1) & (b2.values == 0)).sum()),
        'coder1_0_coder2_1': int(((b1 == 0) & (b2.values == 1)).sum()),
        'DV1': int((U.DV == 1).sum()), 'DV0': int((U.DV == 0).sum()), 'uncertain': int(U.uncertain.sum()),
        'exceptions_ai1': int((u1.scope != 'default').sum()), 'exceptions_ai2': int((u2.scope != 'default').sum()),
    }
    if both.any():
        grp = mem.input_hs6.str[:2].astype(int).map(group)
        rep['units']['kappa_by_input_group'] = {
            g: {'pairs': int(m.sum()), 'kappa': kappa(p1.dv[m], p2.dv[m]),
                'agree': round(float((p1.dv[m] == p2.dv[m]).mean()), 4),
                'coder1_DV1': round(float(p1.dv[m].astype(int).mean()), 4),
                'coder2_DV1': round(float(p2.dv[m].astype(int).mean()), 4)}
            for g in sorted(grp.unique()) for m in [both & (grp == g).values] if m.any()}

    # ---- 4. textile pair sample: coders vs the textile rules
    f1, f2 = c1 / 'sample_pairs.csv', c2 / 'sample_pairs.csv'
    s1 = pd.read_csv(f1, dtype=str, keep_default_na=False)
    s2 = pd.read_csv(f2, dtype=str, keep_default_na=False) if f2.exists() else pd.DataFrame(columns=['item_id'] + DEC)
    S = key.merge(s1.add_suffix('_ai1').rename(columns={'item_id_ai1': 'item_id'}), on='item_id', how='left')
    S = S.merge(s2.add_suffix('_ai2').rename(columns={'item_id_ai2': 'item_id'}), on='item_id', how='left')
    S['dv_rule'] = S.DV.astype(int)
    sb = S.dv_ai1.fillna('').ne('') & S.dv_ai2.fillna('').ne('')
    S['n_both'] = sb
    S['agree'] = sb & (S.dv_ai1 == S.dv_ai2)
    S['dv_cons'] = np.where(S.agree, pd.to_numeric(S.dv_ai1, errors='coerce'), np.nan)
    S['DV_ai'] = np.where(sb, np.where(S.agree, S.dv_cons, 1), np.nan)
    S['weight'] = S.weight.astype(float)
    rep['sample'] = {'items': len(S), 'both_coders': int(sb.sum()), 'kappa': kappa(S.dv_ai1[sb], S.dv_ai2[sb]),
                     'agreement': round(float(S.agree[sb].mean()), 4) if sb.any() else None}

    def acc(g):
        a, b = g[g.agree], g[g.n_both]
        return {'n': len(g), 'coders_agree': len(a),
                'rule_acc_vs_agreed': round(float((a.dv_rule == a.dv_cons).mean()), 4) if len(a) else None,
                'rule_acc_vs_combined': round(float((b.dv_rule == b.DV_ai).mean()), 4) if len(b) else None,
                'rule_DV1': int(g.dv_rule.sum()), 'coders_DV1_agreed': int((a.dv_cons == 1).sum())}

    rep['textile_rule_audit'] = {r: acc(g) for r, g in S.groupby('rule_id')}
    a = S[S.agree]
    rep['textile_rule_audit_weighted'] = round(float(np.average(a.dv_rule == a.dv_cons, weights=a.weight)), 4) \
        if len(a) else None

    # ---- assemble the master list
    F = df.copy()
    for c in ['DV', 'uncertain', 'locked']:
        F[c] = pd.to_numeric(F[c], errors='coerce')
    F['step'] = pd.to_numeric(F.step, errors='coerce')
    Ui = U.set_index('master_id')
    um = F.master_id.isin(Ui.index)
    for c in ['DV', 'uncertain', 'route', 'step', 'source']:
        F.loc[um, c] = F.loc[um, 'master_id'].map(Ui[c]).values
    F.loc[um, 'locked'] = 0
    F['unit_id'] = F.master_id.map(Ui.unit_id).fillna('')
    for c in ['dv', 'route', 'step', 'reason', 'scope']:
        for s in ('ai1', 'ai2'):
            v = F.master_id.map(Ui[f'{c}_{s}'])
            if c in ('dv', 'reason'):                   # exact copies keep the AI codes copied from PTA 2-5
                F[f'{c}_{s}'] = np.where(um, v.fillna(''), F[f'{c}_{s}'] if c == 'dv' else F[f'why_{s}'])
            else:
                F[f'{c}_{s}'] = v.fillna('')
    F['dv_auto'] = np.nan
    Sb = S[sb].set_index('master_id')
    sm = F.master_id.isin(Sb.index)
    F.loc[sm, 'dv_auto'] = F.loc[sm, 'DV']
    for c in ['dv', 'route', 'step', 'reason']:
        for s in ('ai1', 'ai2'):
            F.loc[sm, f'{c}_{s}'] = F.loc[sm, 'master_id'].map(Sb[f'{c}_{s}']).values
    dv, unc, route, step = combine(Sb.dv_ai1, Sb.dv_ai2, Sb.route_ai1, Sb.route_ai2, Sb.step_ai1, Sb.step_ai2)
    sres = pd.DataFrame({'DV': dv, 'uncertain': unc, 'route': route, 'step': step}, index=Sb.index)
    for c in sres:
        F.loc[sm, c] = F.loc[sm, 'master_id'].map(sres[c]).values
    F.loc[sm, 'source'] = 'ai_sample'
    F.loc[sm, 'locked'] = (F.loc[sm, 'route'].eq('same_good') & F.loc[sm, 'uncertain'].astype(int).eq(0)).astype(int)
    left = F.DV.isna()
    if left.any():
        sys.exit(f'{int(left.sum())} pairs still without DV, e.g. {F.master_id[left].head().tolist()}')
    for c in ['DV', 'uncertain', 'locked']:
        F[c] = F[c].astype(int)
    F['step'] = pd.to_numeric(F.step, errors='coerce').astype('Int64')
    rep['dv0_without_step'] = int(((F.DV == 0) & F.step.isna()).sum())
    F = F.drop(columns=['why_ai1', 'why_ai2'])
    F.to_csv(CODED / 'master_coded_combined.csv', index=False)

    # ---- 6. TUR_SGP concordance pairs (HS2012), coded pair by pair
    if (CODED / 'concord_key.csv').exists():
        K = pd.read_csv(CODED / 'concord_key.csv', dtype=str, keep_default_na=False)
        k1 = pd.read_csv(c1 / 'concord_pairs.csv', dtype=str, keep_default_na=False)
        f2c = c2 / 'concord_pairs.csv'
        if not f2c.exists() and not args.draft:
            sys.exit('coder 2 has no concord_pairs.csv; run with --draft for a preview')
        k2 = pd.read_csv(f2c, dtype=str, keep_default_na=False) if f2c.exists() else \
            pd.DataFrame({'item_id': k1.item_id, **{c: '' for c in DEC}})
        C = K.merge(k1.add_suffix('_ai1').rename(columns={'item_id_ai1': 'item_id'}), on='item_id', how='left')
        C = C.merge(k2.add_suffix('_ai2').rename(columns={'item_id_ai2': 'item_id'}), on='item_id', how='left')
        assert C.dv_ai1.notna().all() and (C.dv_ai1 != '').all(), 'coder 1 concord_pairs incomplete'
        cb = C.dv_ai2.fillna('').ne('')
        dv, unc, route, step = combine(C.dv_ai1, np.where(cb, C.dv_ai2, C.dv_ai1), C.route_ai1,
                                       np.where(cb, C.route_ai2, C.route_ai1), C.step_ai1,
                                       np.where(cb, C.step_ai2, C.step_ai1))
        C['DV'], C['uncertain'], C['route'], C['step'] = dv, unc, route, step
        C['source'] = np.where(cb, 'ai_concord', 'ai1_only')
        C['step'] = pd.to_numeric(C.step, errors='coerce').astype('Int64')
        C.to_csv(CODED / 'concord_coded.csv', index=False)
        rep['concord'] = {'pairs': len(C), 'both_coders': int(cb.sum()),
                          'kappa': kappa(C.dv_ai1[cb], C.dv_ai2[cb]),
                          'agreement': round(float((C.dv_ai1[cb] == C.dv_ai2[cb]).mean()), 4) if cb.any() else None,
                          'DV1': int(C.DV.sum()), 'uncertain': int(C.uncertain.sum())}
    S.to_csv(CODED / 'sample_audit.csv', index=False)
    new = F.source != 'exact_copy'
    rep['master'] = {'pairs': len(F), 'source': F.source.value_counts().to_dict(),
                     'new_pairs': int(new.sum()), 'new_DV1': int(F.DV[new].sum()),
                     'new_uncertain': int(F.uncertain[new].sum())}
    json.dump(rep, open(FINAL / 'combine_report.json', 'w'), indent=1, default=str)
    print(json.dumps({k: rep.get(k) for k in ['units', 'sample', 'textile_rule_audit_weighted', 'concord', 'master']},
                     indent=1, default=str))


if __name__ == '__main__':
    main()
