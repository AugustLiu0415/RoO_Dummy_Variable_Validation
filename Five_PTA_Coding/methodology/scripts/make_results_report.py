"""Build the five-PTA result report (HTML, printed to PDF with Chrome) from the final files.

Reads final/<PTA>_coded_2026_10_19.csv, final/policy_report.json, final/combine_report.json,
final/ai_audit_report.json (and the pre-correction audit in final_v3_2026_10_19_pre_audit/), _work/coded/textile_rules.json
and the version sent on 19 October (final_v4_2026_10_19_sent/). Writes Results_5_PTAs_2026_10_19_v2.html next to
this script.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FINAL = ROOT / 'final'
PTAS = [('ASEAN_JPN', 'ASEAN–Japan'), ('BRN_JPN', 'Brunei–Japan'), ('AUS_USA', 'Australia–US'), ('CAFTA', 'CAFTA'),
        ('BHR_USA', 'Bahrain–US')]
REASONS = [('minor constituent of a garment or made-up: other fibre or construction',
            'Minor constituent of a garment or made-up: other fibre (not cotton or man-made) or other construction'),
           ('minor constituent of a yarn or fabric: other fibre',
            'Minor constituent of a yarn or fabric: other fibre (not cotton or man-made)'),
           ('AI coders, or the model and the textile rules, disagree',
            'The two AI coders (or the model and the textile rules) disagree'),
           ('AI coders disagree: sibling or backward', 'The two AI coders disagree: intermediate sibling or backward'),
           ('open case in the ASEAN-Japan labels', 'Open case in the ASEAN–Japan labels'),
           ('possible feed (rock lobster)', 'Possible feed (crustaceans → rock lobster)')]
SOURCES = [('ASEAN–Japan labels (hand-coded, revised)', ['pta1_label']),
           ('Copied from ASEAN–Japan (step 7a)', ['exact_copy']),
           ('Textile rules (step 7e)', ['rule_textile']),
           ('Two AI coders (steps 2–6)', ['ai_units', 'ai_units_ml_reroute', 'ai_sample']),
           ('Model, confirmed by the textile rules (step 7c)', ['ml']),
           ('Self-pairs (step 2)', ['rule']),
           ('Model and textile rules disagree (step 7d)', ['conflict_rule', 'conflict_ml', 'conflict_unresolved'])]


def n(x):
    return f'{x:,}'


def pct(a, b):
    return f'{100 * a / b:.1f}%'


def table(head, rows, num_from=1, widths=None):
    w = widths or [''] * len(head)
    h = ''.join(f'<th class="{"n" if i >= num_from else ""}" style="{f"width:{w[i]}" if w[i] else ""}">{c}</th>'
                for i, c in enumerate(head))
    b = ''.join('<tr>' + ''.join(f'<td class="{"n" if i >= num_from else ""}">{c}</td>' for i, c in enumerate(r))
                + '</tr>' for r in rows)
    return f'<table><tr>{h}</tr>{b}</table>'


def main():
    pol = json.load(open(FINAL / 'policy_report.json'))
    comb = json.load(open(FINAL / 'combine_report.json'))
    aud = json.load(open(FINAL / 'ai_audit_report.json'))
    aud0 = json.load(open(ROOT / 'final_v3_2026_10_19_pre_audit' / 'ai_audit_report.json'))
    trules = json.load(open(HERE.parent / 'coded' / 'textile_rules.json'))
    S, frames = {}, []
    for p, _ in PTAS:
        d = pd.read_csv(FINAL / f'{p}_coded_2026_10_19.csv', dtype=str, keep_default_na=False,
                        usecols=['input_hs6', 'output_hs6', 'DV', 'DV_strict', 'DV_excl_remelt', 'uncertain',
                                 'uncertain_reason', 'source', 'route'])
        sent = pd.read_csv(ROOT / 'final_v4_2026_10_19_sent' / f'{p}_coded_2026_10_19.csv', dtype=str,
                           keep_default_na=False, usecols=['DV', 'uncertain'])
        tex = d.input_hs6.str[:2].between('50', '63') & d.output_hs6.str[:2].between('50', '63')
        S[p] = {'rows': len(d), 'dv1': int((d.DV == '1').sum()), 'strict': int((d.DV_strict == '1').sum()),
                'excl': int((d.DV_excl_remelt == '1').sum()), 'unc': int((d.uncertain == '1').sum()),
                'reasons': d[d.uncertain == '1'].uncertain_reason.value_counts().to_dict(),
                'source': d.source.value_counts().to_dict(), 'tex': int(tex.sum()),
                'dv1_v2': pol['pta'][p]['DV1_v2'], 'unc_v2': pol['pta'][p]['uncertain_v2'],
                'dv1_sent': int((sent.DV == '1').sum()), 'unc_sent': int((sent.uncertain == '1').sum())}
        frames.append(d[['input_hs6', 'output_hs6', 'DV', 'uncertain', 'route', 'uncertain_reason']].assign(pta=p))
    allp = pd.concat(frames, ignore_index=True)
    g = allp.groupby(['input_hs6', 'output_hs6']).agg(k=('pta', 'nunique'), dv=('DV', 'nunique'),
                                                      u=('uncertain', 'nunique'), r=('route', 'nunique'),
                                                      ur=('uncertain_reason', 'nunique'))
    shared = g[g.k > 1]
    diff = int(((shared.dv > 1) | (shared.u > 1) | (shared.r > 1) | (shared.ur > 1)).sum())
    master = comb['master']
    total_rows = sum(S[p]['rows'] for p, _ in PTAS)

    t1 = table(['Agreement', 'Rows', 'DV = 1', 'Share', 'DV_strict = 1', 'DV_excl_remelt = 1', 'Uncertain',
                'Uncertain / DV = 1'],
               [[nm, n(S[p]['rows']), n(S[p]['dv1']), pct(S[p]['dv1'], S[p]['rows']), n(S[p]['strict']),
                 n(S[p]['excl']), n(S[p]['unc']), pct(S[p]['unc'], S[p]['dv1'])] for p, nm in PTAS])
    t2 = table(['Reason'] + [nm for _, nm in PTAS],
               [[lab] + [n(S[p]['reasons'].get(key, 0)) for p, _ in PTAS] for key, lab in REASONS]
               + [['<b>Total uncertain</b>'] + [f'<b>{n(S[p]["unc"])}</b>' for p, _ in PTAS]],
               widths=['40%', '', '', '', '', ''])
    t3 = table(['Method'] + [nm for _, nm in PTAS] + ['Unique pairs, four new PTAs'],
               [[lab] + [n(sum(S[p]['source'].get(s, 0) for s in src)) for p, _ in PTAS]
                + [n(sum(master['source'].get(s, 0) for s in src)) if src != ['pta1_label'] else '–']
                for lab, src in SOURCES]
               + [['<b>Total</b>'] + [f'<b>{n(S[p]["rows"])}</b>' for p, _ in PTAS] + [f'<b>{n(master["pairs"])}</b>']],
               widths=['30%', '', '', '', '', '', ''])
    tex_line = ', '.join(f'{nm} {pct(S[p]["tex"], S[p]["rows"])}' for p, nm in PTAS)
    u = comb['units']
    kg = u['kappa_by_input_group']
    rr = comb['ml_reroute_audit']['by_band']
    a1, a0 = aud, aud0
    t4 = table(['Share of pairs where the final code matches …', 'Before corrections', 'After corrections'],
               [['auditor 1 (new Claude session)', pct(a0['claude']['agree_with_final_weighted'], 1),
                 pct(a1['claude']['agree_with_final_weighted'], 1)],
                ['auditor 2 (new Codex session)', pct(a0['codex']['agree_with_final_weighted'], 1),
                 pct(a1['codex']['agree_with_final_weighted'], 1)],
                [f'both auditors, where they agree ({a1["final_vs_auditor_consensus"]["items_where_auditors_agree"]} pairs)',
                 pct(a0['final_vs_auditor_consensus']['final_agrees_weighted'], 1),
                 pct(a1['final_vs_auditor_consensus']['final_agrees_weighted'], 1)],
                ['pairs where both auditors disagree with the final code',
                 str(a0['review_counts']['1 auditors agree, final differs']),
                 str(a1['review_counts']['1 auditors agree, final differs'])]], widths=['56%', '', ''])
    t5 = table(['Agreement', 'DV = 1, 18 Oct', 'DV = 1, 19 Oct (sent)', 'DV = 1, final', 'Uncertain, 18 Oct',
                'Uncertain, 19 Oct (sent)', 'Uncertain, final'],
               [[nm, n(S[p]['dv1_v2']), n(S[p]['dv1_sent']), n(S[p]['dv1']), n(S[p]['unc_v2']), n(S[p]['unc_sent']),
                 n(S[p]['unc'])] for p, nm in PTAS])
    fish = pol['pta1']['policies']['P_FISH_0']['DV_changed']
    us = [100 * S[p]['unc'] / S[p]['dv1'] for p in ('AUS_USA', 'CAFTA', 'BHR_USA')]
    us_lo, us_hi = min(us), max(us)

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>RoO Input–Output Codes for Five PTAs: Results</title>
<style>
@page {{ size: letter; margin: 0.9in 0.8in 0.85in 0.8in;
  @bottom-left {{ content: "RoO input–output codes for five PTAs · results · 19 October 2026"; font: 8pt "Helvetica Neue", Helvetica, Arial, sans-serif; color: #666; }}
  @bottom-right {{ content: counter(page); font: 8pt "Helvetica Neue", Helvetica, Arial, sans-serif; color: #666; }} }}
body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.42; color: #111; }}
h1 {{ font-size: 18pt; margin: 0 0 3pt 0; }}
h2 {{ font-size: 12.5pt; margin: 15pt 0 5pt 0; page-break-after: avoid; }}
p {{ margin: 3pt 0 6pt 0; }}
.lead {{ color: #444; }}
ul {{ margin: 2pt 0 6pt 0; padding-left: 15pt; }}
li {{ margin: 1.5pt 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 4pt 0 6pt 0; font-size: 8.6pt; page-break-inside: avoid; }}
th {{ background: #eef0f3; text-align: left; font-weight: bold; padding: 3.5pt 4.5pt; border-bottom: 1px solid #c8ccd2; vertical-align: bottom; }}
td {{ padding: 3.2pt 4.5pt; border-bottom: 1px solid #dde0e4; vertical-align: top; }}
td.n, th.n {{ text-align: right; }}
td.n {{ white-space: nowrap; }}
.note {{ font-size: 8.8pt; color: #333; }}
.cap {{ font-weight: bold; font-size: 9.5pt; margin: 9pt 0 2pt 0; page-break-after: avoid; }}
</style></head><body>

<h1>RoO Input–Output Codes for Five PTAs: Results</h1>
<p class="lead">19 October 2026 · August Liu. Companion to the coding workflow document (general coding rules) and
the variable explanation file.</p>

<h2>1. Data</h2>
<ul>
<li>Five agreements: ASEAN–Japan, Brunei–Japan, Australia–US, CAFTA and Bahrain–US, all in HS2002. Each row is one
(restricted input, output) pair at HS6 from the agreement’s product-specific rules: {n(total_rows)} rows in all.</li>
<li>One Stata file per agreement (<i>&lt;PTA&gt;_coded_2026_10_19_v2.dta</i>), with the same 29 variables.</li>
<li>The four new agreements contain {n(master['pairs'])} unique pairs; {n(master['source']['exact_copy'])} of them
are also in ASEAN–Japan. Every pair is coded by the rules of the workflow document, so a pair has the same code in
every agreement.</li>
</ul>

<h2>2. Main results</h2>
<p class="cap">Table 1. Input–output links by agreement</p>
{t1}
<p class="note">DV = 1: the input can be used to make the output (main variable). DV_strict counts only certain
links (DV × (1 − uncertain)). DV_excl_remelt sets direct remelting (route = recycle_direct, for example steel rod →
steel ingots) to 0.</p>

<h2>3. Uncertain pairs</h2>
<p class="cap">Table 2. Pairs kept at DV = 1 with uncertain = 1, by reason</p>
{t2}
<p>Most uncertain pairs in the three US agreements are minor constituents: a yarn or fabric of a less common fibre
(wool, silk, flax, ramie, coarse animal hair) in a garment, made-up, yarn or fabric of another fibre, or a fabric of
the same fibre but another construction (woven fabric in a knitted garment). They are frequent there because the
US yarn-forward rules list almost every yarn and fabric as a restricted input of each garment. Textile pairs
(chapters 50–63 on both sides) make up {tex_line} of the rows. Cotton and man-made fibres as minor constituents are
coded as certain links.</p>

<h2>4. How the codes were obtained</h2>
<p class="cap">Table 3. Rows by coding method</p>
{t3}
<p class="note">ASEAN–Japan was coded by hand and revised under the same conventions; it serves as the master list
for exact copies. The model bands were used only for textile pairs confirmed by the textile rules (section 5).
Where the model and the textile rules disagreed, the rule was applied when it found a route; the remaining pairs
were settled with the audited sample.</p>

<h2>5. Reliability</h2>
<ul>
<li><b>Consistency across agreements.</b> {n(len(shared))} pairs appear in two or more agreements; DV, uncertain,
route and uncertain reason are identical in every agreement for all of them ({diff} differences).</li>
<li><b>Two AI coders.</b> Claude and Codex coded {n(u['pairs_both_coders'])} pairs independently (before the scope
conventions of 19 October). They agreed on {pct(u['agreement_pairs'], 1)} (Cohen’s kappa {u['kappa_pairs']:.2f}).
Agreement was high for plant products and fats (kappa {kg['06-15 plant/fats']['kappa']:.2f}) and textiles
({kg['50-67 textile/footwear']['kappa']:.2f}), and low for chemicals ({kg['28-38 chemical']['kappa']:.2f}),
plastics ({kg['39-40 plastic/rubber']['kappa']:.2f}) and food preparations ({kg['16-24 food']['kappa']:.2f}):
mostly the scope questions (intermediate siblings, chemicals → wastes, minerals → cement, possible uses) that the
conventions now settle. Remaining disagreements are kept at DV = 1 with uncertain = 1.</li>
<li><b>Model.</b> With whole chapter pairs held out, the model reaches an AUC of 0.83. On
{n(comb['ml_reroute_audit']['pairs'])} non-textile pairs in its confidence bands, re-coded by both AI coders, the
≥ 0.9 band was right {pct(rr['keep1']['acc_vs_agreed'], 1)} of the time and the ≤ 0.1 band
{pct(rr['turn0']['acc_vs_agreed'], 1)}. The bands were therefore used only for textile pairs confirmed by the rules;
all other band pairs went to the AI coders.</li>
<li><b>Textile rules.</b> On {n(trules['copied_textile_pairs'])} textile pairs that are also in ASEAN–Japan, the rules
agree with the ASEAN–Japan labels for {pct(trules['rule_vs_copied_PTA1_DV_agreement'], 1)} of pairs.</li>
<li><b>Independent AI audit.</b> A stratified sample of {a1['items']} pairs (by source, step and route) was coded by
two new AI sessions that saw only the codebook and the pairs, not any earlier answer. August reviewed every pair
where both auditors disagreed with the final code. The two auditors agree with each other on
{pct(a1['between_auditors']['agree'], 1)} of pairs (kappa {a1['between_auditors']['kappa']:.2f}). Their
disagreements with the final codes showed groups of errors (intermediate siblings coded 0, sewing thread ↔ yarn,
clothing trims → garments, minor yarns in fabrics, fish of different species), which were corrected by rule in all
five agreements.</li>
</ul>
<p class="cap">Table 4. Independent AI audit ({a1['items']} pairs, weighted by stratum size)</p>
{t4}
<p class="note">The after-correction figures are measured on the same sample that revealed the errors, so they
overstate accuracy. Of the {a1['review_counts']['1 auditors agree, final differs']} remaining differences, four are
single pairs coded 0 by both original AI coders (glass smallwares → glass fibres; pickling preparations → fatty
acids; paper-pulp filter blocks → coated paper; coated paper → cigarette paper) and one is already uncertain (pet food
→ oil-cake). This is an AI audit reviewed by a research assistant, not an expert hand-coding.</p>

<h2>6. Revisions of 18–19 October 2026</h2>
<p class="cap">Table 5. DV = 1 and uncertain pairs by version</p>
{t5}
<ul>
<li><b>18 October:</b> first complete coding of the four new agreements.</li>
<li><b>19 October (sent):</b> scope conventions (intermediate siblings, one synthetic fibre, chemicals → wastes,
minerals → cement, possible uses, minor constituents, direct remelting) and the first audit corrections, applied to
all five agreements, including the ASEAN–Japan labels. Pairs only moved from 0 to 1.</li>
<li><b>Final:</b> (i) fish and other seafood of different species are 0 unless the input could feed the output
({n(fish)} ASEAN–Japan pairs moved from 1 to 0, and their copies in the other agreements); (ii) “of other textile
materials” is read as in the HS (every fibre not named in its group), which added a few hundred links in each US
agreement; (iii) cotton and man-made fibres as minor constituents are certain links, which cut the uncertain share
of DV = 1 in the US agreements from about half to {us_lo:.0f}–{us_hi:.0f}%.</li>
</ul>

<h2>7. Notes</h2>
<ul>
<li>ASEAN–Japan pairs left open in the original hand coding (route = unresolved) are kept at DV = 1 with
uncertain = 1, and the same pairs carry the same code in the other agreements.</li>
<li>concord_flag = 1 marks 13 rows with a code that is not a valid HS2002 subheading (290400 in ASEAN–Japan, 640410
in Australia–US).</li>
<li>The AI coders are Claude (Anthropic) and Codex (OpenAI); their codes and one-sentence reasons are kept in
dv_ai1, dv_ai2, why_ai1 and why_ai2 where they coded the pair.</li>
</ul>
</body></html>
"""
    out = HERE / 'Results_5_PTAs_2026_10_19_v2.html'
    out.write_text(html)
    print(out)


if __name__ == '__main__':
    main()
