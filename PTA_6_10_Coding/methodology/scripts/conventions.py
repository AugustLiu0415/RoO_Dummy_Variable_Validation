"""Conventions of 28-30 October 2026 (Prof. Zhang's questionnaire answers), for pairs coded from PTA 6-10 on.

PTA 1-5 codes stay as delivered (his answers of 30 October: previously coded DVs are not re-judged; the overall principle
is for future coding), so nothing here touches the ASEAN-Japan labels or the PTA 2-5 master. DV is the variable that
counts (August, 30 October): uncertain pairs stay 1 + uncertain, and a pair turns 0 only on clear evidence.
Rules text: PTA6_10/Coding_Rules_2026_10_30.md, section I.9. Applied by PTA6_10/_work/09_apply_policy.py.

  P_Q3E_own    remelting back to the input's own upstream form -> DV 1, certain        (convention 3, answer 3-1 E)
  P_Q3E_other  remelting into another primary or semi-finished form of the same material -> DV 1, uncertain
  P_Q3E_0      remelting into a finished product, vulcanised rubber, thermosets, other polymers -> DV 0 (step 6)
  P_Q2C        parts and metal articles of different headings, or different compounds of one chemical heading,
               linked only as same-material intermediates -> DV 1, uncertain                (convention 2, answer 2 C)
  P_Q2C_same   metal articles of one heading and metal (claimed as remelting) -> DV 1, certain
  P_Q5B        swine meat, offal and fat -> pig bristles (answer 5(b), his example) -> 0
  P_PROF0      pairs both auditors coded 0 in the classes where the professor said so (questions 1 and 2(c)) -> 0
  P_RESCUE     a P_Q3E_0 pair for which the rescue screen named another specific route -> back to 1 + uncertain
               (not plastics: answer 3-2 gives polyethylene film -> polycarbonate sheet as its example of 0)
The class rules (P_Q2C for metal articles and compounds of one heading, P_Q3E for remelting) also reach pairs
both coders coded 0, and P_Q2C replaces the certainty P_Q1_1 gave to split sibling claims.
Each applies to pairs whose 1 rests only on that route (no other route claimed by a coder who coded 1).
"""
import re

import numpy as np
import pandas as pd

# ---- material and level of a good (remelting, question 3) ----
# level 0: primary forms (ingots, semi-finished steel cast from the melt, unwrought metal, pulp, primary plastics,
# glass in the mass, natural and unvulcanised rubber); 1: semi-finished forms (bars, wire, plates, sections, sheet
# piling, rails, tubes, base paper, sheet glass, plastic sheets); 2: articles
PRIMARY = ({'7201', '7202', '7203', '7205', '7206', '7207', '7401', '7402', '7403', '7405', '7501', '7502', '7601',
            '7801', '7901', '8001', '7001', '4001', '4002', '4003', '4005'} | {str(h) for h in range(3901, 3915)}
           | {str(h) for h in range(4701, 4707)})
SEMI = ({str(h) for h in range(7208, 7230)} | {'7301', '7302', '7303', '7304', '7305', '7306'}
        | {'7406', '7407', '7408', '7409', '7410', '7411', '7504', '7505', '7506', '7507', '7603', '7604', '7605',
           '7606', '7607', '7608', '7803', '7804', '7805', '7903', '7904', '7905', '7906', '8003', '8004', '8005',
           '8006', '7002', '7003',
           '7004', '7005', '7006', '7019', '3916', '3917', '3919', '3920', '3921', '4006', '4007', '4008'}
        | {str(h) for h in range(4801, 4812)})
PRIMARY_SUB = {'721810', '721891', '721899', '722410', '722490'}    # stainless and alloy steel ingots, semi-finished
MATTE = {'7401', '7501'}                                            # mattes: smelting products, not remelting
# the semi-finished forms an article is made from (back to them = the input's own upstream form)
MADE_FROM = {**{h: {'7003', '7004', '7005'} for h in ('7007', '7008', '7009')},
             **{h: {'7213', '7217'} for h in ('7312', '7313', '7314', '7315', '7317', '7318')},
             '7308': {'7208', '7209', '7210', '7211', '7212', '7216', '7301'},
             '7610': {'7604', '7606'}, '7612': {'7606', '7607'}, '7614': {'7605'}, '7413': {'7408'},
             **{str(h): {str(s) for s in range(4801, 4812)} for h in range(4812, 4824)}}
