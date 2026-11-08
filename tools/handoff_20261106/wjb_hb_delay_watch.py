"""Record judge-card waiting and the noon fallback decision; never read labels."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import time

from wjb_nine_read_gate import status

ROOT = Path('/data/HZX/Def')
BASE = ROOT / 'results/audit/pair500'
START = datetime.datetime(2026, 11, 8, 13, 56, 42, tzinfo=datetime.timezone.utc)
NOON = datetime.datetime(2026, 11, 9, 3, tzinfo=datetime.timezone.utc)


def main():
    while True:
        now = datetime.datetime.now(datetime.timezone.utc)
        gate = status()
        try:
            memory = subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used',
                '--format=csv,noheader,nounits', '-i', '2,3'], text=True, timeout=15).strip().splitlines()
        except subprocess.SubprocessError:
            memory = ['unavailable']
        scores = list((BASE / 'public255/mapped_scores/rand3').glob('*.json'))
        first = min((p.stat().st_mtime for p in scores), default=None)
        started = datetime.datetime.fromtimestamp(first, datetime.timezone.utc) if first else None
        x = {'utc': now.isoformat(), 'pid': os.getpid(), 'wait_start_utc': START.isoformat(),
             'gpu_memory_mib': memory, 'rand3_scored_rows': len(scores),
             'rand3_first_score_utc': started.isoformat() if started else None,
             'elapsed_until_first_score_s': ((started or now) - START).total_seconds(),
             'phase': 'score_outputs_started' if scores else 'waiting_judge_cards',
             'both_judge_nine_ready': gate['all_nine_both_judges_ready'],
             'hb_top1_nine_complete': all(row['hb_top1'] == 2000 for row in gate['units'].values())}
        p = BASE / 'hb_delay_wait_live.json';t=p.with_suffix('.tmp')
        t.write_text(json.dumps(x, indent=2)+'\n');t.replace(p)
        decision = BASE / 'hb_noon_fallback_decision.json'
        if now >= NOON and not decision.exists():
            decision.write_text(json.dumps({**x, 'rescue_needed': not x['hb_top1_nine_complete'],
                'rule': 'Frozen addendum25: no PAIR interruption; verify model/backend gate before any node01 rescue.'}, indent=2)+'\n')
        if len(scores) == 2000 and x['hb_top1_nine_complete']:
            return
        time.sleep(30)


if __name__ == '__main__': main()
