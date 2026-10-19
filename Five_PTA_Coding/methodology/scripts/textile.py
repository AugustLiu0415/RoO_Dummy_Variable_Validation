"""Textile attributes of HS2002 codes in chapters 50-63 and the rule coding of textile pairs.

The workflow lets steps 2, 4 and 5 be applied by rule, with AI coders checking a sample and the exceptions. PTA 2-5
contain ~175,000 textile pairs (yarn-forward rules of the US agreements) in chapter pairs that PTA_1 never coded,
so the ML model cannot code them; these rules do, and a blind two-coder sample measures their accuracy.

Attributes per code: stage (F fibre, Y yarn, C fabric or industrial textile, T trim, M garment or made-up article,
W waste); fibre identity (specific polymer, plant or animal where the code names one; generic families otherwise);
admixture fibres ('mixed mainly or solely with ...'); knitted; put up for retail sale; parts.
"""
import json
import re
from pathlib import Path

import pandas as pd

H2 = Path(__file__).resolve().parents[3] / 'RoO_Step0/reference_hs/H2.json'

WASTE = {'5003', '5103', '5104', '5202', '5505', '6309', '6310'}
FIBRE = {'5001', '5101', '5102', '5105', '5201', '5203', '5301', '5302', '5303', '5304', '5305', '5501', '5502',
         '5503', '5504', '5506', '5507'}
YARN = {'5002', '5004', '5005', '5006', '5106', '5107', '5108', '5109', '5110', '5204', '5205', '5206', '5207',
        '5306', '5307', '5308', '5401', '5402', '5403', '5404', '5405', '5406', '5508', '5509', '5510', '5511',
        '5604', '5605', '5606', '5607'}
# woven, knitted, pile, nonwoven fabrics and industrial textiles (intermediate goods)
FABRIC = {'5007', '5111', '5112', '5113', '5208', '5209', '5210', '5211', '5212', '5309', '5310', '5311', '5407',
          '5408', '5512', '5513', '5514', '5515', '5516', '5601', '5602', '5603', '5608', '5609', '5801', '5802',
          '5803', '5805', '5809', '5811', '5901', '5902', '5903', '5904', '5905', '5906', '5907', '5908', '5909',
          '5910', '5911', '6001', '6002', '6003', '6004', '6005', '6006'}
TRIM = {'5804', '5806', '5807', '5808', '5810'}           # lace, narrow fabrics, labels, braids, embroidery
FROM_FABRIC = {'5810', '5811', '5901', '5903', '5906', '5907'}   # made by working an existing fabric
SEWING = {'5204', '5401', '5508'}
ACCESSORY = {'611780', '621710'}                        # other made-up clothing accessories (trims, bows)
# rules whose 1s are policy-uncertain (DV 1, uncertain 1): decision 3 and audit group A of 2026-10-19
UNCERTAIN_RULES = {'T_CONSTITUENT', 'T_FORWARD_OTHER_FIBRE', 'T_WASTE_OTHER_FIBRE_MINOR'}
# the same cases with a cotton or man-made input are certain 1 (Prof. Zhang, 2026-10-19, option 2)
COMMON_RULES = {'T_CONSTITUENT_COMMON', 'T_FORWARD_COMMON_FIBRE', 'T_WASTE_COMMON_FIBRE'}

# fibre identities: specific -> generic family
FAMILY = {'nylon': 'syn', 'polyester': 'syn', 'acrylic': 'syn', 'pp': 'syn', 'syn_other': 'syn',
          'viscose': 'art', 'acetate': 'art', 'syn': 'mm', 'art': 'mm',
          'wool': 'woolhair', 'hair_fine': 'woolhair',
          'flax': 'veg', 'hemp': 'veg', 'jute': 'veg', 'veg_other': 'veg', 'sisal': 'veg', 'coir': 'veg', 'abaca': 'veg'}
SPECIFIC = [('nylon', r'nylon|polyamide'), ('polyester', r'polyester'), ('acrylic', r'acrylic'),
            ('pp', r'polypropylene|polyethylene'), ('viscose', r'viscose'), ('acetate', r'acetate'),
            ('flax', r'\bflax'), ('hemp', r'true hemp'), ('jute', r'\bjute|bast fibres'),
            ('sisal', r'sisal|agave'), ('coir', r'\bcoir|coconut'), ('abaca', r'abaca'),
            ('veg_other', r'ramie|paper yarn|vegetable textile'),
            ('woolhair', r'wool or (?:of )?fine animal hair|wool or fine'), ('hair_coarse', r'coarse animal hair|horsehair'),
            ('wool', r'\bwool'), ('hair_fine', r'fine animal hair|kashmir|cashmere'), ('cotton', r'\bcotton'),
            ('silk', r'\bsilk'), ('syn', r'synthetic'), ('art', r'artificial'), ('mm', r'man-made'),
            ('other', r'other textile materials')]
