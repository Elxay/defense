"""Redacted credential-prefix audit. Never emit matching strings or diffs."""
import collections
import datetime
import json
import os
from pathlib import Path
import re
import stat
import subprocess

ROOT=Path('/data/HZX/Def');REPO=ROOT/'prereg_repo'
PAT=re.compile(rb'hf_[A-Za-z0-9]{20,}')


def scan_stream(f,n=None):
    carry=b'';hits=0
    while n is None or n>0:
        chunk=f.read(1024*1024 if n is None else min(n,1024*1024))
        if not chunk:break
        if n is not None:n-=len(chunk)
        data=carry+chunk
        cutoff=len(data) if n==0 else max(0,len(data)-512)
        hits+=sum(m.start()<cutoff for m in PAT.finditer(data))
        carry=data[cutoff:]
    if n!=0:hits+=len(PAT.findall(carry))
    return hits


def main():
    files=set();errors=[];symlinks=0
    roots=[ROOT/p for p in ['paper','docs','night','tools','scripts','src','configs','env','status','logs','prereg_repo']]+[Path('/tmp')]
    if (REPO/'.git/config').is_file():files.add(REPO/'.git/config')
    for p in ROOT.iterdir():
        if p.is_file() and not p.is_symlink():files.add(p)
    for root in roots:
        for directory,dirs,names in os.walk(root,followlinks=False,onerror=lambda e:errors.append({'kind':type(e).__name__,'path':str(e.filename)})):
            dirs[:]=[d for d in dirs if d!='.git' and not (Path(directory)/d).is_symlink()]
            for name in names:
                p=Path(directory)/name
                try:
                    st=p.lstat()
                    if stat.S_ISLNK(st.st_mode):symlinks+=1
                    elif stat.S_ISREG(st.st_mode):files.add(p)
                except OSError as e:errors.append({'kind':type(e).__name__,'path':str(p)})
    hits=[];scanned=0;total_bytes=0
    for p in sorted(files):
        try:
            with p.open('rb') as f:n=scan_stream(f)
            scanned+=1;total_bytes+=p.stat().st_size
            if n:hits.append({'path':str(p),'candidate_prefix_matches':n})
        except OSError as e:errors.append({'kind':type(e).__name__,'path':str(p)})
    git=lambda *args:subprocess.check_output(['git','-C',str(REPO),*args])
    pickaxe=git('log','--all','-S','hf_','--format=%H','--name-only').decode().splitlines()
    objects=git('rev-list','--objects','--all').decode().splitlines()
    object_paths={s.split(' ',1)[0]:s.split(' ',1)[1] if ' ' in s else '' for s in objects}
    checked=subprocess.check_output(['git','-C',str(REPO),'cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize)'],input=('\n'.join(object_paths)+'\n').encode()).decode().splitlines()
    blobs=[line.split()[0] for line in checked if line.split()[1]=='blob']
    # One subprocess per blob keeps binary protocol boundaries simple and auditable.
    history_hits=[]
    for oid in blobs:
        proc=subprocess.Popen(['git','-C',str(REPO),'cat-file','blob',oid],stdout=subprocess.PIPE)
        count=scan_stream(proc.stdout);proc.stdout.close();assert proc.wait()==0
        if count:history_hits.append({'blob':oid,'path_hint':object_paths[oid],'candidate_prefix_matches':count})
    tracked=git('ls-files','-z').decode().split('\0');tracked=[p for p in tracked if p]
    largest=sorted([{'path':p,'bytes':(REPO/p).stat().st_size} for p in tracked],key=lambda x:x['bytes'],reverse=True)[:10]
    forbidden=[p for p in tracked if Path(p).suffix.lower() in {'.npy','.npz','.pt','.pth','.bin','.safetensors','.ckpt'} or '.private' in p or 'generations.private' in p]
    suspicious_json=[]
    def inspect(value,path):
        if isinstance(value,dict):
            for k,v in value.items():
                if k.lower() in {'text','prompt','response','generation','completion'} and isinstance(v,str) and len(v)>160:suspicious_json.append({'path':path,'field':k,'length':len(v)})
                inspect(v,path)
        elif isinstance(value,list):
            for v in value:inspect(v,path)
    for p in tracked:
        if p.endswith('.json'):
            try:inspect(json.loads((REPO/p).read_text()),p)
            except (ValueError,UnicodeError):pass
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_roots':[str(p) for p in roots],
        'root_level_files_included':True,'follow_symlinks':False,'symlink_files_skipped':symlinks,'scanned_files':scanned,'scanned_bytes':total_bytes,
        'working_tree_candidate_hits':hits,'errors_or_unreadable':errors,'git_pickaxe_command':"git log --all -S 'hf_' --format=%H --name-only",
        'git_pickaxe_matching_commits':len({p for p in pickaxe if re.fullmatch('[0-9a-f]{40}',p)}),
        'git_commit_message_candidate_count':len(PAT.findall(git('log','--all','--format=%B'))),
        'history_unique_blobs_scanned':len(blobs),'history_candidate_hits':history_hits,'tracked_count':len(tracked),'largest10':largest,
        'tracked_forbidden_path_or_extension':forbidden,'tracked_long_raw_text_fields':suspicious_json,
        'content_check_limit':'Structured JSON text-field heuristic and forbidden paths/extensions; not a semantic proof that every document is free of attack examples.'}
    out=ROOT/'results/audit/pair500/wildguard/expanded_credential_git_audit.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
