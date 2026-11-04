"""Phase 9: proposed synthesis and characterisation plan (FUTURE WORK, nothing here was performed).

Writes
* results/tables/proposed_experimental_candidates.csv: alloys chosen from Phases 6-8 results
* results/tables/characterisation_matrix.csv: technique x family x property x project gap
* reports/synthesis_characterization_plan.md

Run:  .venv/bin/python -m src.screening.plan
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..data.run_audit import md_table

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "results/tables"

# (purdue_id or comp key, role, reason template). Values are filled from the result tables.
SELECTION = [
    ("La[1]Ni[5]", "benchmark", "AB5 reference with well-known PCT. Validates the Sieverts set-up and data analysis"),
    ("Ti[1]Fe[1]", "benchmark", "AB reference. Tests the activation procedure (TiFe needs activation)"),
    ("Ti[1.2]Cr[1]Mn[1]", "mobile tier", "mobile top-3 under base weights; high-pressure AB2"),
    ("Ti[0.9]Zr[0.2]Mn[1.4]Cr[0.4]V[0.2]", "mobile tier", "mobile top-15 with V (the Vf version ranks higher, but ferrovanadium is not a defined composition)"),
    ("Ti[0.56]V[0.3]Zr[0.1]Mn[0.94]Fe[0.06]Ni[0.04]", "mobile tier / data check", "mobile rank 3, but its own PCI curves give ΔH about 11 kJ/mol lower than the .mh value. Must be re-measured"),
    ("Ti[1]Fe[0.9]Al[0.1]", "stationary tier", "stationary rank 1"),
    ("Ti[0.9]Zr[0.1]Mn[1.4]", "stationary tier", "stationary rank 2; low-pressure AB2"),
    ("Ti[1]Fe[0.85]Mn[0.15]", "stationary tier", "TiFe-Mn family is repeatedly top-10; Mn is known to ease TiFe activation"),
    ("Ca[1]Ni[5]", "stationary tier", "stationary rank 6; rare-earth-free AB5"),
]
ML_TESTS = [("LaNi5-xAlx (AB5)", 0.8), ("TiFe1-xMnx (AB)", 0.25)]


def short(pid: str) -> str:
    return re.sub(r"\[([0-9.]+)\]", lambda m: "" if m.group(1) == "1" else m.group(1), pid)


def candidates() -> pd.DataFrame:
    c = pd.read_csv(T / "screening_candidates.csv").set_index("purdue_id")
    rm = pd.read_csv(T / "screening_mobile_ranking.csv").set_index("purdue_id")["rank"]
    rs = pd.read_csv(T / "screening_stationary_ranking.csv").set_index("purdue_id")["rank"]
    rows = []
    for pid, role, why in SELECTION:
        r = c.loc[pid]
        rows.append({"material": short(pid), "family": r["family"], "role": role, "basis": "experimental (.mh)",
                     "wt_pct_reported": round(r["wt_pct"], 2), "dH_kJmol": round(r["dH_kJmol_weighted"], 1),
                     "T1bar_C": round(r["T1_full_C"], 0), "P25_bar": float(f"{r['P25_bar']:.3g}"),
                     "mobile_rank": int(rm[pid]) if pid in rm else "fail",
                     "stationary_rank": int(rs[pid]) if pid in rs else "fail", "why": why})
    s = pd.read_csv(T / "vant_hoff_ml_series.csv")
    for series, x in ML_TESTS:
        q = s[(s["series"] == series) & (abs(s["x"] - x) < 1e-6)].iloc[0]
        name = {"LaNi5-xAlx (AB5)": f"LaNi{5 - x:g}Al{x:g}", "TiFe1-xMnx (AB)": f"TiFe{1 - x:g}Mn{x:g}"}[series]
        rows.append({"material": name, "family": q["family"], "role": "ML test (not in data)",
                     "basis": "ESTIMATE: ML ΔH + family-median ΔS",
                     "wt_pct_reported": None, "dH_kJmol": round(q["dH_predicted"], 1),
                     "T1bar_C": round(q["T1bar_C_estimate"], 0), "P25_bar": float(f"{q['Peq25_bar_estimate']:.3g}"),
                     "mobile_rank": "-", "stationary_rank": "-",
                     "why": (f"blind test of the ML model: predicted ΔH {q['dH_predicted']:.1f} kJ/mol, 80% interval "
                             f"{q['dH_interval_low']:.1f}–{q['dH_interval_high']:.1f}; T(1 bar) band "
                             f"{q['T1bar_C_band_low']:.0f}–{q['T1bar_C_band_high']:.0f} °C")})
    out = pd.DataFrame(rows)
    out.to_csv(T / "proposed_experimental_candidates.csv", index=False)
    return out


MATRIX = [
    # technique, families, property measured, project gap it closes
    ("Arc melting (Ar, Ti getter, 4–5 remelts with flipping)", "AB5, AB2, AB, BCC/SS", "synthesis", "produce the nominal compositions screened"),
    ("Homogenisation anneal (sealed quartz under Ar, then quench)", "AB5, AB2, AB", "synthesis", "remove segregation, so measured ΔH belongs to the intended phase"),
    ("High-energy ball milling (Ar, sealed vials)", "Mg-based, NaAlH4 (+Ti catalyst)", "synthesis / nanostructuring", "kinetic limitation of Mg and complex hydrides (Phase 7)"),
    ("ICP-OES of dissolved alloy", "all, esp. mischmetal alloys", "bulk composition", "nominal vs actual composition (ML uses nominal); Mm composition is unknown in Purdue"),
    ("XRD + Rietveld refinement", "all", "phases, lattice parameters, C14/C15, hydride expansion", "C14/C15 is invisible to composition features (Phase 4 limitation)"),
    ("SEM/EDS (BSE imaging, point and map analysis)", "all", "microstructure, secondary phases, local composition", "explains sloped plateaus / extra plateaus"),
    ("Activation cycles in the Sieverts rig", "AB (TiFe) especially; all", "activation behaviour", "TiFe activation is not in the data"),
    ("Sieverts (volumetric) PCT, abs + des, ≥4 temperatures over ≥40 K", "all", "plateau P(T), capacity, slope, hysteresis", "replaces literature/digitised data; gives ΔH, ΔS with uncertainty"),
    ("Kinetic uptake / release curves at fixed P/Peq", "all", "rate constants, Ea (several T)", "kinetics comparable across materials (Phase 7 found 7 orders of spread)"),
    ("Cycling (≥100 abs/des cycles) with periodic PCT", "selected candidates", "capacity retention, plateau shift", "cycle life is missing from the screening"),
    ("DSC (heat-flux, high-pressure cell if needed)", "all; Mg, NaAlH4", "reaction enthalpy; Kissinger Ea from heating-rate series", "independent ΔH check of the Van't Hoff value"),
    ("TGA / TPD-MS", "Mg-based, NaAlH4", "desorption temperature, gravimetric capacity, impurity release", "capacity definition (reversible vs total)"),
    ("Thermal conductivity: transient plane source on powder beds/compacts", "selected candidates", "k_eff vs H2 pressure and compaction", "only 14 Purdue materials have k_eff; heat removal limits refuelling"),
    ("Bed density / tapped density", "selected candidates", "packing density", "converts solid-basis volumetric capacity to bed basis (Phase 8)"),
]


def main():
    cand = candidates()
    mat = pd.DataFrame(MATRIX, columns=["technique", "families", "property measured", "gap in this project it addresses"])
    mat.to_csv(T / "characterisation_matrix.csv", index=False)
    text = f"""# Phase 9: proposed synthesis and characterisation methodology

