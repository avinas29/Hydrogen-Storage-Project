"""Parse Purdue Metal Hydride Toolbox ``.mh`` files into a flat table.

The parsing rules mirror the MATLAB toolbox (``@MetalHydride/ReadFile.m``,
``ReadZones.m``, ``ReadNumber.m``, ``ReadThermo.m``):

* everything after the first ``#`` on a line is a comment (we keep the comment
  text separately as a provenance note, the toolbox discards it);
* ``{`` / ``}`` open and close zones; the zone name is the line before ``{``;
* an entry is ``key: value``; the toolbox takes the *first* line whose
  lower-cased text contains ``key:``, we match the key exactly;
* ``[a, b, c]`` is an array (one value per plateau).

Only values that are physically written in the file are extracted.  The
toolbox silently substitutes type-based defaults (``GetTypeProperty.m``) for
absent rho/Cp/keff/kinetics/hysteresis/Tc/slope.  Those defaults are NOT
inserted here: an absent entry stays NaN and is reported as missing.

Sign convention (verified in ``Peq.m`` / ``MetalHydride.m``): DH and DS are
stored as *formation* quantities, negative, in J/mol H2 and J/(mol H2 K):
    Peq = 101325 Pa * exp((DH - T*DS) / (R*T))
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

# Molar masses exactly as hard-coded in @Element/Element.m (g/mol).  Only used
# to reproduce the toolbox's own H/M -> wt% conversion.
TOOLBOX_MOLAR_MASS = {
    "H": 1.0079, "Li": 6.941, "Be": 9.01218, "B": 10.81, "C": 12.011,
    "N": 14.007, "O": 15.999, "F": 18.998, "Na": 22.98977, "Mg": 24.305,
    "Al": 26.98154, "Si": 28.0855, "K": 39.0983, "Ca": 40.078,
    "Sc": 44.9559, "Ti": 47.867, "V": 50.9415, "Cr": 51.996, "Mn": 54.938,
    "Fe": 55.847, "Co": 58.9332, "Ni": 58.693, "Cu": 63.546, "Zn": 65.41,
    "Ga": 69.723, "Ge": 72.64, "Y": 88.9059, "Zr": 91.22, "Nb": 92.9064,
    "Mo": 95.94, "Tc": 97.91, "Ru": 101.07, "Rh": 102.9055, "Pd": 106.4,
    "Ag": 107.868, "Cd": 112.41, "In": 114.82, "Sn": 118.69,
    "La": 138.9055, "Ce": 140.12, "Pr": 140.91, "Nd": 144.24, "Pm": 144.91,
    "Sm": 150.36, "Eu": 151.96, "Gd": 157.25, "Tb": 158.93, "Dy": 162.50,
    "Ho": 164.93, "Er": 167.26, "Tm": 168.93, "Yb": 173.05, "Lu": 174.97,
    "Hf": 178.49, "Ir": 192.22, "Pt": 195.08, "Th": 232.04, "Pa": 231.0359,
    # Pseudo-elements: approximate masses assigned by the toolbox authors
    "Lm": 138.9055,  # La-rich mischmetal
    "Mm": 140.311,   # mischmetal
    "Vf": 53.39,     # ferrovanadium
}
PSEUDO_ELEMENTS = {"Mm", "Lm", "Vf"}
H_MASS_TOOLBOX = 1.008  # value used in ReadThermo.m


# --------------------------------------------------------------------------
# Low-level reading
# --------------------------------------------------------------------------
def _read_lines(path: Path) -> list[tuple[str, str]]:
    """Return (code, comment) pairs, splitting at the first '#'."""
    out = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "#" in raw:
            i = raw.index("#")
            out.append((raw[:i], raw[i + 1:].strip()))
        else:
            out.append((raw, ""))
    return out


def _parse_zones(lines: list[tuple[str, str]]) -> dict:
    """Recursive zone structure: {'entries': [(key, value, comment)], 'zones': {name: zone}, 'comments': [...]}."""
    root = {"entries": [], "zones": {}, "comments": []}
    stack = [root]
    pending_name = None
    for code, comment in lines:
        text = code.strip()
        cur = stack[-1]
        # A line may hold several braces, e.g. "Hydriding { }" - handle char by char
        if "{" in text or "}" in text:
            before = text.split("{")[0].split("}")[0].strip()
            if before and "{" in text:
                pending_name = before
            for ch in text:
                if ch == "{":
                    name = (pending_name or f"zone{len(stack[-1]['zones'])}").strip()
                    z = {"entries": [], "zones": {}, "comments": []}
                    stack[-1]["zones"][name] = z
                    stack.append(z)
                    pending_name = None
                elif ch == "}":
                    if len(stack) > 1:
                        stack.pop()
            if comment:
                stack[-1]["comments"].append(comment)
            continue
        if not text:
            if comment:
                cur["comments"].append(comment)
            continue
        if ":" in text:
            key, val = text.split(":", 1)
            cur["entries"].append((key.strip(), val.strip(), comment))
            pending_name = None
        else:
            # A bare word: the name of the zone opened on the next line
            pending_name = text
            if comment:
                cur["comments"].append(comment)
    return root


def _get(zone: dict | None, key: str):
    """First entry matching key (case-insensitive). Returns (value_str, comment) or (None, None)."""
    if zone is None:
        return None, None
    for k, v, c in zone["entries"]:
        if k.lower() == key.lower():
            return v, c
    return None, None


def _num(val: str | None):
    """Parse a scalar or [array] number. Returns float, list[float] or NaN."""
    if val is None or val == "":
        return np.nan
    v = val.strip()
    if v.startswith("["):
        inner = v.strip("[]")
        out = []
        for s in inner.split(","):
            s = s.strip()
            try:
                out.append(float(s))
            except ValueError:
                out.append(np.nan)
        return out
    try:
        return float(v.split()[0])
    except ValueError:
        return np.nan


def parse_elements(val: str) -> dict[str, float]:
    """'[Ti:1, Mn:1.66, Vf:0.34]' -> {'Ti': 1.0, 'Mn': 1.66, 'Vf': 0.34} (order kept)."""
    inner = val.strip().strip("[]")
    comp = {}
    for part in inner.split(","):
        if ":" not in part:
            continue
        el, amt = part.split(":", 1)
        comp[el.strip()] = float(amt.strip())
    return comp


def _scalar_or_array(x):
    """Split a parsed number into (first plateau scalar, json-ish array string, n)."""
    if isinstance(x, list):
        return x[0], ";".join(f"{v:g}" for v in x), len(x)
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan, "", 0
    return x, "", 1


# --------------------------------------------------------------------------
# One file -> one record
# --------------------------------------------------------------------------
def parse_mh_file(path: Path, pci_dir: Path | None = None) -> dict:
    lines = _read_lines(path)
    root = _parse_zones(lines)
    rec: dict = {"source_file": path.name, "material_id": path.stem}

    el_val, el_comment = _get(root, "Elements")
    comp = parse_elements(el_val) if el_val else {}
    rec["elements_raw"] = el_val
    rec["elements_comment"] = el_comment or ""
    rec["composition"] = ";".join(f"{k}:{v:g}" for k, v in comp.items())
    rec["formula_compact"] = "".join(
        k if v == 1 else f"{k}{v:g}" for k, v in comp.items())
    t_val, _ = _get(root, "Type")
    rec["type"] = t_val

    thermo = root["zones"].get("Thermodynamics")
    deh = thermo["zones"].get("Dehydriding") if thermo else None
    hyd = thermo["zones"].get("Hydriding") if thermo else None

    wt, wt_c = _get(thermo, "Weight Percent")
    hm, hm_c = _get(thermo, "H/M")
    rec["wt_pct_stated"] = _num(wt)
    rec["wt_pct_comment"] = wt_c or ""
    rec["hm_stated"] = _num(hm)
    rec["hm_comment"] = hm_c or ""

    # Toolbox conversion (ReadThermo.m): wt fraction = HM*1.008/(HM*1.008 + W_formula).
    # W_formula is the molar mass of ONE FORMULA UNIT, so the "H/M" entry is
    # effectively H atoms per formula unit, not per metal atom.
    w_fu = sum(TOOLBOX_MOLAR_MASS.get(k, np.nan) * v for k, v in comp.items())
    n_atoms = sum(comp.values())
    rec["molar_mass_fu_toolbox"] = w_fu
    rec["n_atoms_fu"] = n_atoms
    if not np.isnan(rec["wt_pct_stated"]):
        wt_frac = rec["wt_pct_stated"] / 100
        rec["capacity_basis"] = "stated_wt_pct"
    elif not np.isnan(rec["hm_stated"]):
        h = rec["hm_stated"] * H_MASS_TOOLBOX
        wt_frac = h / (h + w_fu)
        rec["capacity_basis"] = "derived_from_HM_per_formula_unit"
    else:
        wt_frac = np.nan
        rec["capacity_basis"] = "missing"
    rec["wt_pct_toolbox"] = wt_frac * 100
    # H atoms per metal atom, as the toolbox's HM property computes it
    rec["h_per_metal_atom_toolbox"] = (
        wt_frac / (1 - wt_frac) * w_fu / (H_MASS_TOOLBOX * n_atoms)
        if n_atoms else np.nan)

    # --- Dehydriding (desorption) thermodynamics
    for prefix, zone in (("des", deh), ("abs", hyd)):
        for key, col in (("DH", "dH_J_per_molH2"), ("DS", "dS_J_per_molH2K")):
            v, c = _get(zone, key)
            s, arr, n = _scalar_or_array(_num(v))
            rec[f"{prefix}_{col}"] = s
            rec[f"{prefix}_{col}_all"] = arr
            rec[f"{prefix}_{key}_comment"] = c or ""
            if key == "DH":
                rec[f"{prefix}_n_values"] = n
        for key in ("slope", "Ts", "Tc", "T", "ln(Pa/Pd)", "centers", "widths", "minSpans"):
            v, c = _get(zone, key)
            if v is None:
                continue
            s, arr, _ = _scalar_or_array(_num(v))
            safe = key.replace("(", "").replace(")", "").replace("/", "_")
            rec[f"{prefix}_{safe}"] = s
            if arr:
                rec[f"{prefix}_{safe}_all"] = arr
        v, _ = _get(zone, "From Isotherms")
        rec[f"{prefix}_from_isotherms"] = (v or "").strip().lower() == "true"
        rec[f"{prefix}_zone_comments"] = " | ".join(zone["comments"]) if zone else ""

    rec["n_plateaus"] = max(rec.get("des_n_values", 0), 1) if rec.get("des_n_values") else 0
    rec["thermo_comments"] = " | ".join(thermo["comments"]) if thermo else ""

    # --- Properties
    props = root["zones"].get("Properties")
    for key, col in (("keff", "keff_W_per_mK"), ("cp", "cp_J_per_kgK"), ("rho", "rho_kg_per_m3")):
        v, c = _get(props, key)
        rec[col] = _num(v) if not isinstance(_num(v), list) else _num(v)[0]
        rec[f"{col}_comment"] = c or ""

    # --- Kinetics: keep every key that is written
    kin = root["zones"].get("Kinetics")
    for prefix, zname in (("kin_abs", "Hydriding"), ("kin_des", "Dehydriding")):
        z = kin["zones"].get(zname) if kin else None
        entries = z["entries"] if z else []
        rec[f"{prefix}_n_entries"] = len(entries)
        for k, v, c in entries:
            safe = re.sub(r"[^A-Za-z0-9]+", "_", k).strip("_")
            num = _num(v)
            rec[f"{prefix}_{safe}"] = num if not isinstance(num, float) or not np.isnan(num) else v
        rec[f"{prefix}_comments"] = " | ".join(z["comments"]) if z else ""

    # --- Notes
    notes = root["zones"].get("Notes")
    note_txt = []
    if notes:
        note_txt += notes["comments"]
        note_txt += [f"{k}: {v}" for k, v, _ in notes["entries"]]
    rec["notes"] = " | ".join(note_txt)

    # --- References
    refs = root["zones"].get("References")
    ref_keys, ref_ids, cites = [], [], []
    if refs:
        for rname, rz in refs["zones"].items():
            d = {k.lower(): v for k, v, _ in rz["entries"]}
            ref_keys.append(rname)
            ref_ids.append(d.get("id", ""))
            cites.append(", ".join(x for x in (d.get("authors", ""), d.get("title", ""),
                                                d.get("journal", ""), d.get("year", "")) if x))
    rec["n_refs"] = len(ref_keys)
    rec["ref_keys"] = "; ".join(ref_keys)
    rec["ref_ids"] = "; ".join(ref_ids)
    rec["ref_citations"] = " || ".join(cites)

    # --- PCI file
    if pci_dir is not None:
        pci = pci_dir / f"{path.stem}_PCI.csv"
        rec["pci_file"] = pci.name if pci.exists() else ""
    # Every comment in the file, for keyword-based provenance flags
    rec["all_comments"] = " | ".join(c for _, c in lines if c)
    return rec


def load_purdue(toolbox_dir: Path) -> pd.DataFrame:
    data_dir = toolbox_dir / "data"
    pci_dir = data_dir / "supporting"
    files = sorted(data_dir.glob("*.mh"))
    return pd.DataFrame([parse_mh_file(f, pci_dir) for f in files])


def read_pci_file(path: Path) -> dict:
    """Read a ``*_PCI.csv`` in the layout used by ReadPCIData.m.

    Rows 1-3: Author/DOI/Location; row 5: Abs/Des per column pair; row 6:
    temperature (K); row 7: units; then (mass %, P bar) column pairs.
    """
    raw = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
    meta = {"author": raw.iat[0, 1], "doi": raw.iat[1, 1], "location": raw.iat[2, 1],
            "note": " ".join(x for x in raw.iloc[0, 2:].tolist() if x).strip()}
    mode_row, temp_row, unit_row = raw.iloc[4].tolist(), raw.iloc[5].tolist(), raw.iloc[6].tolist()
    curves = []
    for j, mode in enumerate(mode_row):
        m = mode.strip().lower()
        if m not in ("abs", "des"):
            continue
        w = pd.to_numeric(raw.iloc[7:, j], errors="coerce")
        p = pd.to_numeric(raw.iloc[7:, j + 1], errors="coerce")
        ok = w.notna() & p.notna()
        curves.append({"mode": m, "T_K": float(temp_row[j]),
                       "x_unit": unit_row[j], "p_unit": unit_row[j + 1],
                       "wt_pct": w[ok].to_numpy(), "P_bar": p[ok].to_numpy()})
    meta["curves"] = curves
    return meta
