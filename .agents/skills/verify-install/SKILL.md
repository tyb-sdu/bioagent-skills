---
name: verify-install
description: Verify that a biological computation tool installed by a reviewed recipe can be invoked and that its environment and source are recorded. Use after an install or when diagnosing a failed install.
license: MIT
compatibility: Requires access to the installed environment or the tool's user-owned binary/container.
---

# Installation verification

Use `verify <id>` through the reviewed `bioinstall` command (or `python scripts/bioinstall.py` from the repository root) for automated conda/Python recipes. For guidance-only routes, run the non-computational smoke test shown by `plan <id>` and compare output with the maintainer's current instructions. Record actual version, executable path, host platform, source link, environment name, and any first-run downloads still pending. If verification fails, report the failed command; do not mark installation complete.

For an existing installation, start with `status <id>`: it reads package metadata and a bounded historical receipt without running the scientific tool. A receipt is not proof that the environment still exists or passes verification today; a matching version is not a dependency or integrity check. Use `usage <id>` to hand off the detected isolated interpreter or CLI invocation after the package is recognized. It only displays a command, and must not be used to launch a research job without a separate user request. Missing, ambiguous or unconfirmed environments require explanation rather than an automatic reinstall. Never replay commands stored in a receipt.

An import, `--version`, or `--help` check establishes basic operability only. A scientific benchmark, force-field validation, or model-quality test is a separate research workflow. Preserve the install receipt and logs needed to reproduce or diagnose the environment. Do not delete existing environments as a troubleshooting shortcut.
