#!/usr/bin/env python3
"""As-of correctness checks for WRDS surfaces."""
from __future__ import annotations

from datetime import date
from typing import Iterable, Sequence

import pandas as pd


def _coerce_date(value: object) -> date:
    return pd.to_datetime(value).date()


def _sample_rows(df: pd.DataFrame, mask: pd.Series) -> list[dict[str, object]]:
    if mask.empty or not mask.any():
        return []
    columns = [
        col
        for col in ("trade_date", "quote_date", "tenor_bucket", "moneyness", "strike")
        if col in df.columns
    ]
    if not columns:
        columns = list(df.columns[:5])
    return df.loc[mask, columns].head(5).to_dict(orient="records")


def assert_quote_date_matches(
    df: pd.DataFrame,
    *,
    expected_date: str | date | None = None,
    context: str,
) -> None:
    """Fail if quote_date does not match trade_date (or explicit expected_date)."""
    if df.empty:
        return
    if "quote_date" not in df.columns:
        raise RuntimeError(
            f"[wrds_pipeline] as-of check failed ({context}): missing quote_date column"
        )
    quote_date = pd.to_datetime(df["quote_date"]).dt.date
    if expected_date is None:
        if "trade_date" not in df.columns:
            raise RuntimeError(
                f"[wrds_pipeline] as-of check failed ({context}): missing trade_date column"
            )
        trade_date = pd.to_datetime(df["trade_date"]).dt.date
        mismatch = quote_date != trade_date
        expected_label = "trade_date"
    else:
        expected = _coerce_date(expected_date)
        mismatch = quote_date != expected
        expected_label = f"next_trade_date={expected.isoformat()}"

    if not mismatch.any():
        return

    sample = _sample_rows(df, mismatch)
    count = int(mismatch.sum())
    raise RuntimeError(
        f"[wrds_pipeline] as-of check failed ({context}): "
        f"{count} rows where quote_date != {expected_label}. "
        f"Sample={sample}"
    )

