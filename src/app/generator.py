"""Constrained alloy-composition generator for the Candidate Discovery Lab.

Two modes:
* **site template** (intermetallics): an A site and a B site, each with a fixed total
  (e.g. AB5: A = 1, B = 5). Each site has a host element and optional substituents with
  [min, max] amounts per formula unit. The host takes the remainder and must stay >= its minimum.
  This preserves the stoichiometry of the structure type (A:B ratio).
* **free fractions** (e.g. BCC solid solutions): atomic fractions on a grid that sum to 1.

Grids are exhaustive. If they exceed ``max_candidates``, a reproducible random subset
(numpy Generator with the given seed) is returned. Duplicates are removed by the same
``comp_key`` used everywhere else in the project.

These are *proposed* compositions. Nothing here implies that a composition forms a stable
or reversible hydride.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
from pymatgen.core import Composition

from ..data.clean import comp_key

EPS = 1e-9


@dataclass
class Site:
    host: str
    total: float
    subs: dict[str, tuple[float, float]] = field(default_factory=dict)  # element -> (min, max) per f.u.
    host_min: float = 0.0


@dataclass
class Preset:
    name: str
    family: str          # used for the ΔS assumption and labelling
    sites: list[Site]
    note: str = ""


PRESETS: dict[str, Preset] = {p.name: p for p in [
    Preset("Ti-Fe-Mn (AB, TiFe1-xMnx)", "AB", [Site("Ti", 1.0), Site("Fe", 1.0, {"Mn": (0.0, 0.4)}, 0.5)],
           "TiFe with Mn on the Fe site"),
    Preset("Ti-Zr-Mn-Cr (AB2 Laves)", "AB2", [Site("Ti", 1.0, {"Zr": (0.0, 0.4)}, 0.5),
                                              Site("Mn", 2.0, {"Cr": (0.0, 1.0)}, 0.8)],
           "Zr on the Ti site, Cr on the Mn site"),
    Preset("Ti-Cr-Mn (AB2 Laves)", "AB2", [Site("Ti", 1.0), Site("Cr", 2.0, {"Mn": (0.0, 1.2)}, 0.6)],
           "Mn on the Cr site"),
    Preset("La-Ni-Al (AB5)", "AB5", [Site("La", 1.0), Site("Ni", 5.0, {"Al": (0.0, 1.0)}, 3.5)],
           "Al on the Ni site"),
    Preset("La-Ni-Sn (AB5)", "AB5", [Site("La", 1.0), Site("Ni", 5.0, {"Sn": (0.0, 0.5)}, 4.0)],
           "Sn on the Ni site"),
    Preset("La-Ce-Ni-Al (AB5)", "AB5", [Site("La", 1.0, {"Ce": (0.0, 0.5)}, 0.4),
                                        Site("Ni", 5.0, {"Al": (0.0, 0.6)}, 4.0)],
           "Ce on the La site, Al on the Ni site"),
]}

FREE_PRESETS = {
    "V-Ti-Cr (BCC solid solution)": ("SS", {"V": (0.5, 0.9), "Ti": (0.05, 0.4), "Cr": (0.0, 0.3)}),
    "Custom (free atomic fractions)": ("(all)", {"Ti": (0.3, 0.6), "Fe": (0.3, 0.6), "Mn": (0.0, 0.2)}),
}


def _grid(lo: float, hi: float, step: float) -> np.ndarray:
    if step <= 0:
        raise ValueError("step must be positive")
    if hi < lo - EPS:
        raise ValueError(f"max ({hi}) is below min ({lo})")
    n = int(np.floor((hi - lo) / step + EPS)) + 1
    return np.round(lo + step * np.arange(n), 6)


def site_options(site: Site, step: float) -> list[dict[str, float]]:
    """All amount assignments for one site that respect ranges, total and host minimum."""
    subs = list(site.subs)
    grids = [_grid(*site.subs[e], step) for e in subs]
    out = []
    for combo in itertools.product(*grids) if subs else [()]:
        host_amt = round(site.total - sum(combo), 6)
        if host_amt < site.host_min - EPS or host_amt < -EPS:
            continue
        amounts = {site.host: host_amt}
        for e, v in zip(subs, combo):
            if v > EPS:
                amounts[e] = amounts.get(e, 0.0) + float(v)
        amounts = {e: v for e, v in amounts.items() if v > EPS}
        if amounts:
            out.append(amounts)
    return out


def formula(amounts: dict[str, float]) -> str:
    return "".join(f"{e}{v:g}" for e, v in amounts.items())


def _finish(raw: list[dict[str, float]], max_candidates: int, seed: int) -> list[dict]:
    seen, unique = set(), []
    for amounts in raw:
        key = comp_key(Composition(amounts))
        if key in seen:
            continue
        seen.add(key)
        unique.append({"formula": formula(amounts), "comp_key": key, "amounts": amounts})
    n_grid = len(unique)
    if n_grid > max_candidates:
        idx = np.sort(np.random.default_rng(seed).choice(n_grid, size=max_candidates, replace=False))
        unique = [unique[i] for i in idx]
    for u in unique:
        u["n_grid_total"] = n_grid
    return unique


def generate_sites(sites: list[Site], step: float, max_candidates: int = 500, seed: int = 0) -> list[dict]:
    per_site = [site_options(s, step) for s in sites]
    raw = []
    for combo in itertools.product(*per_site):
        merged: dict[str, float] = {}
        for d in combo:
            for e, v in d.items():
                merged[e] = merged.get(e, 0.0) + v
        raw.append(merged)
    return _finish(raw, max_candidates, seed)


def generate_free(ranges: dict[str, tuple[float, float]], step: float, max_candidates: int = 500,
                  seed: int = 0) -> list[dict]:
    """Atomic fractions on a grid, summing to 1, each within its range (last element takes the remainder)."""
    els = list(ranges)
    if len(els) < 2:
        raise ValueError("at least two elements are needed")
    raw = []
    for combo in itertools.product(*[_grid(*ranges[e], step) for e in els[:-1]]):
        last = round(1.0 - sum(combo), 6)
        lo, hi = ranges[els[-1]]
        if last < lo - EPS or last > hi + EPS or last < -EPS:
            continue
        amounts = {e: float(v) for e, v in zip(els, list(combo) + [last]) if v > EPS}
        if len(amounts) >= 1:
            raw.append(amounts)
    return _finish(raw, max_candidates, seed)
