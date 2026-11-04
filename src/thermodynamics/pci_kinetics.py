"""Phase 7: PCI (pressure-composition isotherm) curves and kinetics records.

PCI provenance: all 68 files in data/supporting/ were digitised from published figures (the
``Location`` field is "Figure N"). 14 were also shifted along the composition axis by the curator
to remove an irreversible part. They are processed literature curves, not raw measurements.

Plateau extraction (per curve)
* x = wt% / max wt% of that curve. The plateau window is 0.2 ≤ x ≤ 0.8. At least 4 points are required.
* Plateau pressure = exp(median ln P) in the window. Slope = d ln P / d x from a least-squares line.
* Van't Hoff fit, per material and mode, with ≥ 3 distinct temperatures:
  ln(P/atm) = ΔS/R − ΔH/(R T), giving positive desorption-convention magnitudes.
  For absorption the same algebra gives the absorption ΔH and ΔS.
* Multi-plateau materials: a mid-window "plateau" mixes two plateaus, so these are excluded from the fit.

Kinetics: the toolbox rate law (``KineticsModel.dwdt``) is
    dw/dt = Ca · exp(−Ea/RT) · f_p(P, Peq) · f_w(w, wmax).
Rate constants k(T) = Ca exp(−Ea/RT) are only comparable when f_p and f_w are the same. Here that is
f_p = ln(P/Peq) (dimensionless) and f_w = first order. For that group,
    w(t) = wmax [1 − exp(−k |ln(P/Peq)| t)],
so t90 = ln 10 / (k |ln(P/Peq)|). It is reported at P/Peq = 2 (absorption) or 1/2 (desorption), as a
model-based illustration under the source's fitting conditions, not a measured time.

Run:  .venv/bin/python -m src.thermodynamics.pci_kinetics
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..data.purdue_parser import read_pci_file
from .vant_hoff import P0_BAR, R

ROOT = Path(__file__).resolve().parents[2]
PCI_DIR = ROOT / "data/raw/purdue/MetalHydrideToolbox/data/supporting"
TABLES = ROOT / "results/tables"
PROC = ROOT / "data/processed"
WINDOW = (0.2, 0.8)
MIN_PTS = 4

REPRESENTATIVE_PCI = {
    "La[1]Ni[5]": "LaNi5 (AB5)",
    "Ti[1]Fe[0.8]Ni[0.15]V[0.05]": "TiFe0.8Ni0.15V0.05 (AB)",
    "Ti[0.95]Zr[0.05]Mn[1.55]V[0.45]Fe[0.09]": "Ti0.95Zr0.05Mn1.55V0.45Fe0.09 (AB2)",
    "Mg[1]Ni[0.02]": "MgNi0.02 (Mg)",
    "Na[1]Al[1]H[1]": "NaAlH4 + 4 mol% Ti (complex)",
}


PCI_POINTS_CSV = ROOT / "data/processed/pci_points.csv"
PCI_META_CSV = ROOT / "data/processed/pci_curves_meta.csv"


def load_all_pci() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Long table of every point, and a per-curve meta table.

    Reads the digitised toolbox files when the raw data are present (and saves a processed copy once);
    otherwise falls back to that processed copy, so a clone without data/raw still works.
    """
    files = sorted(PCI_DIR.glob("*_PCI.csv"))
    if not files:
        if PCI_POINTS_CSV.exists() and PCI_META_CSV.exists():
            return pd.read_csv(PCI_POINTS_CSV), pd.read_csv(PCI_META_CSV)
        raise FileNotFoundError(f"No PCI files in {PCI_DIR} and no processed copy; see data/raw/README.md")
    pts, meta = [], []
    for f in files:
        mid = f.name.replace("_PCI.csv", "")
        p = read_pci_file(f)
        for j, c in enumerate(p["curves"]):
            cid = f"{mid}|{c['mode']}|{c['T_K']:g}|{j}"
            unit_ok = "bar" in c["p_unit"].lower()
            meta.append({"material_id": mid, "curve_id": cid, "mode": c["mode"], "T_K": c["T_K"],
                         "n_points": len(c["P_bar"]), "x_unit": c["x_unit"].strip(),
                         "p_unit": c["p_unit"].strip(), "flag_pressure_unit_not_stated": not unit_ok,
                         "author": p["author"], "source": p["doi"], "figure": p["location"],
                         "curator_note": p["note"], "flag_shifted_by_curator": "shift" in p["note"].lower()})
            pts.append(pd.DataFrame({"material_id": mid, "curve_id": cid, "mode": c["mode"],
                                     "T_K": c["T_K"], "wt_pct": c["wt_pct"], "P_bar": c["P_bar"]}))
    pts, meta = pd.concat(pts, ignore_index=True), pd.DataFrame(meta)
    if not PCI_POINTS_CSV.exists():
        PCI_POINTS_CSV.parent.mkdir(parents=True, exist_ok=True)
        pts.to_csv(PCI_POINTS_CSV, index=False)
        meta.to_csv(PCI_META_CSV, index=False)
    return pts, meta


