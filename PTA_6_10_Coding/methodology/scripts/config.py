"""Shared paths and helpers for the PTA 6-10 pipeline (same workflow as PTA 2-5, 2026-10-19 v2).

The textile rules (textile.py) and the old-dta reader (dta_old.py) are imported from PTA_2_5/_work, so one copy of
each rule set serves every PTA. The coded master list (workflow step 7a) is the union of the ASEAN-Japan labels of
2026-10-19 and the final PTA 2-5 master; the two agree on every shared pair (asserted by PTA_2_5/_work/09).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent                                   # Dummy_Variable/PTA6_10
PROJECT = HERE.parents[2]                            # RoO_Project
P25 = PROJECT / 'Dummy_Variable/PTA_2_5'
ML = PROJECT / 'Data_Validation_Through_Machine_Learning'
REF = PROJECT / 'RoO_Step0/reference_hs'
sys.path.insert(0, str(P25 / '_work'))

PTAS = ['TUR_SGP', 'NIC_TWN', 'CHL_KOR', 'OMN_USA', 'CAN_CHL']
NAMES = {'TUR_SGP': 'Turkey-Singapore', 'NIC_TWN': 'Nicaragua-Taiwan', 'CHL_KOR': 'Chile-Korea',
         'OMN_USA': 'Oman-US', 'CAN_CHL': 'Canada-Chile'}
LABELS_PTA1 = ML / 'labels_2026_10_19/outputs/PTA_1_labels_2026_10_19.csv'
MASTER_P25 = P25 / 'final/master_coded_final.csv'
CONCORD = HERE / 'concordance/HS2012_to_HS2002_correlation.csv'
INTAKE = HERE / 'intake'
CODED = HERE / 'coded'
AI = BASE / 'ai_coders'
FINAL = BASE / 'final'
SEA = ('0301', '0302', '0303', '0304', '0305', '0306', '0307', '1604', '1605', '2301')   # as in PTA_2_5/_work/09


def hs_leaves(ed):
    """six-digit leaf codes of an HS edition (H1 = HS1996 ... H6 = HS2022)"""
    r = json.load(open(REF / f'{ed}.json'))['results']
    return {x['id'] for x in r if len(x['id']) == 6 and x['id'].isdigit()}


def pta1_uncertain_reason(L):
    """uncertain_reason of the ASEAN-Japan labels, as written by PTA_2_5/_work/09_apply_policy.py"""
    return np.where(L.uncertain == 1, np.where(L.route == 'unresolved', 'open case in the ASEAN-Japan labels',
                                               np.where(L.policy.str.contains('P_AUD_A'),
                                                        'minor constituent of a yarn or fabric: other fibre',
                                                        np.where(L.policy.str.contains('P_FISH'),
                                                                 'possible feed (rock lobster)', 'other'))), '')


def load_coded_master():
    """Coded HS2002 pairs of PTA 1-5, one row per (input_hs6, output_hs6). ASEAN-Japan labels win where both
    exist (they are identical there). Columns: DV, uncertain, uncertain_reason, route, step, locked, policy,
    copy_from, copy_origin (how the pair was coded in its master), dv_ai1, dv_ai2, why_ai1, why_ai2."""
    L = pd.read_csv(LABELS_PTA1, dtype=str, keep_default_na=False)
    for c in ('DV', 'uncertain', 'locked'):
        L[c] = L[c].astype(float).astype(int)
    L['uncertain_reason'] = pta1_uncertain_reason(L)
    L['step'] = L.step.replace({'<NA>': ''})
    L['copy_from'] = 'ASEAN_JPN'
    L['copy_origin'] = 'pta1_label'
    for c in ('dv_ai1', 'dv_ai2', 'why_ai1', 'why_ai2'):
        L[c] = ''
    F = pd.read_csv(MASTER_P25, dtype=str, keep_default_na=False)
    for c in ('DV', 'uncertain', 'locked'):
        F[c] = F[c].astype(int)
    F['copy_from'] = 'PTA_2_5'
    F['copy_origin'] = F.source
    cols = ['input_hs6', 'output_hs6', 'DV', 'uncertain', 'uncertain_reason', 'route', 'step', 'locked', 'policy',
            'copy_from', 'copy_origin', 'dv_ai1', 'dv_ai2', 'why_ai1', 'why_ai2']
    F = F[~F.set_index(['input_hs6', 'output_hs6']).index.isin(L.set_index(['input_hs6', 'output_hs6']).index)]
    M = pd.concat([L[cols], F[cols]], ignore_index=True)
    assert not M.duplicated(['input_hs6', 'output_hs6']).any()
    return M