# plastics: polymer of a subheading (texts of 3916-3921 and 3907 name it); heading-level polymers of primary forms
POLYMER_TEXT = [('PET', r'terephthalate'), ('UP', r'unsaturated'), ('PC', r'polycarbonate'), ('PVB', r'vinyl butyral'),
                ('PE', r'ethylene'), ('PP', r'propylene'), ('PS', r'styrene'), ('PVC', r'vinyl chloride'),
                ('ACR', r'acrylic|methacrylate'), ('PA', r'polyamide'), ('CA', r'cellulose acetate'),
                ('AMINO', r'amino-resin'), ('PHEN', r'phenolic'), ('EPOXY', r'epoxide'), ('ALKYD', r'alkyd'),
                ('PU', r'polyurethane'), ('CELL', r'cellulose|vulcanised fibre'), ('POLYESTER', r'polyester')]
# the polymer of an 'Other' subheading named only by its 5-digit group (no group texts in the HS2002 file)
POLYMER_GROUP = {'39204': 'PVC', '39205': 'ACR', '39206': 'POLYESTER', '39207': 'CELL'}
# rubber in primary forms: natural rubber, and the synthetic rubbers named by group in heading 4002
RUBBER_GROUP = {'40021': 'SBR', '40022': 'BR', '40023': 'IIR', '40024': 'CR', '40025': 'NBR', '40026': 'IR',
                '40027': 'EPDM'}
POLYMER_HEADING = {'3901': 'PE', '3902': 'PP', '3903': 'PS', '3904': 'PVC', '3905': 'PVAC', '3906': 'ACR', '3908': 'PA'}
# not remeltable: thermosets, regenerated cellulose, vulcanised fibre, hardened protein
NOT_THERMOPLASTIC = {'UP', 'AMINO', 'PHEN', 'EPOXY', 'ALKYD'}
NOT_THERMOPLASTIC_CODES = {'391710', '392071', '392072', '392114'} | {f'3909{s}' for s in ('10', '20', '31', '39', '40')} | {
    f'3910{s}' for s in ('00',)} | {f'3911{s}' for s in ('10', '90')} | {f'3912{s}' for s in ('11', '12', '20', '31',
                                                                                        '39', '90')}
PRECIOUS = [('silver', r'\bsilver'), ('gold', r'\bgold'), ('pgm', r'platinum|palladium|rhodium|iridium|osmium|ruthenium')]
SETTLED = r'P_Q1_1|P_Q2C|P_Q2_1|P_Q2_2|P_FISH|P_Q3E|P_Q5B|P_PROF0|P_AUD|P_OPT2|P_CONF'   # a policy decided the pair
# both auditors coded 0 (questions 1 and 2(c) of 30 October: such pairs are 0)
PROF0 = {('HS2002', '382450', '381190'), ('HS2002', '271112', '270220'), ('HS2002', '292214', '293712'),
         ('HS2002', '293291', '294150'), ('HS2002', '280490', '280480'), ('HS2012', '290892', '290891')}


def material(c):
    """base material of a good for remelting: iron and steel, a non-ferrous metal, glass, plastics, paper, rubber"""
    ch, h = c[:2], c[:4]
    if ch in ('72', '73'):
        return 'iron_steel'
    if ch in ('74', '75', '76', '78', '79', '80'):
        return 'metal' + ch
    if ch == '81':
        return 'metal' + h
    return {'70': 'glass', '39': 'plastics', '47': 'paper', '48': 'paper', '49': 'paper', '40': 'rubber'}.get(ch, '')


def level(c, T):
    """0 primary form, 1 semi-finished form, 2 article (T: HS2002 texts, code -> text)"""
    h = c[:4]
    if h[:2] == '81':                                       # chapter 81: the subheading text names the form
        t = T.get(c, '').lower()
        if 'unwrought' in t or t.startswith('powders'):
            return 0
        return 1 if re.search(r'bars|rods|wire|plates|sheets|strip|foil|profiles|raspings|turnings|granules', t) else 2
    if h in PRIMARY or c in PRIMARY_SUB:
        return 0
    return 1 if h in SEMI else 2


def metal_article(h):
    """heading of a metal article (chapters 73, 82, 83 and the articles of chapters 74-81), not a primary or
    semi-finished form"""
    return h.str[:2].isin([str(c) for c in range(72, 84)]) & ~h.isin(PRIMARY | SEMI) & (h.str[:2] != '72')