def plateau_of_curve(g: pd.DataFrame) -> dict:
    g = g[(g["P_bar"] > 0)].sort_values("wt_pct")
    wmax = g["wt_pct"].max()
    x = g["wt_pct"] / wmax
    win = g[(x >= WINDOW[0]) & (x <= WINDOW[1])]
    out = {"wt_max_curve": wmax, "n_window": len(win)}
    if len(win) < MIN_PTS:
        return {**out, "P_plateau_bar": np.nan, "slope_dlnP_dx": np.nan}
    lnp = np.log(win["P_bar"].to_numpy())
    xs = (win["wt_pct"] / wmax).to_numpy()
    slope = np.polyfit(xs, lnp, 1)[0]
    return {**out, "P_plateau_bar": float(np.exp(np.median(lnp))), "slope_dlnP_dx": float(slope)}


def vant_hoff_fit(T, P_bar) -> dict:
    y = np.log(np.asarray(P_bar) / P0_BAR)
    x = 1.0 / np.asarray(T)
    b, a = np.polyfit(x, y, 1)
    yhat = a + b * x
    ss_res = float(np.sum((y - yhat) ** 2)); ss_tot = float(np.sum((y - y.mean()) ** 2))
    return {"dH_fit_kJmol": -b * R / 1000, "dS_fit_JmolK": a * R,
            "R2_fit": 1 - ss_res / ss_tot if ss_tot > 0 else np.nan, "n_T": len(T),
            "T_range_K": f"{min(T):g}-{max(T):g}"}


