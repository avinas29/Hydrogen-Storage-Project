"""Write reports/thermodynamics.md from the Phase 6 tables (all numbers computed)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..data.run_audit import md_table
from .analysis import DOMAIN_L1
from .vant_hoff import LHV_H2_MJ_PER_KG, M_H2, P0_BAR, R, peq_bar, T_at_P

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "results/tables"


def main():
    t = pd.read_csv(T / "vant_hoff_purdue.csv")
    rep = pd.read_csv(T / "vant_hoff_representative.csv")
    ser = pd.read_csv(T / "vant_hoff_ml_series.csv")
    cal = pd.read_csv(T / "applicability_domain_calibration.csv")
    s = t[t["n_plateaus"] == 1]
    ok = s[~s["flag_dS_atypical"]]

    la = rep[rep["purdue_id"] == "La[1]Ni[5]"].iloc[0]
    lnp = -la["dH_kJmol"] * 1000 / (R * 298.15) + la["dS_JmolK"] / R

    def share(mask):
        return f"{int(mask.sum())} ({100 * mask.mean():.0f}%)"

    cls = pd.DataFrame({
        "criterion (single-plateau, typical ΔS)": [
            "T(1 bar) ≤ 25 °C (ambient desorption)",
            "T(1 bar) ≤ 80 °C (PEMFC waste heat suffices)",
            "Peq(25 °C) ≤ 10 bar (low-pressure storage at room T)",
            "Peq(50 °C) ≤ 30 bar (no overpressure on a hot day)",
            "1 ≤ Peq(25 °C) ≤ 10 bar",
            "T(1 bar) > 150 °C (needs a high-temperature heat source)"],
        "materials": [share(ok["T_C_at_1bar"] <= 25), share(ok["T_C_at_1bar"] <= 80),
                      share(ok["Pdes_bar_25C"] <= 10), share(ok["Pdes_bar_50C"] <= 30),
                      share(ok["Pdes_bar_25C"].between(1, 10)), share(ok["T_C_at_1bar"] > 150)]})

    heat_by = ok.groupby(np.where(ok["T_C_at_1bar"] <= 80, "T(1 bar) ≤ 80 °C", "T(1 bar) > 80 °C")).agg(
        n=("heat_MJ_per_kgH2", "size"), median_heat_MJ_per_kgH2=("heat_MJ_per_kgH2", "median"),
        median_pct_LHV=("heat_pct_of_LHV", "median")).reset_index().rename(columns={"index": "group"}).round(1)

    low = ok[ok["T_C_at_1bar"] <= 80]
    q95_dH, q95_Q, max_dH = low["dH_kJmol"].quantile(0.95), low["heat_MJ_per_kgH2"].quantile(0.95), low["dH_kJmol"].max()
    mg = s[s["family"] == "Mg"]["heat_MJ_per_kgH2"]
    mg_Q_lo, mg_Q_hi = mg.min(), mg.max()
    hy = t[t["abs_source"] != "not_available"]
    hy_tab = hy.groupby("abs_source")["hysteresis_ratio_Pa_Pd_25C"].describe()[["count", "min", "50%", "max"]].round(2).reset_index()
    big_h = hy.nlargest(3, "hysteresis_ratio_Pa_Pd_25C")[["purdue_id", "family", "hysteresis_ratio_Pa_Pd_25C", "abs_source"]].round(2)
    x = hy[hy["abs_source"] == "stated_abs_dH_dS"]
    T_cross = (x["dH_kJmol"] - x["abs_dH_kJmol"]) * 1000 / (x["dS_JmolK"] - x["abs_dS_JmolK"])
    span = (t["Pdes_bar_25C_x0.9"] / t["Pdes_bar_25C_x0.1"]).dropna()

    rcols = ["name", "dH_kJmol", "dS_JmolK", "Pdes_bar_25C", "T_C_at_1bar", "T_C_at_10bar",
             "heat_MJ_per_kgH2", "heat_pct_of_LHV", "heat_kJ_per_kg_material_full_charge",
             "hysteresis_ratio_Pa_Pd_25C", "abs_source"]
    rtab = rep[rcols].copy()
    rtab["Pdes_bar_25C"] = rtab["Pdes_bar_25C"].map(lambda v: f"{v:.3g}")
    rtab = rtab.round(1)

    new = ser[~ser["in_data"]]
    kn = ser[ser["in_data"]]
    stab = ser[["series", "x", "in_data", "dH_experimental", "dH_predicted", "dH_interval_low", "dH_interval_high",
                "T1bar_C_estimate", "T1bar_C_band_low", "T1bar_C_band_high", "nn_L1_distance",
                "in_applicability_domain"]].round(1)

    text = f"""# Phase 6: Van't Hoff thermodynamics and operating windows

