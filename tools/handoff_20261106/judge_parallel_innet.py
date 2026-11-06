from pathlib import Path
import runpy,sys
sys.argv=[str(Path(__file__).with_name('idle_gpu_queue.py')),'wjb']
runpy.run_path(sys.argv[0],run_name='__main__')
