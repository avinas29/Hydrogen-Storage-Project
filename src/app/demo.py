"""Run two illustrative scenarios through the real engines and write reports/platform_demo_scenarios.md.

Run:  .venv/bin/python -m src.app.demo
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from ..data.run_audit import md_table
from .discovery import Targets, evaluate, rank
from .generator import PRESETS, generate_sites
from .predictor import Predictor
from .recommend import APPLICATIONS, LABELS, Requirements, explain, run

ROOT = Path(__file__).resolve().parents[2]

SCENARIOS = [
    dict(title="Scenario 1: mobile storage (PEM fuel-cell vehicle/forklift-type, illustrative)",
         req=Requirements(application="Mobile hydrogen storage", ambient_min_C=-10, ambient_max_C=40,
                          heat_source="PEM fuel-cell waste heat", heat_temp_C=70, heat_power_kW=5.0,
                          h2_kg=1.0, P_delivery_bar=3, flow_kg_h=0.5, max_mass_kg=80, min_capacity_wt=1.5,
                          max_pressure_bar=50, charge_pressure_bar=100),
         lab=[("Ti-Cr-Mn (AB2 Laves)", 0.05), ("Ti-Zr-Mn-Cr (AB2 Laves)", 0.05)],
         targets=Targets(T_target_C=25, P_target_bar=3, T_min_C=-20, T_max_C=70)),
    dict(title="Scenario 2: industrial waste-heat-integrated stationary buffer (illustrative)",
         req=Requirements(application="Industrial hydrogen buffering", ambient_min_C=5, ambient_max_C=40,
                          heat_source="industrial waste heat", heat_temp_C=120, heat_power_kW=50.0,
                          cooling_water=True, cooling_temp_C=20, h2_kg=50.0, P_delivery_bar=5, flow_kg_h=5.0,
                          max_pressure_bar=30, charge_pressure_bar=30),
         lab=[("La-Ce-Ni-Al (AB5)", 0.05), ("Ti-Fe-Mn (AB, TiFe1-xMnx)", 0.05)],
         targets=Targets(T_target_C=100, P_target_bar=5, T_min_C=40, T_max_C=120)),
]


def scenario(s, P) -> tuple[str, pd.DataFrame]:
    req = s["req"]
    w = APPLICATIONS[req.application]["weights"]
    res = run(req, w, ("wt_pct", "heat_MJ_per_kgH2"))
    allpass = res[res.status != "fail"]
    ok = allpass[allpass["rank"].notna()]          # ranked = passing and not 'insufficient evidence'
    fail = res[res.status == "fail"]
    reasons = pd.Series([LABELS[k] for _, r in fail.iterrows() for k in LABELS if r.get(f"c_{k}") == "fail"]).value_counts()
    top = ok.head(8)[["rank", "name", "family", "evidence_class", "score", "pareto", "T_required_C", "P_at_T_available_bar",
                      "wt_pct", "heat_MJ_per_kgH2", "material_mass_kg", "heat_power_kW"]].round(2)
    pareto = ok[ok.pareto][["rank", "name", "family", "wt_pct", "heat_MJ_per_kgH2", "evidence_class"]].round(2)
    ev = ok["evidence_class"].value_counts()
    sens = []
    for k in w:
        for f in (0.0, 2.0):
            w2 = dict(w); w2[k] *= f
            r2 = run(req, w2)
            sens.append({"criterion": k, "weight ×": f, "new #1": r2[r2.status != "fail"].iloc[0]["name"]})
    e = explain(ok.iloc[0], req)

    lab_rows, lab_top = [], []
    for preset, step_ in s["lab"]:
        p = PRESETS[preset]
        cands = generate_sites(p.sites, step_, 400, 0)
        d = rank(evaluate(P, cands, p.family, s["targets"]), s["targets"])
        okc = d[d.status == "candidate"]
        lab_rows.append({"alloy system": preset, "generated": len(d), "in domain and in window": len(okc),
                         "rejected": int((d.status == "rejected").sum()),
                         "main rejection reason": d.loc[d.status == "rejected", "reasons"].str.split(";").str[0].value_counts().index[0]
                         if (d.status == "rejected").any() else "–"})
        lab_top.append(okc.head(4).assign(system=preset))
    lt = pd.concat(lab_top)[["system", "formula", "dH_pred_kJmol", "dH_low", "dH_high", "nn_L1", "T_at_Ptarget_C",
                             "T_at_Ptarget_low_C", "T_at_Ptarget_high_C", "nearest_known", "nearest_known_dH_exp", "score"]].round(2)

    spec = {k: v for k, v in asdict(req).items() if v not in (None, "", [], False) and k != "data_sources"}
    text = f"""## {s['title']}

