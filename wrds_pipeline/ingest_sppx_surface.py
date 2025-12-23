#!/usr/bin/env python3
"""OptionMetrics SPX ingestion + aggregation helpers.

If WRDS_LOCAL_ROOT is explicitly set (or a dateset config provides a local
root), local OptionMetrics parquet is read before cache/live WRDS. If
WRDS_CACHE_ROOT is set (or /Volumes/Storage/Data/wrds_cache exists), raw WRDS
slices are cached as parquet and reused on subsequent runs.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

from .bs_utils import bs_vega, implied_vol_from_price

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PATH_ENV = "WRDS_SAMPLE_PATH"
SAMPLE_PATH = Path(__file__).resolve().parent / "sample_data" / "spx_options_sample.csv"
SPOT_FALLBACK = 4500.0
MIN_DTE_DAYS = 21  # ignore ultra-short tenor noise for calibration/OOS
CACHE_ROOT_ENV = "WRDS_CACHE_ROOT"
DEFAULT_CACHE_ROOT = Path("/Volumes/Storage/Data/wrds_cache")
LOCAL_ROOT_ENV = "WRDS_LOCAL_ROOT"


def _resolve_sample_path() -> Path:
    raw = os.environ.get(SAMPLE_PATH_ENV)
    if not raw:
        return SAMPLE_PATH
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return candidate


def _cache_root() -> Path | None:
    root = os.environ.get(CACHE_ROOT_ENV)
    if root:
        return Path(root).expanduser()
    if DEFAULT_CACHE_ROOT.exists():
        return DEFAULT_CACHE_ROOT
    return None


def _local_root(explicit_root: Path | str | None = None) -> Path | None:
    root = explicit_root or os.environ.get(LOCAL_ROOT_ENV)
    if not root:
        return None
    candidate = Path(root).expanduser()
    optionm_root = candidate / "raw" / "optionm"
    if (
        (optionm_root / "opprcd").exists()
        and (optionm_root / "secprd").exists()
        and (optionm_root / "secnmd.parquet").exists()
    ):
        return candidate
    return None


def _local_optionm_root(local_root: Path | None) -> Path | None:
    if local_root is None:
        return None
    return local_root / "raw" / "optionm"


def _local_opprcd_path(trade_date: str, local_root: Path | None) -> Path | None:
    optionm_root = _local_optionm_root(local_root)
    if optionm_root is None:
        return None
    year = pd.to_datetime(trade_date).year
    return optionm_root / "opprcd" / f"opprcd_{year}.parquet"


def _local_secprd_path(trade_date: str, local_root: Path | None) -> Path | None:
    optionm_root = _local_optionm_root(local_root)
    if optionm_root is None:
        return None
    year = pd.to_datetime(trade_date).year
    return optionm_root / "secprd" / f"secprd_{year}.parquet"


def _local_secnmd_path(local_root: Path | None) -> Path | None:
    optionm_root = _local_optionm_root(local_root)
    if optionm_root is None:
        return None
    return optionm_root / "secnmd.parquet"


def _resolve_secid_local(symbol: str, trade_date: str, local_root: Path | None) -> int:
    secnmd_path = _local_secnmd_path(local_root)
    if secnmd_path is None or not secnmd_path.exists():
        raise RuntimeError("Local WRDS secnmd.parquet not found")
    symbol = symbol.upper()
    try:
        import pyarrow.dataset as ds  # type: ignore
        table = ds.dataset(secnmd_path).to_table(
            filter=ds.field("ticker") == symbol,
            columns=["secid", "effect_date", "ticker"],
        )
        df = table.to_pandas()
    except Exception:
        df = pd.read_parquet(secnmd_path, columns=["secid", "effect_date", "ticker"])
        df = df[df["ticker"] == symbol]
    if df.empty:
        raise RuntimeError(f"Local WRDS missing secid for ticker {symbol}")
    df["effect_date"] = pd.to_datetime(df["effect_date"])
    trade_dt = pd.to_datetime(trade_date)
    df = df[df["effect_date"] <= trade_dt]
    if df.empty:
        raise RuntimeError(f"Local WRDS missing secid for ticker {symbol} @ {trade_date}")
    secid = df.sort_values("effect_date").iloc[-1]["secid"]
    return int(secid)


def _fetch_from_local(
    symbol: str, trade_date: str, local_root: Path | None
) -> pd.DataFrame:
    opprcd_path = _local_opprcd_path(trade_date, local_root)
    secprd_path = _local_secprd_path(trade_date, local_root)
    if opprcd_path is None or secprd_path is None:
        raise RuntimeError("Local WRDS OptionMetrics paths not found")
    if not opprcd_path.exists() or not secprd_path.exists():
        raise RuntimeError(f"Local WRDS missing parquet for {trade_date}")
    secid = _resolve_secid_local(symbol, trade_date, local_root)
    secid_val = float(secid)
    try:
        import pyarrow.dataset as ds  # type: ignore
        op_dataset = ds.dataset(opprcd_path)
        filt = (
            (ds.field("secid") == secid_val)
            & (ds.field("date") == str(trade_date))
            & (ds.field("cp_flag") == "C")
            & (ds.field("best_bid") > 0)
            & (ds.field("best_offer") > ds.field("best_bid"))
        )
        columns = [
            "date",
            "exdate",
            "cp_flag",
            "strike_price",
            "best_bid",
            "best_offer",
            "forward_price",
        ]
        table = op_dataset.to_table(filter=filt, columns=columns)
        df = table.to_pandas()
    except Exception:
        df = pd.read_parquet(opprcd_path)
        df = df[
            (df["secid"] == secid_val)
            & (df["date"] == str(trade_date))
            & (df["cp_flag"] == "C")
            & (df["best_bid"] > 0)
            & (df["best_offer"] > df["best_bid"])
        ]
        df = df[
            [
                "date",
                "exdate",
                "cp_flag",
                "strike_price",
                "best_bid",
                "best_offer",
                "forward_price",
            ]
        ]

    if df.empty:
        return df
    df["strike"] = df["strike_price"] / 1000.0
    df.drop(columns=["strike_price"], inplace=True)

    try:
        import pyarrow.dataset as ds  # type: ignore
        sec_dataset = ds.dataset(secprd_path)
        spot_table = sec_dataset.to_table(
            filter=(ds.field("secid") == secid_val) & (ds.field("date") == str(trade_date)),
            columns=["close"],
        )
        spot_df = spot_table.to_pandas()
    except Exception:
        spot_df = pd.read_parquet(secprd_path, columns=["date", "secid", "close"])
        spot_df = spot_df[
            (spot_df["secid"] == secid_val) & (spot_df["date"] == str(trade_date))
        ]
    spot_val = float(spot_df["close"].iloc[0]) if not spot_df.empty else SPOT_FALLBACK
    df["spot"] = spot_val
    if "rate" not in df.columns:
        df["rate"] = 0.015
    if "divyield" not in df.columns:
        df["divyield"] = 0.01
    return df


def _cache_path(symbol: str, trade_date: str) -> Path | None:
    root = _cache_root()
    if root is None:
        return None
    date = pd.to_datetime(trade_date).date()
    symbol = symbol.upper()
    return root / "optionm" / symbol / str(date.year) / f"{symbol.lower()}_{date}.parquet"


def _cache_meta_path(cache_path: Path) -> Path:
    return cache_path.with_suffix(".json")


def _load_cache(symbol: str, trade_date: str) -> pd.DataFrame | None:
    cache_path = _cache_path(symbol, trade_date)
    if cache_path is None or not cache_path.exists():
        return None
    try:
        return pd.read_parquet(cache_path)
    except Exception as exc:  # pragma: no cover
        print(f"[wrds_pipeline] cache read failed ({cache_path}): {exc}")
        return None


def _write_cache(symbol: str, trade_date: str, df: pd.DataFrame, source: str) -> None:
    cache_path = _cache_path(symbol, trade_date)
    if cache_path is None:
        return
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, index=False, compression="zstd")
    meta = {
        "symbol": symbol.upper(),
        "trade_date": str(pd.to_datetime(trade_date).date()),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "source": source,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _cache_meta_path(cache_path).write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")


def _has_wrds_credentials() -> bool:
    return (
        os.environ.get("WRDS_ENABLED") == "1"
        and bool(os.environ.get("WRDS_USERNAME"))
        and bool(os.environ.get("WRDS_PASSWORD"))
    )


def _table_for_trade_date(trade_date: str) -> str:
    year = pd.to_datetime(trade_date).year
    return f"opprcd{year}"


def _secprd_table(trade_date: str) -> str:
    year = pd.to_datetime(trade_date).year
    return f"secprd{year}"


def _resolve_secid(conn, ticker: str, trade_date: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT secid
        FROM optionm.secnmd
        WHERE ticker = %s AND effect_date <= %s
        ORDER BY effect_date DESC
        LIMIT 1
        """,
        (ticker, trade_date),
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        raise RuntimeError(f"WRDS missing secid for ticker {ticker}")
    return int(row[0])


