# Local terminal-agent architecture

This repository runs on the end user's computer. It does not host scientific
computations or require an operator-owned inference server.

```text
User request (Chinese or English)
  -> scripts/bioagent.py
  -> downloaded local model via Ollama loopback API (classification only)
  -> validate task/tool IDs against catalog/*.json
  -> show reviewed recipe, sources, requirements and plan
  -> optional --apply + exact interactive confirmation
  -> scripts/bioinstall.py allowlisted conda/Python route
  -> verify program and write a local receipt
```

The model's output is data, not executable code. It cannot add package names,
commands, URLs, or new recipes. The entry point accesses only
`127.0.0.1:11434`; proxy variables are ignored. It requires a named model
reported as downloaded by the local Ollama `tags` endpoint and rejects model
names containing `cloud`. Users should still check Ollama's own model and
privacy settings. No software is installed merely by sending a natural-language
request, and noninteractive `--apply` is disabled.

Automatic installation is intentionally narrower than task recognition. As of
this release, 5 reviewed conda/PyPI recipes can be applied to fresh isolated
environments; the other 13 are guidance-only because of weights, licenses,
platform artifacts, or unverified dependency resolution. A successful import
or `--help` is an installation smoke test, not evidence that scientific results
are valid. The local model's classification may be wrong, so users must inspect
the displayed plan and sources before confirming an install.

This is a minimal single-turn terminal agent, not a packaged desktop app or a
general computer-use agent. The two CLI commands, 18 recipes, and 10 Skills are
installable as a Python wheel. `bioagent skills export --to <path>/skills`
previews copying Skills to a user-chosen discovery path; `--apply` performs the
copy and refuses any name collision. Wheel installation does not automatically
register Skills with other agents. Exported Skills still need access to the
reviewed `bioinstall` executable or a repository checkout. Users still need
Python, Git for cloning, and Ollama plus a downloaded compatible model for
natural-language routing. Conda is needed for the automatic conda recipes.
The deterministic `bioinstall` command works without Ollama. Software runs on
the user's machine or chosen cluster, not on the maintainer's server.