> **Status: PROPOSED FUTURE WORK.** No material was synthesised, activated or measured in this project.
> Everything in Phases 1–8 is data analysis of published literature data (Purdue Metal Hydride Toolbox and
> ML-HydPARK). This document describes how the computational results *could be tested* in a laboratory.

## 1. Purpose

The computational work leaves specific, measurable questions open:

1. **Thermodynamics of the screened candidates.** Phase 7 showed that for several candidates the digitised PCI
   curves and the tabulated ΔH disagree by more than 5 kJ/mol. Phase 6 showed that ±5 kJ/mol shifts the
   1-bar temperature by tens of kelvin.
2. **Blind test of the ML model.** Predicted ΔH for compositions not in the data comes with an 80% interval of
   about 3–6 kJ/mol either side (Phase 6). Only a measurement can check it.
3. **Properties missing from the data:** activation, cycle life, comparable kinetics, thermal conductivity, actual composition and
   phase (C14/C15), and the definition of capacity (reversible vs total).

## 2. Proposed alloys

Chosen from the Phase 6–8 tables (`results/tables/proposed_experimental_candidates.csv`):

{md_table(cand)}

Rationale: two benchmarks first, to validate the apparatus against well-documented materials. Then three mobile-tier and four
stationary-tier alloys spanning AB, AB2 and AB5. Then two compositions that are **absent from both datasets**, so the ML
prediction is a genuine blind test. All alloys are melt-processable (no ball milling or glovebox chemistry needed for the
core set), which keeps the plan feasible for a B.Tech/M.Tech laboratory. The exception is CaNi5: Ca has a high vapour pressure, so it is
better made by induction melting in a closed crucible than by open arc melting.

