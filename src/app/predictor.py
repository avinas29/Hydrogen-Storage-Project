"""Prediction core for the Metal Hydride ML Explorer (no Streamlit dependency, so it is testable).

Pipeline for a user composition:
1. ``parse_composition``: text -> {element: amount}. Accepts LaNi4.2Al0.8, (Ti0.8Zr0.2)(Cr0.5Mn0.5)2,
   Ti[1]Fe[0.9]Mn[0.1] (Purdue style) and at.% style (V75Ti17.5Zr7.5). Rejects H/D/T (enter the
   metal, not the hydride), mischmetal-type pseudo-elements, unknown symbols and empty input.
2. ``comp_key`` (the same function used in Phase 2): fractions rounded to 3 decimals.
3. ``featurize`` (the same function used in Phase 4), with the element-fraction list stored in the
   bundle, then the stored feature order -> model.predict.
4. Nearest neighbours: L1 distance between atomic-fraction vectors over the union of elements
   (the same metric as the Phase 6 calibration) against all 725 training compositions.
5. Uncertainty: 80% interval from the 10-90% quantiles of out-of-fold residuals of training
   compositions in the same NN-distance bin (``applicability_domain_calibration.csv``).
   Domain: NN distance <= 0.15.
"""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pymatgen.core import Composition, Element

from ..data.clean import comp_key
from ..features.composition import PROPS, element_value, featurize, parse_key
from ..thermodynamics.vant_hoff import T_at_P, peq_bar

warnings.filterwarnings("ignore", category=UserWarning, module="pymatgen")

ROOT = Path(__file__).resolve().parents[2]
BUNDLE_PATH = ROOT / "results/models/dH_predictor_bundle.joblib"
MANIFEST_PATH = ROOT / "results/models/dH_predictor_manifest.json"
PSEUDO = {"Mm", "Lm", "Vf"}
FORBIDDEN = {"H", "D", "T"}


class CompositionError(ValueError):
    """Raised with a user-readable message when a composition cannot be used."""


def parse_composition(text: str) -> dict[str, float]:
    s = (text or "").strip()
    if not s:
        raise CompositionError("Enter a composition, e.g. LaNi4.2Al0.8 or TiFe0.75Mn0.25.")
    if len(s) > 200:
        raise CompositionError("Composition string is too long.")
    s = re.sub(r"\[([0-9.]+)\]", r"\1", s.replace(" ", ""))   # Purdue style Ti[1]Fe[0.9]
    found = set(re.findall(r"[A-Z][a-z]?", s))
    pseudo = found & PSEUDO
    if pseudo:
        raise CompositionError(
            f"{', '.join(sorted(pseudo))} is a pseudo-element (mischmetal / ferrovanadium) with no defined "
            "composition. The model cannot compute elemental descriptors for it.")
    if not re.fullmatch(r"[A-Za-z0-9.()]+", s):
        raise CompositionError("Only element symbols, numbers, '.', and parentheses are allowed.")
    try:
        comp = Composition(s)
    except Exception as e:  # pymatgen raises several types
        raise CompositionError(f"Could not parse '{text}': {e}") from None
    els = {el.symbol: float(v) for el, v in comp.items()}
    if not els or sum(els.values()) <= 0:
        raise CompositionError("Composition has no positive amounts.")
    if any(v <= 0 for v in els.values()):
        raise CompositionError("All amounts must be positive.")
    if set(els) & FORBIDDEN:
        raise CompositionError("Enter the hydrogen-free alloy (e.g. LaNi5, not LaNi5H6). ΔH refers to the hydride of the alloy.")
    for e in els:
        try:
            Element(e)
        except Exception:
            raise CompositionError(f"'{e}' is not a chemical element.") from None
        for p in PROPS:
            v = element_value(e, p)
            if v is None or not np.isfinite(v):
                raise CompositionError(f"Element {e} lacks the tabulated property '{p}' needed by the descriptors.")
    return els


def l1(a: dict, b: dict) -> float:
    return sum(abs(a.get(e, 0.0) - b.get(e, 0.0)) for e in set(a) | set(b))


@dataclass
class Prediction:
    input_text: str
    composition: dict
    comp_key: str
    features: pd.Series
    dH_pred: float
    interval: tuple[float, float]
    interval_bin: str
    bin_MAE: float
    nn_distance: float
    in_domain: bool
    neighbours: pd.DataFrame
    unseen_elements: list = field(default_factory=list)
    in_training: bool = False
    training_row: dict | None = None
    warnings: list = field(default_factory=list)

    @property
    def reliability(self) -> str:
        if self.in_training:
            return "in-training"
        return "in-domain" if self.in_domain else "OUTSIDE DOMAIN"