def polymer(c, T):
    """polymer of a plastics or rubber code, or '' when the text does not name one ("of other plastics")"""
    if c[:2] == '40':
        return 'NR' if c[:4] == '4001' else RUBBER_GROUP.get(c[:5], '')
    if c[:4] in POLYMER_HEADING:
        return POLYMER_HEADING[c[:4]]
    t = T.get(c, '').lower()
    for k, p in POLYMER_TEXT:
        if re.search(p, t):
            return k
    # 'of other plastics' excludes the polymers named in its heading: a polymer of its own for the different-polymer test
    return 'OTHER' if 'other plastics' in t else POLYMER_GROUP.get(c[:5], '')


def precious(c, T):
    t = T.get(c, '').lower()
    for k, p in PRECIOUS:
        if re.search(p, t):
            return k
    return ''


def remelt_tier(a, b, T, A):
    """tier of a pair whose 1 rests only on direct remelting or re-processing: 'own' (1, certain), 'other' (1,
    uncertain), 'zero' (0) or 'keep' (no convention applies). A: textile attributes (textile.attributes)."""
    ia, ib, ha, hb = int(a[:2]), int(b[:2]), a[:4], b[:4]
    if 50 <= ia <= 63 and 50 <= ib <= 63 and a in A.index and b in A.index:
        if hb in ('5604', '5605', '5606', '5607'):
            return 'other'                                    # gimped yarn, twine, rope, rubber thread
        return 'own' if A.loc[b, 'stage'] in ('F', 'Y') and A.loc[a, 'stage'] != 'F' else 'other'
    if '4007' <= ha <= '4017' and ib == 40:
        return 'keep' if hb in ('4003', '4004') else 'zero'   # vulcanised rubber cannot be remelted
    if (ia == 39 and ib == 39) or (ia == 40 and ib == 40):
        pa, pb = polymer(a, T), polymer(b, T)
        if (pa in NOT_THERMOPLASTIC or pb in NOT_THERMOPLASTIC or a in NOT_THERMOPLASTIC_CODES
                or b in NOT_THERMOPLASTIC_CODES):
            return 'zero'
        if pa and pb and pa != pb:
            return 'zero'                                     # thermoplastics: the same polymer only
    if ia == 71 and ib == 71:
        ma, mb = precious(a, T), precious(b, T)
        if not ma or not mb or ma != mb:
            return 'keep'
        if hb in ('7113', '7114', '7115', '7116', '7117', '7118'):
            return 'zero'
        return 'own' if re.search(r'unwrought|powder', T.get(b, '').lower()) else 'other'
    ma, mb = material(a), material(b)
    if ma and ma == mb:
        la, lb = level(a, T), level(b, T)
        if lb == 2:
            return 'zero'                                     # made into a finished product
        if hb in MATTE:
            return 'other'
        same_polymer = ia not in (39, 40) or (polymer(a, T) not in ('', 'OTHER') and polymer(a, T) == polymer(b, T))
        if same_polymer and (lb == 0 and la > 0 or lb == 1 and la == 2 and hb in MADE_FROM.get(ha, ())):
            return 'own'
        return 'other'
    if ia == 37 and ib == 37:
        return 'zero'                                         # film re-made into other film or chemicals
    if 68 <= ia <= 69 and hb in ('6804', '6805'):
        return 'zero'                                         # grinding wheels -> abrasive cloth (questionnaire 3-1)
    if ia >= 82 and not ma:                                   # machines and other articles
        return 'zero' if level(b, T) == 2 and not (28 <= ib <= 38) else ('other' if mb else 'keep')
    return 'keep'


def claims(F):
    """routes claimed by the coders who coded 1 (AI pairs), or the final route of a 1 coded by rule"""
    r1 = np.where(F.dv_ai1 == '1', F.route_ai1, '')
    r2 = np.where(F.dv_ai2 == '1', F.route_ai2, '')
    ai = (F.dv_ai1 != '') | (F.dv_ai2 != '')
    own = np.where(F.DV.astype(int) == 1, F.route, '')
    return [({x for x in (a, b) if x} if i else {o} - {''}) for a, b, i, o in zip(r1, r2, ai, own)]