# 5-digit groups whose subheading texts do not name the fibre (HS2002 group headers are missing in H2.json)
GROUP = {'60012': None, '60019': None, '60031': 'wool', '60032': 'cotton', '60033': 'syn', '60034': 'art',
         '60039': 'other', '60051': 'woolhair', '60052': 'cotton', '60053': 'syn', '60054': 'art', '60059': 'other',
         '60061': 'woolhair', '60062': 'cotton', '60063': 'syn', '60064': 'art', '60069': 'other',
         '54074': 'nylon', '54075': 'polyester', '54076': 'polyester', '54077': 'syn', '54078': 'syn',
         '54079': 'syn', '54082': 'art', '54083': 'art', '55121': 'polyester', '55122': 'acrylic', '55129': 'syn_other',
         '55151': 'polyester', '55152': 'acrylic', '55159': 'syn_other', '55161': 'art', '55162': 'art',
         '55163': 'art', '55164': 'art', '55169': 'art', '55091': 'syn_other', '55095': 'polyester',
         '55096': 'acrylic', '55099': 'syn_other', '55011': 'nylon', '55012': 'polyester', '55013': 'acrylic',
         '55019': 'syn_other',
         # added 2026-10-18 after the sample audit: group headers that name the fibre
         '58012': 'cotton', '58013': 'mm', '58021': 'cotton', '56031': 'mm', '56072': 'sisal', '56074': 'pp',
         '56081': 'mm'}
OTHER_OK = {'silk', 'veg', 'flax', 'hemp', 'jute', 'veg_other', 'hair_coarse', 'other'}


def _clean(t):
    return re.sub(r'^\d+\s*-\s*', '', t).lstrip('- ').strip()


def load_texts():
    r = json.load(open(H2))['results']
    return {x['id']: _clean(x['text']) for x in r}


def fibre_of_text(text):
    t = text.lower()
    for f, p in SPECIFIC:
        if re.search(p, t):
            return f
    return None


def code_fibre(c, sub, head):
    ch, h = c[:2], c[:4]
    if ch == '50':
        return 'silk'
    if ch == '52':
        return 'cotton'
    if ch == '51':
        if h == '5101' or c in ('510510', '510521', '510529'):
            return 'wool'
        if c in ('510211', '510219', '510531', '510539', '510310'):
            return 'hair_fine' if c != '510310' else 'woolhair'
        if c in ('510220', '510540', '510330') or h in ('5110', '5113'):
            return 'hair_coarse'
        return 'woolhair'
    if ch == '53':
        m = {'5301': 'flax', '5302': 'hemp', '5303': 'jute', '5304': 'sisal',
             '5306': 'flax', '5307': 'jute', '5309': 'flax', '5310': 'jute', '5311': 'veg_other'}
        if h in m:
            return m[h]
        if h == '5305':                                   # 5305.1 coir, 5305.2 abaca, 5305.90 ramie and other
            return {'53051': 'coir', '53052': 'abaca'}.get(c[:5], 'veg_other')
        return {'530810': 'coir', '530820': 'hemp'}.get(c, 'veg_other')
    if c[:5] in GROUP and GROUP[c[:5]]:
        return GROUP[c[:5]]
    f = fibre_of_text(sub)
    if f and f != 'other':
        return f
    if ch in ('54', '55'):
        hf = fibre_of_text(head)
        if h in ('5401', '5406', '5508', '5505', '5511'):
            return f or hf or 'mm'
        return f or (hf if hf in ('syn', 'art', 'nylon', 'polyester', 'acrylic', 'pp', 'viscose', 'acetate') else
                     ('art' if 'artificial' in head.lower() else 'syn'))
    if f == 'other':
        return 'other'
    return fibre_of_text(head) if fibre_of_text(head) not in (None, 'other') else ('other' if f else 'any')


