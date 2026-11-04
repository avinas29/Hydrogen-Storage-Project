"""Application-specific recommendation engine (experimental Purdue materials).

1. Requirements (``Requirements``): everything optional except the application type and delivery pressure.
2. Hard constraints, each evaluated as pass / fail / unknown / not specified. A material fails only on
   an evaluated failure. Missing evidence gives "unknown", which is never a silent rejection.
3. Weighted, min-max-normalised criteria among the materials that do not fail. Missing criterion -> 0.5,
   recorded in ``missing``.
4. Pareto front on two user-chosen objectives.
5. Evidence class: data-supported / provisional / insufficient.
6. A plain-language explanation and the measurements needed before deployment.

Data: experimental ΔH, ΔS per plateau (Purdue .mh, Phase 6 table), reported capacity (definition
varies), stated density, hysteresis, family-level kinetics class and qualitative cost class (Phase 8).
Nothing is invented: absent properties stay absent.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from ..thermodynamics.vant_hoff import M_H2, T_at_P, peq_bar
from .pareto import minmax, pareto_mask, weighted

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "results/tables"

APPLICATIONS = {
    "Stationary hydrogen storage": dict(
        weights={"cost": .25, "pressure_fit": .15, "hysteresis": .15, "heat": .10, "temperature_margin": .10,
                 "capacity": .05, "kinetics": .10, "evidence": .10},
        defaults=dict(ambient_min_C=5, ambient_max_C=35, heat_source="none", P_delivery_bar=3, max_pressure_bar=10,
                      h2_kg=10, discharge_time_h=24)),
    "Mobile hydrogen storage": dict(
        weights={"capacity": .30, "heat": .20, "kinetics": .15, "temperature_margin": .10, "pressure_fit": .10,
                 "hysteresis": .05, "evidence": .10},
        defaults=dict(ambient_min_C=-10, ambient_max_C=40, heat_source="PEM fuel-cell waste heat", heat_temp_C=70,
                      P_delivery_bar=3, max_pressure_bar=50, h2_kg=1, discharge_time_h=2)),
    "Low-temperature fuel-cell waste-heat integration": dict(
        weights={"temperature_margin": .25, "heat": .20, "pressure_fit": .15, "kinetics": .10, "capacity": .10,
                 "hysteresis": .10, "evidence": .10},
        defaults=dict(ambient_min_C=10, ambient_max_C=35, heat_source="PEM fuel-cell waste heat", heat_temp_C=65,
                      P_delivery_bar=2, max_pressure_bar=30, h2_kg=2, discharge_time_h=8)),
    "Industrial hydrogen buffering": dict(
        weights={"kinetics": .20, "pressure_fit": .20, "hysteresis": .15, "cost": .15, "heat": .10, "capacity": .10,
                 "evidence": .10},
        defaults=dict(ambient_min_C=5, ambient_max_C=40, heat_source="industrial waste heat", heat_temp_C=120,
                      P_delivery_bar=5, max_pressure_bar=30, h2_kg=50, discharge_time_h=12)),
    "Renewable-energy hydrogen storage": dict(
        weights={"cost": .20, "hysteresis": .20, "heat": .15, "pressure_fit": .15, "temperature_margin": .10,
                 "capacity": .10, "evidence": .10},
        defaults=dict(ambient_min_C=0, ambient_max_C=40, heat_source="none", P_delivery_bar=3, max_pressure_bar=30,
                      charge_pressure_bar=30, h2_kg=20, discharge_time_h=48)),
}
HEAT_SOURCES = ["none", "PEM fuel-cell waste heat", "industrial waste heat", "solar thermal", "electric heater", "other"]
CRITERIA = ["capacity", "volumetric", "temperature_margin", "pressure_fit", "heat", "hysteresis", "kinetics", "cost",
            "evidence"]


@dataclass
class Requirements:
    application: str = "Stationary hydrogen storage"
    location: str = ""                     # free text, recorded only; never used to infer infrastructure
    ambient_min_C: float = 5.0
    ambient_max_C: float = 35.0
    heat_source: str = "none"
    heat_temp_C: float | None = None
    heat_power_kW: float | None = None
    cooling_water: bool = False
    cooling_temp_C: float | None = None
    h2_kg: float | None = None
    P_delivery_bar: float = 3.0
    flow_kg_h: float | None = None
    T_op_min_C: float | None = None
    T_op_max_C: float | None = None
    charge_time_h: float | None = None
    discharge_time_h: float | None = None
    operation: str = "intermittent"
    max_mass_kg: float | None = None
    max_volume_L: float | None = None
    min_capacity_wt: float | None = None
    max_thermal_MJ: float | None = None
    max_pressure_bar: float | None = None
    max_temp_C: float | None = None
    charge_pressure_bar: float | None = None
    cycle_life: int | None = None
    data_sources: list = field(default_factory=lambda: ["manual input"])

    def validate(self) -> list[str]:
        e = []
        if self.ambient_min_C > self.ambient_max_C:
            e.append("Minimum ambient temperature is above the maximum.")
        if self.P_delivery_bar is None or self.P_delivery_bar <= 0:
            e.append("Delivery pressure must be positive.")
        if self.heat_source != "none" and self.heat_temp_C is None:
            e.append("Give the heat-source temperature (or choose 'none').")
        if self.T_op_min_C is not None and self.T_op_max_C is not None and self.T_op_min_C > self.T_op_max_C:
            e.append("Operating temperature range is inverted.")
        for k in ("h2_kg", "flow_kg_h", "max_mass_kg", "max_volume_L", "min_capacity_wt", "max_thermal_MJ",
                  "max_pressure_bar", "heat_power_kW", "discharge_time_h", "charge_time_h", "charge_pressure_bar"):
            v = getattr(self, k)
            if v is not None and v <= 0:
                e.append(f"{k} must be positive if given.")
        if self.max_pressure_bar is not None and self.max_pressure_bar < self.P_delivery_bar:
            e.append("Maximum pressure is below the delivery pressure.")
        return e

    # Derived operating conditions -------------------------------------------------
    def desorption_T_allowed_C(self) -> float:
        """Highest bed temperature available for delivering H2: the heat source if any, else the coldest ambient."""
        t = self.heat_temp_C if (self.heat_source != "none" and self.heat_temp_C is not None) else self.ambient_min_C
        for cap in (self.T_op_max_C, self.max_temp_C):
            if cap is not None:
                t = min(t, cap)
        return float(t)

    def bed_T_max_C(self) -> float:
        return float(max(self.ambient_max_C, self.desorption_T_allowed_C()))

    def charge_T_C(self) -> float:
        return float(self.cooling_temp_C if (self.cooling_water and self.cooling_temp_C is not None) else self.ambient_max_C)

    def required_heat_kW(self, q_MJ_per_kg: float) -> float | None:
        rate = self.flow_kg_h
        if rate is None and self.h2_kg and self.discharge_time_h:
            rate = self.h2_kg / self.discharge_time_h
        return None if rate is None else rate * q_MJ_per_kg / 3.6   # MJ/h -> kW


def short(pid: str) -> str:
    return re.sub(r"\[([0-9.]+)\]", lambda m: "" if m.group(1) == "1" else m.group(1), pid)


def experimental_pool() -> pd.DataFrame:
    c = pd.read_csv(T / "screening_candidates.csv")
    vh = pd.read_csv(T / "vant_hoff_purdue.csv")
    p = pd.read_csv(ROOT / "data/processed/purdue_cleaned.csv").set_index("purdue_id")
    pl = vh.groupby("purdue_id").apply(lambda g: list(zip(g["dH_kJmol"], g["dS_JmolK"])), include_groups=False)
    c["plateaus"] = c["purdue_id"].map(pl)
    c["name"] = c["purdue_id"].map(short)
    c["pci_file"] = c["purdue_id"].map(p["pci_file"]).fillna("")
    for col in ("keff_W_mK", "cp_J_kgK", "kin_abs_Ea_Jmol", "kin_des_Ea_Jmol", "comp_key"):
        c[col] = c["purdue_id"].map(p[col])
    c["evidence_class"], c["evidence_notes"] = zip(*c.apply(evidence_class, axis=1))
    return c


def evidence_class(r) -> tuple[str, str]:
    if not r["data_quality_pass"]:
        return "insufficient evidence", "fails data-quality gate (atypical ΔS or assumed/unconfirmed capacity)"
    notes = []
    if r["flag_pci_dH_inconsistent"]:
        notes.append("own PCI curves disagree with tabulated ΔH by > 5 kJ/mol")
    if r["flag_unverified_ref_sandia"]:
        notes.append("unverified Sandia reference")
    if r["flag_identical_values_other_file"]:
        notes.append("identical data in another file")
    if r["flag_pseudo_element"]:
        notes.append("contains mischmetal/ferrovanadium (exact composition not defined)")
    if r["capacity_definition"] in ("approximated_from_figure", "theoretical_or_reduced_from_theoretical",
                                    "first_plateau_only"):
        notes.append(f"capacity: {r['capacity_definition']}")
    if notes:
        return "provisional", "; ".join(notes)
    return "data-supported", "experimental ΔH/ΔS and a literature capacity (definition not stated)"


EVIDENCE_SCORE = {"data-supported": 1.0, "provisional": 0.5, "insufficient evidence": 0.0}


def _check(limit, value, ok):
    """'not specified' if no limit; 'unknown' if the material value is missing; else pass/fail via ok(value, limit)."""
    if limit is None:
        return "not specified"
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "unknown"
    return "pass" if ok(value, limit) else "fail"


LE = lambda v, lim: v <= lim   # noqa: E731
GE = lambda v, lim: v >= lim   # noqa: E731


def evaluate_constraints(pool: pd.DataFrame, req: Requirements) -> pd.DataFrame:
    T_des = req.desorption_T_allowed_C()
    T_bed = req.bed_T_max_C()
    T_ch = req.charge_T_C()
    rows = []
    for _, r in pool.iterrows():
        pls = r["plateaus"] if isinstance(r["plateaus"], list) else [(r["dH_kJmol_weighted"], r["dS_JmolK_weighted"])]
        T_need = max(float(T_at_P(req.P_delivery_bar, h, s)) - 273.15 for h, s in pls)      # most stable plateau
        P_supply = min(float(peq_bar(T_des + 273.15, h, s)) for h, s in pls)
        P_bed = max(float(peq_bar(T_bed + 273.15, h, s)) for h, s in pls)                     # least stable plateau
        P_charge = max(float(peq_bar(T_ch + 273.15, h, s)) for h, s in pls)
        if np.isfinite(r["hyst_ln_Pa_Pd_25C"]) and len(pls) == 1:
            P_charge *= float(np.exp(r["hyst_ln_Pa_Pd_25C"]))   # stated hysteresis (25 °C value)
            ch_note = "absorption pressure from stated hysteresis"
        else:
            ch_note = "hysteresis not stated: desorption pressure used (optimistic)"
        q = float(r["heat_MJ_per_kgH2"])
        wt = r["wt_pct"] if np.isfinite(r["wt_pct"]) else None
        mass = req.h2_kg / (wt / 100) if (wt and req.h2_kg) else None
        rho = r["rho_kg_m3_stated"] if np.isfinite(r["rho_kg_m3_stated"]) else None
        vol_L = mass / rho * 1000 if (mass and rho) else None
        heat_kW = req.required_heat_kW(q)
        cons = {
            "delivery": _check(T_des, T_need, LE),
            "max_pressure": _check(req.max_pressure_bar, P_bed, LE),
            "charging_pressure": _check(req.charge_pressure_bar, P_charge, LE),
            "min_capacity": _check(req.min_capacity_wt, wt, GE),
            "max_mass": _check(req.max_mass_kg, mass, LE),
            "max_volume": _check(req.max_volume_L, vol_L, LE),
            "heating_power": _check(req.heat_power_kW, heat_kW, LE),
            "thermal_energy": _check(req.max_thermal_MJ, req.h2_kg * q if req.h2_kg else None, LE),
            "cycle_life": "unknown" if req.cycle_life else "not specified",   # no cycle-life data exist
        }
        vals = list(cons.values())
        status = "fail" if "fail" in vals else ("pass (incomplete evidence)" if "unknown" in vals else "pass")
        rows.append({"T_required_C": T_need, "T_available_C": T_des, "P_at_T_available_bar": P_supply,
                     "P_bed_max_bar": P_bed, "P_charge_bar": P_charge, "charge_note": ch_note,
                     "material_mass_kg": mass, "material_volume_L_solid": vol_L, "heat_power_kW": heat_kW,
                     "heat_total_MJ": req.h2_kg * q if req.h2_kg else np.nan,
                     **{f"c_{k}": v for k, v in cons.items()}, "status": status})
    return pd.concat([pool.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def score(df: pd.DataFrame, req: Requirements, weights: dict[str, float]) -> pd.DataFrame:
    ok = df["status"] != "fail"
    d = df.loc[ok].copy()
    s = pd.DataFrame(index=d.index)
    s["capacity"] = minmax(d["wt_pct"])
    s["volumetric"] = minmax(d["vol_H_kg_m3_solid"])            # only where density is stated
    s["temperature_margin"] = minmax((d["T_available_C"] - d["T_required_C"]).clip(upper=100))
    lp = np.log10(d["P_at_T_available_bar"] / req.P_delivery_bar)   # best ≈ 3x delivery pressure
    s["pressure_fit"] = np.clip(1 - np.abs(lp - 0.5), 0, 1)
    s["heat"] = minmax(d["heat_MJ_per_kgH2"], higher_better=False)
    s["hysteresis"] = minmax(d["hyst_ln_Pa_Pd_25C"], higher_better=False)
    s["kinetics"] = d["kinetics_class"]
    s["cost"] = d["cost_class"]
    s["evidence"] = d["evidence_class"].map(EVIDENCE_SCORE)
    missing = pd.Series([[k for k, col in (("volumetric", "vol_H_kg_m3_solid"), ("hysteresis", "hyst_ln_Pa_Pd_25C"))
                          if not np.isfinite(r[col])] + (["kinetics (family has no data)"] if r["flag_kinetics_no_family_data"] else [])
                         for _, r in d.iterrows()], index=d.index)
    d["score"] = weighted(s, weights)
    for k in s:
        d[f"crit_{k}"] = s[k]
    d["missing"] = missing.map(lambda x: ", ".join(x))
    out = pd.concat([d, df.loc[~ok]]).sort_values(["status", "score"], key=lambda c: c.map(
        {"pass": 0, "pass (incomplete evidence)": 1, "fail": 2}) if c.name == "status" else c, ascending=[True, False])
    # Materials with insufficient evidence are scored and shown, but never ranked as recommendations
    insuff = out["evidence_class"] == "insufficient evidence"
    out = pd.concat([out[~insuff | (out["status"] == "fail")], out[insuff & (out["status"] != "fail")]])
    out = pd.concat([out[out["status"] != "fail"], out[out["status"] == "fail"]])
    out.insert(0, "rank", np.nan)
    m = (out["status"] != "fail") & (out["evidence_class"] != "insufficient evidence")
    out.loc[m, "rank"] = np.arange(1, m.sum() + 1)
    return out.reset_index(drop=True)


PARETO_OBJECTIVES = {"wt_pct": "max", "heat_MJ_per_kgH2": "min", "temperature_margin_K": "max",
                     "hyst_ln_Pa_Pd_25C": "min", "evidence_score": "max", "vol_H_kg_m3_solid": "max"}


def add_pareto(df: pd.DataFrame, objectives: tuple[str, str] = ("wt_pct", "heat_MJ_per_kgH2")) -> pd.DataFrame:
    df = df.copy()
    df["temperature_margin_K"] = df["T_available_C"] - df["T_required_C"]
    df["evidence_score"] = df["evidence_class"].map(EVIDENCE_SCORE)
    # front among ranked materials only: unranked (insufficient-evidence) entries must not dominate them
    m = (df["status"] != "fail") & (df["evidence_class"] != "insufficient evidence")
    df["pareto"] = False
    df.loc[m, "pareto"] = pareto_mask(df.loc[m], {o: PARETO_OBJECTIVES[o] for o in objectives})
    return df


LABELS = {"delivery": "delivers the required pressure at the available temperature",
          "max_pressure": "stays below the maximum pressure on the hottest day",
          "charging_pressure": "can be charged at the available charging pressure",
          "min_capacity": "meets the minimum capacity", "max_mass": "meets the mass limit",
          "max_volume": "meets the volume limit", "heating_power": "needs no more heating power than available",
          "thermal_energy": "within the thermal-energy budget", "cycle_life": "cycle life (no data in the dataset)"}


def explain(r: pd.Series, req: Requirements) -> dict:
    sat = [LABELS[k] for k in LABELS if r.get(f"c_{k}") == "pass"]
    fail = [LABELS[k] for k in LABELS if r.get(f"c_{k}") == "fail"]
    unk = [LABELS[k] for k in LABELS if r.get(f"c_{k}") == "unknown"]
    crit = {k: r.get(f"crit_{k}") for k in CRITERIA if pd.notna(r.get(f"crit_{k}"))}
    adv = [k.replace("_", " ") for k, v in sorted(crit.items(), key=lambda kv: -kv[1]) if v >= 0.75][:3]
    lim = [k.replace("_", " ") for k, v in sorted(crit.items(), key=lambda kv: kv[1]) if v <= 0.25][:3]
    meas = ["Sieverts PCT (abs + des, ≥ 4 temperatures) at the intended conditions",
            "reversible capacity between the application's pressure limits", "cycling test (cycle life is not in the data)"]
    if not np.isfinite(r["rho_kg_m3_stated"]):
        meas.append("density / bed packing density")
    if not np.isfinite(r["hyst_ln_Pa_Pd_25C"]):
        meas.append("absorption isotherms (hysteresis)")
    if not np.isfinite(r.get("kin_abs_Ea_Jmol", np.nan)):
        meas.append("absorption/desorption kinetics")
    if not np.isfinite(r.get("keff_W_mK", np.nan)):
        meas.append("bed thermal conductivity")
    why = (f"Needs about {r['T_required_C']:.0f} °C to deliver {req.P_delivery_bar:g} bar; {r['T_available_C']:.0f} °C is available "
           f"({'heat source' if req.heat_source != 'none' else 'coldest ambient, no heat source'}). "
           f"Reaction heat {r['heat_MJ_per_kgH2']:.1f} MJ/kg H2; reported capacity {r['wt_pct']:.2f} wt% (material level, definition varies).")
    return {"why": why, "satisfies": sat, "fails": fail, "cannot_evaluate": unk, "advantages": adv,
            "limitations": lim + ([r["evidence_notes"]] if r["evidence_class"] != "data-supported" else []),
            "missing": r.get("missing", ""), "measurements": meas}


def run(req: Requirements, weights: dict[str, float] | None = None,
        pareto_objectives: tuple[str, str] = ("wt_pct", "heat_MJ_per_kgH2"), pool: pd.DataFrame | None = None) -> pd.DataFrame:
    w = weights or APPLICATIONS[req.application]["weights"]
    pool = experimental_pool() if pool is None else pool
    return add_pareto(score(evaluate_constraints(pool, req), req, w), pareto_objectives)


EXPORT_COLS = ["rank", "name", "purdue_id", "family", "status", "evidence_class", "evidence_notes", "score", "pareto",
               "T_required_C", "T_available_C", "P_at_T_available_bar", "P_bed_max_bar", "P_charge_bar", "charge_note",
               "heat_MJ_per_kgH2", "heat_power_kW", "wt_pct", "capacity_definition", "material_mass_kg",
               "material_volume_L_solid", "hyst_ln_Pa_Pd_25C", "kinetics_class", "cost_label", "missing"] + \
              [f"c_{k}" for k in LABELS]


def export_csv(res: pd.DataFrame, req: Requirements, weights: dict) -> str:
    e = res[[c for c in EXPORT_COLS if c in res]].copy()
    e["basis"] = "experimental ΔH/ΔS (Purdue .mh); capacity = reported material-level value (definition varies)"
    e["assumptions"] = ("flat-plateau Van't Hoff, P0 = 1 atm; mass/volume are material-only (no vessel, porosity or BOP); "
                        "kinetics = family-level class; cost = qualitative element class")
    e["requirements_json"] = json.dumps({**asdict(req), "weights": weights})
    return e.to_csv(index=False)