## 3. Synthesis

**Intermetallics (AB5, AB2, AB, BCC solid solutions): arc melting**
* Weigh high-purity elements (≥ 99.9%) to the nominal composition. Add a small excess of volatile or easily oxidised elements
  (e.g. Mn, which evaporates during melting) only after a first trial melt shows measurable loss.
* Melt on a water-cooled copper hearth under purified argon, after melting a Ti getter button to remove residual O2.
  Remelt 4–5 times, flipping the button each time for homogeneity. Weigh after melting to check mass loss.
* Homogenise in a sealed, Ar-backfilled quartz ampoule, then quench. Temperature and time depend on the alloy
  system and are taken from the phase diagram / source paper for each alloy.
* Crush mechanically in air for AB5/AB, or in an Ar glovebox for oxidation-sensitive alloys, to coarse powder before activation.
  Hydrogen cycling decrepitates the alloy further.

**Mg-based and complex hydrides (only if the high-temperature stationary scenario is pursued)**
* High-energy ball milling under Ar, with a catalyst addition: for example transition-metal or oxide catalysts for MgH2 (Huot et al., 1999),
  or Ti-based dopants for NaAlH4 (Bogdanović & Schwickardi, 1997). Milling time, ball-to-powder ratio and speed are
  experimental variables. Handling in an Ar glovebox is required (pyrophoric and air- and moisture-sensitive powders).

**Activation**
* AB5 alloys usually activate easily: a few absorption/desorption cycles near room temperature (Sandrock 1999).
* TiFe needs a thermal activation step: heating under vacuum, then under H2, then cycling (Reilly & Wiswall 1974).
  Mn substitution is used to ease this (TiFe–Mn candidates above). The number of cycles to full capacity is recorded,
  because it is an engineering property missing from the screening.

## 4. Characterisation

{md_table(mat)}

**Sieverts PCT protocol (core measurement)**
* Calibrate reservoir and sample-cell volumes with He. Run leak tests. Use a real-gas equation of state for H2
  (NIST data), because the ideal-gas error is significant at tens of bar. Follow the best-practice guidance of
  Broom (2011) and Gross et al. (DOE/NREL best-practices report).
* Measure absorption **and** desorption isotherms at **at least 4 temperatures spanning at least 40 K**, plus a repeat isotherm
  after cycling. Phase 7 found that 3 isotherms over a narrow span give unstable ΔH.
* Use an equilibrium criterion per point (pressure drift below a set threshold over a set time) and report it.
* Fit Van't Hoff lines to the plateau mid-points for absorption and desorption separately. Report ΔH and ΔS **with
  regression uncertainty**, the plateau slope (d ln P / d(w/w_max)), the hysteresis ln(Pa/Pd), and the capacity defined
  as the reversible amount between stated pressure limits.

**Independent checks**
* DSC gives the reaction enthalpy directly. A heating-rate series gives an apparent activation energy (Kissinger 1957).
* XRD with Rietveld refinement (Rietveld 1969): phase purity, C14/C15 type for AB2, and lattice expansion on hydriding.
* ICP-OES and SEM/EDS: the actual composition can then be fed back into the Phase 4 descriptors, to see whether nominal-vs-actual
  composition explains part of the ML error.
* Thermal conductivity of powder beds by the transient plane source method (Gustafsson 1991), as a function of H2 pressure.

## 5. How the results would test this project