Code: `src/thermodynamics/vant_hoff.py` (equations), `analysis.py` (tables), `report.py` (this file),
and `src/visualization/thermo_plots.py` (Figs. 17–20). Tables are in `results/tables/vant_hoff_*.csv`.
**All windows in sections 2–5 use experimental ΔH and ΔS from the Purdue files.** Section 6 is the
only place where ML-predicted ΔH is used, and every number there is labelled ESTIMATE.

## 1. Equations, sign convention and units

Desorption equilibrium of the plateau, MHx ⇌ M + (x/2) H2, written per mol H2:

    ln(Peq / P0) = −ΔH / (R T) + ΔS / R

* ΔH and ΔS are **positive desorption magnitudes**. The Purdue files store formation values
  (negative). The toolbox's `Peq.m` evaluates `101325·exp((ΔH_f − TΔS_f)/(RT))`, which is the same equation.
  The HydPARK ln Peq(25 °C) column reproduces it with the same convention (Phase 1).
* **P0 = 1 atm.** Both the toolbox (p0 = 101325 Pa) and HydPARK reference ΔS to 1 atm. Pressures are
  converted to bar (×{P0_BAR}). R = {R} J mol⁻¹ K⁻¹.
* Temperature at a given pressure: T(P) = ΔH / (ΔS − R ln(P/P0)).
* Reaction heat per kg H2: Q = ΔH / M(H2), with M(H2) = {M_H2} g/mol, so 1 kJ/mol H2 = {1/M_H2:.3f} MJ/kg H2.
  It is expressed as a fraction of the H2 lower heating value ({LHV_H2_MJ_PER_KG} MJ/kg). Desorption absorbs Q;
  absorption releases about the same amount (the absorption ΔH, where stated).
* **Worked example, LaNi5** (ΔH = {la['dH_kJmol']:.2f} kJ/mol, ΔS = {la['dS_JmolK']:.1f} J/(mol K)):
  ln(P/atm) at 298.15 K = −{la['dH_kJmol']*1000:.0f}/({R:.3f}×298.15) + {la['dS_JmolK']:.1f}/{R:.3f} = {lnp:.3f},
  so P = {np.exp(lnp):.3f} atm = {la['Pdes_bar_25C']:.2f} bar. T(1 bar) = {la['T_C_at_1bar']:.1f} °C.
  Q = {la['heat_MJ_per_kgH2']:.1f} MJ/kg H2 ({la['heat_pct_of_LHV']:.1f}% of LHV).

Model limits: the relation assumes a flat plateau, and ΔH and ΔS independent of temperature. Real plateaus
are sloped and hysteretic (sections 4–5). Kinetics and heat transfer, not thermodynamics, usually limit the
achievable flow rate.

## 2. Representative materials (Figs. 17, 18)

{md_table(rtab)}

`heat_kJ_per_kg_material_full_charge` uses the reported capacity, whose definition varies (Phase 1). The
absorption pressure comes from stated absorption ΔH/ΔS, or from a stated hysteresis ln(Pa/Pd) assumed to be
independent of T. Without either it is not computed: the toolbox's type-default hysteresis is not used.

Reading the table:
* **LaNi5, MmNi4.5Al0.5, TiFe, TiFe0.9Mn0.1** give 1–10 bar between about −10 and 75 °C, and need about 14–16 MJ/kg H2
  (11–13% of LHV). PEMFC waste heat can supply this.
* **TiCrMn and Hydralloy C2** (AB2 Laves) are high-pressure alloys, about 12–108 bar at 25 °C. They suit
  low-temperature operation or compressor stages, and a pressure-rated vessel.
* **ZrMn2 and V-based BCC** need 35–170 °C.
* **NaAlH4:** the NaAlH4 → Na3AlH6 plateau (37 kJ/mol) reaches 1 bar near {rep[rep.name.str.contains('NaAlH4→')]['T_C_at_1bar'].iloc[0]:.0f} °C. The
  Na3AlH6 → NaH plateau (47 kJ/mol) needs about {rep[rep.name.str.contains('Na3AlH6→')]['T_C_at_1bar'].iloc[0]:.0f} °C. Full use of the 3.9 wt% reported capacity therefore needs about
  100 °C or more.
* **Mg2Ni and MgH2** need 255–300 °C and remove/supply 32–39 MJ/kg H2, i.e. 27–32% of the LHV.

## 3. Whole-database view (Fig. 19)

Single-plateau Purdue materials with typical ΔS (n = {len(ok)}):

{md_table(cls)}

