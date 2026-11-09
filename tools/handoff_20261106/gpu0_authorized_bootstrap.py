"""Launch unchanged pinned workers with the authorized scheduling window only."""
from pathlib import Path
import hashlib,json,runpy,sys
from gpu0_day_authorization import install,R,B
def main():
    install();a=json.loads((B/'gpu0_day_authorization.json').read_text());name=sys.argv[1];assert name in a['workers_sha256'];p=R/'tools/handoff_20261106'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==a['workers_sha256'][name];sys.argv=[str(p),*sys.argv[2:]];runpy.run_path(str(p),run_name='__main__')
if __name__=='__main__':main()
