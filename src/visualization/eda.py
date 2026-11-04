"""Phase 3: exploratory figures.

The two datasets are always drawn as separate series (never pooled), except in
panels explicitly labelled "union", which use the rule-based composition-level
ΔH table from Phase 2.

Run:  .venv/bin/python -m src.visualization.eda
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from .style import (DATASET_COLORS, FAMILY_ORDER, ROOT, apply_style, family_color,
                    save)

PROC = ROOT / "data/processed"
TABLES = ROOT / "results/tables"
R = 8.314
S_H2 = 130.68  # standard molar entropy of H2 gas, J/(mol K) (NIST-JANAF)

REPRESENTATIVE = [  # (purdue_id, label)
    ("La[1]Ni[5]", "LaNi$_5$ (AB$_5$)"),
    ("Ti[1]Fe[1]", "TiFe (AB)"),
    ("Ti[1.01]Cr[1.06]Mn[1]", "TiCrMn (AB$_2$)"),
    ("V[0.855]Cr[0.145]", "V$_{0.855}$Cr$_{0.145}$ (SS)"),
    ("Na[1]Al[1]H[1]", "NaAlH$_4$, Na$_3$AlH$_6$→NaH plateau (complex)"),
    ("Mg[2]Ni[1]", "Mg$_2$Ni (Mg)"),
    ("Mg[1]", "MgH$_2$ (Mg)"),
]


def load():
    p = pd.read_csv(PROC / "purdue_cleaned.csv")
    h = pd.read_csv(PROC / "hydpark_cleaned.csv")
    u = pd.read_csv(PROC / "dH_union_by_composition.csv")
    h["family"] = h["family"].fillna("(missing)")
    u["family"] = u["family"].fillna("(missing)")
    return p, h, u


def ordered(families) -> list[str]:
    fams = list(dict.fromkeys(families))
    return [f for f in FAMILY_ORDER if f in fams] + [f for f in fams if f not in FAMILY_ORDER]


# --------------------------------------------------------------------------
def fig01_class_distribution(p, h):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=False)
    for ax, (name, df, col) in zip(axes, [("Purdue Metal Hydride Toolbox", p, "family"),
                                          ("ML-HydPARK v0.0.5", h, "class_raw")]):
        counts = df[col].fillna("(missing)").value_counts()
        if col == "class_raw":
            order = ["AB2(C14)", "AB2(C15)", "AB2", "AB5", "SS", "MIC", "AB", "Mg", "A2B", "(missing)"]
            counts = counts.reindex([o for o in order if o in counts.index])
            colors = [family_color("AB2" if c.startswith("AB2") else c) for c in counts.index]
        else:
            counts = counts.reindex(ordered(counts.index))
            colors = [family_color(c) for c in counts.index]
        bars = ax.bar(counts.index, counts.values, color=colors, edgecolor="white")
        ax.bar_label(bars, fontsize=9, padding=2)
        ax.set_title(f"{name} (n = {len(df)})")
        ax.set_xlabel("Material class")
        ax.set_ylabel("Number of records")
        ax.tick_params(axis="x", rotation=40)
        ax.set_ylim(0, counts.max() * 1.15)
    fig.suptitle("Fig. 1  Distribution of metal hydride classes", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig01_class_distribution")


def _hist_pair(ax, p_vals, h_vals, bins, xlabel):
    ax.hist(p_vals, bins=bins, histtype="stepfilled", alpha=0.45, color=DATASET_COLORS["Purdue"],
            label=f"Purdue (n = {p_vals.notna().sum()})")
    ax.hist(h_vals, bins=bins, histtype="step", lw=1.8, color=DATASET_COLORS["HydPARK"],
            label=f"HydPARK (n = {h_vals.notna().sum()})")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of records")
    ax.legend()


def fig02_dH_distribution(p, h, u):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    single = p[~p["flag_multi_plateau"]]
    _hist_pair(axes[0], single["dH_kJmol"], h["dH_kJmol"], np.arange(0, 225, 5),
               "Desorption enthalpy ΔH (kJ mol$^{-1}$ H$_2$)")
    axes[0].set_title("All records")
    clip = u[u["dH_kJmol"] <= 90]
    fams = [f for f in ["AB5", "AB2", "AB", "SS", "Mg"] if f in set(u["family"])]
    data = [clip.loc[clip["family"] == f, "dH_kJmol"] for f in fams]
    bp = axes[1].boxplot(data, tick_labels=fams, patch_artist=True, widths=0.6,
                         medianprops={"color": "black"})
    for patch, f in zip(bp["boxes"], fams):
        patch.set_facecolor(family_color(f)); patch.set_alpha(0.6)
    for i, f in enumerate(fams, 1):
        axes[1].text(i, -4, f"n={len(u[u['family'] == f])}", ha="center", fontsize=8.5)
    axes[1].set_ylim(-8, 95)
    axes[1].set_title("By family (composition-level union, ΔH ≤ 90)")
    axes[1].set_xlabel("Material family")
    axes[1].set_ylabel("ΔH (kJ mol$^{-1}$ H$_2$)")
    fig.suptitle("Fig. 2  Enthalpy of hydride decomposition", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig02_dH_distribution")


def fig03_dS_distribution(p, h):
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    single = p[~p["flag_multi_plateau"]]
    bins = np.arange(-10, 270, 5)
    hb = h.copy()
    derived = hb["flag_dS_derived_from_TP"]
    ax.hist([hb.loc[~derived, "dS_JmolK"], hb.loc[derived, "dS_JmolK"]], bins=bins,
            histtype="barstacked", color=[DATASET_COLORS["HydPARK"], "#F5CBA7"], alpha=0.8,
            label=[f"HydPARK, reported (n = {(~derived).sum()})",
                   f"HydPARK, back-calculated from one (T, P) (n = {derived.sum()})"])
    ax.hist(single["dS_JmolK"], bins=bins, histtype="step", lw=2.2, zorder=5,
            color=DATASET_COLORS["Purdue"], label=f"Purdue (n = {len(single)})")
    ax.axvspan(70, 170, color="grey", alpha=0.08, label="Typical-value window used for flags (70–170)")
    ax.axvline(S_H2, color="k", ls="--", lw=1)
    ax.text(S_H2 + 3, ax.get_ylim()[1] * 0.55, "S°(H$_2$ gas)\n= 130.7", fontsize=9)
    ax.set_xlabel("Desorption entropy ΔS (J mol$^{-1}$ H$_2$ K$^{-1}$)")
    ax.set_ylabel("Number of records")
    ax.set_title("Fig. 3  Entropy of hydride decomposition")
    ax.legend(loc="upper right", fontsize=8.5)
    fig.tight_layout()
    return save(fig, "fig03_dS_distribution")


def fig04_capacity_distribution(p, h):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    bins = np.arange(0, 8.0, 0.2)
    ax = axes[0]
    stated = p[p["capacity_basis"] == "stated_wt_pct"]["wt_pct"]
    from_hm = p[p["capacity_basis"] != "stated_wt_pct"]["wt_pct"]
    ax.hist([stated, from_hm], bins=bins, histtype="barstacked",
            color=[DATASET_COLORS["Purdue"], "#9ECAE1"],
            label=[f"stated wt% (n = {len(stated)})", f"converted from H/M (n = {len(from_hm)})"])
    ax.set_title("Purdue: reported capacity")
    ax.set_xlabel("Hydrogen capacity (wt% H, hydride basis)")
    ax.set_ylabel("Number of records")
    ax.legend()
    ax = axes[1]
    ax.hist(h["wt_pct"].dropna(), bins=bins, color=DATASET_COLORS["HydPARK"], alpha=0.75,
            label=f"HydPARK (n = {h['wt_pct'].notna().sum()})")
    ax.axvline(5.5, color="k", ls=":", lw=1)
    ax.text(5.6, ax.get_ylim()[1] * 0.55, "DOE 2025 onboard\nsystem target\n5.5 wt%", fontsize=8.5)
    ax.set_title("HydPARK: reported capacity")
    ax.set_xlabel("Hydrogen capacity (wt% H)")
    ax.set_ylabel("Number of records")
    ax.legend(loc="upper left", bbox_to_anchor=(0.42, 1.0))
    fig.suptitle("Fig. 4  Gravimetric hydrogen capacity (material level; definitions not uniform)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig04_capacity_distribution")


def fig05_dH_vs_dS(p, h):
    fig, ax = plt.subplots(figsize=(8, 6))
    single = p[~p["flag_multi_plateau"]]
    for f in ordered(single["family"]):
        s = single[single["family"] == f]
        ax.scatter(s["dH_kJmol"], s["dS_JmolK"], s=26, color=family_color(f), alpha=0.85,
                   edgecolor="white", lw=0.4, label=f"{f} (Purdue, n={len(s)})")
    hh = h[~h["flag_suspected_entry_error"]]
    ax.scatter(hh["dH_kJmol"], hh["dS_JmolK"], s=12, marker="x", color="grey", alpha=0.45,
               lw=0.8, label=f"HydPARK, all classes (n={len(hh)})")
    # Lines where Peq = 1 atm is reached at temperature T:  dS = dH / T
    x = np.linspace(0, 100, 50)
    for Tc, y_lab in ((0, 232), (25, 214), (100, 196), (300, 160)):
        T = Tc + 273.15
        ax.plot(x, x * 1000 / T, color="k", lw=0.8, ls="--", alpha=0.6)
        x_lab = min(y_lab * T / 1000, 99)
        ax.text(x_lab + 1, x_lab * 1000 / T, f"{Tc} °C", fontsize=8.5, ha="left", va="center",
                bbox={"fc": "white", "ec": "none", "pad": 0.5})
    ax.set_xlim(0, 100); ax.set_ylim(20, 250)
    ax.set_xlabel("ΔH (kJ mol$^{-1}$ H$_2$)")
    ax.set_ylabel("ΔS (J mol$^{-1}$ H$_2$ K$^{-1}$)")
    ax.set_title("Fig. 5  Enthalpy–entropy relation\n(dashed: ΔS = ΔH/T, i.e. P$_{eq}$ = 1 atm at the labelled temperature)")
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    fig.tight_layout()
    return save(fig, "fig05_dH_vs_dS")


def fig06_dH_vs_capacity(p, h):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, (name, df) in zip(axes, [("Purdue", p[~p["flag_multi_plateau"]]),
                                     ("HydPARK", h[~h["flag_suspected_entry_error"]])]):
        # band: T(1 atm) between 0 and 100 C for a typical dS of 110 J/(mol K)
        ax.axvspan(0.110 * 273.15, 0.110 * 373.15, color="green", alpha=0.08)
        for f in ordered(df["family"]):
            s = df[df["family"] == f]
            ax.scatter(s["dH_kJmol"], s["wt_pct"], s=18, color=family_color(f), alpha=0.75,
                       edgecolor="white", lw=0.3, label=f)
        ax.set_xlim(0, 100)
        ax.set_xlabel("ΔH (kJ mol$^{-1}$ H$_2$)")
        ax.set_title(f"{name} (n = {df['wt_pct'].notna().sum()})")
        ax.text(0.110 * 323, 7.6, "1 atm at 0–100 °C\n(ΔS = 110)", ha="center", fontsize=8.5, color="darkgreen")
    axes[0].set_ylabel("Hydrogen capacity (wt% H)")
    axes[0].set_ylim(0, 8.2)
    axes[1].legend(fontsize=8, ncol=2, loc="upper right")
    fig.suptitle("Fig. 6  Capacity vs stability trade-off: high-wt% hydrides are too stable for ambient use",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig06_dH_vs_capacity")


def fig07_ab5_vs_ab2(p, h, u):
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2))
    fams = ["AB5", "AB2"]
    panels = [
        ("ΔH (kJ mol$^{-1}$ H$_2$)", lambda f: u.loc[u["family"] == f, "dH_kJmol"], "ΔH, union"),
        ("ΔS (J mol$^{-1}$ K$^{-1}$)", lambda f: p.loc[(p["family"] == f) & ~p["flag_multi_plateau"], "dS_JmolK"], "ΔS, Purdue"),
        ("Capacity (wt% H)", lambda f: p.loc[(p["family"] == f) & (p["capacity_basis"] == "stated_wt_pct"), "wt_pct"], "Capacity, Purdue stated wt%"),
    ]
    rows = []
    for ax, (ylabel, getter, title) in zip(axes, panels):
        data = [getter(f).dropna() for f in fams]
        vp = ax.violinplot(data, showmedians=True, showextrema=False, widths=0.75)
        vp["cmedians"].set_color("black")
        for body, f in zip(vp["bodies"], fams):
            body.set_facecolor(family_color(f)); body.set_alpha(0.55)
        for i, d in enumerate(data, 1):
            ax.scatter(np.random.default_rng(0).normal(i, 0.05, len(d)), d, s=5, color="k", alpha=0.35)
            rows.append({"quantity": title, "family": fams[i - 1], "n": len(d),
                         "median": d.median(), "q25": d.quantile(0.25), "q75": d.quantile(0.75)})
        ax.set_xticks([1, 2], [f"{f}\n(n={len(d)})" for f, d in zip(fams, data)])
        ax.set_ylabel(ylabel); ax.set_title(title)
    axes[0].set_ylim(0, 70)
    axes[1].set_ylim(55, 175)
    hidden = p[(p["family"].isin(fams)) & ~p["flag_multi_plateau"] & (p["dS_JmolK"] > 175)]
    if len(hidden):
        axes[1].text(0.02, 0.97, "not shown: " + ", ".join(
            f"{r.reduced_formula} ({r.dS_JmolK:.0f})" for r in hidden.itertuples()),
            transform=axes[1].transAxes, fontsize=8, va="top")
    fig.suptitle("Fig. 7  AB$_5$ vs AB$_2$ intermetallic hydrides", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    pd.DataFrame(rows).to_csv(TABLES / "eda_ab5_vs_ab2.csv", index=False)
    return save(fig, "fig07_ab5_vs_ab2")


def fig08_temperature_pressure(p, h):
    pi = p.set_index("purdue_id")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    T = np.linspace(230, 700, 400)
    for (pid, label), c in zip(REPRESENTATIVE, plt.cm.tab10.colors):
        dH, dS = pi.loc[pid, "dH_kJmol"] * 1000, pi.loc[pid, "dS_JmolK"]
        lnP = -dH / (R * T) + dS / R
        P_bar = np.exp(lnP) * 1.01325
        mask = (P_bar > 1e-4) & (P_bar < 1e4)
        axes[0].plot(1000 / T[mask], P_bar[mask], color=c, lw=1.8, label=label)
        axes[1].plot(T[mask] - 273.15, P_bar[mask], color=c, lw=1.8, label=label)
    for ax in axes:
        ax.set_yscale("log")
        ax.axhspan(1, 10, color="green", alpha=0.08)
        ax.set_ylabel("Equilibrium pressure P$_{eq}$ (bar)")
        ax.set_ylim(1e-3, 1e3)
    axes[0].set_xlabel("1000 / T (K$^{-1}$)")
    axes[0].set_title("Van't Hoff plot (plateau midpoint, desorption)")
    axes[1].set_xlabel("Temperature (°C)")
    axes[1].set_title("P$_{eq}$ vs T; shaded: 1–10 bar")
    axes[1].legend(fontsize=8.5, loc="lower right")
    # HydPARK single (T, P) measurement points as a cross-check of the trend
    hp = h[h["T_point_C"].notna() & h["P_point_atm"].notna() & ~h["flag_suspected_entry_error"]
           & h["family"].isin(["AB5", "AB", "AB2", "Mg"])]
    axes[1].scatter(hp["T_point_C"], hp["P_point_atm"] * 1.01325, s=7, color="grey", alpha=0.35,
                    label="HydPARK (T, P) points")
    axes[1].set_xlim(-40, 420)
    axes[1].legend(fontsize=8.5, loc="lower right")
    fig.suptitle("Fig. 8  Operating temperature and equilibrium pressure (ln P = −ΔH/RT + ΔS/R; Purdue ΔH, ΔS)",
                 x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    return save(fig, "fig08_temperature_pressure")


def fig09_property_availability(p):
    props = {
        "Desorption ΔH, ΔS": p["dH_kJmol"].notna(),
        "Capacity (any basis)": p["wt_pct"].notna(),
        "Capacity, stated wt%": p["capacity_basis"] == "stated_wt_pct",
        "Capacity, 'reversible' stated": p["capacity_definition"] == "reversible_stated",
        "Absorption ΔH, ΔS": p["abs_dH_kJmol"].notna(),
        "Hysteresis ln(Pa/Pd)": p["hysteresis_ln_Pa_Pd"].notna(),
        "PCI isotherms (digitised)": p["pci_file"].fillna("") != "",
        "Density ρ": p["rho_kg_m3"].notna(),
        "Absorption kinetics (Ea)": p["kin_abs_Ea_Jmol"].notna(),
        "Heat capacity Cp": p["cp_J_kgK"].notna(),
        "Desorption kinetics (Ea)": p["kin_des_Ea_Jmol"].notna(),
        "Thermal conductivity k": p["keff_W_mK"].notna(),
    }
    fams = ["AB5", "AB2", "AB", "SS", "other"]
    fam = p["family"].where(p["family"].isin(fams[:-1]), "other")
    fig, ax = plt.subplots(figsize=(9, 5.2))
    names = list(props)[::-1]
    left = np.zeros(len(names))
    for f in fams:
        vals = np.array([(props[n] & (fam == f)).sum() for n in names])
        ax.barh(names, vals, left=left, color=family_color(f) if f != "other" else "#999999",
                label=f, edgecolor="white", lw=0.5)
        left += vals
    for i, n in enumerate(names):
        ax.text(left[i] + 3, i, f"{int(left[i])} ({100 * left[i] / len(p):.0f}%)", va="center", fontsize=9)
    ax.set_xlim(0, len(p) * 1.18)
    ax.set_xlabel(f"Number of Purdue materials with a value written in the .mh file (of {len(p)})")
    ax.set_title("Fig. 9  Availability of thermodynamic, kinetic and thermal properties (Purdue)")
    ax.legend(title="Family", loc="lower right")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return save(fig, "fig09_property_availability")


def fig10_missing_data(p, h):
    pcols = {"ΔH,ΔS": p["dH_kJmol"], "wt% stated": p["wt_pct_stated"],
             "H/M stated": p["h_per_formula_unit_stated"], "abs ΔH": p["abs_dH_kJmol"],
             "hysteresis": p["hysteresis_ln_Pa_Pd"], "ρ": p["rho_kg_m3"], "Cp": p["cp_J_kgK"],
             "k": p["keff_W_mK"], "kin abs": p["kin_abs_Ea_Jmol"], "kin des": p["kin_des_Ea_Jmol"],
             "PCI": p["pci_file"].replace("", np.nan), "real formula": p["comp_key"]}
    order_p = p.assign(_o=p["family"].map({f: i for i, f in enumerate(FAMILY_ORDER)})).sort_values(["_o", "purdue_id"]).index
    Mp = pd.DataFrame({k: v.notna() for k, v in pcols.items()}).loc[order_p]
    hcols = {"class": h["class_raw"], "ΔH": h["dH_kJmol"], "ΔS": h["dS_JmolK"],
             "wt%": h["wt_pct"], "H/M": h["h_per_metal_atom"], "T point": h["T_point_C"],
             "P point": h["P_point_atm"], "Peq 25°C": h["Peq25_atm_raw"], "reference": h["reference"]}
    Mh = pd.DataFrame({k: v.notna() for k, v in hcols.items()})
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5), gridspec_kw={"width_ratios": [12, 9]})
    for ax, M, title in [(axes[0], Mp, f"Purdue (rows sorted by family, n = {len(p)})"),
                         (axes[1], Mh, f"HydPARK (rows in file order, n = {len(h)})")]:
        ax.imshow(M.to_numpy(), aspect="auto", cmap=plt.matplotlib.colors.ListedColormap(["#F2F2F2", "#2C7FB8"]),
                  interpolation="nearest")
        ax.set_xticks(range(M.shape[1]), [f"{c} ({100 * M[c].mean():.0f}%)" for c in M.columns],
                      rotation=55, ha="right")
        ax.set_ylabel("Record")
        ax.set_title(title)
        ax.grid(False)
    # block boundaries for HydPARK
    for b in sorted(h["source_block"].unique())[1:]:
        y = h.index[h["source_block"] == b][0]
        axes[1].axhline(y - 0.5, color="red", lw=0.8)
        axes[1].text(Mh.shape[1] - 0.4, y + 8, f"block {b}", color="red", fontsize=8, ha="right")
    # family boundaries for Purdue
    fam_sorted = p.loc[order_p, "family"].to_numpy()
    starts = [0] + [i for i in range(1, len(fam_sorted)) if fam_sorted[i] != fam_sorted[i - 1]]
    ends = starts[1:] + [len(fam_sorted)]
    for s, e in zip(starts, ends):
        if s:
            axes[0].axhline(s - 0.5, color="red", lw=0.6)
        if e - s >= 10:  # label only groups tall enough to read
            axes[0].text(Mp.shape[1] - 0.45, (s + e) / 2, fam_sorted[s], color="red", fontsize=8,
                         ha="right", va="center", bbox={"fc": "white", "ec": "none", "pad": 0.5})
    axes[0].text(Mp.shape[1] - 0.45, len(fam_sorted) - 1, "Mg/Complex/Misc", color="red",
                 fontsize=7, ha="right", va="bottom")
    fig.legend(handles=[Line2D([], [], marker="s", ls="", color="#2C7FB8", ms=9, label="value present"),
                        Line2D([], [], marker="s", ls="", color="#F2F2F2", mec="#CCCCCC", ms=9, label="missing (NaN, not zero)")],
               loc="lower center", ncol=2)
    fig.suptitle("Fig. 10  Missing-data map (percent present in brackets)", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return save(fig, "fig10_missing_data")


def summary_stats(p, h, u) -> pd.DataFrame:
    rows = []
    def add(dataset, fam, s, qty):
        s = s.dropna()
        if len(s):
            rows.append({"dataset": dataset, "family": fam, "quantity": qty, "n": len(s),
                         "mean": s.mean(), "std": s.std(), "min": s.min(), "q25": s.quantile(.25),
                         "median": s.median(), "q75": s.quantile(.75), "max": s.max()})
    ps = p[~p["flag_multi_plateau"]]
    for fam in ["ALL"] + ordered(ps["family"]):
        sub = ps if fam == "ALL" else ps[ps["family"] == fam]
        add("Purdue", fam, sub["dH_kJmol"], "dH_kJmol")
        add("Purdue", fam, sub["dS_JmolK"], "dS_JmolK")
        add("Purdue", fam, sub["wt_pct"], "wt_pct")
    for fam in ["ALL"] + ordered(h["family"]):
        sub = h if fam == "ALL" else h[h["family"] == fam]
        add("HydPARK", fam, sub["dH_kJmol"], "dH_kJmol")
        add("HydPARK", fam, sub["dS_JmolK"], "dS_JmolK")
        add("HydPARK", fam, sub["wt_pct"], "wt_pct")
    for fam in ["ALL"] + ordered(u["family"]):
        sub = u if fam == "ALL" else u[u["family"] == fam]
        add("Union", fam, sub["dH_kJmol"], "dH_kJmol")
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "eda_summary_stats.csv", index=False)
    return out


def correlations(p, h, u) -> pd.DataFrame:
    ps = p[~p["flag_multi_plateau"]]
    rows = []
    for name, df in [("Purdue", ps), ("HydPARK", h[~h["flag_suspected_entry_error"]])]:
        for a, b in [("dH_kJmol", "dS_JmolK"), ("dH_kJmol", "wt_pct")]:
            s = df[[a, b]].dropna()
            rows.append({"dataset": name, "x": a, "y": b, "n": len(s),
                         "pearson_r": s.corr().iloc[0, 1],
                         "spearman_rho": s.corr(method="spearman").iloc[0, 1]})
    out = pd.DataFrame(rows)
    out.to_csv(TABLES / "eda_correlations.csv", index=False)
    return out


def write_report(p, h, u, corr: pd.DataFrame) -> None:
    from scipy.stats import mannwhitneyu
    from ..data.run_audit import md_table

    ps = p[~p["flag_multi_plateau"]]
    ab = pd.read_csv(TABLES / "eda_ab5_vs_ab2.csv")
    ab5, ab2 = u[u["family"] == "AB5"]["dH_kJmol"], u[u["family"] == "AB2"]["dH_kJmol"]
    w5 = p[(p["family"] == "AB5") & (p["capacity_basis"] == "stated_wt_pct")]["wt_pct"]
    w2 = p[(p["family"] == "AB2") & (p["capacity_basis"] == "stated_wt_pct")]["wt_pct"]
    s5 = ps[ps["family"] == "AB5"]["dS_JmolK"]; s2 = ps[ps["family"] == "AB2"]["dS_JmolK"]
    pv = {k: mannwhitneyu(a, b).pvalue for k, (a, b) in
          {"dH": (ab5, ab2), "wt": (w5, w2), "dS": (s5, s2)}.items()}
    T1 = ps["dH_kJmol"] * 1000 / ps["dS_JmolK"] - 273.15
    amb = ((T1 >= 0) & (T1 <= 100)).mean()
    hi = p[p["wt_pct"] > 3][["purdue_id", "family", "wt_pct", "dH_kJmol", "dS_JmolK", "capacity_definition"]].copy()
    hi["T_at_1bar_C"] = (hi["dH_kJmol"] * 1000 / (hi["dS_JmolK"] - R * np.log(1 / 1.01325)) - 273.15).round(0)
    c = corr.set_index(["dataset", "y"])
    uf = u.groupby("family").size()
    low = h["dS_JmolK"] < 80
    n_low_der = int((low & h["flag_dS_derived_from_TP"]).sum())
    # Highest capacity inside the ambient ΔH window (30-41 kJ/mol, dS = 110 -> 1 atm at 0-100 C)
    win = []
    for name, df, fcol in [("Purdue", ps, "purdue_id"),
                           ("HydPARK", h[~h["flag_suspected_entry_error"]], "formula_raw")]:
        w = df[(df["dH_kJmol"] >= 30.0) & (df["dH_kJmol"] <= 41.0)].nlargest(3, "wt_pct")
        win += [{"dataset": name, "material": r[fcol], "family": r["family"],
                 "wt_pct": round(r["wt_pct"], 2), "dH_kJmol": r["dH_kJmol"]} for _, r in w.iterrows()]
    win = pd.DataFrame(win)
    pi = p.set_index("purdue_id")
    vh = []
    for pid, label in REPRESENTATIVE:
        dH, dS = pi.loc[pid, "dH_kJmol"] * 1000, pi.loc[pid, "dS_JmolK"]
        vh.append({"material": pid, "dH_kJmol": dH / 1000, "dS_JmolK": dS,
                   "Peq_25C_bar": float(f"{np.exp(-dH / (R * 298.15) + dS / R) * 1.01325:.3g}"),
                   "T_at_1bar_C": round(dH / (dS - R * np.log(1 / 1.01325)) - 273.15, 0)})
    vh = pd.DataFrame(vh)
    vh.to_csv(TABLES / "eda_representative_vant_hoff.csv", index=False)
    text = f"""# Phase 3: exploratory data analysis