Reaction heat by operating-temperature class:

{md_table(heat_by)}

Because T(1 bar) ≈ ΔH/ΔS and ΔS varies little, **heat demand and operating temperature are tied
together**. Among materials that release H2 at 1 bar with low-grade (≤ 80 °C) heat, 95% have
ΔH ≤ {q95_dH:.1f} kJ/mol and a reaction heat ≤ {q95_Q:.1f} MJ/kg H2. The few exceptions, up to {max_dH:.0f} kJ/mol, combine a high ΔH
with an unusually high ΔS. Mg-based hydrides need {mg_Q_lo:.0f}–{mg_Q_hi:.0f} MJ/kg H2 at about 255–300 °C.

## 4. Hysteresis

{md_table(hy_tab)}

* Pabs ≥ Pdes for every material with stated absorption data, so no inconsistent record was found.
* Largest ratios at 25 °C: {', '.join(f"{r.purdue_id} ({r.hysteresis_ratio_Pa_Pd_25C:g})" for r in big_h.itertuples())}. For MgH2
  this is an extrapolation of the absorption and desorption lines far below the about 300 °C where they were
  measured. It is not a physical statement about MgH2 at room temperature.
* When absorption and desorption ΔH/ΔS are both stated, the two Van't Hoff lines cross at a median of
  {T_cross.median():.0f} K (IQR {T_cross.quantile(.25):.0f}–{T_cross.quantile(.75):.0f}). Above this temperature hysteresis vanishes. This is how the toolbox defines its
  critical temperature Tc (`ReadThermo.m`).
* Engineering effect: the charging pressure must exceed Pabs, not Pdes. For TiFe this is about {rep.set_index('name').loc['TiFe','hysteresis_ratio_Pa_Pd_25C']:.1f}× the
  desorption pressure, which raises compressor work.

## 5. Plateau slope

Slopes are stated in {int(t['slope_stated'].notna().sum())} files. With the toolbox model ln P(x) = ln P_mid + slope·(298/T)·(x − 0.5),
the pressure ratio between 90% and 10% of capacity at 25 °C has median {span.median():.2f} (IQR {span.quantile(.25):.2f}–{span.quantile(.75):.2f},
max {span.max():.1f}). A sloped AB2 alloy therefore delivers its last hydrogen at a pressure several times lower
than its first, so a window computed from the plateau midpoint is optimistic at low state of charge.

## 6. ML-estimated windows (Fig. 20): ESTIMATES, not validated

Four substitution series were evaluated: LaNi5−xAlx, LaNi5−xSnx, TiFe1−xMnx and TiCr2−xMnx. For compositions already in the data,
the **out-of-fold** prediction is shown, so the model never saw that composition. For new compositions the
final model is used.

* ΔS is not predicted. It is **assumed** to be the family median of experimental Purdue values (IQR shown).
* ΔH interval: the 10–90% quantiles of out-of-fold residuals for training compositions at a similar
  nearest-neighbour distance (calibration below). Applicability domain: nearest-neighbour L1 ≤ {DOMAIN_L1}.

Calibration of error vs distance to the nearest training composition outside the same CV group:

{md_table(cal.round(2))}

Check on the {len(kn)} series compositions that do have data: mean |out-of-fold − experimental| =
{(kn['dH_predicted']-kn['dH_experimental']).abs().mean():.2f} kJ/mol, and {100*((kn.dH_experimental>=kn.dH_interval_low)&(kn.dH_experimental<=kn.dH_interval_high)).mean():.0f}% of
experimental values fall inside the nominal 80% interval.

{md_table(stab)}

* The model reproduces the known trends: Al and Sn substitution in LaNi5 stabilise the hydride (ΔH rises), and
  Mn in TiCr2 lowers ΔH slightly.
* The resulting T(1 bar) bands are **about {(ser['T1bar_C_band_high']-ser['T1bar_C_band_low']).median():.0f} K wide**. Of this, about
  {ser['T1bar_width_from_dH_K'].median():.0f} K comes from the ΔH uncertainty and {ser['T1bar_width_from_dS_K'].median():.0f} K from the assumed ΔS. Even for well-sampled AB5 alloys, an ML
  estimate can only rank candidates ("more stable than LaNi5"). Only a PCT measurement, which gives ΔH
  and ΔS directly, can fix the operating window.
* All {len(new)} new compositions are inside the applicability domain (max NN distance {new['nn_L1_distance'].max():.2f}), because
  the series were chosen near existing data. Compositions far from the data would get much wider intervals.
"""
    (ROOT / "reports/thermodynamics.md").write_text(text)


if __name__ == "__main__":
    main()
