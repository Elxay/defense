"""HF target injection adapter preserving the upstream generation kwargs."""
import hashlib,json,socket
import torch


def generate_with_injection(model, encoded, vector, layer, generation_kwargs,
                            original_generate=None):
    ids=encoded['input_ids'];mask=encoded.get('attention_mask',torch.ones_like(ids));batch,width=ids.shape
    positions=(mask*torch.arange(width,device=mask.device)).max(dim=1).values
    assert torch.all(mask[:,-1]==1),'Frozen target batches use left padding'
    v=torch.as_tensor(vector,dtype=torch.float32);assert v.ndim==1 and v.numel()==model.config.hidden_size
    state={'count':0}
    def hook(module,args,output):
        if state['count']:return output
        h=output[0].clone();assert h.shape[:2]==ids.shape
        rows=torch.arange(batch,device=h.device);p=positions.to(h.device);before=h[rows,p].clone()
        h[rows,p]=before+v.to(device=h.device,dtype=h.dtype)
        state['runtime_norms']=(h[rows,p]-before).float().norm(dim=-1).tolist();state['count']+=1
        return(h,)+output[1:]
    handle=model.model.layers[layer].register_forward_hook(hook)
    try:
        with torch.no_grad():out=(original_generate or model.generate)(**encoded,**generation_kwargs)
    finally:handle.remove()
    assert state['count']==1
    return out,{'injection_count_per_row':[1]*batch,'positions':positions.tolist(),
                'rho_runtime':state['runtime_norms'],'batch_size':batch,'host':socket.gethostname(),
                'vector_sha256':hashlib.sha256((v.cpu().numpy()+0.).tobytes()).hexdigest(),
                'input_ids_sha256':hashlib.sha256(json.dumps(ids.tolist(),separators=(',',':')).encode()).hexdigest(),
                'generation_kwargs':generation_kwargs}


def call_upstream_with_injection(upstream_batch_function, target, prompts, vector,
                                 layer, batch_size, **generation_kwargs):
    """Leave upstream tokenization, chunking and decoding unmodified."""
    original=target.model.generate;metadata=[]
    def wrapped(*args,**kwargs):
        assert not args
        encoded={k:kwargs.pop(k)for k in ['input_ids','attention_mask','token_type_ids','position_ids']if k in kwargs}
        output,receipt=generate_with_injection(target.model,encoded,vector,layer,kwargs,original_generate=original)
        metadata.append(receipt);return output
    target.model.generate=wrapped
    try:outputs=upstream_batch_function(target,batch_size,prompts,**generation_kwargs)
    finally:target.model.generate=original
    return outputs,metadata
