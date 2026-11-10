"""B1 utility prefill forward at the deployed final prompt position."""
import hashlib,json,inspect
import torch

def injected_prefill_scores(model,input_ids,attention_mask,vector,layer,candidate_ids):
 assert input_ids.ndim==2 and input_ids.shape[0]==1
 assert bool(torch.all(attention_mask==1)), 'ARC B1 native prompt has no padding'
 width=input_ids.shape[1];state={'count':0};v=torch.as_tensor(vector,dtype=torch.float32)
 assert v.ndim==1 and len(v)==model.config.hidden_size
 def hook(mod,args,output):
  h=output[0]if isinstance(output,tuple)else output
  assert h.shape[:2]==(1,width);z=h.clone();before=z[0,width-1].clone();z[0,width-1]=before+v.to(z.device,z.dtype);state['count']+=1;state['rho_runtime']=float((z[0,width-1]-before).float().norm());return (z,)+output[1:]if isinstance(output,tuple)else z
 kwargs={'input_ids':input_ids,'attention_mask':attention_mask,'position_ids':attention_mask.long().cumsum(-1)-1,'use_cache':True}
 params=inspect.signature(model.forward).parameters
 if 'logits_to_keep'in params:kwargs['logits_to_keep']=1
 elif 'num_logits_to_keep'in params:kwargs['num_logits_to_keep']=1
 hd=model.model.layers[layer].register_forward_hook(hook)
 try:
  with torch.inference_mode():scores=model(**kwargs).logits[0,-1,candidate_ids].float().cpu()
 finally:hd.remove()
 assert state['count']==1
 return scores,dict(injection_count=1,position=width-1,rho_runtime=state['rho_runtime'],input_ids_sha256=hashlib.sha256(json.dumps(input_ids[0].tolist(),separators=(',',':')).encode()).hexdigest(),device_uuid=str(torch.cuda.get_device_properties(input_ids.device).uuid))
