"""Evaluate generated candidate alloys with the existing predictor and Van't Hoff relations.

For each candidate: ML ΔH, calibrated 80% interval, nearest-neighbour distance, domain status,
nearest experimental composition, and an ESTIMATED operating window that uses an *assumed* ΔS
(family median, IQR as the band). Rejection reasons are explicit. Ranking uses configurable
objectives and is accompanied by a Pareto front. Candidates are proposed alloys, not
discovered or validated materials, and nothing here implies hydride stability or reversible
capacity.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..thermodynamics.vant_hoff import M_H2, peq_bar
from .pareto import minmax, pareto_mask, weighted
from .predictor import CompositionError, Predictor

BASIS = "ESTIMATE: ML-predicted ΔH (Random Forest) + assumed ΔS (family median of experimental Purdue values)"


@dataclass
class Targets:
    T_target_C: float = 25.0      # desired operating (desorption) temperature
    P_target_bar: float = 5.0     # desired delivery pressure at that temperature
    T_min_C: float = -20.0        # acceptable desorption temperature window
    T_max_C: float = 80.0


def evaluate(P: Predictor, candidates: list[dict], family: str, tg: Targets) -> pd.DataFrame:
    dS_lo, dS, dS_hi, fam_used = P.dS_for(family)
    rows = []
    for c in candidates:
        try:
            r = P.predict(c["formula"])
        except CompositionError as e:
            rows.append({"formula": c["formula"], "comp_key": c["comp_key"], "status": "rejected",
                         "reasons": f"invalid composition: {e}"})
            continue
        lo, hi = r.interval
        T_c, T_lo, T_hi = P.T_for_pressure(tg.P_target_bar, lo, r.dH_pred, hi, dS_lo, dS, dS_hi)
        reasons = []
        if r.unseen_elements:
            reasons.append(f"element(s) {', '.join(r.unseen_elements)} not in training data")
        if not r.in_domain:
            reasons.append(f"outside applicability domain (NN L1 {r.nn_distance:.3f} > {P.domain_l1})")
        if T_lo > tg.T_max_C:
            reasons.append(f"even the optimistic T({tg.P_target_bar:g} bar) {T_lo:.0f} °C > {tg.T_max_C:g} °C")
        if T_hi < tg.T_min_C:
            reasons.append(f"even the pessimistic T({tg.P_target_bar:g} bar) {T_hi:.0f} °C < {tg.T_min_C:g} °C "
                           "(plateau too high: needs cooling or a high-pressure vessel)")
        nb = r.neighbours.iloc[0]
        rows.append({
            "formula": c["formula"], "comp_key": r.comp_key, "status": "rejected" if reasons else "candidate",
            "reasons": "; ".join(reasons),
            "dH_pred_kJmol": r.dH_pred, "dH_low": lo, "dH_high": hi, "interval_width": hi - lo,
            "nn_L1": r.nn_distance, "in_domain": r.in_domain, "in_training_data": r.in_training,
            "experimental_dH_if_known": r.training_row["dH_kJmol"] if r.in_training else np.nan,
            "nearest_known": nb["comp_key"], "nearest_known_dH_exp": nb["dH_experimental_kJmol"],
            "nearest_known_source": nb["value_source"],
            "dS_assumed": dS, "dS_IQR": f"{dS_lo:.1f}-{dS_hi:.1f}", "dS_family": fam_used,
            "T_at_Ptarget_C": T_c, "T_at_Ptarget_low_C": T_lo, "T_at_Ptarget_high_C": T_hi,
            "Peq_at_Ttarget_bar": float(peq_bar(tg.T_target_C + 273.15, r.dH_pred, dS)),
            "heat_MJ_per_kgH2": r.dH_pred / M_H2,
            "basis": BASIS,
        })
    return pd.DataFrame(rows)


DEFAULT_WEIGHTS = {"temperature_fit": 0.4, "uncertainty": 0.2, "domain_distance": 0.2, "heat": 0.2}


PARETO_CHOICES = {"temp_misfit_K": "min", "nn_L1": "min", "interval_width": "min", "heat_MJ_per_kgH2": "min"}


def rank(df: pd.DataFrame, tg: Targets, weights: dict[str, float] | None = None,
         pareto_objectives: tuple[str, str] = ("temp_misfit_K", "nn_L1")) -> pd.DataFrame:
    """Score the non-rejected candidates (0-1, normalised within this run) and mark the 2-objective Pareto front."""
    w = weights or DEFAULT_WEIGHTS
    out = df.copy()
    ok = out["status"] == "candidate"
    out["temp_misfit_K"] = (out.get("T_at_Ptarget_C") - tg.T_target_C).abs()
    s = pd.DataFrame(index=out.index[ok])
    if ok.any():
        s["temperature_fit"] = minmax(out.loc[ok, "temp_misfit_K"], higher_better=False)
        s["uncertainty"] = minmax(out.loc[ok, "interval_width"], higher_better=False)
        s["domain_distance"] = minmax(out.loc[ok, "nn_L1"], higher_better=False)
        s["heat"] = minmax(out.loc[ok, "heat_MJ_per_kgH2"], higher_better=False)
        out.loc[ok, "score"] = weighted(s, w)
        for k in s:
            out.loc[ok, f"crit_{k}"] = s[k]
        objs = {o: PARETO_CHOICES[o] for o in pareto_objectives}
        out.loc[ok, "pareto"] = pareto_mask(out.loc[ok], objs)
    out["pareto"] = out.get("pareto", False)
    out["pareto"] = out["pareto"].fillna(False).astype(bool)
    out = out.sort_values(["status", "score"], ascending=[True, False], na_position="last")
    out.insert(0, "rank", np.where(out["status"] == "candidate", out.groupby("status").cumcount() + 1, np.nan))
    return out.reset_index(drop=True)