Generated by `src/visualization/eda.py`. Figures are in `results/figures/`, saved as PNG at 300 dpi and as PDF.
The two datasets are drawn as separate series. "Union" means the rule-based
composition-level ΔH table from Phase 2. All ΔH/ΔS values are positive desorption magnitudes.

| Figure | Content |
|---|---|
| fig01_class_distribution | class counts per dataset |
| fig02_dH_distribution | ΔH histogram per dataset; ΔH by family (union) |
| fig03_dS_distribution | ΔS histogram; HydPARK split into reported vs back-calculated |
| fig04_capacity_distribution | wt% per dataset; Purdue split by stated vs converted-from-H/M |
| fig05_dH_vs_dS | ΔH–ΔS scatter with 1 atm Van't Hoff isotherms |
| fig06_dH_vs_capacity | capacity vs ΔH (stability trade-off) |
| fig07_ab5_vs_ab2 | AB5 vs AB2: ΔH, ΔS, capacity |
| fig08_temperature_pressure | Van't Hoff curves for 7 representative hydrides + HydPARK (T, P) points |
| fig09_property_availability | which properties exist in the Purdue files |
| fig10_missing_data | missing-value maps for both datasets |

## Observations (numbers from `results/tables/eda_*.csv`)

1. **Class imbalance.** Two intermetallic families dominate. AB5 + AB2 make up
   {100*(p['family'].isin(['AB5','AB2'])).mean():.0f}% of Purdue and {100*(h['family'].isin(['AB5','AB2'])).mean():.0f}% of HydPARK (Fig. 1). The union has {uf.get('Mg',0)} Mg-based
   compositions and Purdue has {int((p['family']=='Complex').sum())} complex hydride. Family-specific ML is therefore
   only possible for AB5 ({uf.get('AB5',0)}) and AB2 ({uf.get('AB2',0)}).
