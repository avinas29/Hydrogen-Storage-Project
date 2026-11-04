"""Write reports/screening.md from the Phase 8 tables (numbers computed)."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ..data.run_audit import md_table
from .screen import CRITERIA, KINETICS_CLASS, KINETICS_NO_DATA, WEIGHTS

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "results/tables"
REF = {"La[1]Ni[5]": "LaNi5", "Mm[1]Ni[4.5]Al[0.5]": "MmNi4.5Al0.5", "Ca[1]Ni[5]": "CaNi5",
       "Ti[1]Fe[1]": "TiFe", "Ti[1]Fe[0.9]Mn[0.1]": "TiFe0.9Mn0.1", "HydralloyC2": "Hydralloy C2",
       "Ti[1.01]Cr[1.06]Mn[1]": "TiCrMn", "V[0.855]Ti[0.095]Fe[0.05]": "V-Ti-Fe BCC",
       "Na[1]Al[1]H[1]": "NaAlH4 (Ti-doped)", "Mg[2]Ni[1]": "Mg2Ni", "Mg[1]": "MgH2"}
LH2_KG_M3 = 70.8      # liquid H2 at 20 K, 1 atm (NIST)
GH2_700_KG_M3 = 40.2  # H2 gas at 700 bar, 15 C (NIST real-gas density, ~40 kg/m3)


def fail_counts(c: pd.DataFrame, app: str) -> pd.DataFrame:
    labels = {"data quality": "data-quality gate", "T(1 bar)": "T(1 bar) too high",
              "P(25 °C)": "P(25 °C) too high", "P(50 °C)": "P(50 °C) too high",
              "charging P": "charging pressure too high"}
    counts = {v: 0 for v in labels.values()}
    for s in c[f"{app}_fail_reasons"].fillna(""):
        for part in [x.strip() for x in s.split(";") if x.strip()]:
            for k, v in labels.items():
                if part.startswith(k):
                    counts[v] += 1
                    break
    return pd.DataFrame({"reason (a material may fail several)": list(counts), "n_materials": list(counts.values())})


def short(pid: str) -> str:
    return re.sub(r"\[([0-9.]+)\]", lambda m: "" if m.group(1) == "1" else m.group(1), pid)


def main():
    c = pd.read_csv(T / "screening_candidates.csv")
    rk = {a: pd.read_csv(T / f"screening_{a}_ranking.csv") for a in ("mobile", "stationary")}
    mc = {a: pd.read_csv(T / f"screening_{a}_sensitivity_mc.csv") for a in ("mobile", "stationary")}
    oat = {a: pd.read_csv(T / f"screening_{a}_sensitivity_oat.csv") for a in ("mobile", "stationary")}
    sc = pd.read_csv(T / "screening_constraint_scenarios.csv")

    crit_tab = pd.DataFrame([
        ["data quality (both)", "|ΔS| within 70–170 J/(mol K); capacity not 'assumed'/'unconfirmed'", "removes records flagged in Phases 1–2"],
        ["mobile", f"T(1 bar, full capacity) ≤ {CRITERIA['mobile']['T1_full_max_C']:.0f} °C", "desorption driven by PEM fuel-cell waste heat (stack 60–80 °C)"],
        ["mobile", f"P(50 °C) ≤ {CRITERIA['mobile']['P50_max_bar']:.0f} bar", "tank pressure on a hot day stays moderate"],
        ["mobile", f"charging P(25 °C) ≤ {CRITERIA['mobile']['Pcharge25_max_bar']:.0f} bar", "refuelling without very high compression"],
        ["stationary", f"T(1 bar, full capacity) ≤ {CRITERIA['stationary']['T1_full_max_C']:.0f} °C", "low-grade industrial or electrolyser/boiler heat"],
        ["stationary", f"P(25 °C) ≤ {CRITERIA['stationary']['P25_max_bar']:.0f} bar", "low-pressure storage at room temperature (safety, cheaper vessel)"],
        ["stationary", f"P(50 °C) ≤ {CRITERIA['stationary']['P50_max_bar']:.0f} bar", "warm-day pressure limit"],
        ["stationary", f"charging P(25 °C) ≤ {CRITERIA['stationary']['Pcharge25_max_bar']:.0f} bar", "fill directly from a pressurised PEM electrolyser (no compressor) — assumed 30 bar delivery"],
    ], columns=["application", "hard constraint", "engineering reason"])

    wtab = pd.DataFrame(WEIGHTS).fillna(0).rename_axis("criterion").reset_index()

    def top(app, n=10):
        r = rk[app].head(n).copy()
        r["material"] = r["purdue_id"].map(short)
        r["flags"] = [", ".join(s for s, f in (("PCI ΔH mismatch", a), ("Sandia ref unverified", b),
                                               ("duplicate data", d), ("ΔH refit from isotherms", e)) if f)
                      for a, b, d, e in zip(r["flag_pci_dH_inconsistent"], r["flag_unverified_ref_sandia"],
                                            r["flag_identical_values_other_file"], r["flag_thermo_refit_from_isotherms"])]
        return r[["rank", "material", "family", "wt_pct", "T1_full_C", "P25_bar", "heat_MJ_per_kgH2",
                  "cost_label", "score", "flags"]].round(2)

    def ref_tab():
        rows = []
        cc = c.set_index("purdue_id")
        for pid, name in REF.items():
            row = {"material": name, "wt_pct": round(cc.loc[pid, "wt_pct"], 2),
                   "T1_full_C": round(cc.loc[pid, "T1_full_C"], 0), "P25_bar": float(f"{cc.loc[pid, 'P25_bar']:.3g}")}
            for app in ("mobile", "stationary"):
                r = rk[app].set_index("purdue_id")
                row[app] = (f"rank {int(r.loc[pid, 'rank'])} / {len(r)}" if pid in r.index
                            else "fails: " + cc.loc[pid, f"{app}_fail_reasons"])
            rows.append(row)
        return pd.DataFrame(rows)

    def fam_tab():
        rows = []
        for f, g in c.groupby("family"):
            row = {"family": f, "n": len(g)}
            for app in ("mobile", "stationary"):
                row[f"{app}_pass"] = int(g[f"{app}_pass"].sum())
                r = rk[app][rk[app]["family"] == f]
                row[f"{app}_best_rank"] = int(r["rank"].min()) if len(r) else "-"
            rows.append(row)
        return pd.DataFrame(rows).sort_values("n", ascending=False)

    def mc_tab(app, n=10):
        m = mc[app].pivot_table(index=["purdue_id", "base_rank"], columns="scheme", values="p_top10").reset_index()
        m = m.sort_values("base_rank").head(n)
        m["material"] = m["purdue_id"].map(short)
        cols = ["base_rank", "material"] + [s for s in m.columns if s.startswith(("perturbed", "random"))]
        return m[cols].round(2)

    def oat_tab(app):
        o = oat[app].copy()
        return o[["criterion", "weight_factor", "kendall_tau_vs_base", "top10_overlap"]].round(2)

    vol = c[c["vol_H_kg_m3_solid"].notna()].copy()
    vol_rows = vol[vol["purdue_id"].isin(REF)].assign(material=lambda d: d["purdue_id"].map(REF))[
        ["material", "rho_kg_m3_stated", "wt_pct", "vol_H_kg_m3_solid"]].round(1)
    underrep = c[c["family"].isin(["Mg", "Complex"])][["purdue_id", "family", "wt_pct", "capacity_definition",
                                                        "T1_full_C", "heat_MJ_per_kgH2", "mobile_fail_reasons",
                                                        "stationary_fail_reasons"]].round(1)
    s350 = sc[(sc.application == "stationary") & (sc.threshold == "T1_full_max_C") & (sc.value == 350)].iloc[0]
    m10, s10 = rk["mobile"].head(10), rk["stationary"].head(10)
    tife10 = s10[s10["purdue_id"].str.startswith("Ti[1]Fe")]
    def most_sensitive(app):
        o = oat[app].sort_values("kendall_tau_vs_base")
        return ", ".join(f"{r.criterion} ×{r.weight_factor:g} (τ = {r.kendall_tau_vs_base:.2f})" for r in o.head(2).itertuples())
    def oat_top(app, crit, f):
        o = oat[app]
        return o[(o.criterion == crit) & (o.weight_factor == f)]["new_top3"].iloc[0]

    text = f"""# Phase 8: stationary vs mobile screening

