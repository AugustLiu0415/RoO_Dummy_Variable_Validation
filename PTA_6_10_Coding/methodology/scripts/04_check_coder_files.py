"""Check AI coder output files against their input files.

Usage: /usr/local/bin/python3 _work/04_check_coder_files.py <coder folder> [file stem ...]
       e.g. coder2_codex units_batch_01 sample_pairs ; with no stems, every output file in the folder is checked.
Unit files: header unit_id,scope,dv,route,step,reason; one default row per unit; scopes in:/out:/pair: must name
codes of that unit. Pair files: header item_id,dv,route,step,reason; one row per input item, same order.
"""
import csv
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
AI = HERE.parent / 'ai_coders'
ROUTES1 = {'same_good', 'forward', 'ingredient', 'component', 'reconstitute', 'mixture', 'recycle_waste', 'feed',
           'sibling_intermediate', 'recycle_direct'}      # recycle_direct is dv 1 since 2026-10-19
ROUTES0 = {'none', 'recycle_direct'}                           # dv 0 + recycle_direct accepted for older files


def row_problems(r):
    bad = []
    if r.dv not in ('0', '1'):
        return ['dv']
    if r.dv == '1' and r.route not in ROUTES1:
        bad.append('route for dv 1')
    if r.dv == '0' and r.route not in ROUTES0:
        bad.append('route for dv 0')
    if r.route == 'same_good' and r.step != '2':
        bad.append('same_good needs step 2')
    if r.dv == '0' and r.step not in ('3', '4', '5', '6'):
        bad.append('dv 0 needs step 3-6')
    if r.dv == '1' and r.route != 'same_good' and r.step != '':
        bad.append('step must be empty')
    if len(str(r.reason).strip()) < 15:
        bad.append('reason too short')
    return bad


def check_pairs(inp, out):
    err = []
    if list(out.columns) != ['item_id', 'dv', 'route', 'step', 'reason']:
        return [f'header {list(out.columns)}']
    if len(out) != len(inp) or (out.item_id.values != inp.item_id.values).any():
        err.append(f'items differ from input (rows {len(out)} vs {len(inp)}, or order)')
    for i, r in out.iterrows():
        b = row_problems(r)
        if b:
            err.append(f'row {i + 2} {r.item_id}: {", ".join(b)}')
    return err


def check_units(inp, out):
    err = []
    if list(out.columns) != ['unit_id', 'scope', 'dv', 'route', 'step', 'reason']:
        return [f'header {list(out.columns)}']
    units = inp.set_index('unit_id')
    d = out[out.scope == 'default'].unit_id
    if d.duplicated().any():
        err.append(f'units with two defaults: {sorted(set(d[d.duplicated()]))[:5]}')
    miss = set(units.index) - set(d)
    if miss:
        err.append(f'{len(miss)} units without a default row, e.g. {sorted(miss)[:5]}')
    extra = set(out.unit_id) - set(units.index)
    if extra:
        err.append(f'unknown units {sorted(extra)[:5]}')
    for i, r in out.iterrows():
        if r.unit_id not in units.index:
            continue
        u = units.loc[r.unit_id]
        ins = {c.split(':')[0].strip() for c in u.input_codes.split(' ; ')}
        outs = {c.split(':')[0].strip() for c in u.output_codes.split(' ; ')}
        b = row_problems(r)
        m = re.fullmatch(r'(default|in:(\d{6})|out:(\d{6})|pair:(\d{6})>(\d{6}))', r.scope)
        if not m:
            b.append(f'scope {r.scope!r}')
        elif m.group(2) and m.group(2) not in ins:
            b.append(f'{m.group(2)} not an input of the unit')
        elif m.group(3) and m.group(3) not in outs:
            b.append(f'{m.group(3)} not an output of the unit')
        elif m.group(4) and (m.group(4) not in ins or m.group(5) not in outs):
            b.append('pair not in the unit')
        if b:
            err.append(f'row {i + 2} {r.unit_id} {r.scope}: {", ".join(b)}')
    return err


def main():
    coder = sys.argv[1]
    stems = sys.argv[2:] or sorted(p.stem for p in (AI / coder).glob('*.csv') if not p.stem.startswith('_'))
    ok = True
    for s in stems:
        inp = pd.read_csv(AI / 'input' / f'{s}.csv', dtype=str, keep_default_na=False)
        f = AI / coder / f'{s}.csv'
        if not f.exists():
            print(f'{coder}/{s}: MISSING')
            ok = False
            continue
        rows = list(csv.reader(open(f, newline='', encoding='utf-8')))
        badlen = [k + 1 for k, r in enumerate(rows) if r and len(r) != len(rows[0])]
        if badlen:                                 # e.g. an unquoted comma in a reason
            print(f'{coder}/{s}: {len(badlen)} line(s) with a wrong number of fields (unquoted comma?), '
                  f'e.g. lines {badlen[:10]}')
            ok = False
            continue
        out = pd.read_csv(f, dtype=str, keep_default_na=False, index_col=False)
        err = check_units(inp, out) if s.startswith('units') else check_pairs(inp, out)
        print(f'{coder}/{s}: {"OK" if not err else f"{len(err)} problem(s)"}; rows {len(out)}; '
              f'dv {out.dv.value_counts().to_dict() if "dv" in out else {}}')
        for e in err[:25]:
            print('   ', e)
        ok &= not err
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
