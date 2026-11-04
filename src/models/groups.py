"""Cross-validation groups that keep near-identical compositions together.

Each row of the ΔH table is already a unique composition. Phase 2 showed, however, that
compositions differing only by rounding (e.g. Zr1Mn1.22Fe1.11 vs Zr1Mn1.22Fe1.14)
often carry the same literature value. Rows are linked when they have the same element set
and an L1 atomic-fraction distance <= ``L1_LINK``. Connected components become CV groups,
so such near-duplicates can never be split between train and test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..features.composition import parse_key

L1_LINK = 0.02


def near_composition_groups(keys: pd.Series, l1_link: float = L1_LINK) -> np.ndarray:
    comps = [parse_key(k) for k in keys]
    n = len(comps)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    by_set: dict[frozenset, list[int]] = {}
    for i, c in enumerate(comps):
        by_set.setdefault(frozenset(c), []).append(i)
    for idx in by_set.values():
        for a in range(len(idx)):
            for b in range(a + 1, len(idx)):
                i, j = idx[a], idx[b]
                ca, cb = comps[i], comps[j]
                if sum(abs(ca[e] - cb[e]) for e in ca) <= l1_link:
                    parent[find(i)] = find(j)
    roots = [find(i) for i in range(n)]
    _, groups = np.unique(roots, return_inverse=True)
    return groups
