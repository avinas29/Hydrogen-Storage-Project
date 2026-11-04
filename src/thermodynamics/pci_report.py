"""Write reports/pci_kinetics.md from the Phase 7 tables (numbers computed)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..data.run_audit import md_table
from .pci_kinetics import REPRESENTATIVE_PCI, WINDOW, load_all_pci
from .vant_hoff import peq_bar

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "results/tables"
TOOLBOX_DEFAULT_HYST = {"AB": 0.51, "AB2": 0.54, "AB3": 0.29, "AB5": 0.39, "SS": 0.80}  # GetTypeProperty.m


def naalh4_check(pts: pd.DataFrame) -> pd.DataFrame:
    """Compare the two NaAlH4 plateaus visible in the 433 K desorption curve with Van't Hoff values."""
    g = pts[(pts["material_id"] == "Na[1]Al[1]H[1]") & (pts["mode"] == "des")].sort_values("wt_pct")
    x = g["wt_pct"] / g["wt_pct"].max()
    T_K = g["T_K"].iloc[0]
    low = float(np.exp(np.median(np.log(g.loc[(x > 0.05) & (x < 0.35), "P_bar"]))))
    high = float(np.exp(np.median(np.log(g.loc[(x > 0.55) & (x < 0.9), "P_bar"]))))
    return pd.DataFrame([
        {"plateau": "low-H (Na3AlH6 → NaH)", "dH_kJmol": 47, "dS_JmolK": 126, "T_K": T_K,
         "P_curve_bar": low, "P_vant_hoff_bar": float(peq_bar(T_K, 47, 126))},
        {"plateau": "high-H (NaAlH4 → Na3AlH6)", "dH_kJmol": 37, "dS_JmolK": 122, "T_K": T_K,
         "P_curve_bar": high, "P_vant_hoff_bar": float(peq_bar(T_K, 37, 122))}]).round(2)


