"""Independent AI audit of the final PTA 6-10 codes (workflow, "Reliability": a stratified sample of about 300 pairs,
coded blind by two new AI sessions; August reviews every pair where they disagree with the final code).

build:   draws about 300 pairs after 09_apply_policy.py, stratified by how the final code was reached: AI units (by
         input section), textile rules (by rule), TUR_SGP HS2012 concordance pairs, and exact copies (from PTA 2-5 and
         from ASEAN-Japan). Pairs of the AI pair sample (coded pair by pair already), self-pairs and the 295 pairs of
         the PTA 2-5 audit are excluded. Writes audit/audit_pairs.csv (blind: descriptions only) and
         _work/coded/audit_key.csv (stratum, pair weight = stratum pairs / sample size, record weight = stratum
         records / sample size).
enrich:  gives every bare "Other" subheading in audit/audit_pairs.csv its context, as 05c does for the coder inputs v2
         (descriptions only; ids, rows and order unchanged). Run after build.
check:   format check of an auditor file (see AI_Audit_Prompt.md).
compare: auditors vs the final DV and vs each other, weighted by pairs, by records and by the records
         of each agreement, with 95% intervals; writes audit/audit_review.xlsx with the disagreements first for
         August's review and final/ai_audit_report.json. An existing audit_review.xlsx is backed up first and August's
         marks are carried over by audit_id when the row still holds the same pair.
score:   reads August's marks (August_dv: the true value 1 / 0, or unsure) and adds the reviewed accuracy of DV to
         final/ai_audit_report.json, with bounds for unsure or unmarked items. Re-run compare first
         whenever 09 has been re-run (score warns when the final codes of the sample changed).

What is measured. An item is correct when the final value equals the true value of the pair (the auditors' common
answer where they agree with the final DV, August's mark otherwise). DV_strict is no longer computed or scored
(Prof. Zhang, 2026-11-01: DV is the main variable).
DV_excl_remelt differs from DV only on recycle_direct pairs, by definition; compare reports those items instead.

Weights. Pairs: each stratum counts its pairs in the frame. Records: each record with an HS6 input counts once,
split equally over the HS2002 pairs it maps to (TUR_SGP records coded on their HS2012 pair count for that pair);
own self-records (locked at 1) and WO / any records are outside the frame. A record whose pairs differ counts as the
average of its pairs, an approximation of its code (the maximum). Within a stratum, record-weighted shares weight
each sampled pair by its records. Each agreement gets two figures: records_<PTA> applies the stratum shares of all
agreements to that agreement's records (assumes a stratum is as accurate in every agreement); records_<PTA>_own_pairs
uses only the sampled pairs that occur in the agreement (design-based, wider, and it drops strata with no such pair).
The weight_records column of audit_key.csv (build time) is superseded by these weights.

Intervals. 95% Wilson interval with an effective sample size: the variance sums the strata's variances, each from
the Jeffreys-smoothed share (x + 0.5) / (n + 1) (n = effective number of items), so a stratum where every item agrees
still carries uncertainty; the effective sample size is p(1 - p) / variance. The interval always contains the
estimate; in simulations on this sample it covered the true value in 94-99% of cases.

Run: /usr/local/bin/python3 _work/07_audit.py build | enrich | check <file> | compare <file> <file> | score
"""
import csv
import datetime
import hashlib
import importlib.util
import json
import shutil
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import BASE, CODED, FINAL, INTAKE, P25, PTAS, REF  # noqa: E402
from textile import load_texts  # noqa: E402

OUT = BASE / 'audit'
SEED = 20261026
ALLOC = {'ai_units': 178, 'rule_textile': 40, 'ai_concord': 30, 'exact_copy': 62}
GROUPS = [(1, 5, '01-05 animal'), (6, 15, '06-15 plant/fats'), (16, 24, '16-24 food'), (25, 27, '25-27 mineral'),
          (28, 38, '28-38 chemical'), (39, 40, '39-40 plastic/rubber'), (41, 49, '41-49 leather/wood/paper'),
          (50, 67, '50-67 textile/footwear'), (68, 71, '68-71 stone/glass/jewel'), (72, 83, '72-83 metals'),
          (84, 85, '84-85 machinery'), (86, 97, '86-97 transport/other')]
