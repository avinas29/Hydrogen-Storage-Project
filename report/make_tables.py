"""Statistics computed for the report text that are not in an earlier phase output (Table 2.1, Section 1.2).

Run: .venv/bin/python -m report.make_tables   ->  report/tables/purdue_family_summary.csv, purdue_dS_quantiles.csv
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report/tables"
OUT.mkdir(parents=True, exist_ok=True)
v = pd.read_csv(ROOT / "results/tables/vant_hoff_purdue.csv")
s = v[v.n_plateaus == 1]
g = s.groupby("family").agg(n=("dH_kJmol", "size"), median_dH_kJmol=("dH_kJmol", "median"),
                            median_dS_JmolK=("dS_JmolK", "median"), median_wt_pct=("wt_pct_reported", "median"),
                            max_wt_pct=("wt_pct_reported", "max"), median_T1bar_C=("T_C_at_1bar", "median")).round(1)
g.sort_values("n", ascending=False).to_csv(OUT / "purdue_family_summary.csv")
q = s["dS_JmolK"].quantile([0.25, 0.5, 0.75]).round(1).rename("dS_JmolK")
q.to_frame().assign(n=len(s)).to_csv(OUT / "purdue_dS_quantiles.csv", index_label="quantile")
print(g.sort_values("n", ascending=False)); print(q)
