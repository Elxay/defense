"""Prospective rule16 selector. Alpha0 gates only; not an execution grant."""
def choose_tier(actual_spent_GPUh,cells,budget_GPUh=600):
    assert actual_spent_GPUh>=0 and budget_GPUh>0
    assert all(not c.get('nonzero_effects_used',False) for c in cells)
    active=[c for c in cells if c['gate'] in ['active','INVALID_crossing_continue']]
    stopped=[c['cell'] for c in cells if c['gate']=='no_dynamic_range']
    pending=[c['cell'] for c in cells if c['gate'] not in ['active','INVALID_crossing_continue','no_dynamic_range']]
    if actual_spent_GPUh>=budget_GPUh:
        return dict(selected_tier=None,reason='actual search budget exhausted',stopped=stopped,pending=pending)
    if not active:
        return dict(selected_tier=None,reason='no active cells yet' if pending else 'all cells stopped',stopped=stopped,pending=pending)
    # Unknown costs cannot become zero. Reserve the admitted-but-pending cells'
    # remaining first88 work if measured; otherwise withhold a maximum-tier decision.
    reservations=0.
    for c in cells:
        if c['cell'] not in pending:continue
        if c.get('measured_GPUh_per_row') is None:
            return dict(selected_tier=None,reason='pending first88 cost unmeasured',stopped=stopped,pending=pending)
        reservations+=max(0,88-c['completed_rows'])*c['measured_GPUh_per_row']+c.get('remaining_cold_GPUh',0)
    forecasts={}
    for tier in [88,220,440]:
        future=reservations
        for c in active:
            assert c['measured_GPUh_per_row']>=0 and c['completed_rows']>=88
            future+=max(0,tier-c['completed_rows'])*c['measured_GPUh_per_row']
            if tier>c['completed_rows']:future+=c.get('remaining_cold_GPUh',0)
        forecasts[str(tier)]=actual_spent_GPUh+future
    eligible=[n for n in [88,220,440] if forecasts[str(n)]<=budget_GPUh]
    return dict(selected_tier=max(eligible) if eligible else None,forecast_total_GPUh=forecasts,
        sunk_all_cells_GPUh=actual_spent_GPUh,active=[c['cell'] for c in active],stopped=stopped,pending=pending,
        execution_admitted=False,reason='Per-cell gate and final manifest guard still required by execution adapter')

if __name__=='__main__':
    cells=[dict(cell='active',gate='active',completed_rows=88,measured_GPUh_per_row=.1),
           dict(cell='stopped',gate='no_dynamic_range',completed_rows=88,measured_GPUh_per_row=100)]
    assert choose_tier(80,cells,100)['selected_tier']==220
    assert choose_tier(80,cells,100)['forecast_total_GPUh']['440']==115.2
    assert choose_tier(100,cells,100)['selected_tier'] is None
    unknown=cells+[dict(cell='unmeasured',gate='pending88',completed_rows=10,measured_GPUh_per_row=None)]
    assert choose_tier(80,unknown,100)['selected_tier'] is None
    print('Rule16 boundary/accounting fixtures passed; no experiment labels loaded or execution granted.')
