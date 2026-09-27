import contextlib
import io
import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bioinstall


class InstallStateTests(unittest.TestCase):
    def test_guidance_status_does_not_probe_or_verify_software(self):
        with patch.object(bioinstall, "installed_version") as metadata, patch.object(bioinstall, "run") as verify:
            status = bioinstall.installation_status(bioinstall.load_recipe("alphafold3"))
        self.assertEqual(status["state"], "guidance-only")
        metadata.assert_not_called()
        verify.assert_not_called()

    def test_missing_conda_is_unknown_not_missing_environment(self):
        with patch.object(bioinstall, "conda_executable", return_value=None), patch.object(
            bioinstall, "conda_environment_prefix"
        ) as probe:
            status = bioinstall.installation_status(bioinstall.load_recipe("openmm"))
        self.assertEqual(status["state"], "manager-unavailable")
        probe.assert_not_called()

    def test_old_receipt_cannot_make_missing_environment_present(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-state-") as directory, patch.object(
            bioinstall, "INSTALL_ROOT", Path(directory)
        ):
            receipts = Path(directory) / "receipts"
            receipts.mkdir()
            (receipts / "mdanalysis-20260101.json").write_text(json.dumps({
                "id": "mdanalysis", "result": "verified", "package_version": "2.10.0",
                "commands": [["unreviewed-command", "never-run"]],
            }), encoding="utf-8")
            with patch.object(bioinstall, "installed_version") as metadata, patch.object(bioinstall, "run") as verify:
                plan = bioinstall.usage_plan(bioinstall.load_recipe("mdanalysis"))
            self.assertEqual(plan["status"]["state"], "environment-missing")
            self.assertEqual(plan["status"]["receipt"]["historical_result"], "verified")
            self.assertIsNone(plan["invocation_argv"])
            self.assertIsNone(plan["status"]["receipt_version_matches_current"])
            self.assertNotIn("unreviewed-command", json.dumps(plan))
            metadata.assert_not_called()
            verify.assert_not_called()

    def test_existing_python_environment_with_no_version_is_unconfirmed(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-state-") as directory, patch.object(
            bioinstall, "INSTALL_ROOT", Path(directory)
        ):
            bioinstall.env_python("bio-mdanalysis").parent.mkdir(parents=True)
            with patch.object(bioinstall, "installed_version", return_value=None):
                status = bioinstall.installation_status(bioinstall.load_recipe("mdanalysis"))
        self.assertEqual(status["state"], "package-unconfirmed")

    def test_conda_usage_uses_observed_prefix_and_never_launches(self):
        with patch.object(bioinstall, "conda_executable", return_value="conda"), patch.object(
            bioinstall, "conda_environment_prefix", return_value=Path("/isolated env/bio-autodock-vina")
        ), patch.object(bioinstall, "installed_version", return_value="1.2.7"), patch.object(bioinstall, "run") as verify:
            plan = bioinstall.usage_plan(bioinstall.load_recipe("autodock-vina"))
        self.assertEqual(plan["invocation_argv"], ["conda", "run", "--prefix", str(Path("/isolated env/bio-autodock-vina")), "vina"])
        self.assertEqual(plan["status"]["state"], "package-present")
        verify.assert_not_called()

    def test_apbs_usage_shows_scientific_cli_not_verification_wrapper(self):
        with patch.object(bioinstall, "conda_executable", return_value="conda"), patch.object(
            bioinstall, "conda_environment_prefix", return_value=Path("/isolated/bio-apbs")
        ), patch.object(bioinstall, "installed_version", return_value="3.4.1"), patch.object(
            bioinstall, "run"
        ) as verify:
            plan = bioinstall.usage_plan(bioinstall.load_recipe("apbs"))
        self.assertEqual(plan["invocation_argv"][-1], "apbs")
        verify.assert_not_called()

    def test_python_usage_points_to_isolated_interpreter(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-state-") as directory, patch.object(
            bioinstall, "INSTALL_ROOT", Path(directory)
        ):
            python = bioinstall.env_python("bio-mdanalysis")
            python.parent.mkdir(parents=True)
            python.touch()
            with patch.object(bioinstall, "installed_version", return_value="2.10.0"), patch.object(bioinstall, "run") as verify:
                plan = bioinstall.usage_plan(bioinstall.load_recipe("mdanalysis"))
            self.assertEqual(plan["invocation_argv"], [str(python)])
            verify.assert_not_called()

    def test_changed_version_is_distinct_from_historical_receipt(self):
        old = {"receipt": {"package_version": "8.5"}, "receipt_error": None}
        with patch.object(bioinstall, "latest_receipt", return_value=old), patch.object(
            bioinstall, "conda_executable", return_value="conda"
        ), patch.object(bioinstall, "conda_environment_prefix", return_value=Path("/env/bio-openmm")), patch.object(
            bioinstall, "installed_version", return_value="8.6.1"
        ):
            status = bioinstall.installation_status(bioinstall.load_recipe("openmm"))
        self.assertEqual(status["package_version"], "8.6.1")
        self.assertFalse(status["receipt_version_matches_current"])

    def test_corrupt_or_oversized_receipt_is_not_accepted(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-state-") as directory, patch.object(
            bioinstall, "INSTALL_ROOT", Path(directory)
        ):
            receipts = Path(directory) / "receipts"
            receipts.mkdir()
            path = receipts / "openmm-20260101.json"
            path.write_text("{invalid JSON", encoding="utf-8")
            summary = bioinstall.latest_receipt(bioinstall.load_recipe("openmm"))
            self.assertIsNone(summary["receipt"])
            self.assertTrue(summary["receipt_error"])
            path.write_bytes(b"x" * (bioinstall.MAX_RECEIPT_BYTES + 1))
            summary = bioinstall.latest_receipt(bioinstall.load_recipe("openmm"))
            self.assertIn("read limit", summary["receipt_error"])

    def test_receipt_for_another_tool_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-state-") as directory, patch.object(
            bioinstall, "INSTALL_ROOT", Path(directory)
        ):
            receipts = Path(directory) / "receipts"
            receipts.mkdir()
            (receipts / "openmm-20260101.json").write_text(json.dumps({
                "id": "rdkit", "result": "verified", "package_version": "2026.03.6",
            }), encoding="utf-8")
            summary = bioinstall.latest_receipt(bioinstall.load_recipe("openmm"))
        self.assertIsNone(summary["receipt"])
        self.assertTrue(summary["receipt_error"])

    def test_new_receipt_records_architecture_and_reads_as_summary(self):
        with tempfile.TemporaryDirectory(prefix="bioagent-state-") as directory, patch.object(
            bioinstall, "INSTALL_ROOT", Path(directory)
        ), patch.object(bioinstall, "installed_version", return_value="8.6.1"):
            recipe = bioinstall.load_recipe("openmm")
            path = bioinstall.write_receipt(recipe, bioinstall.build_plan(recipe))
            record = json.loads(path.read_text(encoding="utf-8"))
            summary = bioinstall.latest_receipt(recipe)
        self.assertEqual(record["receipt_schema"], 2)
        self.assertEqual(record["architecture"], bioinstall.current_architecture())
        self.assertEqual(record["environment_name"], "bio-openmm")
        self.assertEqual(summary["receipt"]["package_version"], "8.6.1")
        self.assertNotIn("commands", summary["receipt"])

    def test_environment_probe_timeout_becomes_inspection_error(self):
        with patch.object(bioinstall, "conda_executable", return_value="conda"), patch.object(
            bioinstall.subprocess, "run", side_effect=bioinstall.subprocess.TimeoutExpired(["conda"], 30)
        ):
            status = bioinstall.installation_status(bioinstall.load_recipe("openmm"))
        self.assertEqual(status["state"], "inspection-error")
        self.assertIn("timed out", status["inspection_error"])

    def test_ambiguous_conda_environment_is_not_selected(self):
        with patch.object(bioinstall, "require_conda", return_value="conda"), patch.object(bioinstall.subprocess, "run") as command:
            command.return_value.stdout = json.dumps({"envs": ["/one/bio-openmm", "/two/bio-openmm"]})
            with self.assertRaises(bioinstall.RecipeError):
                bioinstall.conda_environment_prefix("bio-openmm")

    def test_inspection_failure_is_reported_without_claiming_absence(self):
        with patch.object(bioinstall, "conda_executable", return_value="conda"), patch.object(
            bioinstall, "conda_environment_prefix", side_effect=bioinstall.RecipeError("ambiguous prefixes")
        ):
            status = bioinstall.installation_status(bioinstall.load_recipe("openmm"))
        self.assertEqual(status["state"], "inspection-error")
        self.assertIn("ambiguous prefixes", status["inspection_error"])

    def test_command_display_quotes_spaces_and_apostrophes(self):
        argv = ["/env with spaces/it's-python", "script with spaces.py"]
        with patch.object(bioinstall.os, "name", "posix"):
            self.assertEqual(shlex.split(bioinstall.display_command(argv)), argv)
        with patch.object(bioinstall.os, "name", "nt"):
            display = bioinstall.display_command(argv)
        self.assertTrue(display.startswith("& "))
        self.assertIn("it''s-python", display)

    def test_cli_status_is_read_only(self):
        with patch.object(bioinstall.sys, "argv", ["bioinstall", "status", "alphafold3"]), patch.object(
            bioinstall, "run"
        ) as verify, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(bioinstall.main(), 0)
        self.assertEqual(json.loads(output.getvalue())["state"], "guidance-only")
        verify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