ROUTES1 = {'same_good', 'forward', 'ingredient', 'component', 'reconstitute', 'mixture', 'recycle_waste',
           'recycle_direct', 'feed', 'sibling_intermediate'}
MARKS = ['August_dv', 'August_note']
# textile rule ids added after the sample was drawn (chapter-59 corrections B3 of 10-29, worn clothing and rags of
# 10-30): their pairs keep the
# stratum they had at build time, so the post-stratified estimates still use the design's strata
BUILD_STRATUM = {'T_CH59_SIBLING': 'T_BACKWARD', 'T_COATED_TO_BELTING': 'T_BACKWARD',
                 'T_CH59_NOT_INPUT': 'T_INTERMEDIATE_SIBLING',
                 'T_WORN_FROM_INPUT': 'T_WORN_NOT_FROM', 'T_RAGS_FROM_FIBRE': 'T_RAGS_NOT_FROM_FIBRE'}   # 5(a), 10-30
VARIANTS = ['DV']                                        # DV only (Prof. Zhang, 2026-11-01)
Z95 = 1.959964
REVIEW = OUT / 'audit_review.xlsx'
REPORT = FINAL / 'ai_audit_report.json'


def group(ch):
    return next((g for a, b, g in GROUPS if a <= ch <= b), 'other')


def sqrt_alloc(sizes, total, floor):
    s = pd.Series(sizes, dtype=float)
    a = np.maximum(floor, np.floor(total * np.sqrt(s) / np.sqrt(s).sum())).astype(int)
    a = np.minimum(a, s.astype(int))
    while a.sum() > total:
        a[a.idxmax()] -= 1
    return a


def final_codes():
    """final pair codes (HS2002 master and HS2012 concordance pairs), indexed by master_id, with record counts"""
    F = pd.read_csv(FINAL / 'master_coded_final.csv', dtype=str, keep_default_na=False)
    n = pd.read_csv(INTAKE / 'master_pairs.csv', dtype=str).set_index('master_id').n_records.astype(int)
    F['n_records'] = F.master_id.map(n)
    F['hs_vintage'] = 'HS2002'
    C = pd.read_csv(FINAL / 'concord_coded_final.csv', dtype=str, keep_default_na=False)
    C['n_records'] = C.n_records.astype(int)
    C['hs_vintage'] = 'HS2012'
    cols = ['master_id', 'input_hs6', 'output_hs6', 'hs_vintage', 'DV', 'uncertain', 'uncertain_reason',
            'route', 'source', 'copy_from', 'rule_id', 'n_records']
    C['copy_from'], C['rule_id'] = '', ''
    return pd.concat([F[cols], C[cols]], ignore_index=True).set_index('master_id')


def frame():
    """the pairs the sample is drawn from, with their stratum (self-pairs, the AI pair sample and the pairs of the
    PTA 2-5 audit are left out)"""
    F = final_codes().reset_index()
    old = set(pd.read_csv(P25 / '_work/coded/human_audit_key.csv', dtype=str).master_id)
    F = F[(F.input_hs6 != F.output_hs6) & ~F.master_id.isin(old) & (F.source != 'ai_sample')].copy()
    F['stratum'] = ''
    F.loc[F.source == 'ai_units', 'stratum'] = 'ai_units:' + F.input_hs6.str[:2].astype(int).map(group)
    F.loc[F.source == 'rule_textile', 'stratum'] = 'rule_textile:' + F.rule_id.replace(BUILD_STRATUM)
    F.loc[F.source == 'ai_concord', 'stratum'] = 'ai_concord'
    F.loc[F.source == 'exact_copy', 'stratum'] = 'exact_copy:' + F.copy_from
    return F[F.stratum != ''].reset_index(drop=True)


