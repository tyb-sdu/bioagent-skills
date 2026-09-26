# Research and installation sources

Installation commands are grounded in current maintainer documentation. Scientific papers explain what a tool does; they are not installation instructions. Each catalog JSON file contains the specific source links used for that software.

| Topic | Primary source | Why it matters here |
| --- | --- | --- |
| Agent Skill structure | [Agent Skills specification](https://agentskills.io/specification) | `SKILL.md` metadata, scripts, references, discovery |
| conda isolation and channels | [Conda channel guidance](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-channels.html) | Per-command channels and dependency resolution |
| Bioconda platform limits | [Bioconda usage](https://bioconda.github.io/) | Linux/macOS support; Windows users need a suitable Linux environment for Bioconda packages |
| Windows Linux environment | [Microsoft WSL installation](https://learn.microsoft.com/en-us/windows/wsl/install) | Optional Windows path for Linux-only software |
| GPU compatibility | [NVIDIA CUDA driver matrix](https://docs.nvidia.com/datacenter/tesla/drivers/cuda-toolkit-driver-and-architecture-matrix.html) | Check driver/toolkit compatibility before choosing GPU packages |
| Containers on clusters | [Apptainer Docker/OCI support](https://apptainer.org/docs/user/latest/docker_and_oci.html) | OCI images can often be used in HPC environments |
| Model downloads | [Hugging Face download guide](https://huggingface.co/docs/huggingface_hub/guides/download) | Pin revisions, estimate size, and manage cache |
| Local model routing | [Ollama local API](https://docs.ollama.com/api/introduction), [chat endpoint](https://docs.ollama.com/api/chat), [structured outputs](https://docs.ollama.com/capabilities/structured-outputs), [local model listing](https://docs.ollama.com/api/tags) | Constrain the terminal entry point to a downloaded local model and validated catalog IDs |
| Python command packaging | [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/), [setuptools package data](https://setuptools.pypa.io/en/latest/userguide/datafiles.html) | Define console commands and include reviewed JSON recipes in the wheel |

Selected scientific references attached to individual recipes include [OpenMM 7](https://doi.org/10.1371/journal.pcbi.1005659), [AutoDock Vina](https://doi.org/10.1002/jcc.21334), [GNINA 1.0](https://doi.org/10.1186/s13321-021-00522-2), [GROMACS](https://doi.org/10.1016/j.softx.2015.06.001), [ProteinMPNN](https://doi.org/10.1126/science.add2187), [LigandMPNN](https://doi.org/10.1038/s41592-025-02626-1), [RFdiffusion](https://doi.org/10.1038/s41586-023-06415-8), [HADDOCK3](https://doi.org/10.1021/acs.jcim.5c00969), and the [Boltz-2 preprint](https://doi.org/10.1101/2025.06.14.659707). These references support tool descriptions and task matching; installation routes come from the linked maintainer pages.

Source review date for this catalog: 2026-09-26. Software documentation, packages and license terms can change; recheck them before expanding automatic execution.
