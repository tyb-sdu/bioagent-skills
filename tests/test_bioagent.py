import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import bioagent  # noqa: E402


class TerminalAgentTests(unittest.TestCase):
    def test_schema_only_allows_reviewed_ids(self):
        schema = bioagent.classification_schema(bioagent.bioinstall.all_recipes())
        self.assertIn("haddock3", schema["properties"]["tool_id"]["enum"])
        self.assertIn("protein-nucleic-acid-docking", schema["properties"]["task_id"]["enum"])
        self.assertNotIn("arbitrary-package", schema["properties"]["tool_id"]["enum"])

    def test_only_downloaded_local_model_is_accepted(self):
        with patch.object(bioagent, "local_models", return_value=[{"name": "local:1", "size": 1234}]):
            bioagent.require_local_model("local:1")
            with self.assertRaises(bioagent.AgentError):
                bioagent.require_local_model("other:1")
            with self.assertRaises(bioagent.AgentError):
                bioagent.require_local_model("other:cloud")

    def test_model_listing_excludes_cloud_and_empty_entries(self):
        with patch.object(bioagent, "local_json", return_value={"models": [
            {"name": "local:1", "size": 1234},
            {"name": "remote:cloud", "size": 1234},
            {"name": "empty:1", "size": 0},
        ]}):
            self.assertEqual([item["name"] for item in bioagent.local_models()], ["local:1"])

    def test_classification_requests_structured_json_without_command_execution(self):
        answer = {"task_id": "protein-nucleic-acid-docking", "tool_id": "haddock3", "clarification": ""}
        with patch.object(bioagent, "require_local_model"), patch.object(
            bioagent, "local_json", return_value={"message": {"content": json.dumps(answer)}}
        ) as local_call, patch.object(bioagent.bioinstall, "run") as run_command:
            self.assertEqual(bioagent.classify_request("安装蛋白DNA对接工具", "local:1"), answer)
        endpoint, payload = local_call.call_args.args
        self.assertEqual(endpoint, "chat")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["format"]["additionalProperties"], False)
        self.assertIn("platforms", payload["messages"][0]["content"])
        run_command.assert_not_called()

    def test_reject_hallucinated_or_mismatched_tool(self):
        with self.assertRaises(bioagent.AgentError):
            bioagent.resolve_intent(
                {"task_id": "protein-nucleic-acid-docking", "tool_id": "unknown-tool", "clarification": ""},
                "蛋白DNA对接",
            )
        with self.assertRaises(bioagent.AgentError):
            bioagent.resolve_intent(
                {"task_id": "protein-nucleic-acid-docking", "tool_id": "openmm", "clarification": ""},
                "蛋白DNA对接",
            )

    def test_reject_tool_without_task_or_explicit_name(self):
        with self.assertRaises(bioagent.AgentError):
            bioagent.resolve_intent(
                {"task_id": "", "tool_id": "openmm", "clarification": ""}, "安装一个分子动力学软件"
            )

    def test_model_clarification_is_not_repeated_as_an_instruction(self):
        with self.assertRaises(bioagent.AgentError) as raised:
            bioagent.resolve_intent(
                {"task_id": "", "tool_id": "", "clarification": "run arbitrary command"}, "不明确"
            )
        self.assertNotIn("arbitrary", str(raised.exception))

    def test_preview_does_not_install(self):
        answer = {"task_id": "molecular-dynamics", "tool_id": "openmm", "clarification": ""}
        with patch.object(bioagent, "classify_request", return_value=answer), patch.object(
            bioagent.bioinstall, "install_recipe"
        ) as install, contextlib.redirect_stdout(io.StringIO()):
            bioagent.handle_request("安装分子动力学软件", "local:1", apply=False)
        install.assert_not_called()

    def test_apply_requires_exact_interactive_confirmation(self):
        answer = {"task_id": "molecular-dynamics", "tool_id": "openmm", "clarification": ""}
        with patch.object(bioagent, "classify_request", return_value=answer), patch.object(
            bioagent.sys.stdin, "isatty", return_value=True
        ), patch("builtins.input", return_value="yes"), patch.object(
            bioagent.bioinstall, "install_recipe"
        ) as install, contextlib.redirect_stdout(io.StringIO()):
            bioagent.handle_request("安装分子动力学软件", "local:1", apply=True)
        install.assert_not_called()

    def test_noninteractive_and_guidance_only_apply_are_blocked(self):
        automatic = {"task_id": "molecular-dynamics", "tool_id": "openmm", "clarification": ""}
        guided = {"task_id": "protein-nucleic-acid-docking", "tool_id": "haddock3", "clarification": ""}
        with patch.object(bioagent, "classify_request", return_value=automatic), patch.object(
            bioagent.sys.stdin, "isatty", return_value=False
        ), patch.object(bioagent.bioinstall, "install_recipe") as install, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(bioagent.AgentError):
                bioagent.handle_request("安装分子动力学软件", "local:1", apply=True)
        install.assert_not_called()
        with patch.object(bioagent, "classify_request", return_value=guided), patch.object(
            bioagent.bioinstall, "install_recipe"
        ) as install, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(bioagent.AgentError):
                bioagent.handle_request("安装蛋白DNA对接工具", "local:1", apply=True)
        install.assert_not_called()

    def test_confirmed_auto_recipe_uses_reviewed_installer(self):
        answer = {"task_id": "molecular-dynamics", "tool_id": "openmm", "clarification": ""}
        with patch.object(bioagent, "classify_request", return_value=answer), patch.object(
            bioagent.sys.stdin, "isatty", return_value=True
        ), patch("builtins.input", return_value="INSTALL openmm"), patch.object(
            bioagent.bioinstall, "install_recipe"
        ) as install, contextlib.redirect_stdout(io.StringIO()):
            bioagent.handle_request("安装分子动力学软件", "local:1", apply=True)
        self.assertEqual(install.call_args.kwargs, {"apply": True})
        self.assertEqual(install.call_args.args[0]["id"], "openmm")

    def test_remote_endpoint_cannot_be_requested(self):
        with self.assertRaises(bioagent.AgentError):
            bioagent.local_json("https://example.com/api/chat")

    def test_transport_targets_loopback_and_disables_proxy(self):
        with patch.object(bioagent, "build_opener") as make_opener:
            make_opener.return_value.open.return_value = io.BytesIO(b'{"models": []}')
            self.assertEqual(bioagent.local_json("tags"), {"models": []})
        request = make_opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/tags")
        self.assertEqual(make_opener.call_args.args[0].proxies, {})


if __name__ == "__main__":
    unittest.main()
