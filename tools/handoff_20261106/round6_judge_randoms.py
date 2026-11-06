"""Called only by the existing controller after both randoms finish300."""
from pathlib import Path
import subprocess,os
B=Path('/data/HZX/Def');PY='/home/kemove/anaconda3/envs/HZX_GLA/bin/python'
assert os.environ.get('CUDA_VISIBLE_DEVICES')=='2,3'
subprocess.run([PY,'-u',str(B/'tools/handoff_20261106/round7_hf_window.py')],check=True)
subprocess.run(['bash','-c','source /data/HZX/Def/night/launch.sh\nwait_gpu cuda:2 || exit 1\nwait_gpu cuda:3 || exit 1'],check=True)
subprocess.run([PY,'-u',str(B/'tools/handoff_20261106/round7_guard_pair.py')],env={**os.environ,'CUDA_VISIBLE_DEVICES':'2'},check=True)
subprocess.run([PY,str(B/'tools/handoff_20261106/round7_analyze_window.py')],check=True)
