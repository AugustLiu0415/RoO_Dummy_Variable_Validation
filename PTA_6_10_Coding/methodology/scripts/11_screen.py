"""A1 screen of one-sided 1s (decision of 2026-10-28; rules Coding_Rules_2026_10_30.md, I.9): build, check, combine.

The pool is written by 09_apply_policy.py (_work/coded/screen_pool.csv): pairs of PTA 6-10 coded 1 by one AI coder and 0
by the other that no rule or convention settled. A screener reads the claim of the coder who coded 1 and the answer of
the one who coded 0, and says whether the 1 is clearly invalid. A pair turns 0 only when both model families say so:
Claude screens the whole pool; Codex screens the pairs Claude found invalid (blind to Claude's verdicts).

  build     ai_coders/screen_a1/input/screen_batch_NN.csv (whole pool, units kept together, ~400 pairs per batch)
            and screen_calib.csv (the audit items in the pool; their true values stay in _work/coded/screen_calib_key.csv)
  check     <claude|codex> [stem ...]: every output row present, verdict valid/invalid, step 3-6 for invalid, reason
  codex     ai_coders/screen_a1/input_codex/screen_batch_NN.csv: the pairs Claude found invalid
  combine   _work/coded/screen_final.csv (pairs both families found invalid, read by 09) and screen_report.json
Rescue of the pairs convention 3 set to 0 (_work/coded/rescue_pool.csv, written by 09): is there another specific route?
  rescue_build    ai_coders/screen_a1/input/rescue_batch_NN.csv
  rescue_check    [stem ...]: Claude's output, header item_id,verdict,route,reason (valid needs a route of dv 1)
  rescue_combine  _work/coded/screen_rescue.csv (pairs back to 1 + uncertain, read by 09)

Run: /usr/local/bin/python3 _work/11_screen.py build|check|codex|combine|rescue_build|rescue_check|rescue_combine
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import AI, BASE, CODED  # noqa: E402

DIR = AI / 'screen_a1'
POOL = CODED / 'screen_pool.csv'
BATCH = 400
COLS = ['item_id', 'unit', 'vintage', 'input_hs6', 'input_description', 'output_hs6', 'output_description',
        'claim_route', 'claim_reason', 'counter_reason']
OUT_COLS = ['item_id', 'verdict', 'step', 'reason']
RESCUE_POOL = CODED / 'rescue_pool.csv'
RESCUE_COLS = ['item_id', 'unit', 'vintage', 'input_hs6', 'input_description', 'output_hs6', 'output_description',
               'excluded_because', 'claim_reason', 'counter_reason']
RESCUE_OUT = ['item_id', 'verdict', 'route', 'reason']
ROUTES1 = {'same_good', 'forward', 'ingredient', 'component', 'reconstitute', 'mixture', 'recycle_waste', 'feed',
           'sibling_intermediate'}


def described(P):
    ctx = importlib_05c()
    h2, h4 = ctx.Context('H2'), ctx.Context('H4')
    text = {}
    for ed, c in ((h2, 'HS2002'), (h4, 'HS2012')):
        text[c] = lambda code, e=ed: f"{e.txt.get(code[:4], '')} | {e.describe(code)}".strip(' |')
    P['input_description'] = [text[v](c) for v, c in zip(P.vintage, P.input_hs6)]
    P['output_description'] = [text[v](c) for v, c in zip(P.vintage, P.output_hs6)]
    return P


def importlib_05c():
    import importlib.util
    spec = importlib.util.spec_from_file_location('enrich05c', Path(__file__).with_name('05c_enrich_other_texts.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build():
    P = pd.read_csv(POOL, dtype=str, keep_default_na=False)
    one1 = P.dv_ai1 == '1'
    P['claim_route'] = P.route_ai1.where(one1, P.route_ai2)
    P['claim_reason'] = P.why_ai1.where(one1, P.why_ai2)
    P['counter_reason'] = P.why_ai2.where(one1, P.why_ai1)
    P = described(P).sort_values(['vintage', 'input_hs6', 'output_hs6']).reset_index(drop=True)
    P['unit'] = P.vintage.str[2:] + ':' + P.input_hs6.str[:4] + '>' + P.output_hs6.str[:4]
    P['item_id'] = [f'S{i:05d}' for i in range(1, len(P) + 1)]
    (DIR / 'input').mkdir(parents=True, exist_ok=True)
    batch, size, b = [], 0, 1
    for _, g in P.groupby('unit', sort=False):
        if size and size + len(g) > BATCH:
            pd.concat(batch)[COLS].to_csv(DIR / 'input' / f'screen_batch_{b:02d}.csv', index=False)
            batch, size, b = [], 0, b + 1
        batch.append(g)
        size += len(g)
    pd.concat(batch)[COLS].to_csv(DIR / 'input' / f'screen_batch_{b:02d}.csv', index=False)
    P[['item_id', 'vintage', 'input_hs6', 'output_hs6', 'n_records', 'dv_ai1', 'dv_ai2']].to_csv(
        CODED / 'screen_key.csv', index=False)
    # calibration: the audit items in the pool with a true value (August's mark, or both auditors and the final
    # code agreeing); the screener does not see the truth
    key = pd.read_csv(CODED / 'audit_key.csv', dtype=str)
    r = pd.read_excel(BASE / 'audit/audit_review.xlsx', dtype=str).fillna('').merge(key[['audit_id', 'master_id']],
                                                                                    on='audit_id')
    group = r.August_note.str.startswith('2026-10-28 不确定配对') | r.August_note.str.startswith('2026-10-28 August 判 1')
    r['truth'] = r.August_dv.where(~group & (r.August_dv != ''), r.claude_dv.where(r.status.str.startswith('3'), ''))
    P['master_id'] = P.vintage.map({'HS2002': 'M|', 'HS2012': 'HS2012|'}) + P.input_hs6 + '>' + P.output_hs6
    cal = P.merge(r.loc[r.truth != '', ['master_id', 'audit_id', 'truth']], on='master_id')
    cal[COLS].to_csv(DIR / 'input' / 'screen_calib.csv', index=False)
    cal[['item_id', 'audit_id', 'truth']].to_csv(CODED / 'screen_calib_key.csv', index=False)
    print(f'{len(P)} pairs, {P.unit.nunique()} units, {b} batches; calibration items {len(cal)} '
          f'(true 0: {int((cal.truth == "0").sum())}, true 1: {int((cal.truth == "1").sum())})')


def problems(inp, out):
    bad = []
    if list(out.columns) != OUT_COLS:
        return [f'header {list(out.columns)}']
    if len(out) != len(inp) or (out.item_id.values != inp.item_id.values).any():
        bad.append('item ids differ from the input (one row per input row, same order)')
    for r in out.itertuples():
        if r.verdict not in ('valid', 'invalid'):
            bad.append(f'{r.item_id}: verdict')
        elif r.verdict == 'invalid' and r.step not in ('3', '4', '5', '6'):
            bad.append(f'{r.item_id}: invalid needs step 3, 4, 5 or 6')
        elif r.verdict == 'valid' and r.step != '':
            bad.append(f'{r.item_id}: step must be empty for valid')
        if len(str(r.reason).strip()) < 15:
            bad.append(f'{r.item_id}: reason too short')
    return bad


def check(who, stems):
    src = DIR / ('input' if who == 'claude' else 'input_codex')
    files = [src / f'{s}.csv' for s in stems] if stems else sorted(src.glob('screen_*.csv'))
    ok = True
    for f in files:
        o = DIR / who / f.name
        if not o.exists():
            print(f'{f.stem}: missing')
            ok = False
            continue
        bad = problems(pd.read_csv(f, dtype=str, keep_default_na=False), pd.read_csv(o, dtype=str,
                                                                                    keep_default_na=False))
        print(f'{f.stem}: ' + ('OK' if not bad else f'{len(bad)} problems: ' + '; '.join(bad[:8])))
        ok &= not bad
    return ok


def verdicts(who):
    rows = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in sorted((DIR / who).glob('screen_batch_*.csv'))]
    return pd.concat(rows).set_index('item_id') if rows else pd.DataFrame(columns=OUT_COLS[1:])


def codex_inputs():
    """Codex inputs for every batch Claude has finished (complete output); rerun to add batches as they finish"""
    C = verdicts('claude')
    inv = set(C.index[C.verdict == 'invalid'])
    (DIR / 'input_codex').mkdir(exist_ok=True)
    n, waiting = 0, []
    for f in sorted((DIR / 'input').glob('screen_batch_*.csv')):
        d = pd.read_csv(f, dtype=str, keep_default_na=False)
        o = DIR / 'claude' / f.name
        if not o.exists() or len(pd.read_csv(o, dtype=str)) != len(d):
            waiting.append(f.stem)
            continue
        d = d[d.item_id.isin(inv)]
        if len(d) and not (DIR / 'input_codex' / f.name).exists():
            d.to_csv(DIR / 'input_codex' / f.name, index=False)
            n += len(d)
    print(f'{n} pairs Claude found invalid written to {DIR / "input_codex"} (new files only); Claude not finished: '
          f'{len(waiting)} batches')


def combine():
    K = pd.read_csv(CODED / 'screen_key.csv', dtype=str).set_index('item_id')
    C, X = verdicts('claude'), verdicts('codex')
    assert set(C.index) == set(K.index), 'Claude screen incomplete'
    inv_c = set(C.index[C.verdict == 'invalid'])
    assert inv_c <= set(X.index), 'Codex has not screened every pair Claude found invalid'
    both = sorted(inv_c & set(X.index[X.verdict == 'invalid']))
    step = X.loc[both, 'step']
    out = K.loc[both, ['vintage', 'input_hs6', 'output_hs6']].assign(step=step.values,
                                                                     reason_claude=C.loc[both, 'reason'].values,
                                                                     reason_codex=X.loc[both, 'reason'].values)
    out.reset_index().to_csv(CODED / 'screen_final.csv', index=False)
    rep = {'pool': len(K), 'claude_invalid': len(inv_c), 'codex_invalid_of_those': len(both),
           'codex_valid_of_those': len(inv_c) - len(both),
           'set_to_0': len(both), 'records_set_to_0': int(K.loc[both, 'n_records'].astype(int).sum())}
    cal = pd.read_csv(CODED / 'screen_calib_key.csv', dtype=str)
    if (DIR / 'claude' / 'screen_calib.csv').exists():
        cc = pd.read_csv(DIR / 'claude' / 'screen_calib.csv', dtype=str).set_index('item_id')
        cal['claude'] = cal.item_id.map(cc.verdict)
        rep['calibration_claude'] = {f'truth {a}, claude {b}': int(n) for (a, b), n in cal.groupby(['truth', 'claude']).size().items()}
    json.dump(rep, open(CODED / 'screen_report.json', 'w'), indent=1, default=str)
    print(json.dumps(rep, indent=1, default=str))


def excluded_because(a, b):
    """why convention 3 (I.9) excludes remelting a into b"""
    if '4007' <= a[:4] <= '4017' and b[:2] == '40':
        return 'vulcanised rubber cannot be remelted'
    if a[:2] == '39' and b[:2] == '39':
        return 'thermoset or cellulose plastic, or a different polymer: cannot be remelted into the output'
    if a[:2] == '37' and b[:2] == '37':
        return 'film cannot be re-made into other film or chemicals by remelting'
    return 'remelting into a finished product is not an input route'


def rescue_build():
    P = pd.read_csv(RESCUE_POOL, dtype=str, keep_default_na=False)
    one1 = P.dv_ai1 == '1'
    P['claim_reason'] = P.why_ai1.where(one1, P.why_ai2)
    both = (P.dv_ai1 == '1') & (P.dv_ai2 == '1')
    P['counter_reason'] = P.why_ai2.where(one1 & ~both, P.why_ai1.where(~one1, ''))
    P.loc[both, 'claim_reason'] = P.why_ai1[both] + ' / ' + P.why_ai2[both]
    P['excluded_because'] = [excluded_because(a, b) for a, b in zip(P.input_hs6, P.output_hs6)]
    P = described(P).sort_values(['vintage', 'input_hs6', 'output_hs6']).reset_index(drop=True)
    P['unit'] = P.vintage.str[2:] + ':' + P.input_hs6.str[:4] + '>' + P.output_hs6.str[:4]
    P['item_id'] = [f'R{i:05d}' for i in range(1, len(P) + 1)]
    (DIR / 'input').mkdir(parents=True, exist_ok=True)
    batch, size, b = [], 0, 1
    for _, g in P.groupby('unit', sort=False):
        if size and size + len(g) > BATCH:
            pd.concat(batch)[RESCUE_COLS].to_csv(DIR / 'input' / f'rescue_batch_{b:02d}.csv', index=False)
            batch, size, b = [], 0, b + 1
        batch.append(g)
        size += len(g)
    pd.concat(batch)[RESCUE_COLS].to_csv(DIR / 'input' / f'rescue_batch_{b:02d}.csv', index=False)
    P[['item_id', 'vintage', 'input_hs6', 'output_hs6', 'n_records']].to_csv(CODED / 'rescue_key.csv', index=False)
    print(f'{len(P)} pairs, {P.unit.nunique()} units, {b} rescue batches')


def rescue_add():
    """rescue batch for P_Q3E_0 pairs not screened yet (after a change of the conventions); item ids continue"""
    K = pd.read_csv(CODED / 'rescue_key.csv', dtype=str)
    P = pd.read_csv(RESCUE_POOL, dtype=str, keep_default_na=False)
    seen = set(zip(K.vintage, K.input_hs6, K.output_hs6))
    P = P[[k not in seen for k in zip(P.vintage, P.input_hs6, P.output_hs6)]].copy()
    if not len(P):
        print('no new pairs')
        return
    one1 = P.dv_ai1 == '1'
    P['claim_reason'] = P.why_ai1.where(one1, P.why_ai2)
    both = (P.dv_ai1 == '1') & (P.dv_ai2 == '1')
    P['counter_reason'] = P.why_ai2.where(one1 & ~both, P.why_ai1.where(~one1, ''))
    P.loc[both, 'claim_reason'] = P.why_ai1[both] + ' / ' + P.why_ai2[both]
    P['excluded_because'] = [excluded_because(a, b) for a, b in zip(P.input_hs6, P.output_hs6)]
    P = described(P).sort_values(['vintage', 'input_hs6', 'output_hs6']).reset_index(drop=True)
    P['unit'] = P.vintage.str[2:] + ':' + P.input_hs6.str[:4] + '>' + P.output_hs6.str[:4]
    start = int(K.item_id.str[1:].astype(int).max()) + 1
    P['item_id'] = [f'R{i:05d}' for i in range(start, start + len(P))]
    b = len(list((DIR / 'input').glob('rescue_batch_*.csv'))) + 1
    P[RESCUE_COLS].to_csv(DIR / 'input' / f'rescue_batch_{b:02d}.csv', index=False)
    pd.concat([K, P[['item_id', 'vintage', 'input_hs6', 'output_hs6', 'n_records']]]).to_csv(CODED / 'rescue_key.csv',
                                                                                             index=False)
    print(f'{len(P)} new pairs -> rescue_batch_{b:02d}.csv')


def rescue_check(stems):
    files = [DIR / 'input' / f'{s}.csv' for s in stems] if stems else sorted((DIR / 'input').glob('rescue_batch_*.csv'))
    ok = True
    for f in files:
        o = DIR / 'claude' / f.name
        if not o.exists():
            print(f'{f.stem}: missing')
            ok = False
            continue
        inp, out = pd.read_csv(f, dtype=str, keep_default_na=False), pd.read_csv(o, dtype=str, keep_default_na=False)
        bad = []
        if list(out.columns) != RESCUE_OUT:
            bad.append(f'header {list(out.columns)}')
        elif len(out) != len(inp) or (out.item_id.values != inp.item_id.values).any():
            bad.append('item ids differ from the input')
        else:
            for r in out.itertuples():
                if r.verdict == 'valid' and r.route not in ROUTES1:
                    bad.append(f'{r.item_id}: valid needs a route of dv 1 (not recycle_direct)')
                elif r.verdict == 'invalid' and r.route != 'none':
                    bad.append(f'{r.item_id}: invalid needs route none')
                elif r.verdict not in ('valid', 'invalid'):
                    bad.append(f'{r.item_id}: verdict')
                if len(str(r.reason).strip()) < 15:
                    bad.append(f'{r.item_id}: reason too short')
        print(f'{f.stem}: ' + ('OK' if not bad else f'{len(bad)} problems: ' + '; '.join(bad[:8])))
        ok &= not bad
    return ok


def rescue_combine():
    K = pd.read_csv(CODED / 'rescue_key.csv', dtype=str).set_index('item_id')
    V = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False)
                   for f in sorted((DIR / 'claude').glob('rescue_batch_*.csv'))]).set_index('item_id')
    assert set(K.index) <= set(V.index), 'rescue screen incomplete'
    v = V[V.verdict == 'valid']
    K.loc[v.index, ['vintage', 'input_hs6', 'output_hs6']].assign(route=v.route, reason=v.reason).reset_index().to_csv(
        CODED / 'screen_rescue.csv', index=False)
    print(f'{len(v)} of {len(K)} pairs back to 1 + uncertain; routes {v.route.value_counts().to_dict()}')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'build':
        build()
    elif cmd == 'check':
        sys.exit(0 if check(sys.argv[2], sys.argv[3:]) else 1)
    elif cmd == 'codex':
        codex_inputs()
    elif cmd == 'combine':
        combine()
    elif cmd == 'rescue_build':
        rescue_build()
    elif cmd == 'rescue_add':
        rescue_add()
    elif cmd == 'rescue_check':
        sys.exit(0 if rescue_check(sys.argv[2:]) else 1)
    elif cmd == 'rescue_combine':
        rescue_combine()