def record_weights(F):
    """records behind each frame pair by agreement (see Weights above), as a master_id x agreement table; also each
    agreement's records with an HS6 input"""
    C = pd.read_csv(FINAL / 'concord_coded_final.csv', dtype=str, usecols=['master_id', 'record_nos'])
    conc = C.assign(record_no=C.record_nos.str.split(';')).explode('record_no')
    conc['record_no'] = conc.record_no.astype(int)
    rp = pd.read_csv(INTAKE / 'record_pairs.csv', dtype=str)
    rp['record_no'] = rp.record_no.astype(int)
    rp['master_id'] = 'M|' + rp.input_hs6 + '>' + rp.output_hs6
    rows, total = [], {}
    for p in PTAS:
        R0 = pd.read_csv(INTAKE / f'records_{p}.csv', dtype=str,
                         usecols=['record_no', 'input_type', 'input_hs6', 'output_hs6'])
        R0['record_no'] = R0.record_no.astype(int)
        hs = R0[R0.input_type == 'hs6']
        total[p] = len(hs)
        keep = set(hs.record_no[hs.input_hs6 != hs.output_hs6])
        cc = conc[conc.record_no.isin(keep)] if p == 'TUR_SGP' else conc.iloc[:0]
        x = rp[(rp.pta == p) & rp.record_no.isin(keep - set(cc.record_no))]
        x = x.assign(w=1 / x.groupby('record_no').record_no.transform('size'))
        rows.append(pd.concat([x[['master_id', 'w']], cc[['master_id']].assign(w=1.0)]).assign(pta=p))
    W = pd.concat(rows, ignore_index=True)
    W = W[W.master_id.isin(set(F.master_id))]
    P = W.pivot_table(index='master_id', columns='pta', values='w', aggfunc='sum', fill_value=0)
    return P.reindex(columns=PTAS, fill_value=0), pd.Series(total)


def weights(key):
    """for each weighting: stratum totals and the weight of each pair within its stratum (None = equal); also the
    share of each agreement's HS6 records in the frame and the sampled pairs that occur in each agreement"""
    F = frame()
    N = F.stratum.value_counts()
    k = key.groupby('stratum')
    assert (N.reindex(k.size().index) == (k.weight.first().astype(float) * k.size()).round()).all(), \
        'the frame differs from the one the sample was drawn from'
    P, total = record_weights(F)
    st = F.set_index('master_id').stratum
    L = P.groupby(P.index.map(st)).sum()
    r_all = P.sum(axis=1)
    W = {'pair_weighted': (N, None), 'record_weighted': (L.sum(axis=1), r_all)}
    for p in PTAS:
        W[f'records_{p}'] = (L[p], r_all)
        W[f'records_{p}_own_pairs'] = (L[p], P[p])
    info = {'frame_share_of_hs6_records': {p: round(float(L[p].sum() / total[p]), 4) for p in PTAS},
            'sampled_pairs_in_agreement': {p: int((key.master_id.map(P[p]).fillna(0) > 0).sum()) for p in PTAS}}
    return W, info


def estimate(ok, items, W, by_pta=True):
    """post-stratified share of ok items (1 / 0; NaN items do not count) with a 95% interval for each weighting (see
    Weights and Intervals above). Strata with no counted item of positive weight are dropped; `weight_covered` gives
    the share of the weight that remains."""
    x = pd.DataFrame({'stratum': items.stratum.to_numpy(), 'master_id': items.master_id.to_numpy(),
                      'ok': np.asarray(ok, float)}).dropna(subset=['ok'])
    if x.empty:
        return None
    out = {'items': len(x)}
    for k, (T, r) in W.items():
        if not by_pta and k.startswith('records_'):
            continue
        w = np.ones(len(x)) if r is None else x.master_id.map(r).fillna(0).to_numpy(float)
        g = pd.DataFrame({'s': x.stratum, 'w': w, 'wo': w * x.ok, 'w2': w ** 2}).groupby('s').sum()
        g = g[g.w > 0]
        t = T.reindex(g.index).fillna(0).to_numpy(float)
        if t.sum() == 0:
            continue
        share, neff, f = (g.wo / g.w).to_numpy(), (g.w ** 2 / g.w2).to_numpy(), t / t.sum()
        est = float(share @ f)
        sm = (neff * share + 0.5) / (neff + 1)
        pbar = float(sm @ f)
        n = pbar * (1 - pbar) / float((f ** 2 * sm * (1 - sm) / neff).sum())
        c = (est + Z95 ** 2 / (2 * n)) / (1 + Z95 ** 2 / n)
        h = Z95 / (1 + Z95 ** 2 / n) * np.sqrt(est * (1 - est) / n + Z95 ** 2 / (4 * n * n))
        out[k] = {'est': round(est, 4), 'ci95': [round(float(c - h), 4), round(float(c + h), 4)]}
        if t.sum() < float(T.sum()) - 1e-9:
            out[k]['weight_covered'] = round(float(t.sum() / T.sum()), 4)
    return out