2. **ΔH distribution.** Purdue's median is {ps['dH_kJmol'].median():.1f} kJ/mol H2 (IQR {ps['dH_kJmol'].quantile(.25):.1f}–{ps['dH_kJmol'].quantile(.75):.1f}).
   HydPARK has a long tail up to {h['dH_kJmol'].max():.0f} kJ/mol, from stable Zr/Th/Ti hydrides that need several
   hundred °C to desorb (Fig. 2). By family, Mg-based hydrides sit far above the rest
   (union median {u[u['family']=='Mg']['dH_kJmol'].median():.1f} kJ/mol).
3. **ΔS is close to the H2 gas entropy.** Purdue's median ΔS is {ps['dS_JmolK'].median():.1f} J/(mol K). It is lower than
   S°(H2) = 130.7 because H in the lattice keeps some entropy. HydPARK's distribution is wider.
   Of its {int(low.sum())} values below 80 J/(mol K), {n_low_der} are back-calculated from a single (T, P) point (Fig. 3, light).
4. **Enthalpy–entropy correlation.** Pearson r(ΔH, ΔS) = {c.loc[('Purdue','dS_JmolK'),'pearson_r']:.2f} for Purdue (n = {int(c.loc[('Purdue','dS_JmolK'),'n'])})
   and {c.loc[('HydPARK','dS_JmolK'),'pearson_r']:.2f} for HydPARK (Fig. 5). Part of this is the well-known compensation effect,
   and part comes from the derivation itself: for back-calculated rows ΔS = R ln P + ΔH/T, which
   correlates with ΔH by construction. This is the reason ΔS must not be an input when predicting ΔH.
