"""Pareto (non-dominated) sets and min-max weighted scores, shared by the Lab and the Designer."""
from __future__ import annotations

import numpy as np
import pandas as pd


def pareto_mask(df: pd.DataFrame, objectives: dict[str, str]) -> np.ndarray:
    """objectives: column -> 'max' | 'min'. Rows with NaN in any objective are never on the front.

    Row i is dominated if some row j is at least as good on every objective and strictly better on one.
    """
    cols = list(objectives)
    X = df[cols].to_numpy(float).copy()
    for j, c in enumerate(cols):
        if objectives[c] == "min":
            X[:, j] = -X[:, j]
    valid = ~np.isnan(X).any(axis=1)
    front = np.zeros(len(df), bool)
    idx = np.where(valid)[0]
    for i in idx:
        others = X[idx]
        dominated = np.any(np.all(others >= X[i], axis=1) & np.any(others > X[i], axis=1))
        front[i] = not dominated
    return front


def minmax(s: pd.Series, higher_better: bool = True) -> pd.Series:
    lo, hi = s.min(), s.max()
    out = (s - lo) / (hi - lo) if pd.notna(lo) and hi > lo else pd.Series(0.5, index=s.index)
    out = out if higher_better else 1 - out
    return out.fillna(0.5)  # missing -> neutral (callers flag it)


def weighted(scores: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    w = {k: v for k, v in weights.items() if v > 0 and k in scores}
    tot = sum(w.values())
    if tot == 0:
        return pd.Series(0.0, index=scores.index)
    return sum(scores[k] * v for k, v in w.items()) / tot
