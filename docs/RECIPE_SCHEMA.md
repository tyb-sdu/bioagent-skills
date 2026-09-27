# Software recipe format

Each `catalog/<id>.json` records one tool, its approved installation route, a minimal verification step, and sources. IDs and filenames use lowercase letters, digits, and single hyphens.

Required fields:

| Field | Meaning |
| --- | --- |
| `id`, `name`, `summary` | Stable identifier and human-facing description |
| `aliases` | Optional reviewed software names used for exact-name routing, e.g. Vina |
| `tasks` | Research tasks that justify offering this tool |
| `install.kind` | `conda`, `python`, `binary`, `source`, `container`, `model-data`, or `restricted` |
| `install.platforms` | Explicitly reviewed subset of `linux`, `macos`, `windows` |
| `install.architectures` | Per-platform reviewed native CPU architectures; required for automatic recipes |
| `install.min_python` | Minimum interpreter version for automatic PyPI recipes |
| `install.python_versions` | Interpreter versions with reviewed pinned wheels for automatic PyPI recipes |
| `install.manual_fallback` | Optional platform-specific guidance when an automatic route is not ready; never executed by the installer |
| `install.automatic` | `true` only for the currently executable conda/Python routes |
| `verify.argv` | Argument vector for a basic test, never a shell command string |
| `usage.executable` | Optional reviewed conda CLI for the read-only usage handoff when verification uses a different executable |
| `sources` | HTTPS links to maintainer documentation, package record, terms, and/or primary paper |

Automated recipes additionally need `package` and `environment`; conda recipes need `channel: conda-forge`. They create an isolated environment and then run verification. For automatic recipes, `supported_here` means OS/architecture/Python match; guidance-only recipes have only an OS-level check. `ready_here` also checks known local prerequisites, not package solver success. A guidance-only recipe needs `steps` and `verify_note`; an automatic recipe can additionally supply `manual_fallback` with reviewed `platforms`, `steps`, and `verify_note` for hosts where automatic installation is unavailable. The presence of a paper or public GitHub repository alone is insufficient evidence for automatic installation.

Before upgrading a guidance-only recipe to `automatic: true`:

1. Check the current official installation instructions and the actual supported platform/architecture.
2. Pin a suitable package version, release asset checksum, or container digest. Record the download size and any first-run asset downloads.
3. Check license terms for code, weights, and databases separately.
4. Run installation and verification on each declared platform. Record the tested platform, date, and version.
5. Add a test covering plan construction, idempotence, and failure behavior.

Automatic execution supports only isolated conda/Python environments. Pip uses `--only-binary=:all:` for the package and dependencies; missing compatible wheels cause failure rather than an implicit source build. Source builds, container images, binaries and model downloads remain guidance-only until their specific artifacts and platform behavior are verified. A Python interface must not be presented as its full command-line suite; document that distinction in the recipe when applicable.
