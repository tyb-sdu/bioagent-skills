---
name: install-model-data
description: Plan and verify separate downloads of biological AI model weights, chemical component data, or reference databases. Use when installing models such as Boltz-2 or AlphaFold 3 whose package installation does not include all inference assets.
license: MIT
compatibility: Requires adequate storage, network access, and permission to obtain the selected assets.
---

# Model weights and reference data

List each required asset separately from software code: maintainer source, version or revision, license, estimated size, cache destination, and whether downloading starts automatically on first inference. Check that the selected storage location has room. Use a pinned revision and a digest when available; verify a completed transfer before loading it. Do not treat an empty or interrupted file as a valid cache hit.

Never bundle, mirror, or redistribute weights through this repository. Read the weight terms separately from the code license. [Hugging Face's download guide](https://huggingface.co/docs/huggingface_hub/guides/download) documents revisions and dry-run size estimates. The [Boltz repository](https://github.com/jwohlwend/boltz/blob/main/README.md) documents installation and inference; [AlphaFold 3 terms](https://github.com/google-deepmind/alphafold3/blob/main/WEIGHTS_TERMS_OF_USE.md) govern its parameters.

Model-data recipes are guidance-only until each asset and its transfer method have been vetted.