def _fetch_from_wrds(symbol: str, trade_date: str) -> pd.DataFrame:
    try:
        import psycopg2
        from psycopg2 import errors
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("psycopg2 is required for WRDS access") from exc

    username = os.environ["WRDS_USERNAME"]
    password = os.environ["WRDS_PASSWORD"]
    conn = psycopg2.connect(
        host="wrds-pgdata.wharton.upenn.edu",
        port=9737,
        database="wrds",
        user=username,
        password=password,
    )
    table = _table_for_trade_date(trade_date)
    secid = _resolve_secid(conn, symbol, trade_date)
    base_query = f"""
        SELECT
            date,
            exdate,
            cp_flag,
            strike_price / 1000.0 AS strike,
            best_bid,
            best_offer,
            forward_price
        FROM optionm.{table}
        WHERE secid = %s
          AND date = %s
          AND cp_flag = 'C'
          AND best_bid IS NOT NULL
          AND best_offer IS NOT NULL
          AND best_bid > 0
          AND best_offer > best_bid
        LIMIT 6000
    """
    fallback_query = base_query
    try:
        df = pd.read_sql(base_query, conn, params=[secid, trade_date])
        spot_query = f"""
            SELECT close
            FROM optionm.{_secprd_table(trade_date)}
            WHERE secid = %s AND date = %s
            LIMIT 1
        """
        spot_df = pd.read_sql(spot_query, conn, params=[secid, trade_date])
        spot_val = float(spot_df["close"].iloc[0]) if not spot_df.empty else SPOT_FALLBACK
        df["spot"] = spot_val
    except errors.UndefinedTable as exc:  # pragma: no cover
        conn.close()
        raise RuntimeError(f"WRDS table optionm.{table} unavailable") from exc
    except Exception as exc:
        conn.close()
        raise
    finally:
        conn.close()
    if "rate" not in df.columns:
        df["rate"] = 0.015
    if "divyield" not in df.columns:
        df["divyield"] = 0.01
    return df


