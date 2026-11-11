from pathlib import Path
import concurrent.futures
import datetime as dt
import heapq
import json
import statistics
import subprocess

R = Path('/data/HZX/Def')
U = R / 'results/audit/unified300'
T = R / 'tools/handoff_20261106'
subprocess.run(['scp', str(T / 'unified300_generation_metadata_snapshot.py'),
                'node01:/home/dell/Def/tools/handoff_20261106/unified300_generation_metadata_snapshot.py'],
               check=True, capture_output=True)


def collect(site):
    if site == 'innet':
        args = ['env', 'DEF_ROOT=' + str(R), '/home/kemove/anaconda3/envs/HZX_GLA/bin/python',
                str(T / 'unified300_generation_metadata_snapshot.py')]
    else:
        args = ['ssh', 'node01', 'env DEF_ROOT=/home/dell/Def /data/ray/env/bin/python '
                '/home/dell/Def/tools/handoff_20261106/unified300_generation_metadata_snapshot.py']
    return site, json.loads(subprocess.check_output(args, text=True))


with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    sources = dict(pool.map(collect, ['innet', 'node01']))
rows = []
for a, b in zip(sources['innet']['rows'], sources['node01']['rows']):
    assert (a['model'], a['family'], a['condition']) == (b['model'], b['family'], b['condition'])
    on_node = (a['model'] == 'llama' and a['family'].startswith('translate-')
               and a['family'] != 'translate-zh-cn')
    rows.append({**(b if on_node else a), 'site': 'node01' if on_node else 'innet'})
assert sum(r['normal_complete'] and r['condition'] == 'alpha0' for r in rows) >= 28
assert all(r['normal_complete'] for r in rows
           if r['model'] == 'qwen' and r['family'].startswith('translate-')
           and r['condition'] == 'alpha0')
lookup = {(r['model'], r['family'], r['condition']): r for r in rows}
state = json.loads((U / 'ready_queue/state.json').read_text())
catalog = json.loads((U / 'ready_queue_catalog.json').read_text())
tasks = {t['id']: t for t in catalog['tasks']}
now = dt.datetime.now(dt.timezone.utc)
completion_tasks = {}
for tid, task in tasks.items():
    if tid.startswith('main_'):
        model, family, condition = task['argv'][2:5]
        completion_tasks[f'results/audit/unified300/ready_generated/{model}/{family}/{condition}/complete.json'] = tid
sim_done = set()
for tid, task in tasks.items():
    if tid.startswith('main_'):
        model, family, condition = task['argv'][2:5]
        if lookup[model, family, condition]['normal_complete']:
            sim_done.add(tid)


def prerequisites_ready(tid):
    for requirement in tasks[tid].get('requires', []):
        dependency = completion_tasks.get(requirement['path'])
        if dependency:
            if dependency not in sim_done:
                return False
            continue
        path = R / requirement['path']
        if not path.exists():
            return False
        if 'key' in requirement:
            value = json.loads(path.read_text())
            for key in requirement['key'].split('.'):
                value = value.get(key) if isinstance(value, dict) else None
            if value != requirement['value']:
                return False
    return True
overheads = {'llama': [], 'qwen': []}
for tid, status in state['tasks'].items():
    if not tid.startswith('main_') or status.get('state') != 'done' or tid not in tasks:
        continue
    model, family, condition = tasks[tid]['argv'][2:5]
    row = lookup.get((model, family, condition))
    resident = status.get('exit', {}).get('resident_seconds')
    if row and row['normal_complete'] and resident is not None:
        overheads[model].append(max(0, resident - row['metric_seconds']))
setup = {m: statistics.median(v) if v else 0 for m, v in overheads.items()}


def rate_for(row):
    if row['rows_per_hour'] and row['N_saved'] >= 16:
        return row['rows_per_hour'], 'own measured cell'
    learned = row['condition'].startswith('s')
    peers = [r['rows_per_hour'] for r in rows
             if r['model'] == row['model'] and r['family'] == row['family']
             and r['condition'] != 'alpha0' and r['condition'].startswith('s') == learned
             and r['rows_per_hour'] and r['N_saved'] >= 16]
    if peers:
        return statistics.median(peers), 'same-family same-class measured median'
    baseline = lookup[row['model'], row['family'], 'alpha0']
    return baseline['rows_per_hour'], 'same-family alpha0 same-speed scenario'


for row in rows:
    row['rate_used'], row['rate_basis'] = rate_for(row)
    row['remaining_net_GPUh'] = ((440 - row['N_saved']) / row['rate_used']
                                 if row['rate_used'] else None)
    row['eta_utc'] = None
    if row['normal_complete']:
        row['status'] = 'done'
        row['eta_utc'] = row['marker_utc']
    elif row['family'] in ['ascii', 'caesar', 'morse', 'atbash']:
        row['status'] = 'blocked_preprocessing_and_execution_admission'
    elif row['family'].startswith('translate-') and row['condition'] != 'alpha0':
        row['status'] = 'blocked_translation_scoring_gate_and_nonzero_plan'
    else:
        row['status'] = 'pending'

pending, active, ends, occupied = [], [], {}, {}
slots = {'llama': [2, 0], 'qwen': [0, 3]}
elapsed = 0.0
for tid, task in tasks.items():
    if not tid.startswith('main_'):
        continue
    model, family, condition = task['argv'][2:5]
    row = lookup[model, family, condition]
    status = state['tasks'].get(tid, {})
    if row['normal_complete']:
        continue
    duration = (row['remaining_net_GPUh'] or 0) * 3600
    if status.get('state') == 'running':
        row['status'] = 'running'
        gpu = status['gpus'][0]
        finish = max(duration, 30.0)
        occupied[gpu] = tid
        heapq.heappush(active, (finish, gpu, tid))
        ends[tid] = finish
    elif status.get('state', 'pending') == 'pending':
        pending.append((task['priority'], tid, duration + setup[model], model))
    elif status.get('state') == 'failed':
        row['status'] = 'failed'
