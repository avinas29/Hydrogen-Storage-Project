"""Stage 3 check: every number in the report content must be traceable to a project result file (or be structural).

Prints numbers that do not occur (at their stated precision) anywhere in reports/, results/ or the figure data.
"""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SMALL = ["dH_cv_summary", "dH_holdout_metrics", "dH_cv_by_family", "dH_leave_family_out", "dH_within_family",
         "dH_sensitivity", "dH_permutation_importance", "dH_grouping_effect", "wt_cv_summary"]
SRC = list((ROOT / "reports").glob("*.md")) + [ROOT / f"results/metrics/{n}.csv" for n in SMALL] + [ROOT / "results/models/dH_predictor_manifest.json",
      ROOT / "report/figures/f_scenarios_top5.csv", ROOT / "report/tables/purdue_family_summary.csv", ROOT / "report/tables/purdue_dS_quantiles.csv", ROOT / "report/refs.py", ROOT / "results/tables/applicability_domain_calibration.csv"]
NUM = re.compile(r"(?<![\w.])[−-]?\d+(?:[.,]\d+)?(?![\w])")
corpus = set()
for f in SRC:
    for m in NUM.finditer(f.read_text(errors="ignore").replace("−", "-")):
        t = m.group(0).replace(",", "")
        try:
            v = float(t)
        except ValueError:
            continue
        corpus.add(t.lstrip("-"))
        for d in range(0, 3):
            corpus.add(f"{abs(v):.{d}f}")
misses = {}
checked = 0
for f in sorted((ROOT / "report/content").glob("0[0-8]*.md")):
    txt = f.read_text().replace("−", "-")
    txt = re.sub(r"\[@[^\]]+\]|@(fig|tab|eq):\w+", "", txt)
    txt = re.sub(r"[₀-₉]+", "", txt)      # subscript stoichiometries are formulas, checked by eye
    for m in NUM.finditer(txt):
        t = m.group(0).lstrip("-").replace(",", "")
        if len(t) <= 2 and "." not in t:
            continue
        checked += 1
        if t in corpus:
            continue
        ctx = txt[max(0, m.start() - 50): m.end() + 30].replace("\n", " ")
        misses.setdefault(f.name, []).append((t, ctx))
for k, v in misses.items():
    print("==", k)
    for t, c in v:
        print(f"  {t:>10} | {c}")
print("checked", checked, "numbers;", sum(len(v) for v in misses.values()), "not found")
