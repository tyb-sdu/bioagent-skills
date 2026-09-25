---
name: install-source
description: Plan a source build when a reviewed biomolecular or quantum chemistry tool lacks a suitable package or binary. Use for CMake, compiler, MPI, or architecture-specific builds of tools such as GROMACS and Psi4.
license: MIT
compatibility: Requires a supported compiler toolchain and sufficient disk/compute resources.
---

# Source build

Use this route only after reading the maintainers' build guide and checking whether a package or binary meets the user's requirements. Pin a release tag or commit, record required compilers and libraries, and choose a user-owned build and install prefix. Explain optional MPI and GPU variants before configuring them; these alter binaries and prerequisites.

Build in a separate directory, retain the configuration and build logs, run the maintainers' tests, then run a basic command from the installed prefix. Do not run `sudo make install`, overwrite system libraries, or change compiler and driver versions automatically. If the build fails, report the exact failing step and preserve the build directory for inspection. See the [GROMACS installation guide](https://manual.gromacs.org/current/install-guide/index.html) and [Psi4 source guide](https://psicode.org/psi4manual/master/build_planning.html).

Source builds are guidance-only in this release. Add a tool-specific, pinned and tested script before enabling automatic execution.
