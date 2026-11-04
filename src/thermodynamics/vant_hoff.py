"""Van't Hoff relations for metal hydride plateaus.

Convention (verified in Phase 1 against the toolbox's ``Peq.m``, and for HydPARK numerically):
ΔH and ΔS are the POSITIVE desorption (decomposition) magnitudes, per mol H2, and the
reference pressure is P0 = 1 atm:

    ln(P / P0) = -ΔH / (R T) + ΔS / R

Peq.m uses p0 = 101325 Pa, and the HydPARK ln Peq(25 C) column is in atm. ΔS values in both
datasets are therefore referenced to 1 atm. Results are reported in bar (1 atm = 1.01325 bar).

Plateau slope: the toolbox models chemical potential as μ = μ0 + A (x - 0.5) with
A = slope · R · Ts (``ReadThermo.m``), so  ln P(x) = ln P_mid + slope · (Ts / T) · (x - 0.5),
with x = w / w_max. Only slopes written in the .mh files are used here. Ts defaults to 298 K,
as in the toolbox.
"""
from __future__ import annotations

import numpy as np

R = 8.314462618          # J/(mol K), CODATA 2018
P0_BAR = 1.01325          # 1 atm in bar, the reference pressure of the data
M_H2 = 2.01588            # g/mol
LHV_H2_MJ_PER_KG = 119.96  # lower heating value of H2, MJ/kg (US DOE H2 Program / NIST)
T_REF_SLOPE = 298.0       # K, toolbox default Ts


def peq_bar(T_K, dH_kJ, dS_J):
    """Equilibrium plateau pressure (bar) at temperature T (K)."""
    T = np.asarray(T_K, dtype=float)
    return P0_BAR * np.exp(-np.asarray(dH_kJ) * 1000 / (R * T) + np.asarray(dS_J) / R)


def T_at_P(P_bar, dH_kJ, dS_J):
    """Temperature (K) at which the plateau pressure equals P (bar)."""
    lnp = np.log(np.asarray(P_bar, dtype=float) / P0_BAR)
    return np.asarray(dH_kJ) * 1000 / (np.asarray(dS_J) - R * lnp)


def window_T(P_low_bar, P_high_bar, dH_kJ, dS_J):
    """Temperature range (K) over which Peq lies between P_low and P_high."""
    return T_at_P(P_low_bar, dH_kJ, dS_J), T_at_P(P_high_bar, dH_kJ, dS_J)


def heat_MJ_per_kg_H2(dH_kJ):
    """Reaction heat per kg of H2 released (desorption, endothermic) or absorbed (exothermic)."""
    return np.asarray(dH_kJ) / M_H2  # kJ/mol / g/mol = kJ/g = MJ/kg


def heat_fraction_of_LHV(dH_kJ):
    return heat_MJ_per_kg_H2(dH_kJ) / LHV_H2_MJ_PER_KG


def heat_kJ_per_kg_material(dH_kJ, wt_pct):
    """Heat per kg of hydrided material for a full charge (wt% on hydride basis H/(H+M))."""
    return heat_MJ_per_kg_H2(dH_kJ) * 1000 * np.asarray(wt_pct) / 100


def plateau_pressure_span(T_K, dH_kJ, dS_J, slope, x_low=0.1, x_high=0.9, Ts=T_REF_SLOPE):
    """Pressures (bar) at fractional capacities x_low and x_high for a sloped plateau."""
    p_mid = peq_bar(T_K, dH_kJ, dS_J)
    f = np.asarray(slope) * Ts / np.asarray(T_K, dtype=float)
    return p_mid * np.exp(f * (x_low - 0.5)), p_mid * np.exp(f * (x_high - 0.5))


def absorption_pressure_bar(T_K, des_dH, des_dS, abs_dH=np.nan, abs_dS=np.nan, ln_pa_pd=np.nan):
    """Absorption plateau pressure from stated data only.

    Priority: stated absorption ΔH/ΔS; otherwise stated hysteresis ln(Pa/Pd), treated as
    independent of temperature (flagged by the caller); otherwise NaN. The toolbox's
    type-default hysteresis is NOT used.
    """
    if np.isfinite(abs_dH) and np.isfinite(abs_dS):
        return peq_bar(T_K, abs_dH, abs_dS), "stated_abs_dH_dS"
    if np.isfinite(ln_pa_pd):
        return peq_bar(T_K, des_dH, des_dS) * np.exp(ln_pa_pd), "stated_hysteresis_const"
    return np.full(np.shape(T_K), np.nan), "not_available"
