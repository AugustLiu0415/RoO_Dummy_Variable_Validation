"""Combine the two AI coders, audit the rules and ML bands with the pair sample, and write the final PTA 2-5 data.

1. Units -> pairs. Each coder's unit rows are resolved to pairs with the codebook precedence pair > in > out >
   default (codebook section 8).
2. Combining rule (workflow, "Two AI coders"): both 0 -> DV 0; both 1 -> DV 1; they disagree -> DV 1, uncertain 1.
   DV_strict = DV x (1 - uncertain). DV_max = 1 when DV = 1 or when either coder's route is recycle_direct.
3. Agreement: Cohen's kappa between the coders, pair-weighted over unit pairs, over unit default rows and over the
   pair sample.
4. Audit (workflow 7d): on the pair sample, the share of rule / ML decisions that match the coders where the coders
   agree, by stratum, plus weighted totals (weights = stratum population / sample size).
5. ML-rule conflicts (textile pairs where the ML band and the textile rule disagree): per rule and band, the side
   that matches the coders more often on the sampled pairs that are conflicts under the current rules wins, if at least MIN_CONFLICT_N sampled conflicts
   have coder agreement and the winner's accuracy is at least MIN_WIN_ACC; otherwise DV 1, uncertain 1.
6. Sampled pairs take the two-coder result (source = ai_sample); the earlier value is kept in dv_auto.
7. Workflow 7d (2026-10-18): non-textile ML-band pairs were re-routed to the coders as units (08_build_reroute_units.py,
   queue ml_reroute, source ai_units_ml_reroute); their ML value is kept in dv_auto and audited (ml_reroute_audit).
Outputs (folder --out, default PTA_2_5/final): master_coded_final.csv (one row per unique pair, both coders' codes
and reasons), <PTA>_coded_<date>.csv / .dta (one row per PTA record), combine_report.json.

Run after both coders finished: /usr/local/bin/python3 _work/06_combine.py
     --coder2 <folder under ai_coders or a path>   (default coder2_codex)
     --draft   use coder 1 alone where coder 2 has no file yet (source ai1_only); for progress notes only
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from textile import attributes, code_pair, load_texts  # noqa: E402

AI = HERE.parent / 'ai_coders'
CODED = HERE / 'coded'
INTAKE = HERE / 'intake'
PTAS = ['BRN_JPN', 'AUS_USA', 'CAFTA', 'BHR_USA']
MIN_CONFLICT_N = 5
MIN_WIN_ACC = 0.8
BAND_THRESHOLD = 0.9          # audit: a band below this accuracy should be narrowed (workflow 7d)
DEC = ['dv', 'route', 'step', 'reason']


def kappa(a, b):
    a, b = np.asarray(a, int), np.asarray(b, int)
    if len(a) == 0:
        return None
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return round(float((po - pe) / (1 - pe)), 4) if pe < 1 else 1.0


def coder_dir(name):
    p = Path(name)
    return p if p.is_absolute() else AI / name


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
    lay = []
    lay.append((dec[sc == 'default'], ['unit_id']))
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
    """two-coder rule; returns DV, uncertain, route, step, DV_max arrays"""
    d1, d2 = d1.astype(int), d2.astype(int)
    agree = d1 == d2
    dv = np.where(agree, d1, 1)
    unc = (~agree).astype(int)
    route = np.where(agree, r1, np.where(d1 == 1, r1, r2))
    st1 = pd.to_numeric(s1, errors='coerce')
    st2 = pd.to_numeric(s2, errors='coerce')
    step = np.where(dv == 0, np.fmin(st1, st2), np.where(agree & (route == 'same_good'), 2, np.nan))
    dvmax = np.where((dv == 1) | (r1 == 'recycle_direct') | (r2 == 'recycle_direct'), 1, 0)
    return dv, unc, route, step, dvmax


def ml_dv(band):
    return band.map({'keep1': 1, 'turn0': 0})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--coder1', default='coder1_claude')
    ap.add_argument('--coder2', default='coder2_codex')
    ap.add_argument('--out', default=str(HERE.parent / 'final'))
    ap.add_argument('--draft', action='store_true')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    c1, c2 = coder_dir(args.coder1), coder_dir(args.coder2)
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
    both = have1 & have2
    U = mem[['master_id', 'unit_id']].copy()
    for c in DEC + ['scope']:
        U[c + '_ai1'] = p1[c].values
        U[c + '_ai2'] = p2[c].values
    dv, unc, route, step, dvmax = combine(p1.dv[both], p2.dv[both], p1.route[both].values, p2.route[both].values,
                                          p1.step[both], p2.step[both])
    U['DV'], U['uncertain'], U['route'], U['step'], U['DV_max'] = np.nan, np.nan, '', np.nan, np.nan
    U.loc[both, ['DV', 'uncertain', 'DV_max']] = np.c_[dv, unc, dvmax]
    U.loc[both, 'route'] = route
    U.loc[both, 'step'] = step
    U['source'] = np.where(both, 'ai_units', 'ai1_only')
    one = ~both                                              # draft only: coder 1 alone
    U.loc[one, 'DV'] = p1.dv[one].astype(int).values
    U.loc[one, 'uncertain'] = 0
    U.loc[one, 'route'] = p1.route[one].values
    U.loc[one, 'step'] = pd.to_numeric(p1.step[one], errors='coerce').values
    U.loc[one, 'DV_max'] = np.where((p1.dv[one].astype(int) == 1) | (p1.route[one] == 'recycle_direct'), 1, 0)
    dflt1 = u1[u1.scope == 'default'].set_index('unit_id').dv
    dflt2 = u2[u2.scope == 'default'].set_index('unit_id').dv
    ud = pd.concat([dflt1.rename('a'), dflt2.rename('b')], axis=1).dropna()
    rep['units'] = {
        'pairs_both_coders': int(both.sum()),
        'kappa_pairs': kappa(p1.dv[both], p2.dv[both]),
        'agreement_pairs': round(float((p1.dv[both] == p2.dv[both]).mean()), 4) if both.any() else None,
        'kappa_unit_defaults': kappa(ud.a, ud.b), 'units_both_coders': len(ud),
        'DV1': int((U.DV == 1).sum()), 'DV0': int((U.DV == 0).sum()), 'uncertain': int(U.uncertain.sum()),
        'exceptions_ai1': int((u1.scope != 'default').sum()), 'exceptions_ai2': int((u2.scope != 'default').sum()),
    }
    for qn, qm in (('original_units', mem.queue != 'ml_reroute'), ('ml_reroute_units', mem.queue == 'ml_reroute')):
        m = both & qm.values
        if m.any():
            rep['units'][qn] = {'pairs': int(m.sum()), 'kappa': kappa(p1.dv[m], p2.dv[m]),
                                'agree': round(float((p1.dv[m] == p2.dv[m]).mean()), 4)}
    if both.any():
        sec = mem.input_hs6.str[:2].astype(int)
        grp = pd.cut(sec, [0, 5, 15, 24, 27, 38, 40, 43, 49, 67, 71, 83, 85, 89, 97],
                     labels=['01-05 animal', '06-15 plant/fats', '16-24 food', '25-27 mineral', '28-38 chemical',
                             '39-40 plastic/rubber', '41-43 leather', '44-49 wood/paper', '50-67 textile/footwear',
                             '68-71 stone/glass/jewel', '72-83 metals', '84-85 machinery', '86-89 transport',
                             '90-97 other'])
        rep['units']['kappa_by_input_group'] = {
            str(g): {'pairs': int(m.sum()), 'kappa': kappa(p1.dv[m], p2.dv[m]),
                     'agree': round(float((p1.dv[m] == p2.dv[m]).mean()), 4)}
            for g in grp.cat.categories for m in [both & (grp == g)] if m.any()}

    # ---- 4. pair sample: coders, audit of rules and ML bands
    s1 = pd.read_csv(c1 / 'sample_pairs_part1.csv', dtype=str, keep_default_na=False)
    s1 = pd.concat([s1, pd.read_csv(c1 / 'sample_pairs_part2.csv', dtype=str, keep_default_na=False)])
    f2 = [c2 / 'sample_pairs_part1.csv', c2 / 'sample_pairs_part2.csv']
    s2 = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in f2 if f.exists()]) if any(
        f.exists() for f in f2) else pd.DataFrame(columns=['item_id'] + DEC)
    S = key.merge(s1.add_suffix('_ai1').rename(columns={'item_id_ai1': 'item_id'}), on='item_id', how='left')
    S = S.merge(s2.add_suffix('_ai2').rename(columns={'item_id_ai2': 'item_id'}), on='item_id', how='left')
    st = df.set_index('master_id')
    S['kind'] = S.stratum.str.split(':').str[0]
    S['rule_id_now'] = S.master_id.map(st.rule_id)
    S['dv_rule'] = pd.to_numeric(S.master_id.map(st.rule_dv), errors='coerce')      # current rules
    S['dv_ml'] = ml_dv(S.band)
    # rule decision when the sample was drawn (textile rules were corrected on 2026-10-18 after it was drawn)
    S['dv_rule_sampled'] = np.where(S.kind == 'rule', pd.to_numeric(S.DV, errors='coerce'),
                                    np.where(S.kind == 'conflict', 1 - S.dv_ml, np.nan))
    S['dv_auto'] = np.where(S.kind == 'ml', S.dv_ml, np.where(S.kind == 'rule', S.dv_rule, np.nan))
    S['queue_now'] = S.master_id.map(st.queue)
    sb = S.dv_ai1.notna() & S.dv_ai2.notna() & (S.dv_ai1 != '') & (S.dv_ai2 != '')
    S['n_both'] = sb
    S['agree'] = sb & (S.dv_ai1 == S.dv_ai2)
    S['dv_cons'] = np.where(S.agree, pd.to_numeric(S.dv_ai1, errors='coerce'), np.nan)
    S['DV_ai'] = np.where(sb, np.where(S.agree, S.dv_cons, 1), np.nan)
    S['weight'] = S.weight.astype(float)
    rep['sample'] = {'items': len(S), 'both_coders': int(sb.sum()),
                     'kappa': kappa(S.dv_ai1[sb], S.dv_ai2[sb]),
                     'agreement': round(float(S.agree[sb].mean()), 4) if sb.any() else None}

    def acc(g, col):
        a, b = g[g.agree], g[g.n_both]
        return {'n': len(g), 'both_coders': len(b), 'coders_agree': len(a),
                'acc_vs_agreed': round(float((a[col] == a.dv_cons).mean()), 4) if len(a) else None,
                'acc_vs_combined': round(float((b[col] == b.DV_ai).mean()), 4) if len(b) else None,
                'auto_DV1': int((g[col] == 1).sum()), 'coders_DV1_agreed': int((a.dv_cons == 1).sum())}

    aud = {}
    for s, g in S[S.kind == 'ml'].groupby('stratum'):
        aud[s] = acc(g, 'dv_auto')
    for s, g in S[S.kind == 'rule'].groupby('stratum'):
        aud[s] = {'rule_now': acc(g, 'dv_rule'), 'rule_at_sampling': acc(g, 'dv_rule_sampled')}
    for s, g in S[S.kind == 'conflict'].groupby('stratum'):
        aud[s] = {'rule_now': acc(g, 'dv_rule'), 'rule_at_sampling': acc(g, 'dv_rule_sampled'), 'ml': acc(g, 'dv_ml')}
    rep['audit_by_stratum'] = aud
    rep['audit_by_rule_now'] = {r: acc(g, 'dv_rule') for r, g in S[S.kind != 'ml'].groupby('rule_id_now')}

    def wacc(g, col):
        a = g[g.agree]
        return round(float(np.average(a[col] == a.dv_cons, weights=a.weight)), 4) if len(a) else None

    R = S[S.kind == 'rule']
    rep['audit_weighted'] = {
        'textile_rules_all': wacc(R, 'dv_rule'),
        'textile_rules_all_at_sampling': wacc(R, 'dv_rule_sampled'),
        'textile_rules_excl_constituent': wacc(R[R.rule_id_now != 'T_CONSTITUENT'], 'dv_rule'),
        'textile_rules_excl_constituent_at_sampling': wacc(R[R.stratum != 'rule:T_CONSTITUENT'], 'dv_rule_sampled'),
        'ml_keep1': wacc(S[S.stratum == 'ml:keep1'], 'dv_auto'),
        'ml_turn0': wacc(S[S.stratum == 'ml:turn0'], 'dv_auto'),
    }
    rep['audit_flags'] = [f'{b}: accuracy {v} < {BAND_THRESHOLD}; narrow the band' for b, v in
                          [('ml_keep1', rep['audit_weighted']['ml_keep1']),
                           ('ml_turn0', rep['audit_weighted']['ml_turn0'])] if v is not None and v < BAND_THRESHOLD]

    # ---- 5. ML-rule conflicts
    cf = df.queue == 'ml_rule_conflict'
    C = df[cf].copy()
    T = load_texts()
    A = attributes([k for k in T if len(k) == 6 and k.isdigit()], T)
    rr = [code_pair(a, b, A) for a, b in zip(C.input_hs6, C.output_hs6)]
    C['r_route'] = [x[2] for x in rr]
    C['r_step'] = [x[3] for x in rr]
    SC = S[(S.queue_now == 'ml_rule_conflict') & S.agree]            # sampled pairs that are conflicts now
    win = {}
    for k in sorted(set(zip(C.rule_id, C.band))):
        g = SC[(SC.rule_id_now == k[0]) & (SC.band == k[1])]
        lvl = 'rule_id x band'
        if len(g) < MIN_CONFLICT_N:
            g, lvl = SC[SC.rule_id_now == k[0]], 'rule_id'
        if len(g) < MIN_CONFLICT_N:
            win[k] = ('none', None, None, len(g), lvl)
            continue
        ar, am = (g.dv_rule == g.dv_cons).mean(), (g.dv_ml == g.dv_cons).mean()
        side, a = ('rule', ar) if ar >= am else ('ml', am)
        win[k] = (side if a >= MIN_WIN_ACC else 'none', round(float(ar), 4), round(float(am), 4), len(g), lvl)
    rep['conflicts'] = {f'{k[0]}|{k[1]}': {'pairs': int(((C.rule_id == k[0]) & (C.band == k[1])).sum()),
                                           'winner': v[0], 'acc_rule': v[1], 'acc_ml': v[2], 'n_agreed': v[3],
                                           'level': v[4]} for k, v in win.items()}
    side = pd.Series([win[(a, b)][0] for a, b in zip(C.rule_id, C.band)], index=C.index)
    rdv = C.rule_dv.astype(int)
    mdv = ml_dv(C.band).astype(int)
    C['DV'] = np.where(side == 'rule', rdv, np.where(side == 'ml', mdv, 1))
    C['uncertain'] = (side == 'none').astype(int)
    ml_route = 'ml_' + C.ml_class.str.lower()
    C['route'] = np.select([side == 'rule', C.DV == 0, rdv == 1], [C.r_route, 'none', C.r_route], ml_route)
    C['step'] = np.where((side == 'rule') & (C.DV == 0), pd.to_numeric(C.r_step, errors='coerce'), np.nan)
    C['DV_max'] = np.where((C.DV == 1) | (C.route == 'recycle_direct'), 1, 0)
    C['source'] = np.where(side == 'none', 'conflict_unresolved', 'conflict_' + side)

    # ---- assemble the master list
    F = df.copy()
    for c in ['DV', 'DV_max', 'uncertain', 'DV_strict', 'locked']:
        F[c] = pd.to_numeric(F[c], errors='coerce')
    F['step'] = pd.to_numeric(F.step, errors='coerce')
    ml = F.source == 'ml'
    F.loc[ml, 'DV_max'] = F.loc[ml, 'DV']
    F.loc[ml, 'uncertain'] = 0
    F.loc[ml, 'locked'] = 0
    Ui = U.set_index('master_id')
    um = F.master_id.isin(Ui.index)
    F['dv_auto'] = np.nan
    rr = F.master_id.isin(mem.master_id[mem.queue == 'ml_reroute'])     # 7d: ML-band pairs sent to the coders
    F.loc[rr, 'dv_auto'] = F.loc[rr, 'DV']
    for c in ['DV', 'uncertain', 'route', 'step', 'DV_max', 'source']:
        F.loc[um, c] = F.loc[um, 'master_id'].map(Ui[c]).values
    F.loc[um, 'locked'] = 0
    for c in ['dv', 'route', 'step', 'reason', 'scope']:
        for s in ('ai1', 'ai2'):
            F[f'{c}_{s}'] = F.master_id.map(Ui[f'{c}_{s}']).fillna('')
    F['unit_id'] = F.master_id.map(Ui.unit_id).fillna('')
    for c in ['DV', 'uncertain', 'route', 'step', 'DV_max', 'source']:
        F.loc[cf, c] = C[c].values
    F.loc[cf, 'locked'] = 0
    F.loc[rr & um, 'source'] = np.where(F.loc[rr & um, 'source'] == 'ai_units', 'ai_units_ml_reroute',
                                        F.loc[rr & um, 'source'])
    # sampled pairs: two-coder result replaces the automatic value
    Sb = S[sb].set_index('master_id')
    sm = F.master_id.isin(Sb.index)
    F.loc[sm, 'dv_auto'] = F.loc[sm, 'DV']
    F.loc[sm & cf, 'dv_auto'] = np.nan                       # conflicts had two automatic values
    for c in ['dv', 'route', 'step', 'reason']:
        for s in ('ai1', 'ai2'):
            F.loc[sm, f'{c}_{s}'] = F.loc[sm, 'master_id'].map(Sb[f'{c}_{s}']).values
    dv, unc, route, step, dvmax = combine(Sb.dv_ai1, Sb.dv_ai2, Sb.route_ai1.values, Sb.route_ai2.values,
                                          Sb.step_ai1, Sb.step_ai2)
    sres = pd.DataFrame({'DV': dv, 'uncertain': unc, 'route': route, 'step': step, 'DV_max': dvmax},
                        index=Sb.index)
    for c in sres:
        F.loc[sm, c] = F.loc[sm, 'master_id'].map(sres[c]).values
    F.loc[sm, 'source'] = 'ai_sample'
    F.loc[sm, 'locked'] = F.loc[sm, 'route'].eq('same_good').astype(int)
    F['DV_strict'] = F.DV * (1 - F.uncertain)
    F['ml_prob'] = pd.to_numeric(F.p_ens, errors='coerce').round(4)
    F['ml_supported'] = (pd.to_numeric(F.cp_n_pta1, errors='coerce') > 30).astype(int)
    h2 = {k for k in T if len(k) == 6 and k.isdigit()}
    F['concord_flag'] = (~F.input_hs6.isin(h2) | ~F.output_hs6.isin(h2)).astype(int)
    left = F.DV.isna()
    if left.any():
        sys.exit(f'{int(left.sum())} pairs still without DV, e.g. {F.master_id[left].head().tolist()}')
    for c in ['DV', 'DV_max', 'uncertain', 'DV_strict', 'locked']:
        F[c] = F[c].astype(int)
    F['step'] = pd.to_numeric(F.step, errors='coerce').astype('Int64')
    bad = (F.DV == 0) & F.step.isna() & ~F.source.isin(['ml', 'conflict_ml'])
    rep['dv0_without_step'] = int(bad.sum())
    R7 = F[F.dv_auto.notna() & F.source.str.startswith('ai_units')]
    if len(R7):
        agr = R7[R7.dv_ai1 == R7.dv_ai2]
        rep['ml_reroute_audit'] = {
            'pairs': len(R7), 'coders_agree': len(agr),
            'ml_acc_vs_agreed': round(float((agr.dv_auto == agr.dv_ai1.astype(int)).mean()), 4) if len(agr) else None,
            'by_band': {('keep1' if b == 1 else 'turn0'): {
                'pairs': int((R7.dv_auto == b).sum()),
                'acc_vs_agreed': round(float((g.dv_auto == g.dv_ai1.astype(int)).mean()), 4) if len(g) else None,
                'acc_vs_combined': round(float((R7[R7.dv_auto == b].DV == b).mean()), 4)}
                for b in (1, 0) for g in [agr[agr.dv_auto == b]]}}

    cols = ['master_id', 'input_hs6', 'output_hs6', 'ptas', 'n_ptas', 'DV', 'DV_max', 'uncertain', 'DV_strict',
            'locked', 'step', 'route', 'source', 'ml_prob', 'ml_supported', 'concord_flag', 'rule_id', 'dv_auto',
            'relation_class', 'pta1_pair_id', 'unit_id',
            'dv_ai1', 'route_ai1', 'step_ai1', 'scope_ai1', 'reason_ai1',
            'dv_ai2', 'route_ai2', 'step_ai2', 'scope_ai2', 'reason_ai2']
    F = F[cols]
    F.to_csv(out / 'master_coded_final.csv', index=False)
    rep['master'] = {'pairs': len(F), 'source': F.source.value_counts().to_dict(),
                     'DV1': int(F.DV.sum()), 'DV_strict1': int(F.DV_strict.sum()), 'DV_max1': int(F.DV_max.sum()),
                     'uncertain': int(F.uncertain.sum()), 'concord_flag': int(F.concord_flag.sum())}

    # ---- per-PTA files
    date = datetime.date.today().strftime('%Y_%m_%d')
    rep['pta'] = {}
    keep = ['DV', 'DV_max', 'uncertain', 'DV_strict', 'locked', 'step', 'route', 'source', 'ml_prob',
            'ml_supported', 'concord_flag', 'dv_ai1', 'dv_ai2', 'master_id']
    Fi = F.set_index(['input_hs6', 'output_hs6'])[keep]
    for p in PTAS:
        R0 = pd.read_csv(INTAKE / f'pairs_{p}.csv', dtype={'input_hs6': str, 'output_hs6': str})
        P = R0.join(Fi, on=['input_hs6', 'output_hs6'])
        assert P.DV.notna().all(), p
        P.to_csv(out / f'{p}_coded_{date}.csv', index=False)
        Pd = P.copy()
        Pd['step'] = Pd.step.astype('float')
        for c in ['dv_ai1', 'dv_ai2']:
            Pd[c] = pd.to_numeric(Pd[c], errors='coerce')
        Pd.to_stata(out / f'{p}_coded_{date}.dta', write_index=False, version=118,
                    variable_labels={'DV': 'input-output link (workflow steps 2-6)',
                                     'DV_max': 'DV with recycle_direct = 1', 'uncertain': 'AI coders disagree or '
                                     'policy-uncertain', 'DV_strict': 'DV x (1 - uncertain)',
                                     'locked': 'same good (step 2)', 'ml_prob': 'ML ensemble probability',
                                     'concord_flag': 'code not in HS2002'})
        rep['pta'][p] = {'records': len(P), 'DV1': int(P.DV.sum()), 'DV1_share': round(float(P.DV.mean()), 4),
                         'DV_strict1_share': round(float(P.DV_strict.mean()), 4),
                         'uncertain_share': round(float(P.uncertain.mean()), 4),
                         'source': P.source.value_counts().to_dict()}
    S.to_csv(out / 'sample_audit.csv', index=False)
    json.dump(rep, open(out / 'combine_report.json', 'w'), indent=1, default=str)
    print(json.dumps({k: rep[k] for k in ['units', 'sample', 'audit_weighted', 'audit_flags', 'master']}, indent=1,
                     default=str))


if __name__ == '__main__':
    main()
