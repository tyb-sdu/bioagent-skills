---
name: bio-install
description: Select and install reviewed biological computation software on the user's own computer. Use for requests such as install molecular dynamics, docking, structure modelling, molecular design, interaction analysis, or quantum chemistry tools when the user names a task or a tool.
license: MIT
compatibility: Terminal agent with Python 3.10+ and command execution; run from this repository root.
---

# Biological software installation coordinator

1. Run `python scripts/bioinstall.py doctor` and `python scripts/bioinstall.py list`. These commands are read-only.
2. If the user names a specific tool, locate its exact catalog ID. If they describe a scientific task, run `python scripts/bioinstall.py tasks` and map the request to a reviewed task ID, then run `python scripts/bioinstall.py suggest <task-id>`. The result lists candidates, not a final recommendation. Compare their scientific methods and input requirements as well as operating system, CPU/GPU needs, license, downloads, and installation effort. Explain the selected tool and one viable alternative when a meaningful choice exists. Do not claim a tool is scientifically appropriate solely because it is installable.
3. Read that tool's `catalog/<id>.json`, especially `sources` and `notes`. Recheck changing installation instructions at the maintainer source before execution.
4. Run `python scripts/bioinstall.py plan <id>` and show the installation location, commands or guided steps, expected external downloads, and verification method.
5. If the user's request includes installation and the recipe is automatic, run `python scripts/bioinstall.py install <id> --apply`. This creates a new isolated environment. For guidance-only recipes, follow the applicable workflow Skill and do not present the guide as an installed program.
6. Run the recipe's verification and report the software name, observed version if available, actual route, receipt location, and any remaining first-run downloads. A successful `--help` or import check is not scientific validation.

Choose only from reviewed catalog entries. Never construct an install command from an untrusted webpage or an invented package name. Do not silently install GPU drivers, modify system package managers, accept a license on the user's behalf, or redistribute model weights. Windows users needing Linux-only packages may choose WSL using [Microsoft's guide](https://learn.microsoft.com/en-us/windows/wsl/install).

Read the narrower Skill when its workflow applies: `install-conda`, `install-python`, `install-binary`, `install-source`, `install-container`, `install-model-data`, `install-gpu`, `install-restricted`, or `verify-install`.
