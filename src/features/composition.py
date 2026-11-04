"""Composition-only descriptors for metal hydride alloys.

Every elemental value comes from pymatgen's bundled periodic table
(``pymatgen.core.periodic_table``, data file ``periodic_table.json``); none is
typed in by hand.  The values used are exported to
``results/tables/elemental_property_table.csv`` for inspection.

Descriptors (x_i = atomic fraction of element i)
* For each elemental property p in PROPS:  weighted mean  sum x_i p_i,
  weighted std  sqrt(sum x_i (p_i - mean)^2), min and max over present elements.
* ``n_elements``, ``config_entropy`` = -sum x_i ln x_i (ideal mixing, units of R),
  ``size_mismatch`` delta = sqrt(sum x_i (1 - r_i / r_mean)^2) (Zhang et al. 2008, HEA literature),
* ``frac_hydride_former``: fraction of atoms from groups 1-5, the lanthanides/actinides,
  and Pd. These are the "A-side" elements that form stable binary hydrides. Group 6-11 transition
  metals and the p-block form weak or no hydrides (Sandrock 1999, J. Alloys Compd. 293-295, 877).
* ``x_<El>`` atomic fractions for the most common elements (chosen from the
  training table by frequency, threshold documented in the report).

Valence electrons use the usual VEC convention for alloys: group number for
groups 1-12, group - 10 for groups 13-18, and 3 for lanthanides/actinides
(pymatgen places them in group 3).
"""
from __future__ import annotations

import re
import warnings

import numpy as np
import pandas as pd
from pymatgen.core import Element

warnings.filterwarnings("ignore", category=UserWarning, module="pymatgen")

PROPS = {
    "mass": ("atomic_mass", "g/mol"),
    "X": ("X", "Pauling electronegativity"),
    "radius": ("atomic_radius", "empirical atomic radius, Å"),
    "Tm": ("melting_point", "K"),
    "vol": ("molar_volume", "cm3/mol"),
    "vec": (None, "valence electrons (group convention)"),
}

# Quantities that are linked to dH (directly or via derivation) and must never
# be used as inputs when predicting dH.
LEAKY_FOR_DH = {"dS_JmolK", "abs_dS_JmolK", "abs_dH_kJmol", "Peq25_atm_raw", "lnPeq25_raw",
                "T_point_C", "P_point_atm", "dH_spread_kJmol", "dS_from_TP", "lnP25_recomputed"}


def parse_key(key: str) -> dict[str, float]:
    return {el: float(x) for el, x in re.findall(r"([A-Z][a-z]?)([0-9.]+)", key)}


def valence_electrons(el: Element) -> int:
    g = el.group
    return g if g <= 12 else g - 10


def element_value(symbol: str, prop: str) -> float:
    el = Element(symbol)
    if prop == "vec":
        return float(valence_electrons(el))
    v = getattr(el, PROPS[prop][0])
    return float(v) if v is not None else np.nan


def is_hydride_former(symbol: str) -> bool:
    el = Element(symbol)
    return el.group <= 5 and el.block in ("s", "d", "f") and symbol != "H" or symbol == "Pd"


def elemental_table(symbols) -> pd.DataFrame:
    rows = []
    for s in sorted(symbols):
        r = {"element": s}
        for p in PROPS:
            r[p] = element_value(s, p)
        r["hydride_former"] = is_hydride_former(s)
        rows.append(r)
    return pd.DataFrame(rows)


def featurize_one(comp: dict[str, float], table: pd.DataFrame, frac_elements: list[str]) -> dict:
    tot = sum(comp.values())
    x = {e: v / tot for e, v in comp.items()}
    els = list(x)
    w = np.array([x[e] for e in els])
    f: dict = {}
    for p in PROPS:
        vals = table.loc[els, p].to_numpy(dtype=float)
        if np.isnan(vals).any():
            for s in ("mean", "std", "min", "max"):
                f[f"{p}_{s}"] = np.nan
            continue
        m = float(np.sum(w * vals))
        f[f"{p}_mean"] = m
        f[f"{p}_std"] = float(np.sqrt(np.sum(w * (vals - m) ** 2)))
        f[f"{p}_min"] = float(vals.min())
        f[f"{p}_max"] = float(vals.max())
    r = table.loc[els, "radius"].to_numpy(dtype=float)
    f["n_elements"] = len(els)
    f["config_entropy"] = float(-np.sum(w * np.log(w)))
    f["size_mismatch"] = float(np.sqrt(np.sum(w * (1 - r / np.sum(w * r)) ** 2)))
    f["frac_hydride_former"] = float(sum(x[e] for e in els if table.loc[e, "hydride_former"]))
    for e in frac_elements:
        f[f"x_{e}"] = x.get(e, 0.0)
    return f


def choose_frac_elements(keys: pd.Series, min_share: float = 0.05) -> list[str]:
    counts: dict[str, int] = {}
    for k in keys:
        for e in parse_key(k):
            counts[e] = counts.get(e, 0) + 1
    n = len(keys)
    return sorted([e for e, c in counts.items() if c / n >= min_share], key=lambda e: -counts[e])


def featurize(keys: pd.Series, frac_elements: list[str] | None = None,
              min_share: float = 0.05) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    keys = keys.reset_index(drop=True)
    symbols = set()
    for k in keys:
        symbols |= set(parse_key(k))
    table = elemental_table(symbols).set_index("element")
    if frac_elements is None:
        frac_elements = choose_frac_elements(keys, min_share)
    X = pd.DataFrame([featurize_one(parse_key(k), table, frac_elements) for k in keys])
    return X, table.reset_index(), frac_elements