| Question | Measurement | Success criterion (defined before measuring) |
|---|---|---|
| Is the ML model useful for screening? | ΔH of the 2 blind-test alloys | measured ΔH inside the predicted 80% interval |
| Are the tabulated ΔH of top candidates right? | PCT of candidates, esp. the flagged Ti0.56V0.3Zr0.1Mn0.94Fe0.06Ni0.04 | |ΔH_meas − ΔH_.mh| < 2 kJ/mol (inter-source scatter, Phase 2) |
| Do screening decisions survive real data? | T(1 bar), P(25/50 °C), Pabs from measured isotherms | each candidate still passes its hard constraints |
| Is capacity comparable? | reversible capacity between fixed limits (e.g. 1–10 bar at 25 °C) | consistent definition for all candidates |
| Is AB2 C14/C15 a hidden variable? | XRD phase identification | correlate C14/C15 with residuals of the ML model |

## 6. Safety

* H2 is flammable over a wide concentration range. Use a ventilated enclosure, H2 detectors, leak-tested fittings,
  pressure-rated components with relief valves, and no ignition sources.
* Activated hydride powders and ball-milled Mg/alanate powders can be pyrophoric. Handle under Ar and passivate before
  exposure to air. Decrepitation produces fine powder, so the rig needs particle filters.
* Arc melter: high current and UV. Follow the equipment SOP and wear eye protection.

## 7. Indicative timeline (one semester, if laboratory access exists)

| Weeks | Task |
|---|---|
| 1–2 | Safety training; Sieverts volume calibration; LaNi5 benchmark purchase/synthesis |
| 3–5 | Arc melting and homogenisation of the 9 melt alloys; XRD, SEM/EDS, ICP-OES |
| 6–8 | Activation; PCT at ≥ 4 temperatures for benchmarks and stationary tier |
| 9–11 | PCT for mobile tier and blind-test alloys; DSC checks |
| 12–13 | Kinetic curves, 100-cycle test on 2 best candidates, k_eff on 1–2 beds |
| 14 | Analysis against the success criteria above; update screening with measured data |

## 8. What was done vs proposed

| Item | Status |
|---|---|
| Data extraction, audit, cleaning, cross-dataset comparison | **done** (Phases 1–2) |
| EDA, composition features, ML models | **done** (Phases 3–5) |
| Van't Hoff, PCI, kinetics analysis of literature data | **done** (Phases 6–7) |
| Mobile/stationary screening with sensitivity | **done** (Phase 8) |
| Synthesis, activation, PCT, XRD, SEM/EDS, DSC, thermal conductivity | **proposed only** (this document) |

## References

* Bogdanović B., Schwickardi M. (1997) Ti-doped alkali metal aluminium hydrides as potential novel reversible hydrogen storage materials. *J. Alloys Compd.* 253–254, 1–9.
* Broom D.P. (2011) *Hydrogen Storage Materials: The Characterisation of Their Storage Properties.* Springer, London.
* Gross K.J. et al. *Recommended Best Practices for the Characterization of Storage Properties of Hydrogen Storage Materials.* U.S. DOE / NREL (2012).
* Gustafsson S.E. (1991) Transient plane source techniques for thermal conductivity and thermal diffusivity measurements of solid materials. *Rev. Sci. Instrum.* 62, 797–804.
* Huot J., Liang G., Boily S., Van Neste A., Schulz R. (1999) Structural study and hydrogen sorption kinetics of ball-milled magnesium hydride. *J. Alloys Compd.* 293–295, 495–500.
* Kissinger H.E. (1957) Reaction kinetics in differential thermal analysis. *Anal. Chem.* 29, 1702–1706.
* Reilly J.J., Wiswall R.H. (1974) Formation and properties of iron titanium hydride. *Inorg. Chem.* 13, 218–222.
* Rietveld H.M. (1969) A profile refinement method for nuclear and magnetic structures. *J. Appl. Crystallogr.* 2, 65–71.
* Sandrock G. (1999) A panoramic overview of hydrogen storage alloys from a gas reaction point of view. *J. Alloys Compd.* 293–295, 877–888.
* Schlapbach L., Züttel A. (2001) Hydrogen-storage materials for mobile applications. *Nature* 414, 353–358.
"""
    (ROOT / "reports/synthesis_characterization_plan.md").write_text(text)
    print(cand.to_string(index=False))


if __name__ == "__main__":
    main()
