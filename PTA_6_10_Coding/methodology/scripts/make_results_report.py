"""Build the PTA 6-10 result report and variable file (HTML, printed to PDF with Chrome) from the final files.

Reads final/<PTA>_coded_2026_10_31.csv, final/{master,concord}_coded_final.csv, final/policy_report.json,
final/combine_report.json, final/ai_audit_report.json, _work/coded/screen_report.json and the draft of 28 October
(final_v2_draft_2026_10_28/). Writes Results_PTA_6_10_2026_10_31.html, Variables_PTA_6_10_2026_10_31.html and
summary_by_pta.csv next to this script.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FINAL = ROOT / 'final'
DRAFT = ROOT / 'final_v2_draft_2026_10_28'
DATE = '2026_10_31'
PTAS = [('TUR_SGP', 'Turkey–Singapore'), ('NIC_TWN', 'Nicaragua–Taiwan'), ('CHL_KOR', 'Chile–Korea'),
        ('OMN_USA', 'Oman–US'), ('CAN_CHL', 'Canada–Chile')]
REASONS = [('AI coders, or the model and the textile rules, disagree',
            'The two AI coders (or the model and the textile rules) disagree'),
           ('AI coders disagree: sibling or backward', 'The two AI coders disagree: intermediate sibling or backward'),
           ('same-material intermediate of another heading, or another compound (convention of 2026-10-30)',
            'Same-material intermediate of another heading, or another compound of one heading (30 Oct)'),
           ('remelting into another primary or semi-finished form (convention of 2026-10-30)',
            'Remelting into another primary or semi-finished form of the same material (30 Oct)'),
           ('remelting excluded (convention of 2026-10-30), another route possible',
            'Remelting excluded, but another specific route is possible (30 Oct)'),
           ('minor constituent of a garment or made-up: other fibre or construction',
            'Minor constituent of a garment or made-up: other fibre (not cotton or man-made) or other construction'),
           ('minor constituent of a yarn or fabric: other fibre',
            'Minor constituent of a yarn or fabric: other fibre (not cotton or man-made)'),
           ('open case in the ASEAN-Japan labels', 'Open case in the ASEAN–Japan labels'),
           ('HS concordance: the HS2002 pairs of this record differ',
            'HS concordance: the HS2002 pairs of a record differ'),
           ('possible feed (rock lobster)', 'Possible feed (crustaceans → rock lobster)')]
SOURCES = [('Copied from the ASEAN–Japan labels (step 7a)', lambda f: (f.source == 'exact_copy') & (f.copy_from == 'ASEAN_JPN')),
           ('Copied from the PTA 2–5 codes (step 7a)', lambda f: (f.source == 'exact_copy') & (f.copy_from == 'PTA_2_5')),
           ('Two AI coders (steps 2–6)', lambda f: f.source.isin(['ai_units', 'ai_sample'])),
           ('Two AI coders on HS2012 codes (step 1)', lambda f: f.source == 'ai_concord'),
           ('Textile rules (step 7e)', lambda f: f.source == 'rule_textile'),
           ('Self-pairs (step 2)', lambda f: f.source == 'rule')]
COLS = ['pta', 'master_id', 'DV', 'DV_strict', 'DV_excl_remelt', 'uncertain', 'uncertain_reason', 'route', 'source',
        'copy_from', 'n_mapped_pairs', 'concord_flag', 'input_hs2002', 'output_hs2002']
# accuracy of the draft of 28 October and of variants, scored with 07_audit.py on the true values of 31 October
# (audit/audit_review.xlsx); the final figures are read from ai_audit_report.json
DRAFT_ACC = {'pair': 0.951, 'record': 0.980}
NO_PROF0_ACC = {'pair': 0.960, 'record': 0.985}


def n(x):
    return f'{x:,}'


def pct(a, b, d=1):
    return f'{100 * a / b:.{d}f}%'


def p1(x):
    return f'{100 * x:.1f}%'


def ci(e):
    return f'{p1(e["est"])} ({100 * e["ci95"][0]:.1f}–{100 * e["ci95"][1]:.1f})'


def table(head, rows, num_from=1, widths=None):
    w = widths or [''] * len(head)
    h = ''.join(f'<th class="{"n" if i >= num_from else ""}" style="{f"width:{w[i]}" if w[i] else ""}">{c}</th>'
                for i, c in enumerate(head))
    b = ''.join('<tr>' + ''.join(f'<td class="{"n" if i >= num_from else ""}">{c}</td>' for i, c in enumerate(r))
                + '</tr>' for r in rows)
    return f'<table><tr>{h}</tr>{b}</table>'


def bold(r):
    return [f'<b>{c}</b>' for c in r]


def load():
    S, frames = {}, []
    for p, _ in PTAS:
        f = pd.read_csv(FINAL / f'{p}_coded_{DATE}.csv', usecols=COLS, dtype=str, keep_default_na=False)
        for c in ('DV', 'DV_strict', 'DV_excl_remelt', 'uncertain', 'concord_flag', 'n_mapped_pairs'):
            f[c] = pd.to_numeric(f[c])
        d = pd.read_csv(DRAFT / f'{p}_coded_2026_10_25.csv', usecols=['DV', 'uncertain', 'input_type'], dtype=str)
        d = d[d.input_type == 'hs6']
        textile = (f.input_hs2002.str[:2].astype(int).between(50, 63)
                   & f.output_hs2002.str[:2].astype(int).between(50, 63))
        S[p] = dict(rows=len(f), DV1=int(f.DV.sum()), DVs=int(f.DV_strict.sum()), DVx=int(f.DV_excl_remelt.sum()),
                    unc=int(f.uncertain.sum()), reasons=f[f.uncertain == 1].uncertain_reason.value_counts().to_dict(),
                    src=[int(m(f).sum()) for _, m in SOURCES], new=int((f.source != 'exact_copy').sum()),
                    textile=int(textile.sum()), concord_flag=int(f.concord_flag.sum()),
                    multi_rep=int(((f.n_mapped_pairs > 1) & (f.source != 'ai_concord')).sum()),
                    d_rows=len(d), d_DV1=int((d.DV == '1').sum()), d_unc=int((d.uncertain == '1').sum()),
                    d_DVs=int(((d.DV == '1') & (d.uncertain == '0')).sum()))
        assert sum(S[p]['src']) == len(f) and sum(S[p]['reasons'].values()) == S[p]['unc']
        assert set(S[p]['reasons']) <= {k for k, _ in REASONS}
        frames.append(f)
    return S, pd.concat(frames)


def cross(a):
    """pairs shared by two or more of the five agreements: do DV, uncertain, route and reason agree?"""
    g = a.groupby('master_id').agg(n=('pta', 'nunique'), dv=('DV', 'nunique'), u=('uncertain', 'nunique'),
                                   r=('route', 'nunique'), ur=('uncertain_reason', 'nunique'))
    m = g[g.n > 1]
    multi = set(a.loc[a.n_mapped_pairs > 1, 'master_id'])
    diff = m[(m.u > 1) | (m.r > 1) | (m.ur > 1)]
    assert set(diff.index) <= multi
    # rows coded on HS2002 that map to several HS2002 pairs take the highest DV: HS2002 pairs coded 0 inside such a
    # row with DV = 1
    mm = a[(a.n_mapped_pairs > 1) & (a.source != 'ai_concord') & (a.DV == 1)]
    inside = {f'M|{i}>{o}' for ii, oo in zip(mm.input_hs2002, mm.output_hs2002)
              for i in ii.split(';') for o in oo.split(';')}
    mdv = pd.read_csv(FINAL / 'master_coded_final.csv', dtype=str, usecols=['master_id', 'DV']).set_index('master_id').DV
    zero = {k for k in inside if mdv.get(k) == '0'}
    own0 = set(a.loc[(a.n_mapped_pairs == 1) & (a.DV == 0), 'master_id'])
    return dict(shared=len(m), dv_diff=int((m.dv > 1).sum()), other_diff=len(diff),
                concord_multi=int(((a.source == 'ai_concord') & (a.n_mapped_pairs > 1)).sum()),
                multi_rows=int((a.n_mapped_pairs > 1).sum()), zero_inside=len(zero), zero_inside_own=len(zero & own0))


CONV2 = REASONS[2][0]


def changes():
    out = {}
    for f in ('master_coded_final.csv', 'concord_coded_final.csv'):
        k = ['input_hs6', 'output_hs6']
        a = pd.read_csv(FINAL / f, dtype=str, keep_default_na=False,
                        usecols=lambda c: c in k + ['DV', 'uncertain', 'uncertain_reason', 'n_ptas'])
        b = pd.read_csv(DRAFT / f, dtype=str, usecols=k + ['DV', 'uncertain'])
        m = a.merge(b, on=k, suffixes=('', '_d'), validate='1:1')
        assert len(m) == len(a) == len(b)
        out[f.split('_')[0]] = dict(pairs=len(m), up=int(((m.DV_d == '0') & (m.DV == '1')).sum()),
                                    down=int(((m.DV_d == '1') & (m.DV == '0')).sum()),
                                    flag=int(((m.DV == m.DV_d) & (m.uncertain != m.uncertain_d)).sum()))
        if f.startswith('master'):
            out['master']['shared'] = int((pd.to_numeric(a.n_ptas) >= 2).sum())
            out['conv2_pairs'] = int(((m.DV == '1') & (m.DV_d == '1') & (m.uncertain_d == '0') & (m.uncertain == '1')
                                      & (m.uncertain_reason == CONV2)).sum())
    rows = 0
    for p, _ in PTAS:
        k = ['record_no']
        f = pd.read_csv(FINAL / f'{p}_coded_{DATE}.csv', dtype=str, keep_default_na=False,
                        usecols=k + ['DV', 'uncertain', 'uncertain_reason'])
        d = pd.read_csv(DRAFT / f'{p}_coded_2026_10_25.csv', dtype=str, usecols=k + ['DV', 'uncertain'])
        m = f.merge(d, on=k, suffixes=('', '_d'), validate='1:1')
        assert len(m) == len(f)
        rows += int(((m.DV == '1') & (m.DV_d == '1') & (m.uncertain_d == '0') & (m.uncertain == '1')
                     & (m.uncertain_reason == CONV2)).sum())
    out['conv2_rows'] = rows
    return out


CSS = '''<style>
@page {{ size: letter; margin: 0.9in 0.8in 0.85in 0.8in;
  @bottom-left {{ content: "{foot}"; font: 8pt "Helvetica Neue", Helvetica, Arial, sans-serif; color: #666; }}
  @bottom-right {{ content: counter(page); font: 8pt "Helvetica Neue", Helvetica, Arial, sans-serif; color: #666; }} }}
body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.42; color: #111; }}
h1 {{ font-size: 18pt; margin: 0 0 3pt 0; }}
h2 {{ font-size: 12.5pt; margin: 15pt 0 5pt 0; page-break-after: avoid; }}
p {{ margin: 3pt 0 6pt 0; }}
.lead {{ color: #444; }}
ul {{ margin: 2pt 0 6pt 0; padding-left: 15pt; }}
li {{ margin: 1.5pt 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 4pt 0 6pt 0; font-size: 8.6pt; page-break-inside: avoid; }}
tr {{ page-break-inside: avoid; }}
th {{ background: #eef0f3; text-align: left; font-weight: bold; padding: 3.5pt 4.5pt; border-bottom: 1px solid #c8ccd2; vertical-align: bottom; }}
td {{ padding: 3.2pt 4.5pt; border-bottom: 1px solid #dde0e4; vertical-align: top; }}
td.n, th.n {{ text-align: right; }}
td.n {{ white-space: nowrap; }}
code, td.v {{ font-family: Menlo, Consolas, monospace; font-size: 8.2pt; }}
pre {{ font-family: Menlo, Consolas, monospace; font-size: 8.4pt; background: #f4f5f7; padding: 6pt 9pt; margin: 4pt 0 8pt 0; }}
.note {{ font-size: 8.8pt; color: #333; }}
.cap {{ font-weight: bold; font-size: 9.5pt; margin: 9pt 0 2pt 0; page-break-after: avoid; }}
</style>'''


def results(S, X, C, pol, comb, aud, scr):
    T = {k: sum(S[p][k] for p, _ in PTAS) for k in ('rows', 'DV1', 'DVs', 'DVx', 'unc', 'new', 'd_rows', 'd_DV1',
                                                    'd_unc', 'd_DVs')}
    names = [nm for _, nm in PTAS]
    master = comb['master']
    new_pairs = master['new_pairs']
    tur = pol['pta']['TUR_SGP']
    u = comb['units']
    kg = u['kappa_by_input_group']
    after = aud['after_August_review']
    bt = aud['between_auditors']
    rc = aud['review_counts']
    h = ['<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<title>PTA 6–10 Coding Results</title>',
         CSS.format(foot='RoO input–output codes for PTA 6–10 · results · 31 October 2026'), '</head><body>']
    a = h.append
    a('<h1>RoO Input–Output Codes for PTA 6–10: Results</h1>')
    a('<p class="lead">31 October 2026 · August Liu. Companion to the coding workflow document (general coding rules, '
      '31 October 2026) and the variable explanation file.</p>')

    a('<h2>1. Data</h2><ul>')
    a(f'<li>Five agreements: Turkey–Singapore (HS2012), Nicaragua–Taiwan, Chile–Korea, Oman–US and Canada–Chile (all '
      f'HS2002). Each row is one (restricted input, output) pair at HS6 from the agreement’s product-specific rules: '
      f'{n(T["rows"])} rows in all. The {n(tur["records_deleted_not_hs6_input"])} Turkey–Singapore rows whose input is '
      f'“WO” (wholly obtained) or “any” rather than an HS code were deleted (decision of 28 October).</li>')
    a('<li>One Stata file per agreement (<i>&lt;PTA&gt;_coded_2026_10_31.dta</i>) with 36 variables; Turkey–Singapore '
      'has one more (special_rule, from its original file).</li>')
    a(f'<li>All pairs are coded on HS2002. Turkey–Singapore was mapped from HS2012 with the UN correlation table, and '
      f'{n(tur["records_mapped_to_several_pairs"])} of its rows map to several HS2002 pairs. '
      f'{n(tur["records_coded_on_HS2012_codes"])} rows, where two HS2012 codes fall into the same HS2002 code, were '
      f'coded on the HS2012 codes by the two AI coders ({n(X["concord_multi"])} of them are among the '
      f'{n(tur["records_mapped_to_several_pairs"])}). The other multi-mapped rows take the highest DV among their HS2002 '
      f'pairs, with uncertain = 1 if the pairs differ, except self-pairs (the same HS2012 code), which are locked as the '
      f'same good.</li>')
    a(f'<li>The five agreements contain {n(master["pairs"])} unique HS2002 pairs. {n(master["source"]["exact_copy"])} '
      f'of them ({pct(master["source"]["exact_copy"], master["pairs"])}) were already coded in PTA 1–5 and were copied; '
      f'the other {n(new_pairs)} were coded under the workflow. A pair has the same code in every agreement.</li></ul>')

    a('<h2>2. Main results</h2><p class="cap">Table 1. Input–output links by agreement</p>')
    rows = [[nm, n(S[p]['rows']), n(S[p]['DV1']), pct(S[p]['DV1'], S[p]['rows']), n(S[p]['DVs']), n(S[p]['DVx']),
             n(S[p]['unc']), pct(S[p]['unc'], S[p]['DV1'])] for p, nm in PTAS]
    rows.append(bold(['Total', n(T['rows']), n(T['DV1']), pct(T['DV1'], T['rows']), n(T['DVs']), n(T['DVx']),
                      n(T['unc']), pct(T['unc'], T['DV1'])]))
    a(table(['Agreement', 'Rows', 'DV = 1', 'Share', 'DV_strict = 1', 'DV_excl_remelt = 1', 'Uncertain',
             'Uncertain / DV = 1'], rows))
    a('<p class="note">DV = 1: the input can be used to make the output (main variable; it includes links that are '
      'possible but unconfirmed, marked uncertain). DV_strict counts only certain links (DV × (1 − uncertain)). '
      'DV_excl_remelt sets every direct-remelting HS2002 pair (route = recycle_direct, for example steel rod → steel '
      'ingots) to 0; a row coded on HS2002 that maps to several HS2002 pairs takes the highest value among them, so 3 '
      'Turkey–Singapore rows shown as recycle_direct keep 1 because another of their pairs has another route. The 591 '
      'Turkey–Singapore rows coded on their HS2012 codes are coded directly (none is recycle_direct).</p>')

    a('<h2>3. Uncertain pairs</h2><p class="cap">Table 2. Rows kept at DV = 1 with uncertain = 1, by reason</p>')
    rows = [[lab] + [n(S[p]['reasons'].get(k, 0)) for p, _ in PTAS] for k, lab in REASONS
            if any(S[p]['reasons'].get(k, 0) for p, _ in PTAS)]
    rows.append(bold(['Total uncertain'] + [n(S[p]['unc']) for p, _ in PTAS]))
    a(table(['Reason'] + names, rows, widths=['40%'] + [''] * 5))
    shares = ', '.join(f'{nm} {pct(S[p]["new"], S[p]["rows"])}' for p, nm in PTAS)
    a(f'<p>Most rows of these agreements are copies of PTA 1–5, so their uncertain pairs are those of PTA 1–5: mainly '
      f'minor constituents of another fibre in textile goods, where US-style yarn-forward rules list almost every yarn '
      f'and fabric as an input of each garment. The newly coded pairs add two kinds: pairs on which the two AI coders '
      f'disagree (about half of them chemicals; the rest mainly stone and glass, mineral products, machinery and '
      f'instruments), and pairs that the conventions of 30 October code as 1 with uncertainty (same-material '
      f'intermediates of another heading, different compounds of one heading, and remelting into another form of the '
      f'same material). The share of newly coded rows is {shares}. Turkey–Singapore has the highest uncertain share '
      f'because it has by far the highest share of newly coded rows, more than half of them chemicals.</p>')

    a('<h2>4. How the codes were obtained</h2><p class="cap">Table 3. Rows by coding method</p>')
    uniq = [master['source']['exact_copy'], None, master['source']['ai_units'] + master['source']['ai_sample'],
            pol['concord_pairs']['pairs'], master['source']['rule_textile'], master['source']['rule']]
    rows = []
    for i, (lab, _) in enumerate(SOURCES):
        v = [n(S[p]['src'][i]) for p, _ in PTAS]
        uq = '' if i == 1 else (f'{n(uniq[0])} (both)' if i == 0 else n(uniq[i]))
        rows.append([lab] + v + [uq])
    rows.append(bold(['Total'] + [n(S[p]['rows']) for p, _ in PTAS]
                     + [n(master['pairs'] + pol['concord_pairs']['pairs'])]))
    a(table(['Method'] + names + ['Unique pairs'], rows, widths=['30%'] + [''] * 6))
    a(f'<p class="note">Copies come from the coded master of PTA 1–5: the ASEAN–Japan labels and the codes of '
      f'Brunei–Japan, Australia–US, CAFTA and Bahrain–US (delivered on 19 October). The AI coders coded '
      f'{n(master["source"]["ai_units"])} pairs in {n(u["units_both_coders"])} heading-pair units and a blind sample of '
      f'{n(master["source"]["ai_sample"])} textile pairs. The model bands were not used for new pairs.</p>')
    a('<p>The conventions of 28–30 October (numbered as in section I.9 of the coders’ rules, '
      '<i>Coding_Rules_2026_10_30.md</i>) were applied by rule to the newly coded pairs, including pairs both AI coders '
      'had coded 0 where a convention covers a whole class (remelting, metal articles of the same metal):</p><ul>')
    pn = pol['policies_on_new_pairs']
    a(f'<li>Remelting (convention 3): {n(pn["P_Q3E_0"]["rows_matched"] - pn["P_RESCUE"]["rows_matched"])} pairs from 1 '
      f'to 0 (made into a finished product, vulcanised rubber, different or non-meltable polymers); '
      f'{n(pn["P_RESCUE"]["rows_matched"])} more stay 1 with uncertainty because another specific route exists. '
      f'{n(pn["P_Q3E_own"]["rows_matched"])} pairs are certain 1s (back to the input’s own upstream form) and '
      f'{n(pn["P_Q3E_other"]["rows_matched"] + pn["P_Q3E_other0"]["rows_matched"])} are 1 with uncertainty (another '
      f'primary or semi-finished form), {n(pn["P_Q3E_other0"]["rows_matched"])} of them coded 0 by both AI coders.</li>')
    a(f'<li>Same-material intermediates (convention 2): {n(pn["P_Q2C_art0"]["rows_matched"] + pn["P_Q2C_same0"]["rows_matched"])} '
      f'metal-article pairs from 0 to 1; parts, metal articles and compounds of one heading linked only by their '
      f'material are 1 with uncertainty.</li>')
    a('<li>Waste (convention 5): yarn, fabric or fibre → worn clothing (6309) and fibre → rags (6310) from 0 to 1 '
      '(textile rules); swine meat, offal and fat → pig bristles 0.</li>')
    a(f'<li>Screen of one-sided 1s (section 5): {n(pn["P_A1"]["rows_matched"])} more pairs to 0 (the screen’s other '
      f'{n(scr["set_to_0"] - pn["P_A1"]["rows_matched"])} pairs, pork → pig bristles, are counted under waste). Pairs '
      f'both independent auditors coded 0 in the classes where Professor Zhang said so: '
      f'{n(pn["P_PROF0"]["rows_matched"] + pol["concord_pairs"]["policies"]["P_PROF0"]["rows_matched"])} pairs to 0.</li>')
    a('<li>Chapter 59 (textile rules): wicks and hosepiping → belting 0; coated or rubberised fabric → belting 1; '
      'gum-coated fabric (5901) → tyre cord fabric 1.</li></ul>')

    a('<h2>5. Reliability</h2><ul>')
    cons = pol['consistency_with_PTA_1_5']
    a(f'<li><b>Consistency with PTA 1–5.</b> The {n(cons["exact_copies"])} copied pairs carry exactly the PTA 1–5 codes '
      f'({cons["DV_differs"]} differences in DV, uncertain and route).</li>')
    a(f'<li><b>Consistency across the five agreements.</b> {n(X["shared"])} pairs (master_id, the HS2002 pair a row is '
      f'coded under) appear in two or more agreements; DV is identical for all of them ({X["dv_diff"]} differences). '
      f'Uncertain, route and uncertain reason are identical too, except for {X["other_diff"]} pairs that also appear in a '
      f'row mapped to several HS2002 pairs (Turkey–Singapore HS2012 codes, invalid Chile–Korea codes), where the row takes '
      f'the highest DV of its pairs. Counting every HS2002 pair such a row maps to, {n(C["master"]["shared"])} pairs '
      f'appear in two or more agreements.</li>')
    a(f'<li><b>Two AI coders.</b> Claude and Codex coded {n(u["pairs_both_coders"])} new pairs independently. They '
      f'agreed on {p1(u["agreement_pairs"])} (Cohen’s kappa {u["kappa_pairs"]:.2f}). Codex coded 1 far more often '
      f'({n(u["DV1_coder2"])} pairs against {n(u["DV1_coder1"])}): in {n(u["coder1_0_coder2_1"])} pairs Codex coded 1 '
      f'and Claude 0, in {n(u["coder1_1_coder2_0"])} the reverse. Agreement was high for animal products (kappa '
      f'{kg["01-05 animal"]["kappa"]:.2f}), plant products ({kg["06-15 plant/fats"]["kappa"]:.2f}) and textiles '
      f'({kg["50-67 textile/footwear"]["kappa"]:.2f}), and close to none for chemicals '
      f'({kg["28-38 chemical"]["kappa"]:.2f}), food preparations ({kg["16-24 food"]["kappa"]:.2f}) and stone and glass '
      f'({kg["68-71 stone/glass/jewel"]["kappa"]:.2f}). Disagreements stay at DV = 1 with uncertain = 1 unless a '
      f'convention settles them. On the blind textile sample ({comb["sample"]["items"]} pairs) kappa was '
      f'{comb["sample"]["kappa"]:.2f}; on the {comb["concord"]["pairs"]} HS2012 pairs, {comb["concord"]["kappa"]:.2f}.</li>')
    a(f'<li><b>Screen of one-sided 1s.</b> {n(scr["pool"])} pairs were coded 1 by one coder and 0 by the other and '
      f'were not settled by a convention. Claude found {n(scr["claude_invalid"])} of them clearly invalid; Codex, '
      f'blind, agreed on {n(scr["set_to_0"])} ({n(scr["records_set_to_0"])} rows): tobacco → garments (180 pairs), '
      f'pork → pig bristles (10), and 20 others such as coal → lignite. Only these became 0; the pork → pig bristles '
      f'pairs are now coded by the waste convention, so the screen’s own policy mark covers '
      f'{n(pn["P_A1"]["rows_matched"])} pairs. Codex named a specific role for almost every chemical, which the convention '
      f'on process inputs codes as 1 with uncertainty, so the screen is conservative.</li>')
    a(f'<li><b>Independent AI audit.</b> A stratified sample of {aud["items"]} pairs (by how the code was reached: '
      f'AI-coded pairs by input section, textile-rule pairs by rule, HS2012 pairs, and copies by origin) was coded by '
      f'two new AI sessions (Claude and Codex) that saw only the rules and the pairs. They '
      f'agree with each other on {p1(bt["agree_unweighted"])} of pairs (kappa {bt["kappa_unweighted"]:.2f}). August '
      f'reviewed the {rc["2 auditors disagree"] + rc["1 auditors agree, final differs"]} pairs where the auditors disagree '
      f'with each other ({rc["2 auditors disagree"]}) or both disagree with the final code '
      f'({rc["1 auditors agree, final differs"]}). The true values of 16 sampled pairs were updated: 15 by the '
      f'conventions of 30 October (8 of them Professor Zhang’s own examples) and 1 by the rule on finished accessories '
      f'(scarf → jacket = 0).</li></ul>')
    a(f'<p class="cap">Table 4. Accuracy of the final codes ({aud["items"]} audited pairs, weighted by stratum size; 95% '
      f'intervals)</p>')
    a(table(['', 'By pairs', 'By rows'],
            [['DV, final (31 October)', ci(after['DV']['pair_weighted']), ci(after['DV']['record_weighted'])],
             ['DV, draft of 28 October, same true values', p1(DRAFT_ACC['pair']), p1(DRAFT_ACC['record'])],
             ['DV_strict, final', ci(after['DV_strict']['pair_weighted']), ci(after['DV_strict']['record_weighted'])]],
            widths=['46%', '27%', '27%']))
    a(table(['DV by rows'] + names,
            [['Final'] + [p1(after['DV'][f'records_{p}']['est']) for p, _ in PTAS]], widths=['26%'] + [''] * 5))
    wrong = after['DV_wrong_by_family']
    a(f'<p class="note">{sum(wrong.values())} sampled pairs remain wrong in DV: 5 complete machines built into another '
      f'good that both AI coders coded 0 (convention 4 has not been applied to pairs coded 0), 6 one-sided 1s the screen '
      f'kept, 1 other HS2012 pair, and 2 copies of PTA 1–5, which are not re-judged. Six sampled pairs were set to 0 '
      f'directly because both auditors coded them 0; counting them as errors gives {p1(NO_PROF0_ACC["pair"])} by pairs '
      f'and {p1(NO_PROF0_ACC["record"])} by rows. DV_strict is lower because many pairs whose true value is 1 are coded '
      f'1 with uncertainty. This is an AI audit reviewed by a research assistant, not an expert hand-coding.</p>')

    a('<h2>6. Revisions of 28–31 October 2026</h2><p class="cap">Table 5. DV = 1 and uncertain rows by version</p>')
    rows = [[nm, n(S[p]['d_DV1']), n(S[p]['DV1']), n(S[p]['d_DVs']), n(S[p]['DVs']), n(S[p]['d_unc']),
             n(S[p]['unc'])] for p, nm in PTAS]
    rows.append(bold(['Total', n(T['d_DV1']), n(T['DV1']), n(T['d_DVs']), n(T['DVs']), n(T['d_unc']), n(T['unc'])]))
    a(table(['Agreement', 'DV = 1, 28 Oct', 'DV = 1, final', 'DV_strict = 1, 28 Oct', 'DV_strict = 1, final',
             'Uncertain, 28 Oct', 'Uncertain, final'], rows))
    m, c = C['master'], C['concord']
    a(f'<ul><li><b>28 October (draft):</b> coded under the conventions of 19 October. The Turkey–Singapore draft also '
      f'had {n(tur["records_deleted_not_hs6_input"])} rows with input “WO” or “any” and no code; they are excluded from '
      f'the figures above.</li>')
    a(f'<li><b>31 October (final):</b> the decisions of 28 October (screen of one-sided 1s, deletion of “WO” and “any”, '
      f'chapter 59) and Professor Zhang’s questionnaire answers of 30 October, applied to the newly coded pairs. Against '
      f'the draft, {n(m["up"])} HS2002 pairs went from 0 to 1, {n(m["down"])} from 1 to 0, and {n(m["flag"])} changed only '
      f'their uncertain flag (HS2012 pairs: {c["up"]}, {c["down"]} and {c["flag"]}). The share of rows with DV = 1 moved '
      f'from {pct(T["d_DV1"], T["d_rows"])} to {pct(T["DV1"], T["rows"])}; DV_strict from {pct(T["d_DVs"], T["d_rows"])} '
      f'to {pct(T["DVs"], T["rows"])}, mainly because convention 2 turned {n(C["conv2_pairs"])} pairs '
      f'({n(C["conv2_rows"])} rows) of certain 1s into 1s with uncertainty. Oman–US is unchanged because all its pairs '
      f'are copies of PTA 1–5.</li></ul>')

    a('<h2>7. Notes</h2><ul>')
    a(f'<li><b>Scope.</b> Codes delivered for PTA 1–5 are not re-judged (Professor Zhang, 30 October), and pairs copied '
      f'from them keep their codes: {pct(T["rows"] - T["new"], T["rows"])} of the rows here. The conventions of 30 '
      f'October therefore change only the newly coded pairs.</li>')
    a('<li><b>Applied in part.</b> Generic process-input claims became 0 only through the screen of one-sided 1s (and, '
      'for sampled pairs both auditors coded 0, through the exception in section 5). The '
      'conventions that could raise a 0 to 1 (complete machines, cut or refitted goods, associated minerals recovered '
      'from an ore, crushed goods as filler, waste of a component) were not applied to pairs both coders had coded 0. '
      'Distinctions between a certain 1 and a 1 with '
      'uncertainty were not re-judged pair by pair; they apply to future coding and affect only DV_strict.</li>')
    a('<li><b>To be confirmed by Professor Zhang.</b> DV as the main variable, with DV_strict as a robustness check. '
      'Whether the complete machines built into another good that both AI coders coded 0 (6,733 HS2002 pairs) are '
      're-reviewed under convention 4. '
      'Three extensions of his answers: thermosets and other non-meltable plastics are 0; rubbers in primary forms only '
      'to the same polymer; no laminate route between different plastics (“other plastics” also count as a polymer of '
      'their own). Also: which convention applies where metal articles (convention 2) and remelting into a finished '
      'product (convention 3) overlap (convention 2 for now).</li>')
    a(f'<li>concord_flag = 1 marks {n(S["TUR_SGP"]["concord_flag"])} Turkey–Singapore rows whose HS2012 code is not '
      f'one-to-one with HS2002, and {n(S["CHL_KOR"]["concord_flag"])} Chile–Korea rows with an invalid code (610340, '
      f'610344, 610345), mapped to every HS2002 subheading of 6103.4. The HS concordance will follow the project’s '
      f'conversion package once it is adopted.</li>')
    a('<li>The AI coders are Claude (Anthropic) and Codex (OpenAI); their codes and one-sentence reasons are kept in '
      'dv_ai1, dv_ai2, why_ai1 and why_ai2 where they coded the pair.</li></ul>')
    a('</body></html>')
    return '\n'.join(h), T


def variables(S, X):
    rows = ''.join(f'<tr><td class="v">{p}_coded_2026_10_31.dta</td><td>{nm}</td><td class="n">{n(S[p]["rows"])}</td></tr>'
                   for p, nm in PTAS)
    total = sum(S[p]['rows'] for p, _ in PTAS)
    reasons = ''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in [
        ('AI coders, or the model and the textile rules, disagree', 'One AI coder found a production route and the '
         'other did not (or the model and the textile rules disagreed), no convention settles the pair, and the screen '
         'did not find the 1 clearly invalid'),
        ('AI coders disagree: sibling or backward', 'One coder saw two intermediate siblings, the other a reverse '
         '(backward) pair'),
        ('same-material intermediate of another heading, or another compound (convention of 2026-10-30)', 'Parts or '
         'metal articles of another heading or material, or another compound of the same chemical heading, linked only '
         'as same-material intermediates'),
        ('remelting into another primary or semi-finished form (convention of 2026-10-30)', 'Remelted or re-processed '
         'into another primary or semi-finished form of the same material (not the input’s own upstream form)'),
        ('remelting excluded (convention of 2026-10-30), another route possible', 'The remelting route is excluded, but '
         'a screen named another specific route (component, ingredient, forward)'),
        ('minor constituent of a garment or made-up: other fibre or construction', 'Yarn or fabric of a fibre other '
         'than cotton or man-made fibres (wool, silk, flax, ramie, coarse hair, other), or of the same fibre but another '
         'construction (woven ↔ knitted), in a garment or made-up article'),
        ('minor constituent of a yarn or fabric: other fibre', 'Fibre, yarn or waste of a fibre other than cotton or '
         'man-made fibres as a minor blend component of a yarn or fabric'),
        ('open case in the ASEAN-Japan labels', 'Left open in the original ASEAN–Japan hand coding (route = '
         'unresolved); copied'),
        ('HS concordance: the HS2002 pairs of this record differ', 'The row maps to several HS2002 pairs whose DV '
         'differ; the row takes DV = 1'),
        ('possible feed (rock lobster)', 'Crustaceans or crustacean meal → rock lobster: a possible but not '
         'established feed use')])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Variables of the PTA 6–10 Files</title>
{CSS.format(foot='Variables of the coded PTA 6–10 files · 31 October 2026')}
</head><body>

<h1>Variables of the Coded PTA 6–10 Files</h1>
<p class="lead">31 October 2026 · August Liu. The coding rules are in the workflow document; results are in the
result report.</p>

<h2>Files</h2>
<table>
<tr><th style="width:42%">File</th><th>Agreement</th><th class="n">Rows</th></tr>
{rows}
<tr><td><b>Total</b></td><td></td><td class="n"><b>{n(total)}</b></td></tr>
</table>
<p>One row is one (restricted input, output) pair from the agreement’s product-specific rules of origin, in the order
of the original files. Turkey–Singapore is in HS2012; the other four are in HS2002. Every pair is coded on HS2002
(input_hs2002, output_hs2002). The files share 36 variables, each with a Stata label; Turkey–Singapore has one more,
special_rule, from its original file. They can be combined with <code>append</code>, which widens string variables
as needed:</p>
<pre>use TUR_SGP_coded_2026_10_31, clear
foreach p in NIC_TWN CHL_KOR OMN_USA CAN_CHL {{
    append using `p'_coded_2026_10_31
}}</pre>
<p>A pair (master_id) has the same DV in every agreement where it appears, and the same DV as in the PTA 1–5 files.
{n(X['multi_rows'])} rows map to several HS2002 pairs. The {n(X['multi_rows'] - X['concord_multi'])} coded on HS2002 take the highest DV among their
pairs; the other {n(X['concord_multi'])} are Turkey–Singapore rows coded directly on their HS2012 codes. So {n(X['zero_inside'])}
HS2002 pairs with DV = 0 fall inside such a row with DV = 1; {n(X['zero_inside_own'])} of them are also coded 0 on rows of
their own.</p>

<h2>Variables</h2>
<table>
<tr><th style="width:19%">Variable</th><th style="width:9%">Type</th><th>Contents</th></tr>
<tr><td class="v">output_hs6</td><td>str6</td><td>Output, 6-digit code in the agreement’s HS vintage (the original output_str)</td></tr>
<tr><td class="v">output_description</td><td>strL</td><td>Output: heading text | subheading text, in the agreement’s HS vintage</td></tr>
<tr><td class="v">input_hs6</td><td>str6</td><td>Restricted input, 6-digit code in the agreement’s HS vintage (the original input_str)</td></tr>
<tr><td class="v">input_description</td><td>strL</td><td>Input: heading text | subheading text</td></tr>
<tr><td class="v">VA_Alternative, VA_Complement</td><td>byte</td><td>From the original agreement file, unchanged</td></tr>
<tr><td class="v">special_rule</td><td>byte</td><td>Turkey–Singapore only: from the original file, unchanged</td></tr>
<tr><td class="v">pta</td><td>str</td><td>Agreement: TUR_SGP, NIC_TWN, CHL_KOR, OMN_USA, CAN_CHL</td></tr>
<tr><td class="v">record_no</td><td>long</td><td>Row number in the original file</td></tr>
<tr><td class="v">pair_id</td><td>str</td><td>Unique row id: pta|input&gt;output|record_no</td></tr>
<tr><td class="v">hs_vintage</td><td>str</td><td>HS vintage of input_hs6 and output_hs6 (HS2012 for TUR_SGP, HS2002 for the others)</td></tr>
<tr><td class="v">input_type</td><td>str</td><td>hs6 for every row (rows whose input was “WO” or “any” were deleted)</td></tr>
<tr><td class="v">input_hs2002, output_hs2002</td><td>str</td><td>The codes mapped to HS2002; several codes are separated by “;”</td></tr>
<tr><td class="v">n_mapped_pairs</td><td>int</td><td>Number of HS2002 pairs the row maps to (1 for most rows)</td></tr>
<tr><td class="v">mapped_DV1_share</td><td>double</td><td>Share of those HS2002 pairs with DV = 1</td></tr>
<tr><td class="v">concord_flag</td><td>byte</td><td>1 = a code is not one-to-one with HS2002, or not a valid code ({n(S['TUR_SGP']['concord_flag'])} TUR_SGP rows, {n(S['CHL_KOR']['concord_flag'])} CHL_KOR rows)</td></tr>
<tr><td class="v">concord_note</td><td>strL</td><td>Type of the concordance link, e.g. “input HS2012 n to 1”, “output invalid code: all HS2002 subheadings of 61034”; empty when one-to-one</td></tr>
<tr><td class="v"><b>DV</b></td><td>byte</td><td><b>Main variable.</b> 1 = the input can be used to make the output (including links that are possible but unconfirmed, marked uncertain); 0 = no link</td></tr>
<tr><td class="v">DV_strict</td><td>byte</td><td>Robustness version: DV × (1 − uncertain), only certain links</td></tr>
<tr><td class="v">DV_excl_remelt</td><td>byte</td><td>Robustness version: as DV, but direct remelting (route = recycle_direct, e.g. steel rod → steel ingots) = 0, per HS2002 pair; a row coded on HS2002 that maps to several HS2002 pairs takes the highest value among them (so 3 TUR_SGP rows shown as recycle_direct keep 1, because another of their pairs has another route); the 591 TUR_SGP rows coded on their HS2012 codes are coded directly</td></tr>
<tr><td class="v">DV_max</td><td>byte</td><td>Same as DV (kept for older code)</td></tr>
<tr><td class="v">uncertain</td><td>byte</td><td>1 = kept at DV = 1, but the link is possible rather than known; the reason is in uncertain_reason</td></tr>
<tr><td class="v">uncertain_reason</td><td>strL</td><td>Why uncertain = 1 (list below); empty when uncertain = 0</td></tr>
<tr><td class="v">locked</td><td>byte</td><td>1 = locked at workflow step 2 as the same good (most, not all, rows with route = same_good)</td></tr>
<tr><td class="v">step</td><td>double</td><td>Workflow step that set DV = 0: 3 unrelated goods, 4 parallel finished goods, 5 reverse direction, 6 no route; 2 = same good, certain (route = same_good, uncertain = 0); missing when DV = 1 through another route, or when a same_good pair is uncertain</td></tr>
<tr><td class="v">route</td><td>str</td><td>Why the pair is 1, or none (list below)</td></tr>
<tr><td class="v">source</td><td>str</td><td>How the code was obtained (list below)</td></tr>
<tr><td class="v">copy_from</td><td>str</td><td>For copies: ASEAN_JPN (ASEAN–Japan labels) or PTA_2_5 (Brunei–Japan, Australia–US, CAFTA, Bahrain–US); empty otherwise</td></tr>
<tr><td class="v">policy</td><td>strL</td><td>Decisions and conventions that changed the pair, separated by “;” (list below); empty when none did</td></tr>
<tr><td class="v">ml_prob</td><td>double</td><td>Model probability that DV = 1 (information only); filled for the newly coded HS2002 pairs (source ai_units, ai_sample, rule_textile, rule), missing for copies of PTA 1–5 and for ai_concord</td></tr>
<tr><td class="v">ml_supported</td><td>double</td><td>1 = the model had enough similar coded pairs to be used (information only); filled for the same rows as ml_prob</td></tr>
<tr><td class="v">dv_ai1, dv_ai2</td><td>double</td><td>Code of AI coder 1 (Claude) and AI coder 2 (Codex) where they coded the pair; otherwise missing</td></tr>
<tr><td class="v">why_ai1, why_ai2</td><td>strL</td><td>The two AI coders’ one-sentence reasons</td></tr>
<tr><td class="v">master_id</td><td>str</td><td>Id of the HS2002 input–output pair (M|input&gt;output), the same in every agreement and in the PTA 1–5 files; HS2012|input&gt;output for pairs coded on HS2012 codes. Of the {n(X['multi_rows'])} rows that map to several HS2002 pairs, the {n(S['TUR_SGP']['multi_rep'] + S['CHL_KOR']['multi_rep'])} coded on HS2002 ({n(S['TUR_SGP']['multi_rep'])} TUR_SGP, {n(S['CHL_KOR']['multi_rep'])} CHL_KOR) have as master_id one of those pairs, whose DV equals the row’s DV; the other {n(X['concord_multi'])} TUR_SGP rows are coded on their HS2012 codes (master_id HS2012|…)</td></tr>
</table>

<h2>Values of route</h2>
<table>
<tr><th style="width:24%">Value</th><th>Meaning</th></tr>
<tr><td class="v">same_good</td><td>Same good, or the same good further processed or packed (step 2 when certain; mostly locked)</td></tr>
<tr><td class="v">forward</td><td>The input is an earlier stage of the output (e.g. yarn → fabric of the same fibre)</td></tr>
<tr><td class="v">ingredient</td><td>The input goes into the output as an ingredient, constituent or process input</td></tr>
<tr><td class="v">component</td><td>The input is a part of the output (e.g. nibs → pens, trims → garments)</td></tr>
<tr><td class="v">mixture</td><td>The input is one component of a mixture or blend</td></tr>
<tr><td class="v">sibling_intermediate</td><td>Two intermediate goods of the same material</td></tr>
<tr><td class="v">recycle_waste</td><td>Through a waste or scrap good</td></tr>
<tr><td class="v">recycle_direct</td><td>Direct remelting or re-processing with no scrap code in between (0 in DV_excl_remelt, per HS2002 pair)</td></tr>
<tr><td class="v">feed</td><td>The input feeds a farmed animal (e.g. feed fish → farmed salmon)</td></tr>
<tr><td class="v">reconstitute</td><td>The output is the input reconstituted (e.g. dried → liquid egg albumin)</td></tr>
<tr><td class="v">ml_forward, ml_ingredient, ml_component, ml_recycle, ml_sibling</td><td>Copied textile pairs kept at 1 by the model and confirmed by the textile rules in PTA 2–5; the route predicted by the model</td></tr>
<tr><td class="v">unresolved</td><td>Open case in the ASEAN–Japan labels (DV = 1, uncertain = 1)</td></tr>
<tr><td class="v">none</td><td>No link (DV = 0)</td></tr>
</table>

<h2>Values of source</h2>
<table>
<tr><th style="width:24%">Value</th><th>Meaning</th></tr>
<tr><td class="v">exact_copy</td><td>Copied from the PTA 1–5 codes (same HS2002 pair); copy_from says from which</td></tr>
<tr><td class="v">ai_units, ai_sample</td><td>The two AI coders (Claude and Codex): heading-pair units, and a blind sample of textile pairs</td></tr>
<tr><td class="v">ai_concord</td><td>TUR_SGP rows where two HS2012 codes fall into the same HS2002 code: coded by the two AI coders on the HS2012 codes</td></tr>
<tr><td class="v">rule_textile</td><td>Explicit textile rules (chapters 50–63)</td></tr>
<tr><td class="v">rule</td><td>Input and output have the same code</td></tr>
</table>

<h2>Values of uncertain_reason</h2>
<table>
<tr><th style="width:40%">Value</th><th>Meaning</th></tr>
{reasons}
</table>

<h2>Values of policy</h2>
<p class="note">Conventions of 19 October 2026 (on copied pairs, as in the PTA 1–5 files; P_Q1_1 and P_Q4 also mark
newly coded pairs, where the conventions of 30 October then refine them: P_Q2C or P_2CFLAG after P_Q1_1, mostly P_Q3E_*
after P_Q4) and of 28–30 October 2026 (on newly coded pairs only); see the summary table of the workflow document.</p>
<table>
<tr><th style="width:14%">Value</th><th>Convention</th></tr>
<tr><td class="v">P_Q1_1</td><td>Intermediate goods of the same material at the same stage = 1 (pairs on which the AI coders disagreed)</td></tr>
<tr><td class="v">P_Q1_2</td><td>Different synthetic fibres count as one fibre</td></tr>
<tr><td class="v">P_Q2_1</td><td>Any chemical (chapters 28–38) → wastes of heading 3825 = 1</td></tr>
<tr><td class="v">P_Q2_2</td><td>Any mineral of chapter 25 → cement (2523) = 1</td></tr>
<tr><td class="v">P_Q4</td><td>Direct remelting = 1 in DV (route recycle_direct), before the limits of 30 October</td></tr>
<tr><td class="v">P_CONF, P_UNC</td><td>Copied textile pairs where the model and the textile rules disagreed (P_CONF), or kept at 1 and marked uncertain as a minor constituent (P_UNC)</td></tr>
<tr><td class="v">P_AUD_A, P_AUD_B, P_AUD_C</td><td>Audit corrections of 19 October: minor fibres in yarn or fabric = 1 with uncertainty; intermediate goods of one material coded 0 by both coders = 1; sewing thread ↔ yarn = 1</td></tr>
<tr><td class="v">P_OPT2</td><td>Cotton or man-made fibre, yarn, fabric or waste as a minor constituent = 1 (certain)</td></tr>
<tr><td class="v">P_FISH</td><td>Fish and other seafood of different species = 0 (step 3), unless the input could feed the output</td></tr>
<tr><td class="v">P_Q3E_own</td><td>Remelting back to the input’s own upstream form = 1 (30 October)</td></tr>
<tr><td class="v">P_Q3E_other</td><td>Remelting into another primary or semi-finished form of the same material = 1 with uncertainty</td></tr>
<tr><td class="v">P_Q3E_0</td><td>Remelting into a finished product, vulcanised rubber, different or non-meltable polymers = 0</td></tr>
<tr><td class="v">P_RESCUE</td><td>A P_Q3E_0 pair with another specific route = 1 with uncertainty</td></tr>
<tr><td class="v">P_Q2C, P_Q2C_same</td><td>Parts and metal articles of another heading or material, or another compound of one heading = 1 with uncertainty (P_Q2C); metal articles of one heading and metal = 1 (P_Q2C_same)</td></tr>
<tr><td class="v">P_2CFLAG</td><td>Uncertain flag only: different compounds of one heading claimed as intermediates, and same-material intermediates that P_Q1_1 had made certain</td></tr>
<tr><td class="v">P_Q5B</td><td>Swine meat, offal and fat → pig bristles = 0 (parallel by-product)</td></tr>
<tr><td class="v">P_A1</td><td>One-sided 1 that both model families found clearly invalid = 0</td></tr>
<tr><td class="v">P_PROF0</td><td>Both independent auditors coded 0, in a class where Professor Zhang said such pairs are 0</td></tr>
</table>

</body></html>'''


def main():
    pol = json.load(open(FINAL / 'policy_report.json'))
    comb = json.load(open(FINAL / 'combine_report.json'))
    aud = json.load(open(FINAL / 'ai_audit_report.json'))
    scr = json.load(open(HERE.parent / 'coded' / 'screen_report.json'))
    assert aud['after_August_review']['complete'] and not aud['after_August_review']['stale']
    S, A = load()
    X, C = cross(A), changes()
    for p, _ in PTAS:
        q = pol['pta'][p]
        assert (q['records'], q['DV1'], q['DV_strict1'], q['uncertain']) == (S[p]['rows'], S[p]['DV1'], S[p]['DVs'],
                                                                             S[p]['unc'])
    html, T = results(S, X, C, pol, comb, aud, scr)
    (HERE / f'Results_PTA_6_10_{DATE}.html').write_text(html, encoding='utf-8')
    (HERE / f'Variables_PTA_6_10_{DATE}.html').write_text(variables(S, X), encoding='utf-8')
    rows = []
    for p, nm in PTAS:
        s = S[p]
        r = dict(pta=p, agreement=nm.replace('–', '-'), rows=s['rows'], DV1=s['DV1'], DV1_share=round(s['DV1'] / s['rows'], 4),
                 DV_strict1=s['DVs'], DV_excl_remelt1=s['DVx'], uncertain=s['unc'],
                 uncertain_share_of_DV1=round(s['unc'] / s['DV1'], 4), newly_coded_rows=s['new'],
                 DV1_draft_2026_10_28=s['d_DV1'], uncertain_draft_2026_10_28=s['d_unc'])
        r.update({f'uncertain: {k}': s['reasons'].get(k, 0) for k, _ in REASONS})
        r.update({f'method: {lab}': s['src'][i] for i, (lab, _) in enumerate(SOURCES)})
        rows.append(r)
    pd.DataFrame(rows).to_csv(HERE / 'summary_by_pta.csv', index=False)
    print(json.dumps(dict(T=T, cross=X, changes=C), indent=1))


if __name__ == '__main__':
    main()
