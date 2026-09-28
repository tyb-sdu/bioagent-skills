import contextlib
import importlib.util
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bioinstall.py"
SPEC = importlib.util.spec_from_file_location("bioinstall", MODULE_PATH)
bioinstall = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bioinstall)


class CatalogTests(unittest.TestCase):
    def test_every_automatic_recipe_platform_has_installation_smoke_job(self):
        workflow = (MODULE_PATH.parents[1] / ".github" / "workflows" / "scientific-smoke.yml").read_text(encoding="utf-8")
        jobs = re.findall(r"^\s*- \{tool: ([a-z0-9-]+), os: (ubuntu-latest|windows-latest|macos-latest|macos-15-intel)\}$", workflow, re.MULTILINE)
        configured = {(tool, "linux" if os_name.startswith("ubuntu") else "windows" if os_name.startswith("windows") else "macos") for tool, os_name in jobs}
        automatic = {
            (recipe["id"], platform)
            for recipe in bioinstall.all_recipes()
            if recipe["install"]["automatic"]
            for platform in recipe["install"]["platforms"]
        }
        self.assertEqual(automatic, configured)
        self.assertIn(("prody", "macos-15-intel"), jobs)

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
        self.assertGreaterEqual(len(recipes), 63)
        for recipe in recipes:
            self.assertTrue(any(source["type"] == "installation" for source in recipe["sources"]))

    def test_coverage_report_separates_workflows_from_software_and_routes(self):
        report = bioinstall.coverage_report()
        self.assertEqual(report["software_count"], 63)
        self.assertEqual(report["automatic_install_count"], 26)
        self.assertEqual(report["guidance_only_count"], 37)
        self.assertEqual(report["task_count"], 79)
        self.assertEqual(report["skill_count"], 10)
        self.assertEqual(len(report["automatic_install_ids"]), report["automatic_install_count"])
        self.assertEqual(len(report["guidance_only_ids"]), report["guidance_only_count"])
        self.assertEqual(set(report["automatic_install_ids"]) & set(report["guidance_only_ids"]), set())
        self.assertIn("ambertools", report["guidance_only_ids"])
        self.assertIn("openbabel", report["automatic_install_ids"])
        self.assertIn("meeko", report["automatic_install_ids"])
        self.assertIn("pdb2pqr", report["automatic_install_ids"])
        self.assertIn("apbs", report["automatic_install_ids"])
        self.assertIn("fpocket", report["automatic_install_ids"])
        self.assertIn("p2rank", report["guidance_only_ids"])
        self.assertIn("smina", report["automatic_install_ids"])
        self.assertIn("binana", report["guidance_only_ids"])
        self.assertIn("dssp", report["automatic_install_ids"])
        self.assertIn("molprobity", report["guidance_only_ids"])
        self.assertIn("viennarna", report["automatic_install_ids"])
        self.assertIn("rnastructure", report["guidance_only_ids"])
        self.assertIn("biotite", report["automatic_install_ids"])
        self.assertIn("peptidebuilder", report["automatic_install_ids"])
        self.assertIn("prody", report["automatic_install_ids"])
        self.assertIn("pdb-tools", report["automatic_install_ids"])
        for tool_id in ("coot", "phenix"):
            self.assertIn(tool_id, report["guidance_only_ids"])
        for tool_id in ("usalign", "tmalign", "modeller"):
            self.assertIn(tool_id, report["guidance_only_ids"])

    def test_coverage_cli_is_read_only(self):
        with patch.object(bioinstall.sys, "argv", ["bioinstall", "coverage"]), patch.object(
            bioinstall, "run"
        ) as run_command, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(bioinstall.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["software_count"], 63)

    def test_pdb_tools_route_is_pinned_and_checks_local_chain_selection(self):
        recipe = bioinstall.load_recipe("pdb-tools")
        self.assertEqual(recipe["install"]["package"], "pdb-tools==2.7.0")
        self.assertEqual(set(recipe["install"]["platforms"]), {"linux", "macos", "windows"})
        self.assertIn("pdb_selchain", recipe["verify"]["argv"][-1])
        self.assertNotIn("https://", recipe["verify"]["argv"][-1])

    def test_graphical_model_building_and_restricted_refinement_are_guidance_only(self):
        for tool_id in ("coot", "phenix"):
            recipe = bioinstall.load_recipe(tool_id)
            self.assertFalse(recipe["install"]["automatic"])
            with patch.object(bioinstall, "run") as command, contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(bioinstall.RecipeError):
                    bioinstall.install_recipe(recipe, apply=True)
            command.assert_not_called()
        self.assertEqual(bioinstall.load_recipe("phenix")["install"]["kind"], "restricted")

    def test_prody_route_is_limited_to_reviewed_conda_platforms(self):
        recipe = bioinstall.load_recipe("prody")
        self.assertEqual(recipe["install"]["package"], "prody=2.6.1")
        self.assertEqual(set(recipe["install"]["platforms"]), {"linux", "macos"})
        self.assertIn("buildKirchhoff", recipe["verify"]["argv"][-1])
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall, "run") as command, contextlib.redirect_stdout(io.StringIO()):
            plan = bioinstall.build_plan(recipe)
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(recipe, apply=True)
        self.assertFalse(plan["supported_here"])
        self.assertTrue(plan["manual_fallback_here"])
        command.assert_not_called()

    def test_classic_alignment_and_licensed_modeling_are_guidance_only(self):
        for tool_id in ("usalign", "tmalign", "modeller"):
            recipe = bioinstall.load_recipe(tool_id)
            self.assertFalse(recipe["install"]["automatic"])
            with patch.object(bioinstall, "run") as command, contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(bioinstall.RecipeError):
                    bioinstall.install_recipe(recipe, apply=True)
            command.assert_not_called()
        self.assertEqual(bioinstall.load_recipe("modeller")["install"]["kind"], "restricted")

    def test_biotite_structure_superposition_is_pinned_and_local(self):
        recipe = bioinstall.load_recipe("biotite")
        self.assertEqual(recipe["install"]["package"], "biotite=1.7.1")
        self.assertEqual(set(recipe["install"]["platforms"]), {"linux", "macos", "windows"})
        self.assertIn("superimpose", recipe["verify"]["argv"][-1])
        self.assertNotIn("https://", recipe["verify"]["argv"][-1])

    def test_peptidebuilder_is_geometry_builder_not_fold_predictor(self):
        recipe = bioinstall.load_recipe("peptidebuilder")
        self.assertEqual(recipe["install"]["package"], "PeptideBuilder==1.1.0")
        self.assertIn("add_residue", recipe["verify"]["argv"][-1])
        self.assertNotIn("protein-structure-prediction", recipe["tasks"])
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall, "current_python_version", return_value=(3, 12)):
            plan = bioinstall.build_plan(recipe)
        self.assertTrue(plan["ready_here"])
        self.assertIn("--only-binary=:all:", plan["commands"][1])

    def test_viennarna_python_scope_and_supported_interpreters(self):
        recipe = bioinstall.load_recipe("viennarna")
        self.assertEqual(recipe["install"]["package"], "ViennaRNA==2.7.2")
        self.assertNotIn("RNAfold", recipe.get("aliases", []))
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall, "current_python_version", return_value=(3, 12)):
            plan = bioinstall.build_plan(recipe)
        self.assertTrue(plan["ready_here"])
        self.assertIn("--only-binary=:all:", plan["commands"][1])
        self.assertEqual(plan["verification_command"][1], "-c")
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="aarch64"
        ), patch.object(bioinstall, "current_python_version", return_value=(3, 12)):
            self.assertFalse(bioinstall.build_plan(recipe)["supported_here"])
        with patch.object(bioinstall, "current_python_version", return_value=(3, 14)):
            plan = bioinstall.build_plan(recipe)
        self.assertFalse(plan["supported_here"])
        self.assertNotIn("commands", plan)

    def test_python_installation_never_silently_builds_source(self):
        for recipe in bioinstall.all_recipes():
            if recipe["install"]["kind"] != "python" or not recipe["install"]["automatic"]:
                continue
            with patch.object(bioinstall, "current_platform", return_value="linux"), patch.object(
                bioinstall, "current_architecture", return_value="x86_64"
            ), patch.object(bioinstall, "current_python_version", return_value=(3, 12)):
                self.assertIn("--only-binary=:all:", bioinstall.build_plan(recipe)["commands"][1])

    def test_failed_viennarna_verification_cannot_write_success_receipt(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bioinstall, "INSTALL_ROOT", Path(directory)), patch.object(
            bioinstall, "current_platform", return_value="windows"
        ), patch.object(bioinstall, "current_architecture", return_value="x86_64"), patch.object(
            bioinstall, "current_python_version", return_value=(3, 12)
        ), patch.object(bioinstall, "run", side_effect=[None, None, RuntimeError("binding failed")]) as command, patch.object(
            bioinstall, "write_receipt"
        ) as receipt, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "binding failed"):
                bioinstall.install_recipe(bioinstall.load_recipe("viennarna"), apply=True)
        self.assertEqual(command.call_count, 3)
        receipt.assert_not_called()

    def test_rnastructure_remains_guidance_only(self):
        recipe = bioinstall.load_recipe("rnastructure")
        self.assertFalse(recipe["install"]["automatic"])
        with patch.object(bioinstall, "run") as command, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(recipe, apply=True)
        command.assert_not_called()

    def test_viennarna_does_not_overwrite_existing_environment(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(bioinstall, "INSTALL_ROOT", Path(directory)), patch.object(
            bioinstall, "current_platform", return_value="windows"
        ), patch.object(bioinstall, "current_architecture", return_value="x86_64"), patch.object(
            bioinstall, "current_python_version", return_value=(3, 12)
        ), patch.object(bioinstall, "run") as command, contextlib.redirect_stdout(io.StringIO()):
            bioinstall.env_python("bio-viennarna").parent.parent.mkdir(parents=True)
            with self.assertRaisesRegex(bioinstall.RecipeError, "Target environment already exists"):
                bioinstall.install_recipe(bioinstall.load_recipe("viennarna"), apply=True)
        command.assert_not_called()

    def test_dssp_and_molprobity_use_distinct_installation_boundaries(self):
        dssp = bioinstall.load_recipe("dssp")
        self.assertEqual(dssp["install"]["package"], "dssp=4.6.1")
        self.assertEqual(dssp["verify"]["argv"], ["mkdssp", "--version"])
        self.assertEqual(set(dssp["install"]["platforms"]), {"linux", "macos", "windows"})
        molprobity = bioinstall.load_recipe("molprobity")
        self.assertFalse(molprobity["install"]["automatic"])
        self.assertEqual(molprobity["install"]["kind"], "source")
        with patch.object(bioinstall, "run") as run_command, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(molprobity, apply=True)
        run_command.assert_not_called()

    def test_smina_and_binana_keep_automatic_and_guided_routes_separate(self):
        smina = bioinstall.load_recipe("smina")
        self.assertEqual(smina["install"]["package"], "smina=2020.12.10")
        self.assertEqual(smina["verify"]["argv"], ["smina", "--help"])
        self.assertEqual(set(smina["install"]["platforms"]), {"linux", "macos", "windows"})
        binana = bioinstall.load_recipe("binana")
        self.assertFalse(binana["install"]["automatic"])
        with patch.object(bioinstall, "run") as run_command, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(binana, apply=True)
        run_command.assert_not_called()
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

    def test_binding_pocket_routes_distinguish_automatic_and_guided_installation(self):
        fpocket = bioinstall.load_recipe("fpocket")
        self.assertEqual(fpocket["install"]["package"], "fpocket=4.2.3")
        self.assertTrue(fpocket["install"]["automatic"])
        self.assertEqual(fpocket["verify"]["argv"], ["fpocket", "-h"])
        p2rank = bioinstall.load_recipe("p2rank")
        self.assertFalse(p2rank["install"]["automatic"])
        self.assertEqual(p2rank["install"]["kind"], "binary")
        self.assertEqual({candidate["id"] for candidate in bioinstall.suggest_recipes("binding-pocket-detection")["candidates"]}, {"fpocket", "p2rank"})
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "current_architecture", return_value="x86_64"
        ), patch.object(bioinstall.shutil, "which", return_value="conda"), patch.object(
            bioinstall, "run"
        ) as run_command, contextlib.redirect_stdout(io.StringIO()):
            plan = bioinstall.build_plan(fpocket)
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(fpocket, apply=True)
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(p2rank, apply=True)
        self.assertFalse(plan["supported_here"])
        self.assertTrue(plan["manual_fallback_here"])
        self.assertNotIn("commands", plan)
        run_command.assert_not_called()

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