def other_named(c, T):
    """Fibres named in the sibling subheadings of an 'of other textile materials' code. In the HS this text means
    every fibre not named in its group: 610990 T-shirts of other textile materials include synthetic fibres, because
    only cotton has its own subheading (610910). Siblings: the same 5-digit group, or for a code ending in 0 (a
    one-dash subheading such as 600690) every code of the other 5-digit groups of the heading."""
    sib = [k for k in T if len(k) == 6 and k.isdigit() and k[:4] == c[:4] and k != c
           and (k[:5] == c[:5] if c[5] != '0' else k[4] != c[4])]
    return ';'.join(sorted({code_fibre(k, T.get(k, ''), T.get(k[:4], '')) for k in sib} - {'other', 'any'}))


def attributes(codes, T=None):
    T = T or load_texts()
    rows = []
    for c in sorted(set(codes)):
        h, ch = c[:4], c[:2]
        if not ('50' <= ch <= '63'):
            continue
        sub, head = T.get(c, ''), T.get(h, '')
        stage = ('W' if h in WASTE else 'F' if h in FIBRE else 'Y' if h in YARN else 'C' if h in FABRIC
                 else 'T' if h in TRIM else 'M')
        if c == '530130':
            stage = 'W'
        if c == '580230':                                   # tufted textile fabrics: tufted into a base fabric
            stage = 'C'
        mixed = re.findall(r'mixed (?:mainly or solely )?with ([a-z ,\-]+)', (sub + ' ' + head).lower())
        mix_f = set()
        for m in mixed:
            for f, p in SPECIFIC:
                if re.search(p, m):
                    mix_f.add(f)
        if re.search(r'less than 85 ?%', (sub + ' ' + head).lower()):
            mix_f.add('any')
        fib = code_fibre(c, sub, head)
        rows.append({'code': c, 'stage': stage, 'fibre': fib, 'mixed_with': ';'.join(sorted(mix_f)),
                     'other_named': other_named(c, T) if fib == 'other' else '',
                     'knit': int(ch in ('60', '61') or bool(re.search(r'knitted|crocheted', sub.lower()))
                                 and not re.search(r'not knitted', sub.lower())),
                     'retail': int(bool(re.search(r'(?<!not )put up for retail', (head + ' ' + sub).lower()))),
                     'parts': int(bool(re.search(r'\bparts\b', sub.lower()))),
                     'from_fabric': int(h in FROM_FABRIC or c == '580230'),
                     'text': f'{head} | {sub}'})
    return pd.DataFrame(rows).set_index('code')


def _covers(g, s):
    """generic fibre g covers specific fibre s"""
    while s in FAMILY:
        s = FAMILY[s]
        if s == g:
            return True
    return False


def _synthetic(f):
    return f == 'syn' or FAMILY.get(f) == 'syn'


def common_fibre(f):
    """Cotton and man-made fibres, the usual blend partners, linings and pocketing of goods of other fibres. As a
    minor constituent they give a certain 1 (Prof. Zhang, 2026-10-19, option 2); other fibres stay 1, uncertain."""
    return f == 'cotton' or f in ('syn', 'art', 'mm') or FAMILY.get(f) in ('syn', 'art', 'mm')


def fibre_compatible(fi, fo, mix_o=''):
    """Can a good of fibre fi be the main material of a good of fibre fo (or a named admixture of it)?
    Different synthetic polymers (nylon, polyester, acrylic, polypropylene, other) count as one fibre: decision of
    Prof. Zhang, 2026-10-19 (question 1-2, as in the ASEAN-Japan data)."""
    if 'any' in (fi, fo) or fi == fo or _covers(fi, fo) or _covers(fo, fi):
        return True
    if _synthetic(fi) and _synthetic(fo):
        return True
    if fo == 'other' and (fi in OTHER_OK or FAMILY.get(fi) == 'veg'):
        return True
    if fi == 'other' and (fo in OTHER_OK or FAMILY.get(fo) == 'veg'):
        return True
    mix = [m for m in mix_o.split(';') if m]
    return 'any' in mix or any(fi == m or _covers(m, fi) or _covers(fi, m) or (_synthetic(fi) and _synthetic(m))
                               for m in mix)


def other_covers(i, o):
    """True when one good is 'of other textile materials' and the other good's fibre is not named in its group
    (HS reading, 2026-10-19), so that fibre can be the main material of the 'other' good."""
    for g, s in ((o, i), (i, o)):
        if g.fibre == 'other' and s.fibre not in ('other', 'any'):
            if not any(fibre_compatible(s.fibre, n) for n in g.other_named.split(';') if n):
                return True
    return False


