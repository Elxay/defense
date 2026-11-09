"""Current operational snapshot; reads no test labels or outcome summaries."""
from pathlib import Path
import csv,datetime,hashlib,json,os,statistics,subprocess
R=Path('/data/HZX/Def');O=R/'results/audit/crossmodel287'
def local_cards(root):
    registry=(root/'logs/pid_registry.txt').read_text(errors='replace')if(root/'logs/pid_registry.txt').exists()else''
    g=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
    apps=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'],text=True)
    cards=[]
    for row in csv.reader(g.splitlines()):
        index,uuid,memory,util=[x.strip()for x in row];processes=[]
        for entry in csv.reader(apps.splitlines()):
            if entry[0].strip()!=uuid:continue
            pid=int(entry[1]);metadata=subprocess.run(['ps','-o','user=,etime=,args=','-p',str(pid)],capture_output=True,text=True).stdout.strip().split(None,2)
            if len(metadata)!=3:continue
            account,elapsed,args=metadata;tokens=args.split();script=next((Path(t).name for t in tokens if t.endswith(('.py','.sh'))),Path(tokens[0]).name)
            registered=any(line.split('|',1)[0]==str(pid)for line in registry.splitlines())
            ours=registered or (root==Path('/home/dell/Def')and pid==2295103)
            project='Def/'+('PAIR search'if pid==2295103 else script)if ours else'external/unregistered; leave untouched'
            processes.append({'pid':pid,'account':account,'project':project,'registered':registered,'command_name':script,'etime':elapsed,'memory_MiB':entry[2].strip()})
        cards.append({'GPU':int(index),'memory_MiB':int(memory),'utilization_pct':int(util),'processes':processes})
    return cards
def main():
    now=datetime.datetime.now(datetime.timezone.utc)
    result={'utc':now.isoformat(),'date_u':subprocess.check_output(['date','-u','+%Y-%m-%d %H:%M:%S UTC'],text=True).strip(),'innet':local_cards(R)}
    # Reuse only this metadata helper on node01. Never transfer credentials or outcome text.
    helper=Path(__file__).read_text().split('def main():',1)[0]
    node=helper+'''\nb=Path('/home/dell/Def/results/audit/pair500')
paths=sorted((b/'generations.private').glob('*.json'),key=lambda p:p.stat().st_mtime)
seconds=[json.loads(p.read_text())['seconds']for p in paths]
live=json.loads((b/'generation_live.json').read_text())
print(json.dumps({'cards':local_cards(Path('/home/dell/Def')),'PAIR':{'n':len(paths),'PID':live['pid'],'heartbeat_utc':live['utc'],'seconds_per_row_recent10':statistics.mean(seconds[-10:]),'seconds_per_row_all':statistics.mean(seconds),'restart_count':1}}))
'''
    remote=json.loads(subprocess.check_output(['ssh','node01','python3','-'],input=node,text=True));result['node01']=remote['cards'];result['PAIR']=remote['PAIR']
    hb=datetime.datetime.fromisoformat(result['PAIR']['heartbeat_utc'].replace('Z','+00:00'));result['PAIR']['heartbeat_age_seconds']=(datetime.datetime.now(datetime.timezone.utc)-hb).total_seconds()
    x=json.loads((R/'results/audit/pair500/lease_priority/controller_live.json').read_text());result['main_dispatch']={k:x[k]for k in ['utc','pid','phase','source_rows']};result['main_dispatch']['jobs']=[{k:v.get(k)for k in ['kind','cards','condition','launcher_pid']}for v in x['jobs'].values()]
    result['PAIR_generation_coverage']={name:len(list((R/'results/audit/pair500/prefix254/generation.private'/name).glob('*.json')))for name in ['alpha0','old_s3','rand0','old_s4','rand1','old_s5','rand2','old_s6','rand3','old_s7','old_s0','SYS_A','SYS_B']}
    result['new_models']={}
    for key in ['qwen','gemma']:
        p=O/(key+'_preflight.json')
        if p.exists():
            x=json.loads(p.read_text());result['new_models'][key]={k:x.get(k)for k in ['phase','rho','measured_residual_norm_median','rho_multiplier','targets_completed','injection_block','donor_block']if k in x}
            if key=='qwen':
                summary=result['new_models'][key]
                summary['historical_probe_field_rho']=summary.pop('rho',None)
                effective=json.loads((O/'qwen_norm_semantics_addendum2.json').read_text())
                summary['measured_residual_norm_median']=effective['measured_residual_norm_median']
                summary['rho']=effective['training_vector_norm_rho']
                summary['rho_multiplier']=0.9
                summary['training_allowed']=False
    for key,file in [('gemma','gemma_download.json'),('vicuna','vicuna_download_http.json')]:
        x=json.loads((O/file).read_text());result['new_models'].setdefault(key,{})['download']={'phase':x['phase'],'pid':x['pid'],'verified_weight_shards':sum(n.endswith(('.safetensors','.bin'))for n in x['files']),'current_file_downloaded_bytes':x.get('downloaded_bytes')}
    p=O/'gemma_norm_queue_live.json'
    if p.exists():result['Gemma_norm_queue']=json.loads(p.read_text())
    result.update(PAIR_outcome_labels_read=False,new_model_training_started=False)
    p=O/('ops_snapshot_'+now.strftime('%Y%m%d_%H%M%S')+'.json');p.write_text(json.dumps(result,indent=2)+'\n');result['snapshot_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();result['file']=str(p.relative_to(R));print(json.dumps(result))
if __name__=='__main__':main()
