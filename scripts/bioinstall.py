#!/usr/bin/env python3
"""Small, dependency-free installer helper for the reviewed BioAgent recipes.

The default commands inspect and plan. `install --apply` is required for writes.
Only isolated conda and Python environments are executable in this release.
"""

from __future__ import annotations

import argparse
from importlib import resources
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = resources.files("bioagent_skills.catalog") if __package__ == "bioagent_skills" else ROOT / "catalog"
INSTALL_ROOT = Path.home() / ".bioagent-skills"
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PACKAGE_PATTERN = re.compile(r"^[A-Za-z0-9_.+\[\],=<>!~-]+$")
KINDS = {"conda", "python", "binary", "source", "container", "model-data", "restricted"}
PLATFORMS = {"linux", "macos", "windows"}
ARCHITECTURES = {"x86_64", "aarch64", "ppc64le"}


class RecipeError(ValueError):
    pass


def current_platform() -> str:
    return {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}.get(
        platform.system(), "unsupported"
    )


def current_architecture() -> str:
    machine = platform.machine().casefold()
    return {
        "amd64": "x86_64", "x64": "x86_64", "x86_64": "x86_64",
        "arm64": "aarch64", "aarch64": "aarch64", "ppc64le": "ppc64le",
    }.get(machine, machine)


def current_python_version() -> tuple[int, int]:
    return sys.version_info[:2]


def target_status(recipe: dict) -> dict:
    """Report known local blockers, not a guarantee that solving will succeed."""
    install = recipe["install"]
    reasons = []
    system = current_platform()
    architecture = current_architecture()
    if system not in install["platforms"]:
        reasons.append(f"Operating system {system} is not in the reviewed platforms")
    elif "architectures" in install and architecture not in install["architectures"].get(system, []):
        reasons.append(f"Architecture {architecture} is not reviewed for {system}")
    if install["kind"] == "python" and install["automatic"]:
        minimum = tuple(map(int, install["min_python"].split(".")))
        version = current_python_version()
        if version < minimum:
            reasons.append(f"Python {install['min_python']}+ is required for this pinned package")
        elif f"{version[0]}.{version[1]}" not in install["python_versions"]:
            reasons.append("No reviewed wheel for Python " + f"{version[0]}.{version[1]}")
    supported = not reasons
    if not install["automatic"]:
        reasons.append("This recipe is guidance-only")
    elif install["kind"] == "conda" and not shutil.which("conda"):
        reasons.append("conda is not on PATH")
    fallback = install.get("manual_fallback", {})
    return {
        "supported_here": supported,
        "ready_here": not reasons,
        "blocking_reasons": reasons,
        "manual_fallback_here": system in fallback.get("platforms", []),
    }


