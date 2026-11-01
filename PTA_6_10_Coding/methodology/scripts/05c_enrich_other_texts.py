"""Inputs v2 for the second Codex run: give every bare "Other" subheading its context.

The round-1 check (Codex_round1_check_2026_10_27.md) found 160 rows where Codex read two different "Other"
subheadings (e.g. 284169 and 284190, both shown as "Other") as the same good. The HS files have no text for 5-digit
groups, so a bare "Other" is described by what it excludes: the other subheadings of its 5-digit group (level 2,
"- --") or of its heading (level 1, "- -"), e.g.
  284169: Other [salts of heading 2841, group 2841.6x, other than: potassium permanganate]
Only the descriptions change; unit ids, item ids, rows, order and worked examples are those of ai_coders/input/, so
04_check_coder_files.py (which reads ai_coders/input/) checks v2 outputs unchanged.
Output: ai_coders/input_v2/*.csv (same file names).

Run: /usr/local/bin/python3 _work/05c_enrich_other_texts.py
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import AI, REF  # noqa: E402

MAX_SIB = 8


def clean(t):
    return re.sub(r'^\d+\s*-\s*', '', t).lstrip('- ').strip()


class Context:
    def __init__(self, ed):
        raw = {x['id']: x['text'] for x in json.load(open(REF / f'{ed}.json'))['results']}
        self.raw = raw
        self.txt = {k: clean(v) for k, v in raw.items()}
        self.leaves = sorted(k for k in raw if len(k) == 6 and k.isdigit())

    def bare(self, c):
        return bool(re.fullmatch(r'(?i)other\.?', self.txt.get(c, '')))

    def describe(self, c):
        t = self.txt.get(c, '')
        if not self.bare(c):
            return t
        level2 = bool(re.match(r'^\d{6}\s*-\s*--', self.raw[c]))
        key = c[:5] if level2 else c[:4]
        sib = [k for k in self.leaves if k[:len(key)] == key and k != c and not self.bare(k)]
        head = self.txt.get(c[:4], '').rstrip('.')
        head = head if len(head) <= 70 else head[:67] + '...'
        names = [self.txt[k] if len(self.txt[k]) <= 50 else self.txt[k][:47] + '...' for k in sib[:MAX_SIB]]
        more = f' and {len(sib) - MAX_SIB} more' if len(sib) > MAX_SIB else ''
        grp = f', group {c[:4]}.{c[4]}x' if level2 else ''
        return (f'Other [{head}{grp}, other than: {"; ".join(names)}{more}]' if names
                else f'Other [{head}{grp}]')


def code_list(s, ctx):
    out = []
    for part in s.split(' ; '):
        code = part.split(':', 1)[0].strip()
        out.append(f'{code}: {ctx.describe(code)}' if ctx.bare(code) else part)
    return ' ; '.join(out)


def pair_desc(desc, code, ctx):
    if not ctx.bare(code):
        return desc
    head = desc.rsplit(' | ', 1)[0] if ' | ' in desc else ''
    return f'{head} | {ctx.describe(code)}' if head else ctx.describe(code)


def main():
    src, dst = AI / 'input', AI / 'input_v2'
    dst.mkdir(exist_ok=True)
    h2, h4 = Context('H2'), Context('H4')
    n = 0
    for f in sorted(src.glob('*.csv')):
        d = pd.read_csv(f, dtype=str, keep_default_na=False)
        ctx = h4 if f.stem == 'concord_pairs' else h2
        before = d.copy()
        if f.stem.startswith('units'):
            d['input_codes'] = d.input_codes.map(lambda s: code_list(s, ctx))
            d['output_codes'] = d.output_codes.map(lambda s: code_list(s, ctx))
        else:
            d['input_description'] = [pair_desc(x, c, ctx) for x, c in zip(d.input_description, d.input_hs6)]
            d['output_description'] = [pair_desc(x, c, ctx) for x, c in zip(d.output_description, d.output_hs6)]
        assert d.shape == before.shape and (d.iloc[:, 0] == before.iloc[:, 0]).all()
        n += int((d != before).any(axis=1).sum())
        d.to_csv(dst / f.name, index=False)
    print(f'rows with an enriched "Other": {n}; files written to {dst}')


if __name__ == '__main__':
    main()