Code: `src/screening/screen.py` (method, constants), `src/screening/report.py` (this file), and
`src/visualization/screening_plots.py` (Figs. 24–26). Tables: `results/tables/screening_*.csv`.

**Scope.** This is a *material-level* screening. Capacities are the reported values from the Purdue files
(definition not uniform, Phase 1). Thermodynamics are the experimental ΔH/ΔS (Phase 6). No ML prediction
is used. A real storage system adds a pressure vessel, heat exchanger, bed porosity and balance of plant, so
its gravimetric capacity is much lower than the material's. The DOE target (5.5 wt%) is a *system* target
and is drawn only for orientation.

## 1. Method

1. Candidates: all {len(c)} Purdue materials. Mischmetal alloys are included here, because screening needs only measured
   properties, not elemental descriptors.
2. A data-quality gate and **hard constraints** remove unsuitable materials (each failure is recorded with its reason).
3. The remaining criteria are normalised to 0–1 among the candidates that pass, and combined with **transparent weights**.
4. A **sensitivity analysis** varies the weights (2000 random draws × 2 schemes, plus one-at-a-time changes) and the
   constraint thresholds.

{md_table(crit_tab)}

Criteria (1 = best):

| criterion | definition |
|---|---|
| capacity | reported wt%, min–max scaled |
| heat | reaction heat per kg H2 (width-weighted over plateaus), lower is better |
| kinetics | family-level class from Phase 7: AB5/AB2/AB/AB3 = {KINETICS_CLASS['AB5']}, complex = {KINETICS_CLASS['Complex']}, Mg = {KINETICS_CLASS['Mg']}; no data (SS, A2B7, Misc) = {KINETICS_NO_DATA} and flagged |
| hysteresis | ln(Pa/Pd) at 25 °C, lower is better; missing = 0.5 (neutral) |
| pressure_fit | 1 if 1 ≤ P(25 °C) ≤ 10 bar, falling to 0 one decade outside |
| pressure_safety | lower log P(25 °C) is better (stationary only) |
| cost | qualitative element indicator: common metals 1; rare earth/mischmetal, Co, V, minor metals 0.5; precious metals 0. **Not a price model** |