5. **Ambient operation.** {100*amb:.0f}% of single-plateau Purdue materials reach 1 atm between 0 and 100 °C
   (T(1 atm) = ΔH/ΔS; median {T1.median():.0f} °C). Most of the Purdue database is designed for near-ambient use.
6. **Capacity–stability trade-off (Fig. 6).** Spearman ρ(ΔH, wt%) is only
   {c.loc[('Purdue','wt_pct'),'spearman_rho']:.2f} (Purdue) and {c.loc[('HydPARK','wt_pct'),'spearman_rho']:.2f} (HydPARK). Within the intermetallics, capacity barely depends on ΔH. The only materials
   above 3 wt% are Mg-based, complex, or V-based solid solutions, and they sit at higher ΔH or need heat:

{md_table(hi)}

   Highest capacities inside the ambient ΔH window (30–41 kJ/mol, i.e. 1 atm at 0–100 °C for ΔS = 110):

{md_table(win)}

   Inside this ΔH window the maximum reported capacity is {win['wt_pct'].max():.1f} wt%. That is a material-level number,
   below the 5.5 wt% DOE *system* target. Of the materials above 3 wt% (first table), only the
   V-based solid solutions reach 1 bar near ambient (T(1 bar) {hi.loc[hi['family']=='SS','T_at_1bar_C'].min():.0f}–{hi.loc[hi['family']=='SS','T_at_1bar_C'].max():.0f} °C), and only because
   their ΔS is high ({hi.loc[hi['family']=='SS','dS_JmolK'].min():.0f}–{hi.loc[hi['family']=='SS','dS_JmolK'].max():.0f}). Their reported capacity has no stated definition in the
   source files. The rest need heat: NaAlH4 (its more stable Na3AlH6 → NaH plateau, which is the value stored
   in the scalar column) {hi.loc[hi['family']=='Complex','T_at_1bar_C'].iloc[0]:.0f} °C, Mg-based
   {hi.loc[hi['family']=='Mg','T_at_1bar_C'].min():.0f}–{hi.loc[hi['family']=='Mg','T_at_1bar_C'].max():.0f} °C. This capacity–temperature trade-off is the central materials constraint for mobile storage.