def fingerprint(master_ids, F):
    """short hash of the final DV and uncertain of the sampled pairs"""
    s = ';'.join(f'{m}:{F.DV[m]}:{F.uncertain[m]}' for m in sorted(master_ids))
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def read_mark(v):
    t = unicodedata.normalize('NFKC', str(v)).strip().lower()
    return {'1': 1.0, '1.0': 1.0, '0': 0.0, '0.0': 0.0, '': np.nan, 'unsure': np.nan}.get(t, 'bad')


def build():
    rng = np.random.default_rng(SEED)
    F = frame()
    picks = []
    for fam, n in ALLOC.items():
        sub = F[F.stratum.str.startswith(fam)]
        sizes = sub.stratum.value_counts()
        floor = 3 if fam in ('ai_units', 'rule_textile') else 10
        alloc = sqrt_alloc(sizes, n, floor) if len(sizes) > 1 else pd.Series({sizes.index[0]: min(n, sizes.iloc[0])})
        for s, k in alloc.items():
            g = sub[sub.stratum == s]
            take = g.iloc[rng.choice(len(g), size=int(k), replace=False)].copy()
            take['weight'] = len(g) / int(k)
            take['weight_records'] = g.n_records.sum() / int(k)
            picks.append(take)
    P = pd.concat(picks).sample(frac=1, random_state=SEED).reset_index(drop=True)
    P['audit_id'] = [f'A{i + 1:03d}' for i in range(len(P))]
    T = load_texts()
    H4 = {x['id']: x['text'] for x in json.load(open(REF / 'H4.json'))['results']}
    clean = lambda t: t.split(' - ', 1)[-1].lstrip('- ').strip() if ' - ' in t else t  # noqa: E731

    def desc(c, v):
        if v == 'HS2012':
            return f'{clean(H4.get(c[:4], ""))} | {clean(H4.get(c, ""))}'
        return f'{T.get(c[:4], "")} | {T.get(c, "")}'

    OUT.mkdir(exist_ok=True)
    blind = pd.DataFrame({'audit_id': P.audit_id, 'hs_vintage': P.hs_vintage, 'input_hs6': P.input_hs6,
                          'input_description': [desc(c, v) for c, v in zip(P.input_hs6, P.hs_vintage)],
                          'output_hs6': P.output_hs6,
                          'output_description': [desc(c, v) for c, v in zip(P.output_hs6, P.hs_vintage)]})
    blind.to_csv(OUT / 'audit_pairs.csv', index=False)
    P[['audit_id', 'master_id', 'stratum', 'weight', 'weight_records']].to_csv(CODED / 'audit_key.csv', index=False)
    print(P.stratum.str.split(':').str[0].value_counts().to_dict(), len(P))