**1. Requirements** (illustrative, manual input; location not used):

{md_table(pd.DataFrame([spec]).T.reset_index().rename(columns={'index': 'field', 0: 'value'}))}

Derived: H₂ must be delivered at ≤ {req.desorption_T_allowed_C():.0f} °C; hottest bed {req.bed_T_max_C():.0f} °C; charging at {req.charge_T_C():.0f} °C.

**2. Materials considered:** {len(res)} experimental Purdue materials, plus ML-generated candidates (section 8, kept separate).

**3. Rejected by hard constraints:** {len(fail)}. Failures by requirement (a material can fail several):

{md_table(reasons.rename_axis('failed requirement').reset_index(name='materials'))}

**4. Remaining after filtering:** {len(allpass)} ({(res.status == 'pass').sum()} pass fully; {(res.status == 'pass (incomplete evidence)').sum()} pass with incomplete evidence).
Evidence classes among them: {', '.join(f'{k} {v}' for k, v in allpass['evidence_class'].value_counts().items())}.
{len(allpass) - len(ok)} with insufficient evidence are listed but not ranked, leaving {len(ok)} ranked.

**5. Final ranking (top 8, default {req.application} weights {w}):**

{md_table(top)}

**6. Pareto trade-offs** (capacity ↑ vs reaction heat ↓): {len(pareto)} non-dominated materials:

{md_table(pareto)}

Weight sensitivity (new #1 when one weight is removed or doubled):

{md_table(pd.DataFrame(sens))}

**7. Evidence and uncertainty for #1 ({ok.iloc[0]['name']}):** {ok.iloc[0]['evidence_class']}. {e['why']}
Advantages: {', '.join(e['advantages']) or '–'}. Limitations: {', '.join(e['limitations']) or '–'}. Missing: {e['missing'] or '–'}.

**8. ML-generated candidate alloys (proposed, not validated; ΔH = ML, ΔS assumed; capacity not predicted):**

{md_table(pd.DataFrame(lab_rows))}

{md_table(lt)}

**9. Recommended future experiments:** {'; '.join(e['measurements'])}. Then test the top generated candidates against their predicted ΔH intervals.
"""
    return text, ok.head(5)


def main():
    P = Predictor()
    parts, tops = [], []
    for s in SCENARIOS:
        t, top = scenario(s, P)
        parts.append(t); tops.append(top)
    both = set(tops[0]["name"]) & set(tops[1]["name"])
    head = f"""# METAL HYDRIDE AI: demonstration scenarios

Generated by `src/app/demo.py` from the real engines, the saved model and the project data. The requirements are illustrative,
not a real design brief. Recommendations are rule-based screenings of experimental literature data, so they need
measurement before use. All mass/volume figures are material-only (no vessel, heat exchanger or bed porosity).

**How the recommendations change:** the top-5 lists of the two scenarios share {len(both)} material(s){': ' + ', '.join(sorted(both)) if both else ''}.
Mobile favours capacity at near-ambient temperature. The 120 °C industrial buffer accepts more stable hydrides (higher ΔH)
and values kinetics, pressure fit and cost.

"""
    (ROOT / "reports/platform_demo_scenarios.md").write_text(head + "\n".join(parts))
    print(head)
    for t in tops:
        print(t[["rank", "name", "family", "evidence_class", "score"]].to_string(index=False))


if __name__ == "__main__":
    main()
