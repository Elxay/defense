"""Recalculate scenario accounting; this does not execute any model or attack."""
from pathlib import Path
import json
import math
import sys

path = Path(sys.argv[1])
x = json.loads(path.read_text())
def same(a, b):
    assert math.isclose(a, b, abs_tol=1e-8), (a, b)

assert x['M'] == 4 and x['conditions']['K'] == 6
assert sum(x['conditions'][k] for k in ['alpha0', 'learned', 'random']) == 6
for i in [0, 1]:
    total = 0
    for row in x['static']:
        expected = 4 * 6 * row['per_model_condition_gpu_hours'][i]
        same(row['matrix_gpu_hours'][i], expected)
        total += expected
    same(x['base_cost_components_gpu_hours']['static_generation_all_templates_active'][i], total)
    base = sum(v[i] for v in x['base_cost_components_gpu_hours'].values())
    same(base, x['base_excluding_TAP_AutoDAN_build_library'][i])
    for idx, key in [(1, 'planning_total_f20pct'), (2, 'planning_total_f50pct')]:
        q = x['AutoDAN_query_scenarios_not_predictions'][idx]
        c = q['autodan_four_models_gpu_hours_at_kappa1' if i == 0 else 'at_kappa3']
        same(base + x['TAP_search_PAIR_ratio_scenario'][i] + c, x[key][i])
for row in x['AutoDAN_query_scenarios_not_predictions']:
    f = row['failed_fraction_hypothesis']
    q = (1 - f) * 6.72 + f * 150
    same(q, row['queries_mean_hypothesis'])
    h = 4 * 300 * q * (382 * 2 / 40) / 3600
    same(h, row['autodan_four_models_gpu_hours_at_kappa1'])
    same(h * 3, row['at_kappa3'])
same(x['base_cost_components_gpu_hours']['adaptive_PAIR_matched_alpha0_plus_s3_plus_random_300_searches'][0], 300 * 382 * 2 / 3600)
print(json.dumps({'accounting_checks': 'passed', 'models': 4, 'conditions': 6,
                  'base_gpu_hours': x['base_excluding_TAP_AutoDAN_build_library'],
                  'total_f20_plus_unmeasured_W': x['planning_total_f20pct'],
                  'total_f50_plus_unmeasured_W': x['planning_total_f50pct']}, indent=2))
