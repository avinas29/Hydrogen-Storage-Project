# Introduction

## Background

Hydrogen can carry energy from electrolysers, industrial processes and renewable generation to fuel cells, engines and chemical plants, but it is difficult to store. Its lower heating value is high per unit mass (119.96 MJ kg⁻¹), whereas its density at ambient conditions is very low. Practical storage therefore has to raise the density, either by compressing the gas to several hundred bar, by liquefying it near 20 K, or by binding it to a solid [@schlapbach2001; @zuttel2003]. Compression and liquefaction are mature, but they cost energy, need heavy pressure vessels or cryogenic insulation, and involve safety measures that limit where storage can be placed.

Metal hydrides take the third route. Many metals and intermetallic compounds absorb hydrogen reversibly: hydrogen molecules dissociate at the surface, and the atoms occupy interstitial sites of the metal lattice. The resulting hydride can hold more hydrogen per unit volume than liquid hydrogen. It releases the hydrogen again at a defined equilibrium pressure when heat is supplied [@sandrock1999; @sakintuna2007]. The storage pressure is moderate, often a few bar, and the hydrogen is released only as fast as heat reaches the bed, which is an inherent safety advantage. The disadvantage is mass. Interstitial hydrides of transition-metal alloys hold about 1–2 wt% hydrogen, far below the U.S. Department of Energy (DOE) 2025 target for an onboard vehicle *system* of 5.5 wt% (1.8 kWh kg⁻¹) [@doe2017]. Light hydrides such as MgH₂ hold more but must be heated to around 300 °C. Metal hydrides are therefore most attractive where volume, pressure or safety matter more than mass, as in stationary buffers, forklifts and other industrial vehicles, and systems that can use waste heat [@hirscher2020].

## Why composition and thermodynamics matter

Whether a hydride suits an application is decided mainly by two numbers: the enthalpy ΔH and the entropy ΔS of the decomposition reaction. Through the Van't Hoff relation (Chapter 2) they set the plateau pressure at each temperature, the temperature needed to deliver hydrogen at a given pressure, and the heat that must be supplied on desorption and removed on absorption. ΔS varies relatively little between hydrides, so ΔH effectively decides the operating temperature. For the Purdue materials analysed in this work the median ΔS is 110.6 J mol⁻¹ K⁻¹ (interquartile range 102.8–118.9). A change of 5 kJ mol⁻¹ in ΔH changes the plateau pressure at 25 °C by a factor of about 7.5 (exp[5000/(8.314 × 298)]).

ΔH depends strongly on composition. Substituting Al or Sn for part of the Ni in LaNi₅, or Mn for Fe in TiFe, shifts the plateau by orders of magnitude, and the large AB₂ Laves-phase family is tuned almost entirely through Ti/Zr and Cr/Mn/V/Fe ratios [@sandrock1999]. The number of possible compositions is very large. Measuring each one requires synthesis, activation and pressure–composition isotherms at several temperatures. A model that estimates ΔH from composition, together with an honest estimate of its error, could narrow the search to the compositions worth measuring.

Two public datasets make such a model possible: the Metal Hydride Toolbox of the Purdue Hydrogen Systems Laboratory [@voskuilen2014; @purduegit] and ML-HydPARK, a machine-learning version of the hydride database collected at Sandia National Laboratories [@witman2020; @hydpark2024]. Both are compilations of literature values, so their quality, units and overlap must be established before any model is trained.

## Problem statement

The task is to go from an alloy composition to a defensible statement about whether that alloy suits a given storage application. This requires (i) a clean, documented dataset in which measured, derived and missing values are distinguished; (ii) a ΔH predictor whose accuracy is measured honestly and whose range of validity is known; (iii) a transparent conversion from thermodynamic data to operating windows and heat demand; and (iv) a screening method that states which requirements a material meets, which it fails, and which cannot be assessed with the available data. @fig:workflow shows how these parts connect in this project.

FIG workflow | report/figures/f_workflow.png | 16 | Project workflow. The ML model predicts ΔH only; experimental ΔH and ΔS are used whenever they exist.

## Objectives

The objectives of the project were to:

- audit the Purdue Metal Hydride Toolbox and ML-HydPARK, document their conventions and quality problems, and build a composition-level ΔH dataset without converting missing values into measured ones;
- develop a composition-based model for ΔH, validate it with grouped and nested cross-validation against simple baselines, and quantify its uncertainty and applicability domain;
- compute Van't Hoff operating windows, reaction heats and related quantities for the experimental materials, and check them against the digitised isotherms;
- screen the experimental materials against mobile and stationary requirements with explicit constraints, weights and sensitivity analysis;
- implement the model and the screening in an interactive software platform; and
- propose, but not perform, a synthesis and characterisation programme that would test the results.

## Scope and limitations

This is a computational project. All property values come from the two public datasets. No alloy was synthesised and no measurement was made, so the experimental plan in Chapter 8 is a proposal only. The ML model predicts ΔH alone; wherever an operating window is estimated from a predicted ΔH, the entropy is an assumed family median. All capacities are material-level values reported in the literature, with definitions that are not uniform. They are not system capacities, and no volumetric capacity is estimated where a density is not stated. Cost and kinetics enter the screening only as qualitative classes.

## Organisation of the report

Chapter 2 reviews the physics of hydrogen absorption, the main hydride families, and the use of machine learning for materials properties. Chapter 3 describes the datasets, the audit, the construction of the modelling dataset, the composition descriptors and the validation design. Chapter 4 presents the development and evaluation of the ΔH model, including its applicability domain. Chapter 5 applies the Van't Hoff relation to the experimental data. Chapter 6 describes the application-specific screening and the software platform built around it. Chapter 7 presents and discusses the main results, and Chapter 8 gives the conclusions and the proposed future work. The appendices list the descriptors, additional results and the proposed characterisation matrix.
