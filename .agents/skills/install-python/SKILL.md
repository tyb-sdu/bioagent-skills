---
name: install-python
description: Install a reviewed Python-based molecular modelling or analysis tool in a new virtual environment. Use when a catalog recipe has install.kind python, such as MDAnalysis.
license: MIT
compatibility: Requires Python 3.10+ with venv and pip.
---

# Python package installation

Use the reviewed `bioinstall` command from this project's virtual environment, or `python scripts/bioinstall.py` from the repository root. Run `plan <id>` and inspect the package name, Python version, platform, and dependencies. For an explicit installation request, run `install <id> --apply` through the resolved installer. The helper creates a fresh virtual environment below the current user's `~/.bioagent-skills/envs/`, invokes pip through that environment's Python executable, and runs the recipe's import or CLI check.

Automatic pip installation is wheel-only, including dependencies. If no compatible wheel exists, report the failed installation and leave any partial environment for inspection; do not retry by compiling source or modifying system libraries. A Python interface may not include the corresponding command-line suite: review the recipe's scope before confirming installation, especially for ViennaRNA.

Do not install into the system Python or add `--user` to this workflow. Do not silently upgrade another tool's environment. If the package needs native libraries or model data, route those prerequisites to `install-conda` or `install-model-data` rather than treating a successful pip command as a complete installation. Python's [venv documentation](https://docs.python.org/3/library/venv.html) describes isolation; [MDAnalysis's install guide](https://www.mdanalysis.org/pages/installation_quick_start/) is the first executable example.
