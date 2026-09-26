"""Exercise the real local HTTP transport without a model or software install."""

import contextlib
import io
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bioagent  # noqa: E402


class OllamaFixture(BaseHTTPRequestHandler):
    chat_payloads = []

    def log_message(self, *args):
        pass

    def send_json(self, value):
        content = json.dumps(value).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == "/api/tags":
            self.send_json({"models": [{"name": "local-model:1", "size": 12345}]})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(404)
            return
        length = int(self.headers["Content-Length"])
        self.chat_payloads.append(json.loads(self.rfile.read(length)))
        self.send_json({"message": {"content": json.dumps({
            "task_id": "molecular-dynamics", "tool_id": "openmm", "clarification": ""
        })}})


class LoopbackIntegrationTests(unittest.TestCase):
    def test_cli_previews_reviewed_recipe_via_local_http(self):
        OllamaFixture.chat_payloads = []
        server = HTTPServer(("127.0.0.1", 0), OllamaFixture)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}/api/"
            with patch.object(bioagent, "OLLAMA_BASE", base), patch.object(
                bioagent.sys, "argv", [
                    "bioagent", "ask", "我需要选择分子动力学模拟程序", "--model", "local-model:1"
                ]
            ), patch.object(bioagent.bioinstall, "install_recipe") as install, contextlib.redirect_stdout(
                io.StringIO()
            ) as output:
                self.assertEqual(bioagent.main(), 0)
            self.assertIn('"id": "openmm"', output.getvalue())
            self.assertIn("Preview only", output.getvalue())
            self.assertEqual(len(OllamaFixture.chat_payloads), 1)
            self.assertFalse(OllamaFixture.chat_payloads[0]["stream"])
            install.assert_not_called()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
