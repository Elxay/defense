"""CPU contract tests: unequal left padding, alternate position, EOS and cache."""
from types import SimpleNamespace
import torch
from batched_injection300 import generate_batch_with_injection


class Tokenizer:
    padding_side = 'left'
    pad_token_id = 90
    def pad(self, data, **kwargs):
        ids=data['input_ids'];width=max(map(len,ids))
        class Enc(dict):
            def to(self, device):return Enc({k:v.to(device)for k,v in self.items()})
        return Enc(input_ids=torch.tensor([[90]*(width-len(x))+x for x in ids]),
                   attention_mask=torch.tensor([[0]*(width-len(x))+[1]*len(x)for x in ids]))
    def decode(self, ids, **kwargs):return ','.join(map(str,ids))


class Block(torch.nn.Module):
    def forward(self, h):return (h,)


class Model(torch.nn.Module):
    def __init__(self):
        super().__init__();self.anchor=torch.nn.Parameter(torch.zeros(1))
        self.model=SimpleNamespace(layers=[Block()]);self.config=SimpleNamespace(hidden_size=3)
        self.generation_config=SimpleNamespace(eos_token_id=[99,98])
    def generate(self, input_ids, attention_mask, **kwargs):
        n,w=input_ids.shape;assert n==2
        self.prefill=self.model.layers[0](torch.zeros(n,w,3))[0]
        self.decode=self.model.layers[0](torch.ones(n,1,3))[0]
        return torch.cat([input_ids,torch.tensor([[10,98,90],[11,12,13]])],dim=1)


def main():
    tok=Tokenizer();ids=[[3,4],[5,6,7]]
    for positions,expected in [(None,[(0,2),(1,2)]),([0,1],[(0,1),(1,1)])]:
        m=Model();rows=generate_batch_with_injection(m,tok,ids,[1.,2.,2.],layer=0,max_new_tokens=3,positions=positions)
        touched={(int(x[0]),int(x[1]))for x in (m.prefill.norm(dim=-1)>0).nonzero()}
        assert touched==set(expected)
        assert torch.equal(m.decode,torch.ones(2,1,3)), 'No repeated cached decode injection'
        assert [r['injection_count']for r in rows]==[1,1]
        assert [r['rho_runtime']for r in rows]==[3.,3.]
        assert [r['new_tokens']for r in rows]==[2,3]
        assert [r['eos']for r in rows]==[True,False]
        assert [r['input_ids_sha256']for r in rows][0]!=rows[1]['input_ids_sha256']
    m=Model();generate_batch_with_injection(m,tok,ids,[0.,0.,0.],layer=0,max_new_tokens=3)
    assert not torch.any(m.prefill)
    print('PASS: unequal padding, P1/P2 coordinates, one injection per row, decode cache, EOS set, zero delta')


if __name__=='__main__':main()
