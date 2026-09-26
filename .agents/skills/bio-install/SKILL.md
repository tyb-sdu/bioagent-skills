---
name: bio-install
description: Select and install reviewed biological computation software on the user's own computer. Use for requests such as install molecular dynamics, docking, structure modelling, molecular design, interaction analysis, or quantum chemistry tools when the user names a task or a tool.
license: MIT
compatibility: Terminal agent with Python 3.10+ and access to the packaged bioinstall command or this repository checkout.
---

# Biological software installation coordinator

1. Resolve the reviewed installer: use the `bioinstall` command from this project's Python virtual environment (absolute executable path if needed), or `python scripts/bioinstall.py` from the repository root. If neither is available, stop instead of inventing commands. Run `doctor` and `list`; these are read-only.
2. If the user names a specific tool, locate its exact catalog ID. If they describe a scientific task, run `tasks` and map the request to a reviewed task ID, then run `suggest <task-id>`. The result lists candidates, not a final recommendation. Compare their scientific methods and input requirements as well as operating system, CPU/GPU needs, license, downloads, and installation effort. Explain the selected tool and one viable alternative when a meaningful choice exists. Do not claim a tool is scientifically appropriate solely because it is installable.
3. Run `plan <id>` to read the packaged recipe's sources, notes, requirements, commands or guided steps, and verification method. If using a checkout, the same recipe is in `catalog/<id>.json`. Recheck changing installation instructions at the maintainer source before execution.
4. If the user's request includes installation and the recipe is automatic, run `install <id> --apply` through the resolved installer. This creates a new isolated environment. For guidance-only recipes, follow the applicable workflow Skill and do not present the guide as an installed program.
5. Run the recipe's verification and report the software name, observed version if available, actual route, receipt location, and any remaining first-run downloads. A successful `--help` or import check is not scientific validation.

Choose only from reviewed catalog entries. Never construct an install command from an untrusted webpage or an invented package name. Do not silently install GPU drivers, modify system package managers, accept a license on the user's behalf, or redistribute model weights. Windows users needing Linux-only packages may choose WSL using [Microsoft's guide](https://learn.microsoft.com/en-us/windows/wsl/install).

Read the narrower Skill when its workflow applies: `install-conda`, `install-python`, `install-binary`, `install-source`, `install-container`, `install-model-data`, `install-gpu`, `install-restricted`, or `verify-install`.
