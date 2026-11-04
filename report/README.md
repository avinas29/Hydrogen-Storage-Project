# B.Tech project report

**Machine Learning-Assisted Discovery and Application-Specific Screening of Metal Hydride Materials for Hydrogen Storage**

| File | What it is |
|---|---|
| `BTP_Report.docx` | the editable report, built inside the official template (`template/BTP_Report_Format_Word.docx`) |
| `BTP_Report.pdf` | LibreOffice rendering of the same file |
| `content/*.md` | chapter text (source of truth; light markup, see `build_report.py`) |
| `content_verified/` | snapshot of the technically reviewed text before the humanizer pass |
| `refs.py`, `references.md` | bibliography (Vancouver) and the verification status of every entry |
| `figures/` | new figures (`make_figures.py`) and title-free copies of project figures (`figures/existing/`, `clean_figures.py`) |
| `tables/` | statistics computed only for the report text (`make_tables.py`) |
| `REPORT_PLAN.md` | Stage 1 plan and evidence map |

Length: 9 preliminary pages (i–ix) and 36 pages of chapters and references (1–36), for 45 pages in total. Appendices A–F add 9 pages.
It contains 19 figures, 29 tables (11 of them in the appendices) and 24 references.

## Rebuild

```bash
MPLCONFIGDIR=.mplcache .venv/bin/python -m report.make_figures     # new figures (scenario plot calls the real engines)
MPLCONFIGDIR=.mplcache .venv/bin/python -m report.clean_figures    # project figures without their "Fig. N" titles
.venv/bin/python -m report.make_tables
.venv/bin/python -m report.make_appendices                          # appendix tables from result files
.venv/bin/python -m report.build_report                             # two-pass build: DOCX -> PDF -> page numbers -> DOCX
.venv/bin/python report/check_numbers.py                            # every number traced to a result file
.venv/bin/python report/check_humanize.py                           # numbers/citations unchanged since the review
```

## Checks performed

* **Numbers (Stage 3).** `check_numbers.py` looks up every number in the text in the phase reports, metric tables, manifest and report tables. It checked 687 numbers. The 6 it does not find are R² values printed to 3 decimals (0.715, 0.744), the "SHA-256" label, and the LaNi₅ worked-example arithmetic (32 151 J, 15.95 MJ kg⁻¹).
* **Humanizer (Stage 4).** `check_humanize.py` compares the final text with `content_verified/`. Citations, cross-references and table rows are unchanged. The only number differences are three figure widths and five values removed from a Ch. 7 recap. Each of those five is still stated in its source chapter: ΔS quartiles in Ch. 1, 13% and 38.8 MJ kg⁻¹ in Ch. 5, 1.76 kJ mol⁻¹ in Ch. 5 and 8.
* **DOCX.** Passes the OOXML schema validation of the docx skill.
* **Platform fix found while writing.** The Designer's Pareto front included unranked insufficient-evidence materials, so in the industrial scenario the front among ranked materials was empty. `src/app/recommend.py` now computes the front among ranked materials only, and a regression test was added (77 tests pass). `reports/platform_demo_scenarios.md` was regenerated; its rankings did not change.

## Still open

1. The certificate's Date line and the supervisor's signature are filled in by hand on the printed copy.
2. Check the entries marked **check** in `references.md`: the co-authors of the 1970 Philips LaNi₅ paper, the exact Zenodo title and creators of ML-HydPARK, and the co-author lists of Witman 2020, Hirscher 2020 and Meredig 2018.
3. In Word, update the Contents, List of Figures and List of Tables (*Update field → Update entire table*) if the pagination changes after editing.
4. The AI-use statement was removed at the student's request (the supervisor did not require one). Add it to the Acknowledgements if a wording is agreed later.
