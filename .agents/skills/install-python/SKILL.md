---
name: install-python
description: Install a reviewed Python-based molecular modelling or analysis tool in a new virtual environment. Use when a catalog recipe has install.kind python, such as MDAnalysis.
license: MIT
compatibility: Requires Python 3.10+ with venv and pip.
---

# Python package installation

Run `python scripts/bioinstall.py plan <id>` and inspect the package name, Python version, platform, and dependencies. For an explicit installation request, run `python scripts/bioinstall.py install <id> --apply`. The helper creates a fresh virtual environment below the current user's `~/.bioagent-skills/envs/`, invokes pip through that environment's Python executable, and runs the recipe's import or CLI check.

Do not install into the system Python or add `--user` to this workflow. Do not silently upgrade another tool's environment. If the package needs native libraries or model data, route those prerequisites to `install-conda` or `install-model-data` rather than treating a successful pip command as a complete installation. Python's [venv documentation](https://docs.python.org/3/library/venv.html) describes isolation; [MDAnalysis's install guide](https://www.mdanalysis.org/pages/installation_quick_start/) is the first executable example.
