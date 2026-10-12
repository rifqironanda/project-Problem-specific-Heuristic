"""Strict daily-return ingestion; no implicit filling or future information."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd


def validate_returns(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError('Index must be dates')
    if frame.index.has_duplicates or frame.index.isna().any():
        raise ValueError('Dates must be unique and valid')
    if frame.columns.has_duplicates or len(frame.columns) < 2:
        raise ValueError('Need at least two unique asset columns')
    frame = frame.sort_index().astype(float)
    if len(frame) < 80:
        raise ValueError('Need at least 80 daily observations')
    if not np.isfinite(frame.to_numpy()).all() or (frame <= -1).any().any():
        raise ValueError('Returns must be finite decimal values greater than -1; no missing values')
    if (frame.abs() > 2).any().any():
        raise ValueError('Unexpected return scale: use decimal, not percentage')
    frame.columns = frame.columns.astype(str)
    return frame


def read_csv(path_or_buffer, kind='returns'):
    frame = pd.read_csv(path_or_buffer)
    if 'date' not in frame:
        raise ValueError('CSV requires date column')
    dates = pd.to_datetime(frame.pop('date'), errors='raise')
    frame.index = pd.DatetimeIndex(dates)
    frame = frame.sort_index().astype(float)
    if kind == 'prices':
        if not np.isfinite(frame.to_numpy()).all() or (frame <= 0).any().any():
            raise ValueError('Prices must be positive and complete')
        frame = frame.pct_change(fill_method=None).iloc[1:]
    elif kind != 'returns':
        raise ValueError('kind must be prices or returns')
    return validate_returns(frame)


def statistics(returns):
    """Appendix A: geometric annual return and population covariance (ddof=0)."""
    a = returns.to_numpy(dtype=float)
    mu = np.expm1(np.log1p(a).mean(axis=0) * 252)
    cov = np.atleast_2d(np.cov(a, rowvar=False, ddof=0)) * 252
    return mu, cov


def fingerprint(frame):
    return hashlib.sha256(frame.to_csv(index_label='date', float_format='%.12g').encode()).hexdigest()


def synthetic(n=8, days=756, seed=42):
    """Correlated synthetic returns; NOT market data or evidence of profitability."""
    rng = np.random.default_rng(seed)
    factors = rng.normal(0, 0.006, (days, 3))
    loading = rng.uniform(-0.3, 0.9, (3, n))
    a = factors @ loading + rng.normal(0, 0.007, (days, n))
    a += np.linspace(0.0001, 0.0008, n)
    return pd.DataFrame(a, index=pd.bdate_range('2020-01-01', periods=days),
                        columns=[f'ASSET_{i+1:02}' for i in range(n)])


def chronological_split(frame, train=0.6, val=0.2):
    a, b = int(len(frame)*train), int(len(frame)*(train+val))
    return frame.iloc[:a], frame.iloc[a:b], frame.iloc[b:]
