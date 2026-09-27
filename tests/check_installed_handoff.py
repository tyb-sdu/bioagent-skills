"""Integration assertion for a disposable runner after a real installation.

Not part of unit-test discovery: it needs the requested recipe already installed.
Only local metadata is read; no scientific tool or arbitrary command is launched.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bioinstall


def check(tool_id: str) -> dict:
    recipe = bioinstall.load_recipe(tool_id)
    plan = bioinstall.usage_plan(recipe)
    status = plan["status"]
    if status["state"] != "package-present" or not status["environment_prefix"]:
        raise RuntimeError("Installed environment was not recognized: " + status["state"])
    if not status["receipt"] or status["receipt_version_matches_current"] is not True:
        raise RuntimeError("Current package version does not match the successful installation receipt")
    argv = plan["invocation_argv"]
    if not argv or not plan["invocation_command"]:
        raise RuntimeError("No installed invocation was provided")
    if recipe["install"]["kind"] == "conda" and (
        argv[:3] != [bioinstall.require_conda(), "run", "--prefix"]
        or argv[3] != status["environment_prefix"]
    ):
        raise RuntimeError("Invocation does not target the observed isolated conda environment")
    return {
        "id": tool_id, "state": status["state"], "package_version": status["package_version"],
        "environment_prefix": status["environment_prefix"],
        "receipt_version_matches_current": status["receipt_version_matches_current"],
        "invocation_argv": argv, "note": "Invocation checked, not executed",
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python tests/check_installed_handoff.py <reviewed-tool-id>")
    print(json.dumps(check(sys.argv[1]), ensure_ascii=False, indent=2))
