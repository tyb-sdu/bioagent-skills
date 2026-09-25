---
name: verify-install
description: Verify that a biological computation tool installed by a reviewed recipe can be invoked and that its environment and source are recorded. Use after an install or when diagnosing a failed install.
license: MIT
compatibility: Requires access to the installed environment or the tool's user-owned binary/container.
---

# Installation verification

Use `python scripts/bioinstall.py verify <id>` for automated conda/Python recipes. For guidance-only routes, run the non-computational smoke test listed in the catalog and compare output with the maintainer's current instructions. Record actual version, executable path, host platform, source link, environment name, and any first-run downloads still pending. If verification fails, report the failed command; do not mark installation complete.

An import, `--version`, or `--help` check establishes basic operability only. A scientific benchmark, force-field validation, or model-quality test is a separate research workflow. Preserve the install receipt and logs needed to reproduce or diagnose the environment. Do not delete existing environments as a troubleshooting shortcut.
