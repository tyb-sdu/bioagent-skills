import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bioinstall.py"
SPEC = importlib.util.spec_from_file_location("bioinstall", MODULE_PATH)
bioinstall = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bioinstall)


class CatalogTests(unittest.TestCase):
    def test_conda_batch_launcher_resolves_sibling_native_executable(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-conda-") as directory:
            root = Path(directory) / "Miniforge With Spaces"
            launcher = root / "condabin" / "conda.bat"
            executable = root / "Scripts" / "conda.exe"
            launcher.parent.mkdir(parents=True)
            executable.parent.mkdir()
            launcher.touch()
            executable.touch()
            with patch.object(bioinstall.shutil, "which", side_effect=lambda name: str(launcher) if name == "conda" else None):
                self.assertEqual(bioinstall.conda_executable(), str(executable.resolve()))
                plan = bioinstall.build_plan(bioinstall.load_recipe("openmm"))
            self.assertEqual(plan["commands"][0][0], str(executable.resolve()))
            self.assertEqual(plan["verification_command"][0], str(executable.resolve()))

    def test_orphan_batch_launcher_does_not_enable_installation(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-conda-") as directory:
            launcher = Path(directory) / "condabin" / "conda.bat"
            launcher.parent.mkdir()
            launcher.touch()
            with patch.object(bioinstall.shutil, "which", side_effect=lambda name: str(launcher) if name == "conda" else None):
                self.assertIsNone(bioinstall.conda_executable())
                with self.assertRaises(bioinstall.RecipeError):
                    bioinstall.require_conda()

    def test_environment_probe_uses_resolved_executable_without_shell(self):
        with patch.object(bioinstall, "conda_executable", return_value="C:/Miniforge/Scripts/conda.exe"), patch.object(
            bioinstall.subprocess, "run"
        ) as command:
            command.return_value.stdout = '{"envs": []}'
            self.assertFalse(bioinstall.conda_environment_exists("bio-pdbfixer"))
        self.assertEqual(command.call_args.args[0][0], "C:/Miniforge/Scripts/conda.exe")
        self.assertNotIn("shell", command.call_args.kwargs)

    def test_cli_reports_missing_executable_without_traceback(self):
        with patch.object(bioinstall.sys, "argv", ["bioinstall", "verify", "mdanalysis"]), patch.object(
            bioinstall, "run", side_effect=OSError("test executable is missing")
        ), patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall, "current_python_version", return_value=(3, 12)), contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(bioinstall.main(), 2)
        self.assertIn("Error: test executable is missing", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_catalog_is_valid_and_sourced(self):
        recipes = bioinstall.all_recipes()
        self.assertGreaterEqual(len(recipes), 46)
        for recipe in recipes:
            self.assertTrue(any(source["type"] == "installation" for source in recipe["sources"]))

    def test_coverage_report_separates_workflows_from_software_and_routes(self):
        report = bioinstall.coverage_report()
        self.assertEqual(report["software_count"], 46)
        self.assertEqual(report["automatic_install_count"], 18)
        self.assertEqual(report["guidance_only_count"], 28)
        self.assertEqual(report["task_count"], 62)
        self.assertEqual(report["skill_count"], 10)
        self.assertEqual(len(report["automatic_install_ids"]), report["automatic_install_count"])
        self.assertEqual(len(report["guidance_only_ids"]), report["guidance_only_count"])
        self.assertEqual(set(report["automatic_install_ids"]) & set(report["guidance_only_ids"]), set())
        self.assertIn("ambertools", report["guidance_only_ids"])
        self.assertIn("openbabel", report["automatic_install_ids"])
        self.assertIn("meeko", report["automatic_install_ids"])
        self.assertIn("pdb2pqr", report["automatic_install_ids"])
        self.assertIn("apbs", report["automatic_install_ids"])

    def test_coverage_cli_is_read_only(self):
        with patch.object(bioinstall.sys, "argv", ["bioinstall", "coverage"]), patch.object(
            bioinstall, "run"
        ) as run_command, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(bioinstall.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["software_count"], 46)
        run_command.assert_not_called()

    def test_task_suggestions_are_read_only_and_include_platform_state(self):
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "run"
        ) as run_command:
            result = bioinstall.suggest_recipes("protein-nucleic-acid-docking")
        self.assertEqual(result["task"], "protein-nucleic-acid-docking")
        self.assertEqual([item["id"] for item in result["candidates"]], ["haddock3"])
        self.assertFalse(result["candidates"][0]["supported_here"])
        self.assertFalse(result["candidates"][0]["ready_here"])
        run_command.assert_not_called()

    def test_windows_arm64_is_not_reported_as_ready_for_win64_conda_build(self):
        recipe = bioinstall.load_recipe("openmm")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="aarch64"
        ), patch.object(bioinstall.shutil, "which", return_value="conda"):
            plan = bioinstall.build_plan(recipe)
        self.assertFalse(plan["supported_here"])
        self.assertFalse(plan["ready_here"])
        self.assertIn("Architecture", plan["blocking_reasons"][0])

    def test_missing_conda_is_distinct_from_unsupported_platform(self):
        recipe = bioinstall.load_recipe("openmm")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall.shutil, "which", return_value=None):
            plan = bioinstall.build_plan(recipe)
        self.assertTrue(plan["supported_here"])
        self.assertFalse(plan["ready_here"])
        self.assertIn("conda executable is unavailable", plan["blocking_reasons"][0])

    def test_pinned_mdanalysis_requires_python_311(self):
        recipe = bioinstall.load_recipe("mdanalysis")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall, "current_python_version", return_value=(3, 10)):
            plan = bioinstall.build_plan(recipe)
            with self.assertRaises(bioinstall.RecipeError), contextlib.redirect_stdout(io.StringIO()):
                bioinstall.install_recipe(recipe, apply=True)
        self.assertFalse(plan["supported_here"])
        self.assertFalse(plan["ready_here"])
        self.assertIn("Python 3.11+", plan["blocking_reasons"][0])

    def test_unreviewed_future_python_wheel_is_not_assumed_available(self):
        recipe = bioinstall.load_recipe("mdanalysis")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall, "current_python_version", return_value=(3, 15)):
            plan = bioinstall.build_plan(recipe)
        self.assertFalse(plan["supported_here"])
        self.assertIn("No reviewed wheel", plan["blocking_reasons"][0])

    def test_pdbfixer_has_reviewed_conda_route(self):
        recipe = bioinstall.load_recipe("pdbfixer")
        self.assertTrue(recipe["install"]["automatic"])
        self.assertEqual(recipe["install"]["package"], "pdbfixer=1.12")
        plan = bioinstall.build_plan(recipe)
        self.assertEqual(plan["commands"][0][-1], "pdbfixer=1.12")

    def test_freesasa_is_linux_macos_only_and_propka_is_pinned_python(self):
        freesasa = bioinstall.load_recipe("freesasa")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ):
            plan = bioinstall.build_plan(freesasa)
        self.assertFalse(plan["supported_here"])
        self.assertNotIn("commands", plan)
        self.assertEqual(freesasa["install"]["package"], "freesasa-c=2.1.2")
        propka = bioinstall.load_recipe("propka")
        self.assertEqual(propka["install"]["package"], "propka==3.5.1")
        self.assertEqual(propka["verify"]["argv"], ["python", "-m", "propka", "--help"])

    def test_electrostatics_tools_use_pinned_isolated_routes(self):
        pdb2pqr = bioinstall.load_recipe("pdb2pqr")
        self.assertEqual(pdb2pqr["install"]["package"], "pdb2pqr==3.7.1")
        self.assertEqual(pdb2pqr["verify"]["argv"], ["python", "-m", "pdb2pqr", "--help"])
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall, "current_python_version", return_value=(3, 14)):
            plan = bioinstall.build_plan(pdb2pqr)
        self.assertFalse(plan["supported_here"])
        self.assertNotIn("commands", plan)
        apbs = bioinstall.load_recipe("apbs")
        self.assertEqual(apbs["install"]["package"], "apbs=3.4.1")
        self.assertEqual(apbs["verify"]["argv"][0], "python")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall.shutil, "which", return_value="conda"):
            plan = bioinstall.build_plan(apbs)
        self.assertTrue(plan["ready_here"])
        self.assertEqual(plan["commands"][0][-1], "apbs=3.4.1")

    def test_new_conda_routes_are_pinned_and_platform_reviewed(self):
        expected = {
            "openbabel": ("openbabel=3.2.1", "obabel"),
            "meeko": ("meeko=0.8.0", "python"),
            "mdtraj": ("mdtraj=1.11.1", "python"),
            "parmed": ("parmed=4.3.1", "python"),
            "gemmi": ("gemmi=0.7.5", "python"),
            "prolif": ("prolif=2.1.0", "python"),
            "openmmforcefields": ("openmmforcefields=0.16.0", "python"),
            "apbs": ("apbs=3.4.1", "python"),
        }
        for tool_id, (package, executable) in expected.items():
            with self.subTest(tool_id=tool_id):
                recipe = bioinstall.load_recipe(tool_id)
                self.assertTrue(recipe["install"]["automatic"])
                self.assertEqual(recipe["install"]["package"], package)
                self.assertEqual(recipe["verify"]["argv"][0], executable)
                if tool_id == "openmmforcefields":
                    self.assertNotIn("windows", recipe["install"]["platforms"])
                else:
                    self.assertEqual(recipe["install"]["architectures"]["windows"], ["x86_64"])

    def test_openmmforcefields_windows_is_guidance_only_after_failed_runner_install(self):
        recipe = bioinstall.load_recipe("openmmforcefields")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall.shutil, "which", return_value="conda"), patch.object(
            bioinstall, "run"
        ) as run_command, contextlib.redirect_stdout(io.StringIO()):
            plan = bioinstall.build_plan(recipe)
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(recipe, apply=True)
        self.assertFalse(plan["supported_here"])
        self.assertTrue(plan["manual_fallback_here"])
        self.assertNotIn("commands", plan)
        run_command.assert_not_called()

    def test_vina_windows_shows_manual_fallback_but_cannot_auto_apply(self):
        recipe = bioinstall.load_recipe("autodock-vina")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall.shutil, "which", return_value="conda"), patch.object(
            bioinstall, "run"
        ) as run_command:
            plan = bioinstall.build_plan(recipe)
            with self.assertRaises(bioinstall.RecipeError), contextlib.redirect_stdout(io.StringIO()):
                bioinstall.install_recipe(recipe, apply=True)
        self.assertFalse(plan["supported_here"])
        self.assertTrue(plan["manual_fallback_here"])
        self.assertIn("manual_fallback", plan)
        self.assertNotIn("commands", plan)
        run_command.assert_not_called()

    def test_unknown_task_does_not_resolve_to_arbitrary_package(self):
        with self.assertRaises(bioinstall.RecipeError):
            bioinstall.suggest_recipes("some-unreviewed-task")

    def test_automatic_recipes_use_isolated_environments(self):
        for recipe in bioinstall.all_recipes():
            plan = bioinstall.build_plan(recipe)
            if not plan["automatic"]:
                self.assertNotIn("commands", plan)
                continue
            if not plan["supported_here"]:
                self.assertNotIn("commands", plan)
                continue
            self.assertIn("=", recipe["install"]["package"])
            commands = plan["commands"]
            self.assertTrue(commands)
            self.assertTrue(all(isinstance(command, list) for command in commands))
            self.assertNotIn("sudo", json.dumps(commands))
            self.assertNotIn("curl", json.dumps(commands))
            self.assertNotIn("--user", json.dumps(commands))
            self.assertTrue(plan["verification_command"])

    def test_preview_never_executes_commands(self):
        recipe = bioinstall.load_recipe("openmm")
        with patch.object(bioinstall, "run") as run_command, patch.object(
            bioinstall, "write_receipt"
        ) as write_receipt, contextlib.redirect_stdout(io.StringIO()):
            bioinstall.install_recipe(recipe, apply=False)
        run_command.assert_not_called()
        write_receipt.assert_not_called()

    def test_guidance_only_recipe_cannot_apply(self):
        recipe = bioinstall.load_recipe("alphafold3")
        with patch.object(bioinstall, "current_platform", return_value="linux"), contextlib.redirect_stdout(
            io.StringIO()
        ):
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(recipe, apply=True)

    def test_reject_existing_conda_environment(self):
        recipe = bioinstall.load_recipe("openmm")
        with patch.object(bioinstall, "shutil") as fake_shutil, patch.object(
            bioinstall, "conda_environment_exists", return_value=True
        ), patch.object(bioinstall, "run") as run_command, contextlib.redirect_stdout(io.StringIO()):
            fake_shutil.which.return_value = "conda"
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(recipe, apply=True)
        run_command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
