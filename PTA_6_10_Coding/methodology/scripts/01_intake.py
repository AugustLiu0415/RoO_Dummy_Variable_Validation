"""Workflow step 1 for PTA 6-10: read each agreement's pair list, check its HS vintage, map codes to HS2002 (the
vintage of every coded PTA so far) and build the pair master list.

Input  : Dummy_Variable/PTA6_10/{TUR_SGP,NIC_TWN,CHL_KOR,OMN_USA,CAN_CHL}.dta (read-only; R-written format 110,
         decoded by PTA_2_5/_work/dta_old.py) and the UN correlation table HS2012 -> HS2002
         (_work/concordance/HS2012_to_HS2002_correlation.csv, from unstats.un.org, see concordance_source.json).
Mapping: the vintage is the HS edition that contains every code of the file.
         HS2002 files: a valid code maps to itself. A code that is in no HS edition (CHL_KOR 610340, 610344, 610345)
           maps to every HS2002 subheading of its 5-digit group (or heading), concord_flag = 1.
         HS2012 files (TUR_SGP): every HS2002 code linked to the code in the correlation table. A code whose link is
           not "1 to 1" gets concord_flag = 1 (workflow step 1: flag non-one-to-one mappings).
         A record maps to every (input, output) combination of its mapped codes. The record's code is set later
         from these HS2002 pairs (09_apply_policy.py: DV = max over the mapped pairs).
         Inputs that are not HS6 codes (TUR_SGP: "WO" wholly obtained, "any") are kept as records without pairs;
         their DV stays missing until Prof. Zhang decides (decision of August, 2026-10-25).
Output : _work/intake/records_<PTA>.csv (one row per original record), record_pairs.csv (record -> HS2002 pairs),
         master_pairs.csv (unique HS2002 pairs across PTA 6-10), vintage_check.csv, intake.json.

Run: /usr/local/bin/python3 -I _work/01_intake.py
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import BASE, CONCORD, INTAKE, PTAS, hs_leaves  # noqa: E402
from dta_old import read_any_dta  # noqa: E402

EDITIONS = {'H1': 'HS1996', 'H2': 'HS2002', 'H3': 'HS2007', 'H4': 'HS2012', 'H5': 'HS2017', 'H6': 'HS2022'}


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def group_fallback(c, h2):
    """HS2002 subheadings sharing the longest prefix (5 digits, else 4) with an invalid code"""
    for k in (5, 4):
        s = sorted(x for x in h2 if x[:k] == c[:k])
        if s:
            return s, f'invalid code: all HS2002 subheadings of {c[:k]}'
    raise ValueError(c)


def mapper(vintage, h2, corr):
    """code -> (list of HS2002 codes, concord_flag, note)"""
    cache = {}

    def m(c):
        if c in cache:
            return cache[c]
        if vintage == 'HS2002':
            out = ([c], 0, '') if c in h2 else (*group_fallback(c, h2)[:1], 1, group_fallback(c, h2)[1])
        elif c in corr.index:
            g = corr.loc[[c]]
            rel = ';'.join(sorted(set(g.relationship)))
            out = (sorted(set(g.hs2002)), int(rel != '1 to 1'), '' if rel == '1 to 1' else f'HS2012 {rel}')
        else:
            codes, note = group_fallback(c, h2)
            out = (codes, 1, note)
        cache[c] = out
        return out
    return m


def main():
    INTAKE.mkdir(parents=True, exist_ok=True)
    ed = {e: hs_leaves(e) for e in EDITIONS}
    h2 = ed['H2']
    corr = pd.read_csv(CONCORD, dtype=str).set_index('hs2012')
    info, vint, rp_all = {}, [], []
    for pta in PTAS:
        f = BASE / f'{pta}.dta'
        raw, meta = read_any_dta(f)
        cols = list(raw.columns)
        assert {'input_str', 'output_str'} <= set(cols), (pta, cols)
        d = raw.copy()
        d['input_hs6'] = d.input_str.astype(str).str.strip()
        d['output_hs6'] = d.output_str.astype(str).str.strip()
        six_in = d.input_hs6.str.fullmatch(r'\d{6}')
        assert d.output_hs6.str.fullmatch(r'\d{6}').all(), pta
        d['input_type'] = d.input_hs6.where(~six_in, 'hs6')
        codes = set(d.input_hs6[six_in]) | set(d.output_hs6)
        share = {e: len(codes & ed[e]) / len(codes) for e in EDITIONS}
        vintage = EDITIONS[max(share, key=share.get)]
        vint.append({'pta': pta, 'codes': len(codes), 'vintage': vintage,
                     **{f'share_in_{EDITIONS[e]}': round(share[e], 4) for e in EDITIONS},
                     **{f'not_in_{EDITIONS[e]}': len(codes - ed[e]) for e in EDITIONS}})
        m = mapper(vintage, h2, corr)
        d['pta'] = pta
        d['record_no'] = range(1, len(d) + 1)
        d['pair_id'] = pta + '|' + d.input_hs6 + '>' + d.output_hs6 + '|' + d.record_no.astype(str)
        d['hs_vintage'] = vintage
        mi = [m(c) if t == 'hs6' else ([], 0, '') for c, t in zip(d.input_hs6, d.input_type)]
        mo = [m(c) for c in d.output_hs6]
        d['input_hs2002'] = [';'.join(x[0]) for x in mi]
        d['output_hs2002'] = [';'.join(x[0]) for x in mo]
        d['n_mapped_pairs'] = [len(a[0]) * len(b[0]) for a, b in zip(mi, mo)]
        d['concord_flag'] = [max(a[1], b[1]) for a, b in zip(mi, mo)]
        d['concord_note'] = ['; '.join(x for x in (f'input {a[2]}' if a[2] else '', f'output {b[2]}' if b[2] else '')
                                       if x) for a, b in zip(mi, mo)]
        rp = [(pta, r, a, b) for r, A, B in zip(d.record_no, mi, mo) for a in A[0] for b in B[0]]
        rp = pd.DataFrame(rp, columns=['pta', 'record_no', 'input_hs6', 'output_hs6'])
        rp_all.append(rp)
        d.to_csv(INTAKE / f'records_{pta}.csv', index=False)
        hs = d[d.input_type == 'hs6']
        info[pta] = {'file': f.name, 'sha256': sha(f), 'dta_format': meta.get('format'), 'records': len(d),
                     'columns': cols, 'hs_vintage': vintage,
                     'input_type': d.input_type.value_counts().to_dict(),
                     'duplicate_records_same_pair': int(hs.duplicated(['input_hs6', 'output_hs6']).sum()),
                     'unique_pairs_own_vintage': int((~hs.duplicated(['input_hs6', 'output_hs6'])).sum()),
                     'self_pairs_own_vintage': int((hs.input_hs6 == hs.output_hs6).sum()),
                     'records_concord_flag': int(d.concord_flag.sum()),
                     'records_mapped_to_several_pairs': int((d.n_mapped_pairs > 1).sum()),
                     'hs2002_pairs': int((~rp.duplicated(['input_hs6', 'output_hs6'])).sum()),
                     'invalid_codes': sorted({c for c in codes if c not in ed[{v: k for k, v in EDITIONS.items()}
                                                                               [vintage]]})}
    rp = pd.concat(rp_all, ignore_index=True)
    rp.to_csv(INTAKE / 'record_pairs.csv', index=False)
    u = rp.drop_duplicates(['pta', 'input_hs6', 'output_hs6'])
    master = (u.groupby(['input_hs6', 'output_hs6']).pta.apply(lambda s: ';'.join(sorted(s))).reset_index()
              .rename(columns={'pta': 'ptas'}))
    master['n_ptas'] = master.ptas.str.count(';') + 1
    master['n_records'] = master.set_index(['input_hs6', 'output_hs6']).index.map(
        rp.groupby(['input_hs6', 'output_hs6']).size()).values
    master['master_id'] = 'M|' + master.input_hs6 + '>' + master.output_hs6
    master.to_csv(INTAKE / 'master_pairs.csv', index=False)
    pd.DataFrame(vint).to_csv(INTAKE / 'vintage_check.csv', index=False)
    info['master'] = {'unique_hs2002_pairs_across_pta_6_10': len(master),
                      'pairs_in_k_agreements': master.n_ptas.value_counts().sort_index().to_dict()}
    info['concordance'] = json.load(open(CONCORD.parent / 'concordance_source.json'))
    info['vintage_check'] = vint
    json.dump(info, open(INTAKE / 'intake.json', 'w'), indent=1, default=int)
    print(json.dumps({k: v for k, v in info.items() if k != 'vintage_check'}, indent=1, default=int))


if __name__ == '__main__':
    main()