class Predictor:
    def __init__(self, bundle_path: Path = BUNDLE_PATH):
        if not Path(bundle_path).exists():
            raise FileNotFoundError(
                f"Model bundle not found at {bundle_path}. Create it with:  .venv/bin/python -m src.models.export_bundle")
        b = joblib.load(bundle_path)
        self.model = b["model"]
        self.features: list[str] = b["features"]
        self.frac_elements: list[str] = b["frac_elements"]
        self.train: pd.DataFrame = b["train"].reset_index(drop=True)
        self.cal: pd.DataFrame = b["calibration"]
        self.bins = pd.IntervalIndex.from_breaks(b["nn_bins"])
        self.domain_l1: float = b["domain_l1"]
        self.dS: pd.DataFrame = b["dS_assumption"].set_index("family")
        self.params = b["params"]
        self._train_comps = [parse_key(k) for k in self.train["comp_key"]]
        self._train_keys = set(self.train["comp_key"])
        self._train_elements = set().union(*self._train_comps)

    # ---------------------------------------------------------------
    def featurise(self, key: str) -> pd.DataFrame:
        X, _, _ = featurize(pd.Series([key]), frac_elements=self.frac_elements)
        return X[self.features]

    def _calibration_row(self, nn: float) -> pd.Series:
        i = self.bins.get_indexer([min(nn, self.bins[-1].right - 1e-9)])[0]
        return self.cal.iloc[i]

    def predict(self, text: str, k: int = 5) -> Prediction:
        els = parse_composition(text)
        key = comp_key(Composition(els))
        # comp_key rounds fractions to 3 decimals and is not idempotent: re-keying an
        # already-rounded key (e.g. one copied from the neighbour table) can shift a digit.
        # If the input literally IS a training key, use it unchanged.
        raw = "".join(f"{e}{round(v, 3):g}" for e, v in sorted(els.items()))
        if raw in self._train_keys:
            key = raw
        frac = parse_key(key)
        X = self.featurise(key)
        if X.isna().any(axis=None):
            raise CompositionError("Descriptor computation produced missing values for this composition.")
        dH = float(self.model.predict(X.to_numpy(float))[0])

        dist = np.array([l1(frac, t) for t in self._train_comps])
        exact = np.where(dist < 1e-9)[0]
        in_training = len(exact) > 0
        # For a training composition, the honest distance is to its nearest *other* composition
        dist_other = dist.copy()
        if in_training:
            dist_other[exact] = np.inf
        nn = float(dist_other.min())
        cal = self._calibration_row(nn)
        lo, hi = dH - float(cal["res_q90"]), dH - float(cal["res_q10"])   # residual = pred - true
        order = np.argsort(dist)[: k + len(exact)]
        nb = self.train.iloc[order][["comp_key", "family", "dH_kJmol", "value_source", "purdue_id", "hydpark_ids"]].copy()
        nb.insert(1, "L1_distance", dist[order])
        nb = nb.rename(columns={"dH_kJmol": "dH_experimental_kJmol"}).head(k + len(exact)).reset_index(drop=True)

        unseen = sorted(set(els) - self._train_elements)
        warn = []
        if unseen:
            warn.append(f"Element(s) {', '.join(unseen)} never occur in the training data.")
        in_domain = nn <= self.domain_l1 and not unseen
        if not in_domain:
            warn.append(f"Nearest training composition is at L1 = {nn:.3f} (domain limit {self.domain_l1}). "
                        f"Out-of-fold error at this distance: MAE ≈ {cal['MAE']:.1f} kJ/mol. Treat the value as unreliable.")
        row = None
        if in_training:
            r = self.train.iloc[exact[0]]
            row = r.to_dict()
            warn.append("This composition is in the training data. The model has seen its ΔH, so the prediction is "
                        "in-sample. Compare with the experimental value and the out-of-fold prediction instead.")
        return Prediction(text, els, key, X.iloc[0], dH, (lo, hi), str(cal["bin"]), float(cal["MAE"]), nn,
                          in_domain, nb, unseen, in_training, row, warn)

    # ---------------------------------------------------------------
    def dS_for(self, family: str | None) -> tuple[float, float, float, str]:
        fam = family if family in self.dS.index else "(all)"
        r = self.dS.loc[fam]
        return float(r["q25"]), float(r["median"]), float(r["q75"]), fam

    def nearest_family(self, pred: Prediction) -> str | None:
        fams = pred.neighbours["family"].dropna()
        return fams.iloc[0] if len(fams) else None

    @staticmethod
    def vant_hoff_band(T_K: np.ndarray, dH_lo, dH, dH_hi, dS_lo, dS, dS_hi):
        """Peq (bar) for the central estimate and the envelope over the ΔH interval x ΔS IQR corners."""
        centre = peq_bar(T_K, dH, dS)
        corners = np.array([peq_bar(T_K, h, s) for h in (dH_lo, dH_hi) for s in (dS_lo, dS_hi)])
        return centre, corners.min(axis=0), corners.max(axis=0)

    @staticmethod
    def T_for_pressure(P_bar, dH_lo, dH, dH_hi, dS_lo, dS, dS_hi):
        c = float(T_at_P(P_bar, dH, dS)) - 273.15
        corners = [float(T_at_P(P_bar, h, s)) - 273.15 for h in (dH_lo, dH_hi) for s in (dS_lo, dS_hi)]
        return c, min(corners), max(corners)