def validate_recipe(recipe: dict, path) -> None:
    required = ("id", "name", "summary", "tasks", "install", "verify", "sources")
    missing = [key for key in required if key not in recipe]
    if missing:
        raise RecipeError(f"{path.name}: missing {', '.join(missing)}")
    if not isinstance(recipe["id"], str) or not ID_PATTERN.fullmatch(recipe["id"]):
        raise RecipeError(f"{path.name}: invalid id")
    if Path(path.name).stem != recipe["id"]:
        raise RecipeError(f"{path.name}: filename must match id")
    if "aliases" in recipe and (
        not isinstance(recipe["aliases"], list)
        or not all(isinstance(alias, str) and alias.strip() and len(alias) <= 100 for alias in recipe["aliases"])
    ):
        raise RecipeError(f"{path.name}: aliases must be a list of nonempty names")
    if not isinstance(recipe["tasks"], list) or not recipe["tasks"] or not all(
        isinstance(task, str) and ID_PATTERN.fullmatch(task) for task in recipe["tasks"]
    ):
        raise RecipeError(f"{path.name}: tasks must be a nonempty list of task IDs")
    install = recipe["install"]
    if not isinstance(install, dict) or install.get("kind") not in KINDS:
        raise RecipeError(f"{path.name}: unsupported install kind")
    if not isinstance(install.get("platforms"), list) or not set(install["platforms"]) <= PLATFORMS:
        raise RecipeError(f"{path.name}: invalid platforms")
    if not install["platforms"]:
        raise RecipeError(f"{path.name}: platforms cannot be empty")
    architectures = install.get("architectures")
    if install.get("automatic") or architectures is not None:
        if not isinstance(architectures, dict) or set(architectures) != set(install["platforms"]):
            raise RecipeError(f"{path.name}: architectures must cover every listed platform")
        if not all(
            isinstance(values, list) and values and set(values) <= ARCHITECTURES
            for values in architectures.values()
        ):
            raise RecipeError(f"{path.name}: invalid architecture list")
    if not isinstance(install.get("automatic"), bool):
        raise RecipeError(f"{path.name}: automatic must be boolean")
    if install["automatic"] and install["kind"] not in {"conda", "python"}:
        raise RecipeError(f"{path.name}: this install kind is guidance-only")
    if install["automatic"]:
        package = install.get("package")
        environment = install.get("environment")
        if not isinstance(package, str) or not PACKAGE_PATTERN.fullmatch(package):
            raise RecipeError(f"{path.name}: invalid package spec")
        if not isinstance(environment, str) or not ID_PATTERN.fullmatch(environment):
            raise RecipeError(f"{path.name}: invalid environment name")
        if install["kind"] == "conda" and install.get("channel") != "conda-forge":
            raise RecipeError(f"{path.name}: automated conda channel must be conda-forge")
        if install["kind"] == "python" and not re.fullmatch(r"3\.[0-9]{1,2}", install.get("min_python", "")):
            raise RecipeError(f"{path.name}: automated Python package needs min_python")
        if install["kind"] == "python" and (
            not isinstance(install.get("python_versions"), list)
            or not install["python_versions"]
            or not all(isinstance(value, str) and re.fullmatch(r"3\.[0-9]{1,2}", value) for value in install["python_versions"])
        ):
            raise RecipeError(f"{path.name}: automated Python package needs reviewed python_versions")
        fallback = install.get("manual_fallback")
        if fallback is not None and (
            not isinstance(fallback, dict)
            or not isinstance(fallback.get("platforms"), list)
            or not fallback["platforms"]
            or not set(fallback["platforms"]) <= PLATFORMS
            or not isinstance(fallback.get("steps"), list)
            or not fallback["steps"]
            or not all(isinstance(step, str) and step.strip() for step in fallback["steps"])
            or not isinstance(fallback.get("verify_note"), str)
            or not fallback["verify_note"].strip()
        ):
            raise RecipeError(f"{path.name}: invalid manual_fallback")
    elif not isinstance(install.get("steps"), list) or not install["steps"] or not all(
        isinstance(step, str) and step.strip() for step in install["steps"]
    ):
        raise RecipeError(f"{path.name}: guidance-only recipe needs nonempty steps")
    verify = recipe["verify"]
    if not isinstance(verify, dict) or not isinstance(verify.get("argv"), list):
        raise RecipeError(f"{path.name}: verify.argv must be a list")
    if not all(isinstance(arg, str) and arg for arg in verify["argv"]):
        raise RecipeError(f"{path.name}: verify.argv must contain nonempty strings")
    if install["automatic"] and not verify["argv"]:
        raise RecipeError(f"{path.name}: automatic recipe needs a verification command")
    if not isinstance(recipe["sources"], list) or not recipe["sources"]:
        raise RecipeError(f"{path.name}: at least one source is required")
    for source in recipe["sources"]:
        if not isinstance(source, dict) or not str(source.get("url", "")).startswith("https://"):
            raise RecipeError(f"{path.name}: each source needs an HTTPS URL")


def load_recipe(tool_id: str) -> dict:
    if not ID_PATTERN.fullmatch(tool_id):
        raise RecipeError("Invalid tool id")
    path = CATALOG.joinpath(f"{tool_id}.json")
    if not path.is_file():
        raise RecipeError(f"Unknown tool: {tool_id}")
    recipe = json.loads(path.read_text(encoding="utf-8"))
    validate_recipe(recipe, path)
    return recipe


