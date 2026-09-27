# Reviewed software coverage

This is an installation catalog, not a claim that the agent can perform every scientific analysis or install every tool with one click. Each software package has one `catalog/<id>.json` recipe. The 10 Agent Skills describe reusable workflows shared by many recipes. Run `python scripts/bioinstall.py coverage` for live counts, `tasks` for all task labels, and `plan <id>` for a platform-specific assessment.

The table assigns each of the 46 reviewed packages to one primary domain so nothing is double-counted. Many packages support additional tasks; consult their individual recipe. **Auto** means a pinned conda/PyPI route exists for selected OS/architectures, not that this computer is ready or a scientific calculation has been validated. **Guide** means the agent presents reviewed instructions and cannot execute the installation.

| Primary domain | Auto | Guide |
| --- | --- | --- |
| Protein/complex structure prediction | — | AlphaFold 2, AlphaFold 3, Boltz-2, LocalColabFold, RoseTTAFold3 |
| Protein design | — | ProteinMPNN, LigandMPNN, RFdiffusion, RFdiffusion3, Rosetta, PyRosetta |
| Docking and interactions | AutoDock Vina, Meeko, ProLIF | AutoDock-GPU, GNINA, DiffDock, HADDOCK3, LightDock, PLIP |
| Molecular dynamics and free energy | GROMACS, OpenMM, MDAnalysis, MDTraj, OpenMMForceFields | NAMD, AmberTools, OpenFE |
| Structure preparation, electrostatics and surface analysis | RDKit, PDBFixer, PROPKA, FreeSASA, Open Babel, ParmEd, Gemmi, PDB2PQR, APBS | — |
| Nucleic-acid thermodynamics and simulation | — | NUPACK 4, oxDNA |
| Cryo-EM processing and model building | — | RELION, CryoSPARC, ModelAngelo |
| Molecular visualization | — | VMD, UCSF ChimeraX, PyMOL Open Source |
| Quantum chemistry | Psi4 | — |

Read [installation-test boundaries](INSTALL_TESTING.md) before interpreting the automatic routes. Each declared operating-system route of the 18 automatic recipes has a configured installation smoke job, but only a subset of its declared architectures may be tested, and a configured job is not a passing result. Model weights, genetic databases, GPU drivers, commercial permissions, user registration, scientific input preparation, and research computation are not silently supplied by this repository.
