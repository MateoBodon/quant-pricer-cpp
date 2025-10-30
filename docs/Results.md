# Results

## Heston Smile Calibration (2024-06-14)
FAST calibration on the bundled SPX sample keeps the smile within roughly 20 vol points of the synthesized surface, illustrating the full plot/JSON/CSV pipeline without touching the heavy nightly grid.

```bash
python scripts/calibrate_heston.py --input data/samples/spx_20240614_sample.csv --fast
```

- Params: [`artifacts/heston/params_20240614.json`](../artifacts/heston/params_20240614.json)
- Table: [`artifacts/heston/fit_20240614.csv`](../artifacts/heston/fit_20240614.csv)

![Heston fit](../artifacts/heston/fit_20240614.png)

## QMC vs PRNG RMSE Scaling
Sobol QMC shows the expected steeper error decay versus pseudorandom Monte Carlo for both the GBM call and arithmetic Asian payoffs; slopes come directly from randomized replicates stored in the CSV.

```bash
python scripts/qmc_vs_prng.py --fast
```

- Summary: [`artifacts/qmc_vs_prng.csv`](../artifacts/qmc_vs_prng.csv)
- Manifest slice: [`artifacts/manifest.json`](../artifacts/manifest.json)

![QMC vs PRNG](../artifacts/qmc_vs_prng.png)

## American Pricing Consistency
PSOR, CRR, and LSMC agree across the {0.8, 1.0, 1.2} × {0.2, 0.4} grid with LSMC spreads contained within the ±2σ bars, providing regression-quality parity for the American put implementations.

```bash
python scripts/american_consistency.py --fast
```

- Grid dump: [`artifacts/american_consistency.csv`](../artifacts/american_consistency.csv)
- Manifest slice: [`artifacts/manifest.json`](../artifacts/manifest.json)

![American consistency](../artifacts/american_consistency.png)

## PDE Convergence Study
The log–log slope of −2.0± confirms second-order convergence of the Crank–Nicolson PDE engine over successively finer spatial meshes while staying within sub-basis runtime targets.

```bash
python scripts/pde_convergence.py --fast --skip-build
```

- Convergence series: [`artifacts/pde_convergence.csv`](../artifacts/pde_convergence.csv)
- Manifest slice: [`artifacts/manifest.json`](../artifacts/manifest.json)

![PDE convergence](../artifacts/pde_convergence.png)