def all_recipes() -> list[dict]:
    paths = sorted(
        (path for path in CATALOG.iterdir() if path.name.endswith(".json")),
        key=lambda path: path.name,
    )
    return [load_recipe(Path(path.name).stem) for path in paths]


def all_tasks() -> list[str]:
    return sorted({task for recipe in all_recipes() for task in recipe["tasks"]})


def suggest_recipes(task: str) -> dict:
    """Return task-matched candidates; this is not a scientific recommendation."""
    if task not in all_tasks():
        raise RecipeError(f"Unknown task: {task}. Run 'tasks' to see reviewed task IDs")
    candidates = []
    for recipe in all_recipes():
        if task not in recipe["tasks"]:
            continue
        install = recipe["install"]
        status = target_status(recipe)
        candidates.append({
            "id": recipe["id"],
            "name": recipe["name"],
            "summary": recipe["summary"],
            "kind": install["kind"],
            "automatic": install["automatic"],
            **status,
        })
    candidates.sort(key=lambda item: (not item["supported_here"], item["id"]))
    return {
        "task": task,
        "candidates": candidates,
        "warning": "Task matching does not establish scientific suitability. Review inputs, methods, license, hardware, and plan before installing.",
    }


def env_python(environment: str) -> Path:
    base = INSTALL_ROOT / "envs" / environment
    return base / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def resolve_verify(recipe: dict) -> list[str]:
    install = recipe["install"]
    argv = recipe["verify"]["argv"]
    if not argv:
        return []
    if install["kind"] == "conda":
        return ["conda", "run", "--name", install["environment"], *argv]
    if install["kind"] == "python":
        executable = str(env_python(install["environment"]))
        if argv[0] != "python":
            raise RecipeError("Automated Python verification must start with python")
        return [executable, *argv[1:]]
    return argv


def build_plan(recipe: dict) -> dict:
    install = recipe["install"]
    status = target_status(recipe)
    result = {
        "id": recipe["id"],
        "name": recipe["name"],
        "kind": install["kind"],
        **status,
        "automatic": install["automatic"],
        "sources": recipe["sources"],
        "notes": recipe.get("notes", []),
    }
    if not status["ready_here"] and status["manual_fallback_here"]:
        result["manual_fallback"] = install["manual_fallback"]
    if not install["automatic"]:
        result["steps"] = install["steps"]
        result["verify"] = install.get("verify_note", "Follow the official verification instructions.")
        return result
    if not status["supported_here"]:
        return result
    if install["kind"] == "conda":
        result["commands"] = [[
            "conda", "create", "--yes", "--name", install["environment"],
            "--override-channels", "--channel", install["channel"],
            "--strict-channel-priority", install["package"],
        ]]
    else:
        python = env_python(install["environment"])
        base = python.parent.parent
        result["commands"] = [
            [sys.executable, "-m", "venv", str(base)],
            [str(python), "-m", "pip", "install", install["package"]],
        ]
    result["verification_command"] = resolve_verify(recipe)
    return result


def run(argv: list[str]) -> None:
    subprocess.run(argv, check=True)


def conda_environment_exists(environment: str) -> bool:
    result = subprocess.run(
        ["conda", "env", "list", "--json"], check=True, capture_output=True, text=True
    )
    environments = json.loads(result.stdout).get("envs", [])
    return any(Path(prefix).name.lower() == environment.lower() for prefix in environments)


def installed_version(recipe: dict) -> str | None:
    install = recipe["install"]
    package = re.split(r"[=<>!~\[]", install["package"], maxsplit=1)[0]
    try:
        if install["kind"] == "conda":
            result = subprocess.run(
                ["conda", "list", "--name", install["environment"], "--json"],
                check=True, capture_output=True, text=True,
            )
            packages = json.loads(result.stdout)
            matches = [item["version"] for item in packages if item.get("name", "").lower() == package.lower()]
            return matches[0] if matches else None
        result = subprocess.run(
            [str(env_python(install["environment"])), "-m", "pip", "show", package],
            check=True, capture_output=True, text=True,
        )
        for line in result.stdout.splitlines():
            if line.startswith("Version: "):
                return line.partition(": ")[2]
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError):
        return None
    return None


