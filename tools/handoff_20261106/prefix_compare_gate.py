"""Node gate: compare frozen innet reference rows, never judge harmfulness."""
import argparse
from prefix_support import ROOT,BASE,PREFIX,RUNTIME,load,save,sha,utc,verify_record


def main():
    p=argparse.ArgumentParser();p.add_argument('--task',required=True);a=p.parse_args();task=load(a.task);cfg=load(RUNTIME);name=task['condition'];rows=[]
    assert len(task['items'])==20
    for item in task['items']:
        key=item['id'];ref=PREFIX/'generation.private'/name/(key+'.json');other=PREFIX/'node_gate_generated'/name/(key+'.json')
        assert sha(ref)==task['reference_sha256'][key]
        x=verify_record(ref,name,item,cfg);y=verify_record(other,name,item,cfg)
        rows.append({'id':key,'reference_sha256':sha(ref),'node_sha256':sha(other),
            'input_ids_match':x['result']['input_ids_sha256']==y['result']['input_ids_sha256'],
            'byte_identical':x['result']['text'].encode()==y['result']['text'].encode()})
    passed=all(x['byte_identical'] and x['input_ids_match'] for x in rows)
    save(PREFIX/'node_gate_results'/(name+'.json'),{'utc':utc(),'condition':name,'n':20,'passed':passed,'rows':rows})
    if not passed:raise SystemExit(75)


if __name__=='__main__':main()
