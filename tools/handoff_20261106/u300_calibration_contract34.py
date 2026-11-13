"""Shared calibration execution contract. Must be called before selection admission."""
import hashlib,json,math
def assert_runtime_norm(runtime,alpha,rho,tolerance=.01):
 expected=float(alpha)*float(rho)
 assert math.isfinite(runtime) and math.isfinite(expected)
 error=abs(runtime-expected)
 assert error<=1e-7 if expected==0 else error/expected<=tolerance
 return dict(expected=expected,runtime=runtime,relative_error=error/expected if expected else 0.)
def assert_distinct_adjacent(previous,current):
 assert set(previous)==set(current) and previous
 equal=sum(previous[i]==current[i] for i in previous)
 assert equal<len(previous),'Adjacent alpha output hashes are all identical; block selection'
 return dict(N=len(previous),byte_identical=equal,all_identical=False)