pending.sort()
while pending or active:
    made = True
    while made:
        made = False
        for i, (_, tid, duration, model) in enumerate(pending):
            if not prerequisites_ready(tid):
                continue
            free = next((g for g in slots[model] if g not in occupied), None)
            if free is not None:
                occupied[free] = tid
                finish = elapsed + max(duration, 30.0)
                heapq.heappush(active, (finish, free, tid))
                ends[tid] = finish
                pending.pop(i)
                made = True
                break
    if not active:
        break
    elapsed, gpu, completed_tid = heapq.heappop(active)
    occupied.pop(gpu, None)
    sim_done.add(completed_tid)
for tid, end in ends.items():
    model, family, condition = tasks[tid]['argv'][2:5]
    lookup[model, family, condition]['eta_utc'] = (now + dt.timedelta(seconds=end)).isoformat()
for row in rows:
    if not row['family'].startswith('translate-') or row['condition'] != 'alpha0' or row['normal_complete']:
        continue
    for tid, task in tasks.items():
        if task['kind'] != 'alpha0_family_generate':
            continue
        if row['family'] not in task['argv'] or row['model'] not in task['argv']:
            continue
        status = state['tasks'].get(tid, {})
        if status.get('state') == 'running':
            row['status'] = 'running'
            if row['remaining_net_GPUh'] is not None:
                row['eta_utc'] = (now + dt.timedelta(hours=row['remaining_net_GPUh'])).isoformat()
        elif status.get('state') == 'pending':
            row['status'] = 'pending_language_resource'

orders = {'llama': ['alpha0', 's3', 'rand0', 's4', 'rand1', 's5'],
          'qwen': ['alpha0', 's3', '61000', 's4', '61001', 's5']}
families = list(dict.fromkeys(r['family'] for r in rows))
meta = {'utc': now.isoformat(), 'snapshot_source_utc': {s: x['utc'] for s, x in sources.items()},
        'N_static_family_definitions': 19, 'N_search_family_definitions': 3,
        'N_static_cells': len(rows), 'condition_order': orders,
        'ETA_version': 2,
        'ETA_correction': 'Honor frozen per-family predecessor-completion dependencies; v1 omitted these in prediction only, actual queue order was correct.',
        'ETA': 'Conditional generation-only queue simulation on innet0/2/3; frozen predecessor '
               'completion dependencies honored; own-cell or '
               'same-family/class measured rate, fallback alpha0; median observed setup. '
               'No new external occupancy/preemption. Not upper bound/CI. '
               'No labels read. Blocked cells have no calendar ETA.',
        'observed_setup_median_seconds': setup, 'rows': rows}
for model in ['llama', 'qwen']:
    for family in families:
        group = [lookup[model, family, c] for c in orders[model][1:]]
        if all(r.get('eta_utc') for r in group):
            times = [dt.datetime.fromisoformat(r['eta_utc']) for r in group]
            assert times == sorted(times), (model, family, 'predecessor ETA violation')
(U / 'family_condition_status_20261111.json').write_text(json.dumps(meta, indent=2) + '\n')
lines = ['# 家族×条件生成状态与条件ETA', '', 'UTC ' + now.isoformat(), '',
         '440✓=正常齐全；数字*=运行中；0=待运行；锁=前置未齐。ETA只含生成。', '']
tz = dt.timezone(dt.timedelta(hours=9))
for model in ['llama', 'qwen']:
    lines += ['## ' + model, '',
              '| 家族 | α0 | s3 | r0 | s4 | r1 | s5 | α0行/时 | 全六条件齐全ETA JST |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for family in families:
        group = [lookup[model, family, c] for c in orders[model]]
        cells = [('440✓' if r['normal_complete'] else str(r['N_saved']) + '*'
                  if r['status'] == 'running' else str(r['N_saved']) + '锁'
                  if r['status'].startswith('blocked') else str(r['N_saved'])) for r in group]
        dates = [dt.datetime.fromisoformat(r['eta_utc']) for r in group if r.get('eta_utc')]
        eta = ('已齐' if all(r['normal_complete'] for r in group) else
               max(dates).astimezone(tz).strftime('%m/%d %H:%M')
               if all(r.get('eta_utc') for r in group) else '前置未齐，未定')
        rate = group[0]['rows_per_hour']
        lines.append('| ' + family + ' | ' + ' | '.join(cells) + ' | '
                     + (f'{rate:.0f}' if rate else '未测') + ' | ' + eta + ' |')
    lines.append('')
lines += ['## 逐条件ETA', '', '| 模型 | 家族 | 条件 | 保存行数 | 采用行/时 | ETA JST |',
          '|---|---|---|---:|---:|---|']
for row in rows:
    if row['normal_complete'] or not row.get('eta_utc'):
        continue
    eta = dt.datetime.fromisoformat(row['eta_utc']).astimezone(tz)
    lines.append(f"| {row['model']} | {row['family']} | {row['condition']} | "
                 f"{row['N_saved']} | {row['rate_used']:.0f} | {eta:%m/%d %H:%M} |")
(U / 'family_condition_status_20261111.md').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines[:55]))
print('SETUP_SECONDS', setup)
