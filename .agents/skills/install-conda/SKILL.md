---
name: install-conda
description: Install a reviewed computational biology or chemistry package from conda-forge in a new isolated environment. Use when a catalog recipe has install.kind conda, including OpenMM, RDKit, GROMACS, and Psi4.
license: MIT
compatibility: Requires conda on PATH; package platform must match the host.
---

# Conda installation

Use the reviewed `bioinstall` command from this project's virtual environment, or `python scripts/bioinstall.py` from the repository root. Run `doctor` and `plan <id>` first to read the exact catalog recipe. Inspect the requested package, host platform, and selected channel. The shared installer calls `conda create` with an environment name unique to the tool and a per-command `conda-forge` channel override; it does not edit `.condarc` or the base environment.

For an explicit installation request, run `install <id> --apply` through the resolved installer. If the environment name already exists or the solver fails, stop and report the conflict. Do not remove or overwrite an existing environment as an automatic repair. After installation, run `verify <id>` and record the resolved package version and platform in the handoff. The current receipt stores commands and verification status; exact dependency lock export is future work.

Conda's [channel guidance](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-channels.html) explains priority and mixing risks. For Bioconda recipes added later, consult its [platform and channel instructions](https://bioconda.github.io/) rather than assuming Windows support.
