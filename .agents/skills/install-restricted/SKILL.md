---
name: install-restricted
description: Guide a user through software or model installation when code, weights, datasets, or use are subject to separate access or licence terms. Use for AlphaFold 3 model parameters and similarly restricted packages.
license: MIT
compatibility: Requires access to the current official terms and the user's authorized account.
---

# Restricted distribution

Read current official terms for each component: code, model weights, databases, and generated outputs may have different conditions. State what the user must obtain from the rights holder and where official instructions are published. Ask the user to complete any required access, agreement, or download using their own account. Continue only with files they are authorized to use in their own environment.

Do not cache credentials in the repository, bypass access checks, rehost assets, or treat public source code as permission to share trained parameters. For AlphaFold 3, consult its [installation guide](https://github.com/google-deepmind/alphafold3/blob/main/docs/installation.md) and [model-parameter terms](https://github.com/google-deepmind/alphafold3/blob/main/WEIGHTS_TERMS_OF_USE.md). A restricted recipe is never automatically executed by the shared installer.
