"""Pre-read overflow policy: token bisection, same backend, explicit row flags."""
def chunk_bounds(n,limit=2048,margin=200):
    assert n>0 and limit>2*margin
    result=[]
    def split(lo,hi):
        if hi-lo<=limit:result.append((lo,hi));return
        mid=lo+(hi-lo)//2
        split(lo,min(hi,mid+margin));split(max(lo,mid-margin),hi)
    split(0,n);return result

def self_test():
    assert chunk_bounds(2048)==[(0,2048)]
    assert chunk_bounds(2100)==[(0,1250),(850,2100)]
    # The legacy +/-200 indices share400 tokens, rather than200 in total.
    assert 1250-850==400
    for n in [1,1900,1962,2048,2049,2100,4096,8192,32768]:
        bounds=chunk_bounds(n);assert bounds[0][0]==0 and bounds[-1][1]==n
        assert all(0<=a<b<=n and b-a<=2048 for a,b in bounds)
        assert all(bounds[i][1]>=bounds[i+1][0]for i in range(len(bounds)-1))
    return {'cases':9,'coverage_and_max_length':'PASS','legacy_midpoint_indices':'PASS','model_inference_performed':False}