def analyse_pci():
    pts, meta = load_all_pci()
    plat = pts.groupby("curve_id").apply(lambda g: pd.Series(plateau_of_curve(g)), include_groups=False).reset_index()
    curves = meta.merge(plat, on="curve_id")
    p = pd.read_csv(PROC / "purdue_cleaned.csv").set_index("purdue_id")
    curves["family"] = curves["material_id"].map(p["family"])
    curves["n_plateaus_mh"] = curves["material_id"].map(p["n_plateaus"])
    curves.to_csv(TABLES / "pci_curve_plateaus.csv", index=False)

    fits = []
    for (mid, mode), g in curves.dropna(subset=["P_plateau_bar"]).groupby(["material_id", "mode"]):
        g = g.groupby("T_K", as_index=False)["P_plateau_bar"].apply(lambda s: np.exp(np.log(s).mean()))
        if g["T_K"].nunique() < 3:
            continue
        r = p.loc[mid]
        multi = bool(r["flag_multi_plateau"])
        f = vant_hoff_fit(g["T_K"], g["P_plateau_bar"])
        ref_dH = r["dH_kJmol"] if mode == "des" else r["abs_dH_kJmol"]
        ref_dS = r["dS_JmolK"] if mode == "des" else r["abs_dS_JmolK"]
        fits.append({"material_id": mid, "family": r["family"], "mode": mode, **f,
                     "dH_mh_kJmol": ref_dH, "dS_mh_JmolK": ref_dS,
                     "mh_thermo_from_isotherms": bool(r["flag_des_thermo_from_isotherm_fit"]) if mode == "des" else np.nan,
                     "multi_plateau_excluded": multi})
    fits = pd.DataFrame(fits)
    fits["d_dH"] = fits["dH_fit_kJmol"] - fits["dH_mh_kJmol"]
    fits["d_dS"] = fits["dS_fit_JmolK"] - fits["dS_mh_JmolK"]
    fits.to_csv(TABLES / "pci_vant_hoff_fits.csv", index=False)

    # Hysteresis from curves at the same temperature
    c = curves.dropna(subset=["P_plateau_bar"])
    hy = (c.pivot_table(index=["material_id", "T_K"], columns="mode", values="P_plateau_bar", aggfunc="median")
          .dropna().reset_index())
    hy["ln_Pa_Pd_pci"] = np.log(hy["abs"] / hy["des"])
    hy["family"] = hy["material_id"].map(p["family"])
    hy.to_csv(TABLES / "pci_hysteresis.csv", index=False)
    return pts, curves, fits, hy


# --------------------------------------------------------------------------
def analyse_kinetics() -> pd.DataFrame:
    raw = pd.read_csv(ROOT / "data/interim/purdue_extracted.csv")
    rows = []
    for _, r in raw.iterrows():
        for mode, pre in (("abs", "kin_abs"), ("des", "kin_des")):
            if r[f"{pre}_n_entries"] == 0 or pd.isna(r.get(f"{pre}_Ea")):
                continue
            pf, wf = str(r[f"{pre}_pFcn"]).strip(), str(r[f"{pre}_wFcn"]).strip()
            comparable = pf.lower() == "log" and wf.lower() == "1st order"
            Ca, Ea = float(r[f"{pre}_Ca"]), float(r[f"{pre}_Ea"])
            note = str(r[f"{pre}_comments"]) if pd.notna(r[f"{pre}_comments"]) else ""
            row = {"material_id": r["material_id"], "family": r["type"], "mode": mode, "Ca_per_s": Ca,
                   "Ea_kJmol": Ea / 1000, "pFcn": pf, "wFcn": wf, "model_form_comparable": comparable,
                   "source_note": note,
                   "flag_data_assumed": "assumed" in note.lower(),
                   "flag_conflicting_source": "conflict" in note.lower()}
            for Tc in (25, 80):
                k = Ca * np.exp(-Ea / (R * (Tc + 273.15)))
                row[f"k_per_s_{Tc}C"] = k if comparable else np.nan
                row[f"t90_s_{Tc}C"] = np.log(10) / (k * np.log(2)) if comparable else np.nan
            rows.append(row)
    k = pd.DataFrame(rows)
    k.to_csv(TABLES / "kinetics_purdue.csv", index=False)
    return k


def main():
    pd.set_option("display.width", 220)
    pts, curves, fits, hy = analyse_pci()
    k = analyse_kinetics()
    print("curves:", len(curves), "with plateau:", curves["P_plateau_bar"].notna().sum(),
          "unit-not-stated:", curves["flag_pressure_unit_not_stated"].sum())
    print(fits.round(2).to_string(index=False))
    print("hysteresis pairs:", len(hy), hy["ln_Pa_Pd_pci"].describe().round(2).to_dict())
    print(k.groupby(["mode", "model_form_comparable"]).size())
    print(k[k.model_form_comparable].groupby(["family", "mode"])["Ea_kJmol"].describe()[["count", "min", "50%", "max"]].round(1))


if __name__ == "__main__":
    main()