ORDER = {'F': 1, 'Y': 2, 'C': 3, 'T': 3, 'M': 4}
# yarn headings and their retail counterparts (retail packing is the same yarn only)
YARN_KIND = {**{h: 'silk' for h in ('5004', '5005', '5006')}, **{h: 'wool' for h in ('5106', '5107', '5108', '5109')},
             **{h: 'cotton' for h in ('5205', '5206', '5207')}, **{h: 'filament' for h in ('5402', '5403', '5406')},
             **{h: 'staple' for h in ('5509', '5510', '5511')}}
CARDED = re.compile(r'carded|combed')
FINISH = [('printed', 3), ('dyed', 2), ('yarns of different colours', 2), ('unbleached or bleached', 0),
          ('unbleached', 0), ('bleached', 1)]


# finishing state by 5-digit group where the subheading text does not say it (HS2002 group headers)
FINISH_GROUP = {**{f'{h}{g}': r for h in ('5208', '5209', '5210', '5211')
                   for g, r in (('1', 0), ('2', 1), ('3', 2), ('4', 2), ('5', 3))},
                **{f'{h}{g}': r for h in ('5513', '5514') for g, r in (('1', 0), ('2', 2), ('3', 2), ('4', 3))}}


def finish_rank(text, code=None):
    """0 unbleached, 1 bleached, 2 dyed or of yarns of different colours, 3 printed; None if not stated."""
    if code is not None and code[:5] in FINISH_GROUP:
        return FINISH_GROUP[code[:5]]
    t = text.split('|')[-1].lower()
    for k, v in FINISH:
        if k in t:
            return v
    return None