def enrich():
    spec = importlib.util.spec_from_file_location('enrich05c', Path(__file__).with_name('05c_enrich_other_texts.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ctx = {'HS2002': m.Context('H2'), 'HS2012': m.Context('H4')}
    p = pd.read_csv(OUT / 'audit_pairs.csv', dtype=str, keep_default_na=False)
    before = p.copy()
    for side in ('input', 'output'):
        p[f'{side}_description'] = [m.pair_desc(x, c, ctx[v]) for x, c, v in
                                    zip(p[f'{side}_description'], p[f'{side}_hs6'], p.hs_vintage)]
    assert p.shape == before.shape and (p.audit_id == before.audit_id).all()
    p.to_csv(OUT / 'audit_pairs.csv', index=False)
    print(f'rows with an enriched "Other": {int((p != before).any(axis=1).sum())}')


def check(path):
    """format check of an auditor file (audit_id,dv,route,step,reason; one row per item, input order)"""
    path = Path(path) if Path(path).is_absolute() else BASE / path
    rows = list(csv.reader(open(path, newline='', encoding='utf-8')))
    err = []
    if rows[0] != ['audit_id', 'dv', 'route', 'step', 'reason']:
        err.append(f'header {rows[0]}')
    bad = [k + 1 for k, r in enumerate(rows) if r and len(r) != 5]
    if bad:
        err.append(f'{len(bad)} line(s) with a wrong number of fields (unquoted comma?), e.g. {bad[:10]}')
    if not err:
        a = pd.read_csv(path, dtype=str, keep_default_na=False)
        ids = pd.read_csv(OUT / 'audit_pairs.csv', dtype=str).audit_id
        if len(a) != len(ids) or (a.audit_id.values != ids.values).any():
            err.append(f'items differ from the input (rows {len(a)} vs {len(ids)}, or order)')
        for i, r in a.iterrows():
            b = []
            if r.dv not in ('0', '1'):
                b.append('dv')
            elif r.dv == '1' and r.route not in ROUTES1:
                b.append('route for dv 1')
            elif r.dv == '0' and r.route != 'none':
                b.append('route for dv 0 must be none')
            if r.route == 'same_good' and r.step != '2':
                b.append('same_good needs step 2')
            if r.dv == '0' and r.step not in ('3', '4', '5', '6'):
                b.append('dv 0 needs step 3-6')
            if r.dv == '1' and r.route != 'same_good' and r.step != '':
                b.append('step must be empty')
            if len(r.reason.strip()) < 15:
                b.append('reason too short')
            if b:
                err.append(f'row {i + 2} {r.audit_id}: {", ".join(b)}')
    print(f'{path.name}: {"OK" if not err else f"{len(err)} problem(s)"}')
    for e in err[:25]:
        print('   ', e)
    sys.exit(0 if not err else 1)


def kappa(a, b):
    a, b = np.asarray(a, int), np.asarray(b, int)
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return round(float((po - pe) / (1 - pe)), 4) if pe < 1 else 1.0


def wavg(ok, w):
    return round(float(np.average(ok, weights=w)), 4) if len(ok) else None


def compare(paths):
    key = pd.read_csv(CODED / 'audit_key.csv', dtype=str)
    pairs = pd.read_csv(OUT / 'audit_pairs.csv', dtype=str, keep_default_na=False)
    F = final_codes()
    d = key.merge(pairs, on='audit_id')
    d['weight'] = d.weight.astype(float)
    d['family'] = d.stratum.str.split(':').str[0]
    for c in VARIANTS + ['route', 'source', 'uncertain', 'uncertain_reason']:
        d[f'final_{c}'] = d.master_id.map(F[c])
    for v in VARIANTS:
        d[f'final_{v}'] = d[f'final_{v}'].astype(int)
    W, info = weights(key)
    names = []
    for path in paths:
        path = Path(path) if Path(path).is_absolute() else BASE / path
        nm = path.stem.replace('audit_', '')
        a = pd.read_csv(path, dtype=str, keep_default_na=False).set_index('audit_id')
        d[f'{nm}_dv'] = d.audit_id.map(a.dv).astype(int)
        d[f'{nm}_route'] = d.audit_id.map(a.route)
        d[f'{nm}_reason'] = d.audit_id.map(a.reason)
        names.append(nm)
    assert len(set(names)) == len(names), f'two auditor files with the same name: {names}'
    rep = {'run': datetime.datetime.now().isoformat(timespec='seconds'), 'auditors': names, 'items': len(d),
           'final_fingerprint': fingerprint(d.master_id, F), **info}
    for nm in names:
        ok = d[f'{nm}_dv'] == d.final_DV
        rep[nm] = {'agree_with_final': {v: estimate(d[f'{nm}_dv'] == d[f'final_{v}'], d, W, by_pta=False)
                                        for v in VARIANTS},
                   'agree_with_final_unweighted': round(float(ok.mean()), 4),
                   'auditor1_final0': int(((d[f'{nm}_dv'] == 1) & (d.final_DV == 0)).sum()),
                   'auditor0_final1': int(((d[f'{nm}_dv'] == 0) & (d.final_DV == 1)).sum()),
                   'by_family': {k: {'n': len(g), 'agree': wavg(g[f'{nm}_dv'] == g.final_DV, g.weight)}
                                 for k, g in d.groupby('family')}}
    av = d[[f'{nm}_dv' for nm in names]]
    same = av.nunique(axis=1) == 1
    cons = av.iloc[:, 0]
    if len(names) > 1:
        rep['between_auditors'] = {'agree_unweighted': round(float(same.mean()), 4),
                                   'kappa_unweighted': kappa(av.iloc[:, 0], av.iloc[:, 1]),
                                   'agree_weighted': estimate(same, d, W, by_pta=False)}
        rep['final_vs_auditor_consensus'] = {
            'items_where_auditors_agree': int(same.sum()),
            **{v: estimate((cons == d[f'final_{v}']).where(same), d, W) for v in VARIANTS},
            'by_family_DV': {k: {'n': int(m.sum()), 'agree': wavg((cons == d.final_DV)[m], d.weight[m])}
                          for k in sorted(d.family.unique()) for m in [same & (d.family == k)] if m.any()}}
    rd = d.final_route == 'recycle_direct'           # the only pairs where DV_excl_remelt differs from DV
    rep['recycle_direct_items'] = {'n': int(rd.sum()), **{f'{nm}_dv1': int((d[f'{nm}_dv'][rd] == 1).sum())
                                                          for nm in names},
                                   **{f'{nm}_route_recycle_direct': int((d[f'{nm}_route'][rd] == 'recycle_direct').sum())
                                      for nm in names}}
    allok = same & (cons == d.final_DV)
    d['status'] = np.where(allok, '3 all agree',
                           np.where(same, '1 auditors agree, final differs', '2 auditors disagree'))
    rep['review_counts'] = d.status.value_counts().sort_index().to_dict()
    d = d.sort_values(['status', 'family', 'audit_id'])
    out = REVIEW
    d['August_dv'], d['August_note'] = '', ''
    if out.exists():                                   # never lose August's marks
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.copy(out, out.with_name(f'audit_review_backup_{stamp}.xlsx'))
        old = pd.read_excel(out, dtype=str).fillna('').set_index('audit_id')
        pair = lambda t: t.hs_vintage + '|' + t.input_hs6 + '>' + t.output_hs6  # noqa: E731
        same_pair = d.audit_id.map(pair(old)) == pair(d)    # a mark stays only on the pair it was made for
        for c in MARKS:
            if c in old:
                d[c] = d.audit_id.map(old[c]).where(same_pair).fillna('')
        lost = (~same_pair & d.audit_id.map(old.August_dv if 'August_dv' in old else pd.Series(dtype=str))
                .fillna('').ne(''))
        if lost.any():
            print(f'WARNING: {int(lost.sum())} mark(s) not carried over (row holds another pair): '
                  f'{sorted(d.audit_id[lost])}')
    cols = (['status', 'audit_id', 'family', 'hs_vintage', 'input_hs6', 'input_description', 'output_hs6',
             'output_description', 'final_DV', 'final_route', 'final_source', 'final_uncertain']
            + [f'{nm}_{c}' for nm in names for c in ('dv', 'route', 'reason')] + MARKS)
    d[cols].to_excel(out, index=False)
    try:
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.worksheet.datavalidation import DataValidation
        wb = openpyxl.load_workbook(out)
        ws = wb.active
        ws.freeze_panes = 'E2'
        for i, w in enumerate([24, 8, 11, 8, 9, 40, 9, 40, 8, 18, 14, 8] + [7, 16, 40] * len(names) + [10, 30], 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
        fills = {'1': 'F8D7DA', '2': 'FFF3CD', '3': 'FFFFFF'}
        for row in ws.iter_rows(min_row=2):
            f = PatternFill('solid', fgColor=fills[str(row[0].value)[0]])
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical='top')
                c.fill = f
        for c in ws[1]:
            c.font = Font(bold=True)
        dv = DataValidation(type='list', formula1='"1,0,unsure"', allow_blank=True, showErrorMessage=True,
                            errorTitle='August_dv', error='Enter 1, 0 or unsure')
        ws.add_data_validation(dv)
        col = openpyxl.utils.get_column_letter(len(cols) - 1)
        dv.add(f'{col}2:{col}{ws.max_row}')
        wb.save(out)
    except ImportError:
        pass
    json.dump(rep, open(REPORT, 'w'), indent=1)
    print(json.dumps(rep, indent=1))


def score():
    """accuracy after August's review. The true value of an item is August's mark where he gave one (August_dv 1 or
    0) and otherwise the final DV where both auditors agree with it (status 3); review items left unsure or unmarked
    have no true value. The point estimate leaves them out; lower and upper count them as wrong and as right."""
    r = pd.read_excel(REVIEW, dtype=str).fillna('')
    key = pd.read_csv(CODED / 'audit_key.csv', dtype=str)
    r = r.merge(key[['audit_id', 'master_id', 'stratum']], on='audit_id')
    F = final_codes()
    W, _ = weights(key)
    rep = json.load(open(REPORT))
    stale = fingerprint(r.master_id, F) != rep.get('final_fingerprint')
    if stale:
        print('WARNING: the final codes of the sample changed since compare; re-run compare first')
    mark = r.August_dv.map(read_mark)
    bad = r.audit_id[mark.eq('bad')]
    if len(bad):
        sys.exit(f'August_dv must be 1, 0, unsure or empty; fix: {sorted(bad)}')
    mark = mark.astype(float)
    review = ~r.status.str.startswith('3')
    fdv = r.final_DV.astype(float)
    truth = mark.where(mark.notna(), fdv.where(~review))
    missing = truth.isna()
    if missing.any():
        print(f'WARNING: {int(missing.sum())} review item(s) unsure or unmarked; see lower and upper')
    res = {'complete': not bool(missing.any()), 'stale': bool(stale), 'review_items': int(review.sum()),
           'marked_1': int((review & (mark == 1)).sum()), 'marked_0': int((review & (mark == 0)).sum()),
           'unsure': int((review & r.August_dv.str.strip().str.lower().eq('unsure')).sum()),
           'unmarked': int((review & r.August_dv.str.strip().eq('')).sum()),
           'marked_same_as_final_DV': int((review & (mark == fdv)).sum()),
           'marks_overriding_all_agree': int((~review & mark.notna() & (mark != fdv)).sum())}
    for v in VARIANTS:
        fv = r.master_id.map(F[v]).astype(float)
        ok = (fv == truth).astype(float)
        res[v] = estimate(ok.where(~missing), r, W)
        res[v]['lower'] = estimate(ok.where(~missing, 0.0), r, W)
        res[v]['upper'] = estimate(ok.where(~missing, 1.0), r, W)
        for b in ('lower', 'upper'):                    # keep the bounds short: point estimates only
            res[v][b] = {k: e['est'] for k, e in res[v][b].items() if isinstance(e, dict)}
        res[f'{v}_wrong_by_family'] = r[~missing & (fv != truth)].family.value_counts().to_dict()
    rep['after_August_review'] = res
    json.dump(rep, open(REPORT, 'w'), indent=1)
    print(json.dumps(res, indent=1))

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'check':
        check(sys.argv[2])
    elif cmd == 'compare':
        compare(sys.argv[2:])
    else:
        {'build': build, 'enrich': enrich, 'score': score}[cmd]()