def _load_sample(symbol: str, trade_date: str) -> pd.DataFrame:
    sample_path = _resolve_sample_path()
    if not sample_path.exists():
        raise RuntimeError(f"Sample data file not found: {sample_path}")
    df = pd.read_csv(sample_path, comment="#")
    for col in ("trade_date", "quote_date", "exdate"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    df = df[df["trade_date"] == pd.to_datetime(trade_date)]
    if df.empty:
        raise RuntimeError(f"Sample data missing trade date {trade_date}")
    df = df.copy()
    df["cp_flag"] = "C"
    df["strike"] = df["strike_price"] / 1.0
    bid_col = "best_bid" if "best_bid" in df.columns else "bid"
    offer_col = "best_offer" if "best_offer" in df.columns else "ask"
    if bid_col not in df.columns or offer_col not in df.columns:
        raise RuntimeError("Sample data missing bid/ask columns")
    df["best_bid"] = df[bid_col]
    df["best_offer"] = df[offer_col]
    df["rate"] = df.get("rate", 0.015)
    df["divyield"] = df.get("dividend", 0.01)
    df["underlying_bid"] = df.get("spot", SPOT_FALLBACK)
    df["underlying_ask"] = df.get("spot", SPOT_FALLBACK)
    if "quote_date" not in df.columns:
        df["quote_date"] = df["trade_date"]
    return df[
        [
            "trade_date",
            "quote_date",
            "exdate",
            "cp_flag",
            "strike",
            "best_bid",
            "best_offer",
            "forward_price",
            "underlying_bid",
            "underlying_ask",
            "rate",
            "divyield",
        ]
    ]


def load_surface(
    symbol: str,
    trade_date: str,
    force_sample: bool = False,
    *,
    local_root: Path | None = None,
) -> Tuple[pd.DataFrame, str]:
    trade_date = pd.to_datetime(trade_date).date()
    if not force_sample:
        resolved_local = _local_root(local_root)
        if resolved_local is not None:
            try:
                local_df = _fetch_from_local(symbol, str(trade_date), resolved_local)
                if not local_df.empty:
                    local_df["trade_date"] = pd.to_datetime(local_df["date"])
                    local_df.drop(columns=["date"], inplace=True)
                    return _standardize_quote_date(local_df), "local"
            except Exception as exc:
                print(f"[wrds_pipeline] local WRDS fetch failed ({exc}); falling back")
        cached = _load_cache(symbol, str(trade_date))
        if cached is not None and not cached.empty:
            return _standardize_quote_date(cached), "cache"
    if not force_sample and _has_wrds_credentials():
        try:
            raw = _fetch_from_wrds(symbol, str(trade_date))
            raw["trade_date"] = pd.to_datetime(raw["date"])
            raw.drop(columns=["date"], inplace=True)
            raw = _standardize_quote_date(raw)
            _write_cache(symbol, str(trade_date), raw, "wrds")
            return raw, "wrds"
        except Exception as exc:  # pragma: no cover
            print(
                f"[wrds_pipeline] WRDS fetch failed ({exc}); falling back to sample data"
            )
    sample = _load_sample(symbol, str(trade_date))
    return _standardize_quote_date(sample), "sample"


def _standardize_quote_date(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    if "quote_date" in df.columns:
        df["quote_date"] = pd.to_datetime(df["quote_date"])
    else:
        df["quote_date"] = df["trade_date"]
    return df


def _prepare_quotes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["quote_date"] = pd.to_datetime(df.get("quote_date", df["trade_date"]))
    df["exdate"] = pd.to_datetime(df["exdate"])
    df["days_to_expiration"] = (df["exdate"] - df["trade_date"]).dt.days
    df = df[df["days_to_expiration"] >= MIN_DTE_DAYS]
    df["ttm_years"] = df["days_to_expiration"] / 365.0
    df["option_mid"] = 0.5 * (df["best_bid"] + df["best_offer"])
    df = df[(df["option_mid"] > 0.01)]
    if "underlying_bid" in df.columns and "underlying_ask" in df.columns:
        underlying_mid = 0.5 * (df["underlying_bid"] + df["underlying_ask"])
    else:
        underlying_mid = pd.Series(np.nan, index=df.index)
    base_spot = df["spot"] if "spot" in df.columns else pd.Series(np.nan, index=df.index)
    forward = df["forward_price"] if "forward_price" in df.columns else pd.Series(np.nan, index=df.index)
    df["spot"] = (
        base_spot.fillna(underlying_mid).fillna(forward).fillna(SPOT_FALLBACK)
    )
    df["spot"] = np.clip(df["spot"], 1000.0, 20000.0)
    df["rate"] = df.get("rate", 0.015).fillna(0.015)
    df["dividend"] = df.get("dividend", df.get("divyield", 0.01)).fillna(0.01)
    df["strike"] = df["strike"].fillna(df.get("strike_price", df["spot"]))
    df = df[df["strike"] > 0]
    df["moneyness"] = df["strike"] / df["spot"]
    # Trim wings; extreme OTM quotes dominate error tails but carry little vega.
    df = df[df["moneyness"].between(0.75, 1.25)]

    def _compute_iv(row: pd.Series) -> float:
        return implied_vol_from_price(
            price=float(row["option_mid"]),
            spot=float(row["spot"]),
            strike=float(row["strike"]),
            rate=float(row["rate"]),
            div=float(row["dividend"]),
            T=float(row["ttm_years"]),
            option="call",
        )

    df["mid_iv"] = df.apply(_compute_iv, axis=1).clip(0.05, 3.0)
    # Discard nodes that hit the clip boundaries; they originate from noisy quotes
    # and destabilise the Heston calibration objective.
    df = df[(df["mid_iv"] > 0.051) & (df["mid_iv"] < 2.99)]
    df["vega"] = df.apply(
        lambda row: bs_vega(
            float(row["spot"]),
            float(row["strike"]),
            float(row["rate"]),
            float(row["dividend"]),
            float(row["mid_iv"]),
            float(row["ttm_years"]),
        ),
        axis=1,
    )
    df = df[df["vega"] > 1e-5]
    return df


def aggregate_surface(df: pd.DataFrame) -> pd.DataFrame:
    quotes = _prepare_quotes(df)
    if quotes.empty:
        raise RuntimeError("No valid quotes after filtering")
    bins_days = [0, 45, 75, 120, 240, 720]
    labels = ["30d", "60d", "90d", "6m", "1y"]
    quotes["tenor_bucket"] = pd.cut(
        quotes["days_to_expiration"],
        bins=bins_days,
        labels=labels,
        include_lowest=True,
    )
    quotes = quotes.dropna(subset=["tenor_bucket"])
    quotes["moneyness_bucket"] = np.round(quotes["moneyness"], 2)
    grouped = (
        quotes.groupby(
            ["tenor_bucket", "moneyness_bucket"],
            observed=True,
            as_index=True,
        )
        .agg(
            trade_date=("trade_date", "first"),
            quote_date=("quote_date", "first"),
            spot=("spot", "mean"),
            strike=("strike", "mean"),
            rate=("rate", "mean"),
            dividend=("dividend", "mean"),
            ttm_years=("ttm_years", "mean"),
            days_to_expiration=("days_to_expiration", "mean"),
            mid_price=("option_mid", "mean"),
            mid_iv=("mid_iv", "mean"),
            vega=("vega", "mean"),
            quotes=("option_mid", "count"),
        )
        .reset_index()
    )
    grouped = grouped[grouped["quotes"] >= 1]
    grouped["symbol"] = "SPX"
    grouped["moneyness"] = grouped["moneyness_bucket"]
    columns = [
        "symbol",
        "trade_date",
        "quote_date",
        "tenor_bucket",
        "moneyness",
        "ttm_years",
        "days_to_expiration",
        "spot",
        "strike",
        "rate",
        "dividend",
        "mid_price",
        "mid_iv",
        "vega",
        "quotes",
    ]
    return (
        grouped[columns]
        .sort_values(["tenor_bucket", "moneyness"])
        .reset_index(drop=True)
    )


def write_surface(out_path: Path, df: pd.DataFrame) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


def has_wrds_credentials(local_root: Path | None = None) -> bool:
    if _has_wrds_credentials():
        return True
    if _local_root(local_root) is not None:
        return True
    cache_root = _cache_root()
    if cache_root is None:
        return False
    return (cache_root / "cache_manifest.json").exists()


if __name__ == "__main__":  # pragma: no cover
    data, source = load_surface("SPX", datetime.now().strftime("%Y-%m-%d"))
    agg = aggregate_surface(data)
    write_surface(Path("docs/artifacts/wrds/spx_surface_debug.csv"), agg)
    print(f"{source}: wrote {len(agg)} aggregated rows")