def main():
    pts, meta = load_all_pci()
    curves = pd.read_csv(T / "pci_curve_plateaus.csv")
    fits = pd.read_csv(T / "pci_vant_hoff_fits.csv")
    hy = pd.read_csv(T / "pci_hysteresis.csv")
    k = pd.read_csv(T / "kinetics_purdue.csv")
    idx = pd.read_csv(ROOT / "data/interim/purdue_pci_index.csv")

    single = fits[~fits["multi_plateau_excluded"] & fits["d_dH"].notna()].copy()
    single["abs_d"] = single["d_dH"].abs()
    single["T_span_K"] = single["T_range_K"].str.split("-").apply(lambda v: float(v[1]) - float(v[0]))
    rho = single[["abs_d", "T_span_K"]].corr(method="spearman").iloc[0, 1]
    multi = fits[fits["multi_plateau_excluded"] & fits["d_dH"].notna()]
    worst = single.nlargest(4, "abs_d")[["material_id", "mode", "dH_fit_kJmol", "dH_mh_kJmol", "d_dH",
                                         "n_T", "T_range_K", "R2_fit"]].round(2)
    hyf = hy.groupby("family")["ln_Pa_Pd_pci"].agg(n_pairs="count", median="median", min="min", max="max").round(2)
    hyf["n_materials"] = hy.groupby("family")["material_id"].nunique()
    hyf["toolbox_type_default"] = hyf.index.map(TOOLBOX_DEFAULT_HYST)
    hyf = hyf.reset_index()
    comp = k[k["model_form_comparable"]]
    kfam = comp.groupby(["family", "mode"])["Ea_kJmol"].agg(n="count", min="min", median="median", max="max").round(1).reset_index()
    other = k[~k["model_form_comparable"]][["material_id", "mode", "Ea_kJmol", "pFcn", "wFcn"]]
    other["wFcn"] = other["wFcn"].str.slice(0, 40)
    rep_rows = []
    for mid, lab in REPRESENTATIVE_PCI.items():
        m = meta[meta["material_id"] == mid]
        c = curves[curves["material_id"] == mid]
        rep_rows.append({"material": lab, "source": f"{m['author'].iloc[0]}, {m['figure'].iloc[0]}",
                         "curves (abs/des)": f"{(m['mode']=='abs').sum()}/{(m['mode']=='des').sum()}",
                         "T range (K)": f"{m['T_K'].min():g}–{m['T_K'].max():g}",
                         "max wt% in curves": round(c["wt_max_curve"].max(), 2),
                         "median plateau slope dlnP/dx": round(c["slope_dlnP_dx"].median(), 2),
                         "curator-shifted": bool(m["flag_shifted_by_curator"].any())})
    rep = pd.DataFrame(rep_rows)
    na = naalh4_check(pts)
    lc = curves[(curves["material_id"] == "La[1]Ni[5]") & (curves["mode"] == "des")].set_index("T_K")["P_plateau_bar"]
    la_ratio = lc.loc[298] / lc.loc[273]   # 323 K desorption curve has too few window points
    la_vh = float(peq_bar(298, 32.151, 112.8) / peq_bar(273, 32.151, 112.8))

    text = f"""# Phase 7: PCI isotherms and kinetics

Code: `src/thermodynamics/pci_kinetics.py`, `src/thermodynamics/pci_report.py`, `src/visualization/pci_plots.py`
(Figs. 21–23). Tables: `results/tables/pci_*.csv` and `kinetics_purdue.csv`.

## 1. What the PCI files are

* {len(idx)} files, {len(curves)} curves ({(curves['mode']=='abs').sum()} absorption, {(curves['mode']=='des').sum()} desorption) and {len(pts)} points in total.
* **All {int(idx['digitized_from_figure'].sum())} are digitised from published figures** (field `Location` = "Figure N"). **{int(idx['shifted_by_curator'].sum())} were shifted
  along the composition axis** by the curator to remove an irreversible part. Absolute capacities in these
  curves are therefore *reversible-portion* capacities under the authors' conditions, not total uptake.
* Composition is in mass% H. Pressure is in bar. {int(meta['flag_pressure_unit_not_stated'].sum())} curves (file
  `La[1]Ni[4.61]Mn[0.26]Al[0.13]_PCI.csv`) only say "eq. pressure"; they are read as bar, as `ReadPCIData.m` does, and flagged.
* Digitisation error was not quantified by the curators. Treat points as ±a few % in P and ±0.02–0.05 wt%.

## 2. Representative materials (Fig. 21)

{md_table(rep)}

* **LaNi5** shows the textbook behaviour: a flat plateau over about 0.2–1.3 wt% and small hysteresis. The desorption plateau rises
  {la_ratio:.1f}× from 273 to 298 K in the curves, against {la_vh:.1f}× from the .mh ΔH, ΔS.
* **TiFe0.8Ni0.15V0.05** (AB): a sloped plateau at 393–423 K. Substitution in TiFe is commonly used to tune the plateau and
  ease activation (Sandrock 1999).
* **Ti–Zr–Mn–V–Fe AB2** (Hydralloy-type): the largest capacity of the three intermetallics shown (about 1.9 wt%), a
  strongly sloped plateau, and clear hysteresis.
* **MgNi0.02** (absorption only): about 7 wt% but only at 547–653 K.
* **NaAlH4 + Ti**: two plateaus in one isotherm. They are a direct check of the Phase 6 plateau assignment:

{md_table(na)}

  The low-H plateau corresponds to the 47 kJ/mol step (Na3AlH6 → NaH): curve/Van't Hoff = {na.P_curve_bar[0]/na.P_vant_hoff_bar[0]:.2f}. The high-H plateau
  corresponds to the 37 kJ/mol step (NaAlH4 → Na3AlH6): ratio {na.P_curve_bar[1]/na.P_vant_hoff_bar[1]:.2f}. The reverse assignment would be off by a factor of about 10,
  so this confirms the relabelling made in Phase 6.

## 3. Plateau extraction and Van't Hoff check (Fig. 22)

Plateau = exp(median ln P) over {WINDOW[0]} ≤ w/w_max ≤ {WINDOW[1]}, with at least 4 points. It was extracted for {int(curves['P_plateau_bar'].notna().sum())} of {len(curves)} curves;
the rest have too few points in the window. Median plateau slope d ln P / d(w/w_max): absorption
{curves[curves['mode']=='abs']['slope_dlnP_dx'].median():.2f}, desorption {curves[curves['mode']=='des']['slope_dlnP_dx'].median():.2f}.

A Van't Hoff fit was made for each material and mode with at least 3 temperatures: {len(fits)} fits ({len(single)} single-plateau
with a tabulated reference value).

* **Single-plateau:** median |ΔH_PCI − ΔH_.mh| = {single['abs_d'].median():.2f} kJ/mol. {100*(single['abs_d']<=2).mean():.0f}% are within 2 kJ/mol.
* **This is a consistency check, not independent validation.** For {int(fits[(fits['mode']=='des')]['mh_thermo_from_isotherms'].fillna(False).astype(bool).sum())} of the desorption fits, the `.mh` value is flagged
  `From Isotherms: true`: the toolbox authors fitted it to these same curves, using their sloped-plateau model.
* The size of the disagreement is {'not explained by' if rho > -0.3 else 'larger for'} {'' if rho > -0.3 else 'narrower '}temperature spans (Spearman ρ(|ΔΔH|, ΔT span) = {rho:.2f}).
  The largest deviations are mostly strongly sloped AB2/AB plateaus. There, the fixed 0.2–0.8 window and the toolbox's
  sloped-plateau fit pick different "plateau" pressures:

{md_table(worst)}

* **Multi-plateau** materials ({len(multi)} fits) disagree strongly, as expected: a single "mid-curve" pressure mixes plateaus.
  They are excluded from conclusions.

## 4. Hysteresis from PCI curves

ln(Pa/Pd) at the same temperature, from abs/des pairs ({len(hy)} pairs):

{md_table(hyf)}

The toolbox's **type-default** hysteresis values (`GetTypeProperty.m`, used when a file states none) differ from the
curve-derived medians, by up to several times for AB, AB3 and SS. The samples are small (often 1–3 materials per
family), so the medians are indicative only. This supports the decision not to use the defaults.
Physically, hysteresis is a loss: it raises the charging pressure (compressor work) or the temperature
swing needed per cycle.

## 5. Kinetics

{len(k[k['mode']=='abs'])} absorption and {len(k[k['mode']=='des'])} desorption records, giving the rate law
dw/dt = Ca·exp(−Ea/RT)·f_p(P, Peq)·f_w(w). The type-default kinetics the toolbox would substitute are not included.

**Comparable group** (f_p = ln(P/Peq), first order in w; {len(comp)} records). Activation energies:

{md_table(kfam)}

**Not comparable**: other rate-law forms, which make Ca carry different units:

{md_table(other)}

* Absorption activation energies: median {comp[(comp.family=='AB5')&(comp['mode']=='abs')].Ea_kJmol.median():.0f} kJ/mol (AB5) and {comp[(comp.family=='AB2')&(comp['mode']=='abs')].Ea_kJmol.median():.0f} kJ/mol (AB2),
  against {k[(k.material_id=='Na[1]Al[1]H[1]')&(k['mode']=='abs')].Ea_kJmol.iloc[0]:.0f} kJ/mol for Ti-doped NaAlH4 and {k[(k.material_id=='Mg[1]')&(k['mode']=='abs')].Ea_kJmol.iloc[0]:.0f} kJ/mol for MgH2. For absorption the ordering
  intermetallics ≪ complex < Mg is consistent with Mg and complex hydrides being kinetically limited. (The MgH2
  *desorption* record, {k[(k.material_id=='Mg[1]')&(k['mode']=='des')].Ea_kJmol.iloc[0]:.0f} kJ/mol, uses a different rate-law form, so its Ea is not directly comparable.)
* The model t90 at 25 °C spans **{np.log10(comp['t90_s_25C'].max()/comp['t90_s_25C'].min()):.0f} orders of magnitude**
  ({comp['t90_s_25C'].min():.2g}–{comp['t90_s_25C'].max():.2g} s) within the comparable group. Even for one family, the fitted Ca
  depends on the test reactor, particle size, activation and heat-transfer limitation of each study. Several records carry notes
  such as "data assumed" ({int(k['flag_data_assumed'].sum())}) or "conflicts with Satheesh B" ({int(k['flag_conflicting_source'].sum())}).
* **Conclusion:** the kinetic records are suitable for qualitative family comparison (Ea ranges) only. They are **not**
  used to rank individual materials in Phase 8. Kinetics enters the screening as a family-level qualitative criterion.
"""
    (ROOT / "reports/pci_kinetics.md").write_text(text)


if __name__ == "__main__":
    main()