Weights (sum to 1 per application). Mobile emphasises capacity and heat; stationary emphasises cost, low pressure and cycling
loss (hysteresis):

{md_table(wtab)}

Multi-plateau materials use the *most stable* plateau for T(1 bar), because full capacity is needed, and the *highest*
pressure plateau for pressure limits.

## 2. Constraint outcome (Fig. 24)

| | mobile | stationary |
|---|---|---|
| pass data-quality gate | {int(c['data_quality_pass'].sum())} | {int(c['data_quality_pass'].sum())} |
| pass all constraints | {int(c['mobile_pass'].sum())} | {int(c['stationary_pass'].sum())} |

Why materials fail:

**Mobile**

{md_table(fail_counts(c, 'mobile'))}

**Stationary**

{md_table(fail_counts(c, 'stationary'))}

By family:

{md_table(fam_tab())}

## 3. Rankings (Fig. 25)

### Mobile: top 10

{md_table(top('mobile'))}

### Stationary: top 10

{md_table(top('stationary'))}

### Reference materials

{md_table(ref_tab())}

**Interpretation.**
* *Mobile.* The best candidates are Ti-based AB2 Laves alloys (Ti–Cr–Mn, Ti–Zr–Mn–Cr) and TiFe-type alloys. The top 10 reach
  {m10['wt_pct'].min():.2f}–{m10['wt_pct'].max():.2f} wt% at the material level, reach 1 bar at or below {m10['T1_full_C'].max():.0f} °C, and need
  {m10['heat_MJ_per_kgH2'].min():.1f}–{m10['heat_MJ_per_kgH2'].max():.1f} MJ/kg H2 ({100*m10['heat_MJ_per_kgH2'].min()/119.96:.0f}–{100*m10['heat_MJ_per_kgH2'].max()/119.96:.0f}% of LHV).
  The two highest-ranked AB2 alloys run at {m10['P25_bar'].head(2).min():.0f}–{m10['P25_bar'].head(2).max():.0f} bar at 25 °C, so they are high-pressure hydrides. LaNi5 passes but ranks only
  {int(rk['mobile'].set_index('purdue_id').loc['La[1]Ni[5]','rank'])} because of its low capacity ({c.set_index('purdue_id').loc['La[1]Ni[5]','wt_pct']:.2f} wt%).
  **No interstitial hydride comes near the 5.5 wt% system target.** Material-level capacities of about 2 wt% suit mobile
  uses where mass matters less than volume, safety or low pressure.
* *Stationary.* Constraints and weights favour **low-pressure alloys made of common metals**: TiFe and its Al- and Mn-substituted
  variants (Ni and Cr variants follow just below the top 10), Ti–Zr–Mn AB2 and CaNi5. TiFe-type alloys make up {len(tife10)} of the top 10. They combine a plateau of
  {tife10['P25_bar'].min():.1f}–{tife10['P25_bar'].max():.1f} bar at 25 °C, cheap elements and {tife10['wt_pct'].min():.1f}–{tife10['wt_pct'].max():.1f} wt%, and weight barely matters in stationary use. Ti-doped NaAlH4 passes (T(1 bar) about 100 °C ≤ 150 °C),
  but ranks {int(rk['stationary'].set_index('purdue_id').loc['Na[1]Al[1]H[1]','rank'])} because of its family-level kinetics class and heat demand.