def apply_conventions(F, mask, T, A, apply, vintage='HS2002'):
    """the conventions of 28-30 October on the rows in mask (new pairs); apply: PTA_2_5 09 apply(); returns
    {policy: (DV changed, rows)}"""
    pol = {}
    cl = pd.Series(claims(F), index=F.index)
    only = lambda r: cl.map(lambda s: s == {r})                    # noqa: E731
    one = mask & (F.DV.astype(int) == 1)
    # convention 3: remelting (route recycle_direct, the 1 rests on it alone)
    rd = one & (only('recycle_direct') | ((F.route == 'recycle_direct') & cl.map(lambda s: s <= {'recycle_direct'})))
    tier = pd.Series('keep', index=F.index)
    tier[rd] = [remelt_tier(a, b, T, A) for a, b in zip(F.input_hs6[rd], F.output_hs6[rd])]
    # metal articles of the same metal are same-material intermediates (answer 2(b): bolts -> pipes, household
    # articles -> tubes): convention 2 decides them, not the remelting route the coder happened to claim
    ih, oh = F.input_hs6.str[:4], F.output_hs6.str[:4]
    li = F.input_hs6.map(lambda c: level(c, T))
    lo = F.output_hs6.map(lambda c: level(c, T))
    mat_i, mat_o = F.input_hs6.map(material), F.output_hs6.map(material)
    art = (li == 2) & (lo == 2) & (mat_i == mat_o) & (mat_i.str.startswith('iron') | mat_i.str.startswith('metal'))
    pol['P_Q2C_same'] = apply(F, rd & art & (ih == oh), 'P_Q2C_same', DV=1, uncertain=0,
                              route='sibling_intermediate', step='')
    pol['P_Q2C_art'] = apply(F, rd & art & (ih != oh), 'P_Q2C', DV=1, uncertain=1, route='sibling_intermediate',
                             step='')
    rd = rd & ~art
    pol['P_Q3E_own'] = apply(F, rd & (tier == 'own'), 'P_Q3E_own', DV=1, uncertain=0)
    pol['P_Q3E_other'] = apply(F, rd & (tier == 'other'), 'P_Q3E_other', DV=1, uncertain=1)
    pol['P_Q3E_0'] = apply(F, rd & (tier == 'zero'), 'P_Q3E_0', DV=0, uncertain=0, route='none', step='6')
    # convention 2: same-material intermediates of different headings, or different compounds of one heading
    ic, oc = F.input_hs6.str[:2].astype(int), F.output_hs6.str[:2].astype(int)
    sib = one & ~F.policy.str.contains('P_Q2C') & (only('sibling_intermediate') | (
        (F.route == 'sibling_intermediate') & cl.map(lambda s: s <= {'sibling_intermediate'})))
    parts = ic.between(84, 90) & oc.between(84, 90) & (ih != oh)
    metal = ic.between(72, 83) & oc.between(72, 83) & (ih != oh) & ((li == 2) | (lo == 2))
    chem = ic.between(28, 38) & oc.between(28, 38) & (ih == oh) & (F.input_hs6 != F.output_hs6) & ~(
        (ic == 37) & (oc == 37))
    pol['P_Q2C'] = apply(F, sib & (parts | metal | chem), 'P_Q2C', uncertain=1)
    # flags only (P_2CFLAG, not a settling policy, so the A1 screen can still zero a pair both screens found invalid,
    # as the professor's 2(c) note allows): 2(c) covers every pair of different compounds of one heading, whatever
    # route the coders claimed (a process role
    # would be 1 + uncertain under answer 1 C as well); and convention 2 replaces the certainty that P_Q1_1 gave to split
    # sibling claims: certain only for the same heading and material, which the codes cannot show for these pairs
    now1 = mask & (F.DV.astype(int) == 1) & ~F.policy.str.contains('P_Q2C')
    sib_claim = cl.map(lambda s: 'sibling_intermediate' in s) | (F.route == 'sibling_intermediate')
    pol['P_Q2C_chem'] = apply(F, now1 & chem & sib_claim & (F.locked != 1), 'P_2CFLAG', uncertain=1)
    pol['P_Q2C_q11'] = apply(F, mask & (F.DV.astype(int) == 1) & F.policy.str.contains('P_Q1_1')
                             & ~F.policy.str.contains('P_Q2C') & (F.uncertain.astype(int) == 0), 'P_2CFLAG', uncertain=1)
    # the answers to 2(b) and 3-1 are rules for whole classes, so they also reach pairs both coders coded 0
    zero = mask & (F.DV.astype(int) == 0) & cl.map(len).eq(0) & ~(ic.between(50, 63) & oc.between(50, 63))
    pol['P_Q2C_same0'] = apply(F, zero & art & (ih == oh), 'P_Q2C_same', DV=1, uncertain=0,
                               route='sibling_intermediate', step='')
    pol['P_Q2C_art0'] = apply(F, zero & art & (ih != oh), 'P_Q2C', DV=1, uncertain=1, route='sibling_intermediate',
                              step='')
    # only goods that are remelted or repulped (semi-finished goods and articles); turning one primary form into another
    # (wood pulp -> cotton linters pulp) is a conversion, not remelting
    same = zero & ~art & (mat_i != '') & (mat_i == mat_o) & (li >= 1)
    t0 = pd.Series('keep', index=F.index)
    t0[same] = [remelt_tier(a, b, T, A) for a, b in zip(F.input_hs6[same], F.output_hs6[same])]
    pol['P_Q3E_own0'] = apply(F, same & (t0 == 'own'), 'P_Q3E_own', DV=1, uncertain=0, route='recycle_direct',
                              step='')
    pol['P_Q3E_other0'] = apply(F, same & (t0 == 'other'), 'P_Q3E_other', DV=1, uncertain=1,
                                route='recycle_direct', step='')
    # answer 5(b): pig bristles are a parallel by-product of slaughter, not a waste of pork (his example)
    pork = F.input_hs6.str[:4].isin(['0203', '0209']) | F.input_hs6.isin(['020630', '020641', '020649', '021011',
                                                                          '021012', '021019'])
    pol['P_Q5B'] = apply(F, mask & (F.DV.astype(int) == 1) & pork & (F.output_hs6 == '050210'), 'P_Q5B', DV=0,
                         uncertain=0, route='none', step='3')
    # pairs both auditors coded 0 where the professor said such pairs are 0
    key = pd.Series(list(zip([vintage] * len(F), F.input_hs6, F.output_hs6)), index=F.index)
    pol['P_PROF0'] = apply(F, mask & key.isin(PROF0), 'P_PROF0', DV=0, uncertain=0, route='none', step='3')
    return pol