def write_receipt(recipe: dict, plan: dict) -> Path:
    receipts = INSTALL_ROOT / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    installed_at = datetime.now(timezone.utc)
    stamp = installed_at.strftime("%Y%m%dT%H%M%S%fZ")
    path = receipts / f"{recipe['id']}-{stamp}.json"
    record = {
        "id": recipe["id"],
        "installed_at_utc": installed_at.isoformat(),
        "platform": current_platform(),
        "commands": plan["commands"],
        "verification_command": plan["verification_command"],
        "package_version": installed_version(recipe),
        "sources": recipe["sources"],
        "result": "verified",
    }
    with path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    return path


def install_recipe(recipe: dict, apply: bool) -> None:
    plan = build_plan(recipe)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not apply:
        print("Preview only. Pass --apply to install into a new isolated environment.")
        return
    if not plan["automatic"]:
        raise RecipeError("This recipe provides reviewed guidance; automated installation is not available")
    if not plan["ready_here"]:
        raise RecipeError("Local prerequisites are not met: " + "; ".join(plan["blocking_reasons"]))
    install = recipe["install"]
    if install["kind"] == "conda":
        if not shutil.which("conda"):
            raise RecipeError("conda is not on PATH")
        if conda_environment_exists(install["environment"]):
            raise RecipeError(f"Conda environment already exists: {install['environment']}")
    else:
        target = env_python(install["environment"]).parent.parent
        if target.exists():
            raise RecipeError(f"Target environment already exists: {target}")
    for command in plan["commands"]:
        run(command)
    run(plan["verification_command"])
    receipt = write_receipt(recipe, plan)
    print(f"Verified. Receipt: {receipt}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan reviewed biological software installations")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List curated software recipes")
    sub.add_parser("tasks", help="List reviewed research-task IDs")
    sub.add_parser("validate", help="Validate all catalog entries")
    sub.add_parser("doctor", help="Inspect local prerequisites without changing them")
    suggestion = sub.add_parser("suggest", help="Show read-only candidates for a reviewed task ID")
    suggestion.add_argument("task_id")
    for command in ("plan", "install", "verify"):
        subparser = sub.add_parser(command)
        subparser.add_argument("tool_id")
        if command == "install":
            subparser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "list":
            for recipe in all_recipes():
                install = recipe["install"]
                print(f"{recipe['id']:<18} {install['kind']:<12} {'auto' if install['automatic'] else 'guide':<5} {recipe['name']}")
        elif args.command == "tasks":
            for task in all_tasks():
                print(task)
        elif args.command == "suggest":
            print(json.dumps(suggest_recipes(args.task_id), ensure_ascii=False, indent=2))
        elif args.command == "validate":
            recipes = all_recipes()
            print(f"Validated {len(recipes)} recipes")
        elif args.command == "doctor":
            data = {
                "platform": current_platform(),
                "architecture": platform.machine(),
                "normalized_architecture": current_architecture(),
                "python": sys.version.split()[0],
                "conda": shutil.which("conda"),
                "docker": shutil.which("docker"),
                "apptainer": shutil.which("apptainer"),
                "cmake": shutil.which("cmake"),
                "nvidia_smi": shutil.which("nvidia-smi"),
                "free_disk_gb": round(shutil.disk_usage(Path.home()).free / 1_000_000_000, 1),
            }
            print(json.dumps(data, ensure_ascii=False, indent=2))
        elif args.command == "plan":
            print(json.dumps(build_plan(load_recipe(args.tool_id)), ensure_ascii=False, indent=2))
        elif args.command == "install":
            install_recipe(load_recipe(args.tool_id), args.apply)
        elif args.command == "verify":
            recipe = load_recipe(args.tool_id)
            plan = build_plan(recipe)
            if not plan["ready_here"]:
                raise RecipeError("Automated verification is not available for this recipe here")
            run(plan["verification_command"])
            print("Verification passed")
    except (RecipeError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