7. **AB5 vs AB2 (Fig. 7; Mann–Whitney tests).**
   * ΔH: AB2 is lower, median {ab5.median():.1f} (AB5) vs {ab2.median():.1f} kJ/mol (AB2), p = {pv['dH']:.1e}. AB2 is also much more
     spread out, because Laves-phase compositions span a wide range of stability.
   * Capacity, stated wt%: AB2 is higher, {w5.median():.2f} vs {w2.median():.2f} wt%, p = {pv['wt']:.1e}.
   * ΔS: no significant difference ({s5.median():.1f} vs {s2.median():.1f}, p = {pv['dS']:.2f}).
8. **Temperature–pressure (Fig. 8).** Computed from Purdue's experimental ΔH, ΔS:

{md_table(vh)}

   LaNi5 and TiFe give a few bar at 25 °C. TiCrMn (ΔH = 21.8) is a *high-pressure* AB2, about
   100 bar at 25 °C, and needs sub-zero temperatures for 1 bar; it was studied for low-temperature use.
   V–Cr is in between. NaAlH4's Na3AlH6 → NaH plateau (ΔH = 47 kJ/mol) reaches 1 bar near 100 °C. Its
   NaAlH4 → Na3AlH6 plateau (37 kJ/mol) is lower; see Phase 6. Mg2Ni and MgH2 need
   about 255 °C and 300 °C respectively. The HydPARK single (T, P) points fall in the same range. The curves are flat-plateau
   desorption estimates: slope, hysteresis and multi-plateau effects are ignored here and
   handled in Phase 6.
