"""Workflow step 1 for PTA 2-5: read each agreement's pair list, check its HS vintage, build the pair master list.

Input  : RoO_Project/Original Data/{BRN_JPN,AUS_USA,CAFTA,BHR_USA}.dta (read-only; old formats decoded by dta_old.py)
Output : _work/intake/  pairs_<PTA>.csv (one row per original record, with pair_id), master_pairs.csv (unique HS6
         pairs across PTA 2-5 with the agreements that list them), vintage_check.csv, intake.json.
Pairs are written input -> output. Codes are compared with every HS edition (H1 = HS1996 ... H6 = HS2022) from the
UN Comtrade reference files already in RoO_Step0/reference_hs.

Run: /usr/local/bin/python3 -I _work/01_intake.py
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from dta_old import read_any_dta  # noqa: E402

PROJECT = HERE.parents[2]
RAW = PROJECT / 'Original Data'
REF = PROJECT / 'RoO_Step0/reference_hs'
OUT = HERE / 'intake'
PTAS = ['BRN_JPN', 'AUS_USA', 'CAFTA', 'BHR_USA']
EDITIONS = {'H1': 'HS1996', 'H2': 'HS2002', 'H3': 'HS2007', 'H4': 'HS2012', 'H5': 'HS2017', 'H6': 'HS2022'}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def leaves(ed):
    r = json.load(open(REF / f'{ed}.json'))['results']
    return {x['id'] for x in r if len(x['id']) == 6 and x['id'].isdigit()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ed_codes = {e: leaves(e) for e in EDITIONS}
    info, frames, vint = {}, [], []
    for pta in PTAS:
        f = RAW / f'{pta}.dta'
        raw, meta = read_any_dta(f)
        cols = list(raw.columns)
        assert {'input_str', 'output_str'} <= set(cols), (pta, cols)
        d = raw.rename(columns={'input_str': 'input_hs6', 'output_str': 'output_hs6'})
        for c in ('input_hs6', 'output_hs6'):
            d[c] = d[c].astype(str).str.strip().str.zfill(6)
        bad = d[~d.input_hs6.str.fullmatch(r'\d{6}') | ~d.output_hs6.str.fullmatch(r'\d{6}')]
        d['pta'] = pta
        d['record_no'] = range(1, len(d) + 1)
        d['pair_id'] = pta + '|' + d.input_hs6 + '>' + d.output_hs6
        dup = int(d.duplicated(['input_hs6', 'output_hs6']).sum())
        codes = set(d.input_hs6) | set(d.output_hs6)
        row = {'pta': pta, 'codes': len(codes)}
        for e, name in EDITIONS.items():
            row[f'share_in_{name}'] = round(len(codes & ed_codes[e]) / len(codes), 4)
            row[f'not_in_{name}'] = len(codes - ed_codes[e])
        vint.append(row)
        info[pta] = {'file': f.name, 'sha256': sha(f), 'dta_format': meta.get('format'), 'records': len(d),
                     'columns': cols, 'malformed_codes': len(bad), 'duplicate_pairs_within_file': dup,
                     'unique_pairs': int(len(d) - dup), 'unique_codes': len(codes),
                     'unique_input_codes': d.input_hs6.nunique(), 'unique_output_codes': d.output_hs6.nunique(),
                     'self_pairs': int((d.input_hs6 == d.output_hs6).sum())}
        d.to_csv(OUT / f'pairs_{pta}.csv', index=False)
        frames.append(d.drop_duplicates(['input_hs6', 'output_hs6']))
    allp = pd.concat(frames)
    master = (allp.groupby(['input_hs6', 'output_hs6']).pta.apply(lambda s: ';'.join(sorted(s))).reset_index()
              .rename(columns={'pta': 'ptas'}))
    master['n_ptas'] = master.ptas.str.count(';') + 1
    master['master_id'] = 'M|' + master.input_hs6 + '>' + master.output_hs6
    master.to_csv(OUT / 'master_pairs.csv', index=False)
    pd.DataFrame(vint).to_csv(OUT / 'vintage_check.csv', index=False)
    info['master'] = {'unique_pairs_across_pta_2_5': len(master),
                      'pairs_in_k_agreements': master.n_ptas.value_counts().sort_index().to_dict()}
    info['vintage_check'] = vint
    json.dump(info, open(OUT / 'intake.json', 'w'), indent=1, default=int)
    print(json.dumps(info, indent=1, default=int))


if __name__ == '__main__':
    main()
