"""Bibliography (Vancouver). Numbering is assigned by order of first citation when the report is built.

status: "verified" = title, journal/publisher, year, volume and pages (and DOI where given) confirmed online on 2026-11-04;
"check" = the item exists and the main record is confirmed, but the detail named in `note` could not be confirmed.
No DOI is given unless it was confirmed.
"""

REFS = {
    "schlapbach2001": dict(status="verified", text=(
        "Schlapbach L, Züttel A. Hydrogen-storage materials for mobile applications. Nature. 2001;414(6861):353–8. "
        "doi:10.1038/35104634")),
    "zuttel2003": dict(status="verified", text=(
        "Züttel A. Materials for hydrogen storage. Mater Today. 2003;6(9):24–33.")),
    "doe2017": dict(status="verified", text=(
        "U.S. Department of Energy, Office of Energy Efficiency and Renewable Energy. DOE technical targets for onboard "
        "hydrogen storage for light-duty vehicles [Internet]. Washington (DC): U.S. DOE; 2017 [cited 2026 Nov 4]. "
        "Available from: https://www.energy.gov/eere/fuelcells/doe-technical-targets-onboard-hydrogen-storage-light-duty-vehicles")),
    "sakintuna2007": dict(status="verified", text=(
        "Sakintuna B, Lamari-Darkrim F, Hirscher M. Metal hydride materials for solid hydrogen storage: a review. "
        "Int J Hydrogen Energy. 2007;32:1121–40. doi:10.1016/j.ijhydene.2006.11.022")),
    "sandrock1999": dict(status="verified", text=(
        "Sandrock G. A panoramic overview of hydrogen storage alloys from a gas reaction point of view. "
        "J Alloys Compd. 1999;293–295:877–88. doi:10.1016/S0925-8388(99)00384-9")),
    "hirscher2020": dict(status="verified", text=(
        "Hirscher M, Yartys VA, Baricco M, Bellosta von Colbe J, Blanchard D, Bowman RC Jr, et al. Materials for "
        "hydrogen-based energy storage – past, recent progress and future outlook. J Alloys Compd. 2020;827:153548. "
        "doi:10.1016/j.jallcom.2019.153548"), note="co-author list after the first author taken from the journal record; check"),
    "broom2011": dict(status="verified", text=(
        "Broom DP. Hydrogen storage materials: the characterisation of their storage properties. London: Springer; 2011. "
        "(Green Energy and Technology). doi:10.1007/978-0-85729-221-6")),
    "vanvucht1970": dict(status="check", text=(
        "van Vucht JHN, et al. Reversible room-temperature absorption of large quantities of hydrogen by intermetallic "
        "compounds. Philips Res Rep. 1970;25:133–40."),
        note="title, journal, volume, pages confirmed (OSTI 4129528); co-authors (Kuijpers, Bruning) not confirmed online"),
    "reilly1974": dict(status="verified", text=(
        "Reilly JJ, Wiswall RH. Formation and properties of iron titanium hydride. Inorg Chem. 1974;13(1):218–22. "
        "doi:10.1021/ic50131a042")),
    "huot1999": dict(status="verified", text=(
        "Huot J, Liang G, Boily S, Van Neste A, Schulz R. Structural study and hydrogen sorption kinetics of ball-milled "
        "magnesium hydride. J Alloys Compd. 1999;293–295:495–500.")),
    "bogdanovic1997": dict(status="verified", text=(
        "Bogdanović B, Schwickardi M. Ti-doped alkali metal aluminium hydrides as potential novel reversible hydrogen "
        "storage materials. J Alloys Compd. 1997;253–254:1–9.")),
    "bogdanovic2000": dict(status="verified", text=(
        "Bogdanović B, Brand R, Marjanović A, et al. Metal-doped sodium aluminium hydrides as potential new hydrogen "
        "storage materials. J Alloys Compd. 2000;302:36–58.")),
    "lundin1977": dict(status="verified", text=(
        "Lundin CE, Lynch FE, Magee CB. A correlation between the interstitial hole sizes in intermetallic compounds and "
        "the thermodynamic properties of the hydrides formed from those compounds. J Less-Common Met. 1977;56(1):19–37.")),
    "zhang2008": dict(status="verified", text=(
        "Zhang Y, Zhou YJ, Lin JP, Chen GL, Liaw PK. Solid-solution phase formation rules for multi-component alloys. "
        "Adv Eng Mater. 2008;10(6):534–8. doi:10.1002/adem.200700240")),
    "ward2016": dict(status="verified", text=(
        "Ward L, Agrawal A, Choudhary A, Wolverton C. A general-purpose machine learning framework for predicting "
        "properties of inorganic materials. npj Comput Mater. 2016;2:16028. doi:10.1038/npjcompumats.2016.28")),
    "ong2013": dict(status="verified", text=(
        "Ong SP, Richards WD, Jain A, Hautier G, Kocher M, Cholia S, et al. Python Materials Genomics (pymatgen): a "
        "robust, open-source python library for materials analysis. Comput Mater Sci. 2013;68:314–9. "
        "doi:10.1016/j.commatsci.2012.10.028")),
    "witman2020": dict(status="verified", text=(
        "Witman M, Ling S, Grant DM, Walker GS, Agarwal S, Stavila V, et al. Extracting an empirical intermetallic "
        "hydride design principle from limited data via interpretable machine learning. J Phys Chem Lett. "
        "2020;11(1):40–7. doi:10.1021/acs.jpclett.9b02971"), note="co-author order after the first author: check against the article"),
    "hydpark2024": dict(status="check", text=(
        "Sandia National Laboratories. ML-HydPARK: machine-learning-ready hydride property database, version 0.0.5 "
        "[dataset]. Zenodo; 2024 Feb 19 [cited 2026 Nov 4]. Available from: https://zenodo.org/records/10680097"),
        note="record, version and date confirmed; exact dataset title and creator list on Zenodo to be copied verbatim"),
    "voskuilen2014": dict(status="verified", text=(
        "Voskuilen TG, Waters EL, Pourpoint TL. A comprehensive approach for alloy selection in metal hydride thermal "
        "systems. Int J Hydrogen Energy. 2014;39:13240–54. doi:10.1016/j.ijhydene.2014.06.119")),
    "purduegit": dict(status="verified", text=(
        "Purdue Hydrogen Systems Laboratory. Metal Hydride Toolbox [software and database, MATLAB]. GitHub "
        "[cited 2026 Nov 4]. Available from: https://github.com/PurdueH2Lab/MetalHydrideToolbox")),
    "breiman2001": dict(status="verified", text=(
        "Breiman L. Random forests. Mach Learn. 2001;45(1):5–32. doi:10.1023/A:1010933404324")),
    "pedregosa2011": dict(status="verified", text=(
        "Pedregosa F, Varoquaux G, Gramfort A, Michel V, Thirion B, Grisel O, et al. Scikit-learn: machine learning in "
        "Python. J Mach Learn Res. 2011;12:2825–30.")),
    "varma2006": dict(status="verified", text=(
        "Varma S, Simon R. Bias in error estimation when using cross-validation for model selection. BMC Bioinformatics. "
        "2006;7:91. doi:10.1186/1471-2105-7-91")),
    "meredig2018": dict(status="verified", text=(
        "Meredig B, Antono E, Church C, Hutchinson M, Ling J, Paradiso S, et al. Can machine learning identify the next "
        "high-temperature superconductor? Examining extrapolation performance for materials discovery. Mol Syst Des Eng. "
        "2018;3(5):819–25. doi:10.1039/C8ME00012C"), note="co-authors after the first author: check against the article"),
}
