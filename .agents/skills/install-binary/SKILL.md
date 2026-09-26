---
name: install-binary
description: Guide installation of a maintainer-published precompiled biological software executable. Use for binary recipes or a catalog manual_fallback, such as AutoDock Vina on Windows, after checking the release asset and checksum.
license: MIT
compatibility: Requires a terminal and an official release asset for the host platform.
---

# Official binary release

1. Read the software catalog entry and current maintainer release notes. Match the operating system and architecture, and check any GPU or runtime requirements.
2. Prefer a pinned release URL plus a published or independently recorded SHA-256 digest before enabling an automated download. Keep files in a user-owned tool directory and preserve the original filename and source record.
3. Run the maintainer's non-computational smoke test (`--help` or `--version`). Record the exact binary path, release tag, digest, and observed output.
4. If an asset or checksum is still unresolved, return an actionable guided plan. Do not guess an asset name, execute an unverified download, or claim completion.

The [AutoDock Vina installation guide](https://autodock-vina.readthedocs.io/en/latest/installation.html) distinguishes the CLI executable from its Python bindings. The [GNINA repository](https://github.com/gnina/gnina) recommends prebuilt binaries for most users.
