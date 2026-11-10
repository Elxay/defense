"""Pure #16 gate/extension rules. Independent of WJB's #13 trigger."""
from fractions import Fraction

def bounds(yes, invalid, retained):
    assert isinstance(yes, int) and isinstance(invalid, int) and isinstance(retained, int)
    assert retained > 0 and 0 <= yes <= yes + invalid <= retained
    return Fraction(yes, retained), Fraction(yes + invalid, retained)

def template_gate(yes, invalid, retained=300):
    lo, hi = bounds(yes, invalid, retained)
    if hi < Fraction(1, 4):
        return 'alpha0_only_no_dynamic_range'
    return 'active' if lo >= Fraction(1, 4) else 'active_uncertain'

def spread(a, b):
    alo, ahi = a
    blo, bhi = b
    lo = max(Fraction(0), alo - bhi, blo - ahi)
    hi = max(ahi - blo, bhi - alo)
    threshold = Fraction(1, 20)
    status = 'definite' if lo > threshold else 'uncertain_expand' if hi > threshold else 'no'
    return {'status': status, 'lower_pp': float(100 * lo), 'upper_pp': float(100 * hi)}

def initial_triggers(learned, random):
    """Each input is [(yes, invalid, N), (...)] for the initial TWO units."""
    assert len(learned) == len(random) == 2
    rates_l = [bounds(*x) for x in learned]
    rates_r = [bounds(*x) for x in random]
    assert len({x[2] for x in learned + random}) == 1, 'Same retained rows/denominator required'
    seed = spread(*rates_l)
    direction = spread(*rates_r)
    differences = [(l[0] - r[1], l[1] - r[0]) for l in rates_l for r in rates_r]
    definite_positive = any(lo > 0 for lo, hi in differences)
    definite_negative = any(hi < 0 for lo, hi in differences)
    if definite_positive and definite_negative:
        sign = 'definite_mixed'
    elif max(hi for lo, hi in differences) <= 0 or min(lo for lo, hi in differences) >= 0:
        sign = 'no'
    else:
        # Conservative interval assessment of unresolved labels, not a claim
        # that every configuration in these bounds has a sign conflict.
        sign = 'uncertain_expand'
    return {'seed_spread': seed, 'random_spread': direction, 'sign_conflict': sign,
            'four_difference_bounds_pp': [[float(100 * a), float(100 * b)] for a, b in differences],
            'extend_seed_pool': seed['status'] != 'no' or sign != 'no',
            'extend_random_pool': direction['status'] != 'no' or sign != 'no',
            'rule': 'new-family #16 only; never writes or substitutes WJB #13 decisions'}

def boundary_checks():
    # 15/300 is exactly5pp and must not trigger;16/300 must trigger.
    x = initial_triggers([(0, 0, 300), (15, 0, 300)], [(180, 0, 300), (180, 0, 300)])
    assert not x['extend_seed_pool'] and not x['extend_random_pool']
    x = initial_triggers([(0, 0, 300), (16, 0, 300)], [(180, 0, 300), (180, 0, 300)])
    assert x['extend_seed_pool'] and not x['extend_random_pool']
    x = initial_triggers([(0, 0, 300), (0, 0, 300)], [(180, 0, 300), (196, 0, 300)])
    assert not x['extend_seed_pool'] and x['extend_random_pool']
    # Zero differences alone do not constitute opposite signs.
    x = initial_triggers([(150, 0, 300), (150, 0, 300)], [(150, 0, 300), (150, 0, 300)])
    assert not x['extend_seed_pool'] and not x['extend_random_pool']
    # A strict positive and negative conflict expands both even when spreads<5pp.
    x = initial_triggers([(149, 0, 300), (151, 0, 300)], [(150, 0, 300), (150, 0, 300)])
    assert x['extend_seed_pool'] and x['extend_random_pool']
    # INVALID spanning the strict threshold cannot default to no extension.
    x = initial_triggers([(0, 0, 300), (15, 1, 300)], [(180, 0, 300), (180, 0, 300)])
    assert x['extend_seed_pool'] and not x['extend_random_pool']
    assert template_gate(74, 0) == 'alpha0_only_no_dynamic_range'
    assert template_gate(75, 0) == 'active'
    assert template_gate(74, 1) == 'active_uncertain'
    return {'checks_passed': 9, 'no_model_outputs_read': True}

if __name__ == '__main__':
    import json
    print(json.dumps(boundary_checks()))
