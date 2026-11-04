"""Quality / provenance flags for the parsed Purdue table.

Every flag is derived from text actually present in the .mh file (values,
comments, reference IDs) - nothing is inferred from outside knowledge.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .purdue_parser import PSEUDO_ELEMENTS

DS_TYPICAL = (70.0, 170.0)  # |dS| window, J/(mol H2 K); see hydpark.DS_TYPICAL


def capacity_definition(row) -> str:
    """Classify what the capacity number means, from its source comment."""
    note = f"{row['wt_pct_comment']} {row['hm_comment']}".lower()
    if row["capacity_basis"] == "missing":
        return "missing"
    if "assum" in note:
        return "assumed"
    if "theor" in note:
        return "theoretical_or_reduced_from_theoretical"
    if "todo" in note or "?" in note or "could not be confirmed" in note:
        return "unconfirmed_source"
    if "approx" in note or "adjusted" in note:
        return "approximated_from_figure"
    if "revers" in note:
        return "reversible_stated"
    if "plateau only" in note:
        return "first_plateau_only"
    return "literature_value_definition_unstated"


def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    comp_elements = df["composition"].str.split(";").apply(
        lambda parts: {p.split(":")[0] for p in parts if p})

    df["flag_unverified_ref_sandia"] = df["ref_ids"].str.contains("SandiaDBRef", na=False)
    df["flag_pseudo_element"] = comp_elements.apply(lambda s: bool(s & PSEUDO_ELEMENTS))
    df["pseudo_elements"] = comp_elements.apply(lambda s: ",".join(sorted(s & PSEUDO_ELEMENTS)))
    df["flag_trade_name_file"] = ~df["material_id"].str.contains(r"\[")
    df["flag_composition_approximate"] = df["elements_comment"].str.contains(
        "approx|actually", case=False, na=False)
    df["flag_contains_H_in_formula"] = comp_elements.apply(lambda s: "H" in s)
    df["flag_ambiguous_formula"] = (
        df["flag_pseudo_element"] | df["flag_trade_name_file"]
        | df["flag_composition_approximate"] | df["flag_contains_H_in_formula"])

    df["flag_multi_plateau"] = df["n_plateaus"] > 1
    df["flag_des_thermo_from_isotherm_fit"] = df["des_from_isotherms"]
    df["flag_has_pci_digitized"] = df["pci_file"] != ""

    df["capacity_definition"] = df.apply(capacity_definition, axis=1)
    df["flag_capacity_from_HM"] = df["capacity_basis"].str.startswith("derived")
    df["flag_capacity_uncertain"] = df["capacity_definition"].isin(
        ["assumed", "unconfirmed_source", "approximated_from_figure",
         "theoretical_or_reduced_from_theoretical"])

    dS = df["des_dS_J_per_molH2K"].abs()
    df["flag_dS_atypical"] = (dS < DS_TYPICAL[0]) | (dS > DS_TYPICAL[1])
    df["flag_todo_in_file"] = df["all_comments"].str.contains("TODO", na=False)

    # Properties that the toolbox fills with a type default when absent
    df["has_rho"] = df["rho_kg_per_m3"].notna()
    df["has_cp"] = df["cp_J_per_kgK"].notna()
    df["has_keff"] = df["keff_W_per_mK"].notna()
    df["has_kin_abs"] = df["kin_abs_n_entries"] > 0
    df["has_kin_des"] = df["kin_des_n_entries"] > 0
    df["has_abs_thermo"] = df["abs_dH_J_per_molH2"].notna() | df["abs_dS_J_per_molH2K"].notna()
    df["has_hysteresis"] = df.get("abs_lnPa_Pd", pd.Series(np.nan, index=df.index)).notna()
    return df
