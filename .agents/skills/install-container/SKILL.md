---
name: install-container
description: Plan installation of a biological computation tool distributed as a Docker or OCI/Apptainer image. Use when a catalog recipe has install.kind container, such as PLIP, or when an official image is the reviewed route.
license: MIT
compatibility: Requires an available compatible container runtime.
---

# Container installation

Check the runtime (`docker` or `apptainer`), target architecture, GPU support when requested, and the official image repository. Prefer an immutable image digest or a tested fixed tag; show the expected download size. Review every host bind mount and the working/output directory so the container reads only user-selected data and writes only to the intended location.

Pull the selected image, record its digest, and run the maintainer's small smoke test. Do not use `latest` as a reproducibility claim. Do not add `--privileged`, mount the entire home directory, or install Docker itself as an incidental step. [Apptainer's OCI documentation](https://apptainer.org/docs/user/latest/docker_and_oci.html) covers image use on shared systems; [PLIP's README](https://github.com/pharmai/plip/blob/master/README.md) describes its prebuilt container route.

Container recipes are guidance-only until a specific image and digest have been checked on the target platform.