def apply_rescue(F, mask, R, apply, vintage='HS2002'):
    """pairs set to 0 by convention 3 for which a screener named another specific route (forward, ingredient, ...):
    back to DV 1 + uncertain with that route (R: vintage, input_hs6, output_hs6, route)"""
    if R is None or not len(R):
        return {'P_RESCUE': (0, 0)}
    # not for plastics: answer 3-2 codes different polymers 0 with this very case as its example (polyethylene film ->
    # polycarbonate sheet), so a laminate route does not override it
    R = R[~(R.input_hs6.str[:2].eq('39') & R.output_hs6.str[:2].eq('39'))]
    r = R[R.vintage == vintage].set_index(['input_hs6', 'output_hs6'])
    key = pd.MultiIndex.from_arrays([F.input_hs6, F.output_hs6])
    hit = mask & F.policy.str.contains('P_Q3E_0') & pd.Series(key.isin(r.index), index=F.index)
    route = pd.Series(r.route.reindex(key).values, index=F.index)
    return {'P_RESCUE': apply(F, hit, 'P_RESCUE', DV=1, uncertain=1, route=route, step='')}


def screen_pool(F, mask):
    """one-sided 1s that no rule or convention settled: the pairs for the screen of clearly invalid 1s (A1)"""
    split = (F.dv_ai1 != '') & (F.dv_ai2 != '') & (F.dv_ai1 != F.dv_ai2)
    return mask & split & (F.DV.astype(int) == 1) & ~F.policy.str.contains(SETTLED)


def apply_screen(F, mask, S, apply, vintage='HS2002'):
    """A1: set to 0 the pairs both model families judged clearly invalid (S: vintage, input_hs6, output_hs6, step)"""
    if S is None or not len(S):
        return {'P_A1': (0, 0)}
    s = S[S.vintage == vintage].set_index(['input_hs6', 'output_hs6'])
    key = pd.MultiIndex.from_arrays([F.input_hs6, F.output_hs6])
    hit = mask & pd.Series(key.isin(s.index), index=F.index)
    step = pd.Series(s.step.reindex(key).values, index=F.index).fillna('3').astype(str)
    return {'P_A1': apply(F, hit, 'P_A1', DV=0, uncertain=0, route='none', step=step)}
