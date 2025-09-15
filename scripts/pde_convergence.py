#!/usr/bin/env python3
import subprocess
import os

def run(cmd: str) -> str:
    out = subprocess.check_output(cmd, shell=True, text=True)
    return out.strip()

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
build_dir = os.path.join(root, 'build')
os.makedirs(build_dir, exist_ok=True)
subprocess.check_call(f'cmake -S {root} -B {build_dir} -DCMAKE_BUILD_TYPE=Release', shell=True)
subprocess.check_call(f'cmake --build {build_dir} -j', shell=True)

S, K, r, q, sig, T = 100, 100, 0.02, 0.00, 0.2, 1.0
bs_price = float(run(f'{build_dir}/quant_cli bs {S} {K} {r} {q} {sig} {T} call'))

print("M,N,error (PDE log-space Neumann)")
for M in [101, 201, 401]:
    N = M - 1
    cmd = f'{build_dir}/quant_cli pde {S} {K} {r} {q} {sig} {T} call {M} {N} 4.0 1 1'
    price = float(run(cmd))
    err = abs(price - bs_price)
    print(M, N, err)
