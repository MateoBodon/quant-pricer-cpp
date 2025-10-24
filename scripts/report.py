#!/usr/bin/env python3
"""
Generate figures and a PDF report from options CSV, calibration JSON, and returns CSV.

Outputs to artifacts/ by default:
  - heston_error_heatmap.png (price error in bps across moneyness×tenor)
  - var_backtest.png (rolling VaR and exceptions)
  - onepager.pdf / twopager.pdf (stitched overview)

Usage:
  python scripts/report.py \
    --options_csv data/options.csv \
    --calib_json artifacts/heston_calib.json \
    --returns_csv data/returns.csv \
    --artifacts_dir artifacts
"""
import argparse
import json
import math
import os
import subprocess
import sys


def ensure_matplotlib():
    try:
        import matplotlib.pyplot as plt  # noqa: F401
        from matplotlib.backends.backend_pdf import PdfPages  # noqa: F401
        import numpy as np  # noqa: F401
        import pandas as pd  # noqa: F401
    except Exception:  # pragma: no cover
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'matplotlib', 'pandas', 'numpy'])


def run_cli(args):
    out = subprocess.check_output(args, text=True).strip()
    return out


def price_heston_cli(cli_path, row, calib):
    args = [
        cli_path, 'heston',
        str(calib['kappa']), str(calib['theta']), str(calib['sigma']), str(calib['rho']), str(calib['v0']),
        str(row['spot']), str(row['strike']), str(row['rate']), str(row['q']), str(row['maturity_years']),
        '0', '1', '0', '--analytic'
    ]
    try:
        return float(run_cli(args))
    except Exception:
        return float('nan')


def build_error_heatmap(cli_path, options_csv, calib_json, out_png):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    with open(calib_json, 'r') as fh:
        calib = json.load(fh)

    df = pd.read_csv(options_csv)
    df = df[(df['maturity_years'] > 1/365.0) & (df['mid'] > 0)]
    df['moneyness'] = df['strike'] / df['spot']
    # model price
    df['model'] = df.apply(lambda r: price_heston_cli(cli_path, r, calib), axis=1)
    # parity for puts
    df.loc[df['call_put'] == 'put', 'model'] = (
        df.loc[df['call_put'] == 'put', 'model'] - df.loc[df['call_put'] == 'put', 'spot'] * np.exp(-df.loc[df['call_put'] == 'put', 'q'] * df.loc[df['call_put'] == 'put', 'maturity_years'])
        + df.loc[df['call_put'] == 'put', 'strike'] * np.exp(-df.loc[df['call_put'] == 'put', 'rate'] * df.loc[df['call_put'] == 'put', 'maturity_years'])
    )
    df['err_bps'] = 1e4 * (df['model'] - df['mid']) / df['spot']

    # pivot into heatmap grid
    m_bins = np.linspace(0.7, 1.3, 25)
    t_bins = np.linspace(df['maturity_years'].min(), df['maturity_years'].max(), 20)
    H = np.full((len(t_bins)-1, len(m_bins)-1), np.nan)
    for i in range(len(t_bins)-1):
        for j in range(len(m_bins)-1):
            cell = df[(df['maturity_years'] >= t_bins[i]) & (df['maturity_years'] < t_bins[i+1]) &
                      (df['moneyness'] >= m_bins[j]) & (df['moneyness'] < m_bins[j+1])]
            if not cell.empty:
                H[i, j] = cell['err_bps'].mean()

    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(H, aspect='auto', origin='lower',
                   extent=[m_bins[0], m_bins[-1], t_bins[0], t_bins[-1]], cmap='coolwarm')
    ax.set_xlabel('Moneyness K/S')
    ax.set_ylabel('Maturity (years)')
    ax.set_title('Heston price error (bps)')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('bps')
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close(fig)


def build_var_plot(returns_csv, out_png, alpha=0.99):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    df = pd.read_csv(returns_csv)
    df = df.dropna(subset=['ret'])
    window = 250
    z = 2.3263478740408408
    var = []
    exc = []
    for i in range(len(df)):
        if i < window:
            var.append(float('nan'))
            exc.append(float('nan'))
            continue
        mu = df['ret'].iloc[i-window:i].mean()
        sd = df['ret'].iloc[i-window:i].std()
        v = -(mu - z * sd)
        var.append(v)
        exc.append(1.0 if df['ret'].iloc[i] < -v else 0.0)
    df['var'] = var
    df['exc'] = exc
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(df['var'], label='VaR (1d, 99%)')
    ax.plot(-df['ret'], alpha=0.5, label='-Return')
    ax.scatter(df.index[df['exc'] == 1.0], -df['ret'][df['exc'] == 1.0], color='red', s=8, label='Exceptions')
    ax.legend(loc='upper right')
    ax.set_title('VaR backtest (rolling normal)')
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close(fig)


def stitch_pdf(artifacts_dir, images, pdf_name):
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    pdf_path = os.path.join(artifacts_dir, pdf_name)
    with PdfPages(pdf_path) as pdf:
        rows = 2
        cols = 2
        fig, axes = plt.subplots(rows, cols, figsize=(11.0, 8.5))
        axes = axes.flatten()
        for ax, img in zip(axes, images):
            if not os.path.exists(img):
                continue
            im = plt.imread(img)
            ax.imshow(im)
            ax.axis('off')
        pdf.savefig(fig)
        plt.close(fig)
    print('wrote', pdf_path)


def main():
    ensure_matplotlib()
    import pandas as pd

    ap = argparse.ArgumentParser()
    ap.add_argument('--options_csv', required=True)
    ap.add_argument('--calib_json', required=True)
    ap.add_argument('--returns_csv', required=True)
    ap.add_argument('--artifacts_dir', default='artifacts')
    ap.add_argument('--cli', default=os.path.join('build', 'quant_cli'))
    args = ap.parse_args()

    os.makedirs(args.artifacts_dir, exist_ok=True)
    heatmap = os.path.join(args.artifacts_dir, 'heston_error_heatmap.png')
    build_error_heatmap(args.cli, args.options_csv, args.calib_json, heatmap)

    var_png = os.path.join(args.artifacts_dir, 'var_backtest.png')
    build_var_plot(args.returns_csv, var_png)

    # stitch
    stitch_pdf(args.artifacts_dir, [heatmap, var_png], 'onepager.pdf')


if __name__ == '__main__':
    main()


