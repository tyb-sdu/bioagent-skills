---
name: install-gpu
description: Assess GPU prerequisites for molecular dynamics, docking, and biomolecular AI software before selecting a CPU or accelerated install variant. Use when a user requests CUDA, ROCm, or GPU acceleration.
license: MIT
compatibility: Requires read-only access to platform and GPU information.
---

# GPU prerequisite review

Run `python scripts/bioinstall.py doctor`, inspect the GPU model and installed driver using available read-only vendor tools, and compare the application's current compatibility table. Distinguish driver, CUDA toolkit/runtime, framework build, and model hardware requirements. Check GPU memory and disk requirements before selecting a variant. If the user can use a supported CPU route, present that option with its performance limitation.

Do not install or replace GPU drivers or reboot the machine as part of a package Skill. For NVIDIA systems, use the [official toolkit/driver matrix](https://docs.nvidia.com/datacenter/tesla/drivers/cuda-toolkit-driver-and-architecture-matrix.html). [OpenMM's guide](https://docs.openmm.org/latest/userguide/application/01_getting_started.html) shows that CUDA packaging and vendor drivers have separate responsibilities.