9. **Property availability (Figs. 9–10).** Kinetics ({int(p['kin_abs_Ea_Jmol'].notna().sum())}/{int(p['kin_des_Ea_Jmol'].notna().sum())}),
   heat capacity ({int(p['cp_J_kgK'].notna().sum())}), density ({int(p['rho_kg_m3'].notna().sum())}) and thermal conductivity ({int(p['keff_W_mK'].notna().sum())}) are sparse.
   They support descriptive engineering comparison, not ML. HydPARK has T/P only in blocks 0 and 2, and
   references only in blocks 1–3.

## Implications for the next phases

* ΔH is the only target with enough clean, comparable data for ML ({len(u)} compositions).
* Capacity ML is limited to Purdue stated wt% ({int((p['capacity_basis']=='stated_wt_pct').sum())} values, mostly AB5/AB2 within
  0.6–2.9 wt%). Its usefulness is doubtful because the range is narrow; this is decided in Phase 5.
* Mg-based and complex hydrides will be assessed with their experimental thermodynamics plus
  cited literature, not with ML.

Reference values used in figures: S°(H2, 298 K) = 130.68 J/(mol K) (NIST-JANAF tables); DOE onboard
storage-system target for 2025 of 5.5 wt% (1.8 kWh/kg) (US DOE Hydrogen and Fuel Cell Technologies Office, Technical Targets
for Onboard Hydrogen Storage for Light-Duty Vehicles). The DOE target applies to the complete system,
not to the material, which makes it a stricter test than shown.
"""
    (ROOT / "reports/eda_summary.md").write_text(text)


def main():
    apply_style()
    p, h, u = load()
    paths = [fig01_class_distribution(p, h), fig02_dH_distribution(p, h, u),
             fig03_dS_distribution(p, h), fig04_capacity_distribution(p, h),
             fig05_dH_vs_dS(p, h), fig06_dH_vs_capacity(p, h), fig07_ab5_vs_ab2(p, h, u),
             fig08_temperature_pressure(p, h), fig09_property_availability(p),
             fig10_missing_data(p, h)]
    summary_stats(p, h, u)
    corr = correlations(p, h, u)
    write_report(p, h, u, corr)
    print(corr.to_string(index=False))
    for x in paths:
        print(x.relative_to(ROOT))


if __name__ == "__main__":
    main()
