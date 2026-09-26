import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "bioinstall.py"
SPEC = importlib.util.spec_from_file_location("bioinstall", MODULE_PATH)
bioinstall = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bioinstall)


class CatalogTests(unittest.TestCase):
    def test_catalog_is_valid_and_sourced(self):
        recipes = bioinstall.all_recipes()
        self.assertGreaterEqual(len(recipes), 18)
        for recipe in recipes:
            self.assertTrue(any(source["type"] == "installation" for source in recipe["sources"]))

    def test_task_suggestions_are_read_only_and_include_platform_state(self):
        with patch.object(bioinstall, "current_platform", return_value="windows"), patch.object(
            bioinstall, "run"
        ) as run_command:
            result = bioinstall.suggest_recipes("protein-nucleic-acid-docking")
        self.assertEqual(result["task"], "protein-nucleic-acid-docking")
        self.assertEqual([item["id"] for item in result["candidates"]], ["haddock3"])
        self.assertFalse(result["candidates"][0]["supported_here"])
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
        with patch.object(bioinstall, "run") as run_command, patch.object(bioinstall, "write_receipt") as write_receipt:
            bioinstall.install_recipe(recipe, apply=False)
        run_command.assert_not_called()
        write_receipt.assert_not_called()

    def test_guidance_only_recipe_cannot_apply(self):
        recipe = bioinstall.load_recipe("alphafold3")
        with patch.object(bioinstall, "current_platform", return_value="linux"):
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(recipe, apply=True)

    def test_reject_existing_conda_environment(self):
        recipe = bioinstall.load_recipe("openmm")
        with patch.object(bioinstall, "shutil") as fake_shutil, patch.object(
            bioinstall, "conda_environment_exists", return_value=True
        ), patch.object(bioinstall, "run") as run_command:
            fake_shutil.which.return_value = "conda"
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.install_recipe(recipe, apply=True)
        run_command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
