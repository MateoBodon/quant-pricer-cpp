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

S, K, r, q, sig, T = 100, 110, 0.02, 0.00, 0.25, 1.0
bs_price = float(run(f'{build_dir}/quant_cli bs {S} {K} {r} {q} {sig} {T} call'))

rows = [("paths", "prng_err", "qmc_err")]
for paths in [20000, 40000, 80000, 160000, 320000]:
    prng = run(f'{build_dir}/quant_cli mc {S} {K} {r} {q} {sig} {T} {paths} 42 0 none none 64')
    qmc  = run(f'{build_dir}/quant_cli mc {S} {K} {r} {q} {sig} {T} {paths} 42 0 sobol bb 64')
    prng_price = float(prng.split()[0])
    qmc_price  = float(qmc.split()[0])
    rows.append((paths, abs(prng_price - bs_price), abs(qmc_price - bs_price)))

print("QMC vs PRNG absolute error:")
for r in rows:
    print(r)