* Data caveats are kept visible. Several top-ranked entries cite unverified Sandia references, or have PCI curves whose
  Van't Hoff ΔH differs by more than 5 kJ/mol from the tabulated one (e.g. {short(rk['mobile'][rk['mobile'].flag_pci_dH_inconsistent].purdue_id.iloc[0])}).
  Two files (Ti1Mn1.4V0.62, Ti1Mn1.5V0.62) carry identical data. Any candidate taken forward needs its own PCT measurement (Phase 9).

## 4. Sensitivity (Fig. 26)

Probability of staying in the top 10 under weight perturbation. "Perturbed": Dirichlet centred on the base weights
(concentration 20). "Random": uniform Dirichlet, i.e. any weights.

**Mobile**

{md_table(mc_tab('mobile'))}

**Stationary**

{md_table(mc_tab('stationary'))}

One-at-a-time changes (weight × 0 or × 2). Kendall τ of the full ranking vs base, and overlap of the top 10:

**Mobile**

{md_table(oat_tab('mobile'))}

**Stationary**

{md_table(oat_tab('stationary'))}

Constraint thresholds:

{md_table(sc)}

Conclusions from the sensitivity analysis:
* The *composition of the top group* is robust: Ti-based AB2/AB alloys for mobile, TiFe-type and Ti–Zr–Mn alloys for stationary.
  The exact order inside it is not, and depends on the weights. Rankings should be read as tiers, not as a single winner.
* The largest one-at-a-time effects are, for mobile: {most_sensitive('mobile')}; for stationary: {most_sensitive('stationary')}.
* Doubling the mobile capacity weight moves the V–Ti–Fe BCC solid solutions (3.4–3.7 wt%) to the top
  ({oat_top('mobile', 'capacity', 2.0)}). Their high capacity is offset in the base case by higher heat demand and
  the neutral (no-data) kinetics class.
* Setting the stationary cost weight to zero brings a Ca–mischmetal AB5 alloy into the top 3 ({oat_top('stationary', 'cost', 0.0)}).
* Mg-based hydrides enter the stationary set only when heat at about 350 °C is available. In that case
  {s350['n_pass']} materials pass, including all 4 Mg-based ones.

## 5. Under-represented families (MgH2, Mg2Ni, NaAlH4)

{md_table(underrep)}

These families have the highest capacities in the dataset (3.6–7.6 wt%). They are excluded from mobile PEMFC use
by thermodynamics alone: ΔH of 47–78 kJ/mol means 100–300 °C for 1 bar and 23–39 MJ/kg H2 (19–32% of LHV). Their kinetic
records show absorption activation energies about 3–6× those of the intermetallics (92–132 vs median 24–31 kJ/mol, Phase 7). This agrees with standard reviews (Sandrock
1999, J. Alloys Compd. 293–295, 877; Schlapbach & Züttel 2001, Nature 414, 353): Mg-based and complex hydrides need
destabilisation, catalysis or nanostructuring, plus high-temperature heat integration. For stationary systems with a high-temperature
heat source (e.g. solid-oxide fuel cell or concentrated solar heat), MgH2 becomes a candidate (scenario above).
With only 4 Mg-based and 1 complex hydride in the Purdue data, this assessment rests on individual records, not statistics.

## 6. Volumetric density (where density is stated)

Hydrogen per unit volume of *solid* material, ρ·w/(1−w), for {len(vol)} materials with a stated density. It is an upper bound:
no bed porosity (often 40–50%) and no lattice expansion on hydriding, and some densities were back-calculated by the
curator ("assuming a porosity of 40%").

{md_table(vol_rows)}

Range over all {len(vol)}: {vol['vol_H_kg_m3_solid'].min():.0f}–{vol['vol_H_kg_m3_solid'].max():.0f} kg H2/m³. For comparison, liquid H2 is {LH2_KG_M3} kg/m³ and compressed H2 at 700 bar
about {GH2_700_KG_M3:.0f} kg/m³ (NIST). Even after allowing about 50% bed porosity, hydrides store hydrogen at least as densely as
700 bar gas and at a few bar. This is their main argument for stationary and volume-limited applications, against
their weight penalty.

## 7. Limits of this screening

* Material level only. No vessel, heat exchanger or system mass and volume.
* Capacity definitions are not uniform. Cost is a qualitative element indicator. Kinetics enter only as a family-level class.
* Hysteresis is missing for {int(c['hyst_ln_Pa_Pd_25C'].isna().sum())} of {len(c)} materials and scored as neutral.
* Cycle life, activation behaviour, impurity tolerance (O2, H2O, CO) and safety (pyrophoricity) are not in the data. These
  are often decisive in practice (e.g. TiFe needs activation).
"""
    (ROOT / "reports/screening.md").write_text(text)


if __name__ == "__main__":
    main()