def code_pair(a, b, A):
    """Rule decision for a textile pair a -> b (both in chapters 50-63, a != b).
    Returns (dv_main, dv_strict, route, step, rule). dv_strict differs from dv_main only on the rules in
    UNCERTAIN_RULES (another fibre or construction as a minor constituent, other than cotton or man-made fibres)."""
    i, o = A.loc[a], A.loc[b]
    si, so = i.stage, o.stage
    same_fib = fibre_compatible(i.fibre, o.fibre) or other_covers(i, o)
    fwd_fib = fibre_compatible(i.fibre, o.fibre, o.mixed_with) or other_covers(i, o)
    mm = all(f in ('syn', 'art', 'mm') or FAMILY.get(f) in ('syn', 'art') for f in (i.fibre, o.fibre))
    if so == 'W':
        if b[:4] == '6310':
            return (1, 1, 'recycle_waste', None, 'T_RAGS') if si in ('M', 'C', 'T', 'Y', 'W') else \
                   (0, 0, 'none', 3, 'T_RAGS_NOT_FROM_FIBRE')
        if b[:4] == '6309':
            return (1, 1, 'forward', None, 'T_WORN_CLOTHING') if si in ('M',) else (0, 0, 'none', 3, 'T_WORN_NOT_FROM')
        if same_fib:
            return 1, 1, 'recycle_waste', None, 'T_WASTE_SAME_FIBRE'
        return 0, 0, 'none', 3, 'T_WASTE_OTHER_FIBRE'
    if si == 'W':
        if a[:4] in ('6309', '6310'):
            if so == 'M' or (a[:4] == '6310' and so in ('F', 'C')):
                return 1, 1, 'recycle_waste', None, 'T_RAG_REUSE'
            return 0, 0, 'none', 3, 'T_RAG_NO_ROUTE'
        if fwd_fib:
            return 1, 1, 'recycle_waste', None, 'T_WASTE_REPROCESSED'
        # audit of 2026-10-19 (group A): waste of another fibre can be a minor blend fibre -> 1, uncertain;
        # certain for cotton or man-made waste (option 2)
        if common_fibre(i.fibre):
            return 1, 1, 'recycle_waste', None, 'T_WASTE_COMMON_FIBRE'
        return 1, 0, 'recycle_waste', None, 'T_WASTE_OTHER_FIBRE_MINOR'
    ri, ro = ORDER[si], ORDER[so]
    if (si, so) in (('C', 'T'), ('T', 'C')):
        if so == 'T' and b[:4] == '5810':                      # embroidery on a ground fabric
            return (1, 1, 'forward', None, 'T_FABRIC_PROCESSED') if fwd_fib else (0, 0, 'none', 3, 'T_SAME_STAGE_OTHER_FIBRE')
        ri = ro                                                # other trims are fabrics made from yarn
    if ri < ro:                                                # forward stage
        if (a[:4] in SEWING or si == 'T' or a[:4] in ('5604', '5605', '5606')) and so == 'M':
            return 1, 1, 'component', None, 'T_THREAD_TRIM_TO_ARTICLE'
        knit_ok = not (si == 'C' and so == 'M' and b[:2] in ('61', '62') and i.knit != o.knit)
        if fwd_fib and knit_ok:
            return 1, 1, ('forward' if same_fib else 'mixture'), None, 'T_FORWARD'
        # another fibre (option 2: certain when the input is cotton or man-made) or, for fabric -> garment, the
        # other construction (knitted / woven; stays uncertain)
        common = not fwd_fib and common_fibre(i.fibre)
        if so == 'M':
            return (1, 1, 'ingredient', None, 'T_CONSTITUENT_COMMON') if common else \
                   (1, 0, 'ingredient', None, 'T_CONSTITUENT')
        # audit of 2026-10-19 (group A): fibre or yarn of another fibre can be a minor yarn in a yarn or fabric -> 1,
        # uncertain (the same treatment as minor constituents of garments, decision 3)
        if common:
            return 1, 1, 'mixture', None, 'T_FORWARD_COMMON_FIBRE'
        return 1, 0, 'mixture', None, 'T_FORWARD_OTHER_FIBRE'
    if ri > ro:                                                # backward stage
        if mm and same_fib:
            return 0, 0, 'recycle_direct', 5, 'T_BACKWARD_MELT'
        return 0, 0, 'none', 5, 'T_BACKWARD'
    # same stage
    if si == 'M':
        if i.parts and not o.parts:
            return 1, 1, 'component', None, 'T_PARTS'
        if a in ACCESSORY and b[:2] in ('61', '62') and b[:4] not in ('6117', '6217'):
            return 1, 1, 'component', None, 'T_ACCESSORY_TO_GARMENT'     # trims attached to garments (audit group D)
        return 0, 0, 'none', 4, 'T_FINISHED_SIBLING'
    if not same_fib:
        return 0, 0, 'none', 3, 'T_SAME_STAGE_OTHER_FIBRE'
    if si == 'F':
        ci, co = bool(CARDED.search(i.text.split('|')[-1])), bool(CARDED.search(o.text.split('|')[-1]))
        if a[:4] in ('5503', '5504') and b[:4] in ('5506', '5507') or co and not ci:
            return 1, 1, 'forward', None, 'T_CARDING'
        if ci and not co:
            return (0, 0, 'recycle_direct', 5, 'T_BACKWARD_MELT') if mm else (0, 0, 'none', 5, 'T_UNCARDING')
    if si == 'Y' and a[:4] in SEWING and b[:4] not in SEWING:   # thread and yarn: intermediate siblings (1-1, audit C)
        return (1, 1, 'forward' if b[:4] in ('5604', '5605', '5606', '5607') else 'sibling_intermediate', None,
                'T_THREAD_TO_YARN')
    if (si == 'Y' and o.retail and not i.retail and YARN_KIND.get(a[:4]) is not None
            and YARN_KIND.get(a[:4]) == YARN_KIND.get(b[:4]) and (i.fibre == o.fibre or _covers(o.fibre, i.fibre))):
        return 1, 1, 'same_good', 2, 'T_RETAIL_PACKING'           # the same yarn put up for retail sale
    if si == 'C' and o.from_fabric and not i.from_fabric:
        return 1, 1, 'forward', None, 'T_FABRIC_PROCESSED'
    if si == 'C' and i.from_fabric and not o.from_fabric:
        return 0, 0, 'none', 5, 'T_BACKWARD'
    if si == 'C' and a[:4] == b[:4]:
        ti, to = finish_rank(i.text, a), finish_rank(o.text, b)
        if ti is not None and to is not None and ti > to:
            return 0, 0, 'none', 5, 'T_UNDO_FINISH'
        if ti is not None and to is not None and to > ti:
            return 1, 1, 'same_good', 2, 'T_FINISH'
    return 1, 1, 'sibling_intermediate', None, 'T_INTERMEDIATE_SIBLING'
