"""Re-render the project figures used in the report without their 'Fig. N' titles (the report numbers them itself).

Output: report/figures/existing/*.png. Nothing in results/figures is touched.
Run: MPLCONFIGDIR=.mplcache .venv/bin/python -m report.clean_figures
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from src.visualization import style  # noqa: E402

OUT = Path(__file__).resolve().parent / "figures/existing"
FIGNUM = re.compile(r"^\s*Fig\.\s*\d+\s*")


def _strip(orig):
    def f(self, label, *a, **k):
        if isinstance(label, str) and FIGNUM.match(label):
            return None
        return orig(self, label, *a, **k)
    return f


Figure.suptitle = _strip(Figure.suptitle)
Axes.set_title = _strip(Axes.set_title)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.png", dpi=220)
    matplotlib.pyplot.close(fig)
    return OUT / f"{name}.png"


style.save = save

if __name__ == "__main__":
    from src.visualization import eda, ml_plots, pci_plots, screening_plots, thermo_plots
    for mod in (ml_plots, thermo_plots, pci_plots, screening_plots):
        mod.save = save
        pass
    eda.save = save
    style.apply_style()
    p, h, u = eda.load()
    eda.fig01_class_distribution(p, h)
    eda.fig10_missing_data(p, h)
    for f in (ml_plots.fig11_dH_model_comparison, ml_plots.fig12_dH_parity, ml_plots.fig14_importance, ml_plots.fig15_lofo,
              thermo_plots.fig17_vant_hoff, thermo_plots.fig18_windows, thermo_plots.fig19_heat, thermo_plots.fig20_ml_series,
              pci_plots.fig21_pci, screening_plots.fig24_map):
        f()
    print(sorted(x.name for x in OUT.glob("*.png")))
