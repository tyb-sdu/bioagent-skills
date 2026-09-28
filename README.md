# BioAgent Skills

面向**用户自己电脑上的终端智能体**的生物计算软件安装 Skill 包。项目帮助智能体根据科研任务和本机条件选择软件、预览安装方案、安装到隔离环境，并运行基础验收。计算任务仍在用户选择的计算机或集群执行。仓库还提供一个最小化的本地模型终端入口 `scripts/bioagent.py`。

本仓库依据 [Agent Skills 规范](https://agentskills.io/specification)编写，Skill 放在 `.agents/skills/`，软件的具体来源与安装方式放在 `catalog/`。支持读取该目录的终端智能体可以按需加载 Skill；其他智能体需要将这些 Skill 接入其自身的加载机制。Skill 是指令和工作流，需要宿主智能体提供命令执行能力。

## 当前范围

| 流程 | 状态 | 首批软件 |
| --- | --- | --- |
| conda-forge 包安装到独立环境 | 可预览、可执行、可验收 | OpenMM、RDKit、GROMACS、Psi4、PDBFixer、AutoDock Vina、FreeSASA、Open Babel、Meeko、MDTraj、ParmEd、Gemmi、ProLIF、OpenMMForceFields、APBS（Vina、FreeSASA、OpenMMForceFields 限 Linux/macOS） |
| PyPI 包安装到独立虚拟环境 | 可预览、可执行、可验收 | MDAnalysis、PROPKA、PDB2PQR、pdb-tools |
| 官方二进制、容器、源码、权重、受限软件及尚未锁定版本的包 | 资料核对与安装引导 | AlphaFold、RoseTTAFold3、RFdiffusion3、NUPACK、oxDNA、RELION、CryoSPARC、ModelAngelo、ChimeraX 等；完整清单见[覆盖矩阵](docs/COVERAGE.md) |

引导流程尚未提供一键安装。它们需要进一步锁定平台专用发布文件、镜像摘要、模型文件或许可条件。`plan` 不会改变电脑；`install` 默认也只预览，只有加 `--apply` 才会执行自动安装。脚本不会安装驱动、修改系统 Python、改动 conda 的全局配置、运行 `curl | sh`、安装受限权重或删除已有环境。

## 使用

运行安装器需要 Python 3.10+；固定版本的 MDAnalysis 2.10.0 要求 Python 3.11+，目前仅审核了 Python 3.11–3.14 的预编译包；PDB2PQR 3.7.1 目前仅审核 Python 3.11–3.13。自动安装 conda 配方还需要用户电脑已经安装 conda；Windows 用户使用 Linux-only 配方前需要先准备 Linux/WSL 环境。以下命令在仓库根目录执行：

```bash
git clone https://github.com/tyb-sdu/bioagent-skills.git
cd bioagent-skills
```

如果希望直接使用 `bioagent` / `bioinstall` 命令，可在**独立虚拟环境**中安装本仓库。以下示例以 Windows PowerShell 为例，不会把安装器装进系统 Python：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\bioinstall.exe validate
.\.venv\Scripts\bioagent.exe --help
```

Linux/macOS 将 `.venv\Scripts\` 换成 `.venv/bin/`。终端命令、63 个配方和 10 个 Skill 会进入虚拟环境，不依赖运行时所在目录；安装 Python 包**不会自动把 Skill 注册到其他智能体**。不安装 Python 包也可以直接运行下面的 `python scripts/...` 命令。

要把 Skill 放进另一个支持 Agent Skills 的项目，先查明该智能体的 Skill 发现目录，再显式导出。例如在 Windows PowerShell 中：

```powershell
.\.venv\Scripts\bioagent.exe skills list
.\.venv\Scripts\bioagent.exe skills export --to "C:\ResearchProject\.agents\skills"
.\.venv\Scripts\bioagent.exe skills export --to "C:\ResearchProject\.agents\skills" --apply
```

前一条 `export` 仅预览，`--apply` 才复制；遇到任何同名 Skill 会整体拒绝，不会覆盖。导出只是复制文件，**不会替其他智能体修改配置或保证其自动发现**。使用导出的 Skill 时，还需让智能体能调用本项目虚拟环境中的 `bioinstall` 命令；若只使用克隆仓库，则在仓库根目录运行 `python scripts/bioinstall.py`。

```bash
python scripts/bioinstall.py doctor
python scripts/bioinstall.py list
python scripts/bioinstall.py coverage
python scripts/bioinstall.py tasks
python scripts/bioinstall.py suggest protein-nucleic-acid-docking
python scripts/bioinstall.py plan openmm
python scripts/bioinstall.py install openmm
python scripts/bioinstall.py install openmm --apply
python scripts/bioinstall.py verify openmm
python scripts/bioinstall.py status openmm
python scripts/bioinstall.py usage openmm
```

`coverage` 从实际仓库内容计算数量，当前是 **10 个通用流程 Skill、63 款软件配方、79 类任务标签**，其中 26 款具有自动安装路径，37 款仅有安装引导；不同平台能否自动安装还要看 `plan` 的检查结果。一个 Skill 可以处理多款软件，因此 Skill 数不等于软件数。按科研领域查看全部软件见[覆盖矩阵](docs/COVERAGE.md)。26 款自动配方的全部已声明操作系统路线在 [72 项一次性安装测试](https://github.com/tyb-sdu/bioagent-skills/actions/runs/36392762085)中通过；其中 pdb-tools 在 Linux、Windows、macOS 均通过，ProDy 的 macOS 路线使用 Intel x86_64 运行器，原生 Windows 不在自动范围内。架构、GPU、科学结果及未来依赖变化仍需单独验证，详见[测试边界](docs/INSTALL_TESTING.md)。

新增 pdb-tools 的本机 PDB 文件编辑自动路线，以及 Phenix、Coot 的冷冻电镜模型构建/修整引导。Phenix 的下载权限和许可由用户自行办理；Coot 的 GUI 和平台包需在目标机检查。两者都不会由 `install --apply` 自动执行。

新增 ProDy 的局部结构动力学分析自动路线，以及 US-align、TM-align、MODELLER 的安装引导。MODELLER 需用户自行取得适用许可；结构比对软件不等于蛋白结构预测器。

Biotite 用于结构坐标分析与叠合，PeptideBuilder 按指定几何参数生成肽链；二者都不是蛋白质天然结构预测或蛋白-肽对接引擎。

ViennaRNA 的自动路线仅安装可 `import RNA` 的 Python 接口，**不会安装 RNAfold 等命令行套件**。需要完整套件时应按配方中的官方下载/安装说明另行选择。RNAstructure 暂时仅提供安装引导。所有自动 pip 路线只接受 wheel（含依赖），缺少兼容包时停止，不会偷偷转为源代码编译；第三方软件各自的许可不因本仓库采用 MIT 而改变。

`plan` 和 `suggest` 的 `supported_here` 对自动配方检查当前操作系统、处理器架构和已知 Python 版本；引导型配方仅检查已列出的操作系统。`ready_here` 还要求本机已有安装前提（例如 conda），具体障碍见 `blocking_reasons`。不支持的自动安装目标不会展示可执行命令；某些配方会显示只提供步骤的 `manual_fallback`。这些状态不是依赖求解或安装成功的保证。`install --apply` 将软件装入全新的独立环境，随后运行配方中的基础验收命令。成功时，会在当前用户的 `~/.bioagent-skills/receipts/` 写入安装记录。已有环境不会被脚本清理或覆盖。验收仅证明程序可被调用，不证明科研结果的正确性。

### 安装后的状态与调用方式

`status <id>` 只读取环境、包版本和最新安装收据摘要；不会导入科研软件、重装包或跑计算。可能的 `state` 包括：

| 状态 | 含义 |
| --- | --- |
| `package-present` | 找到目标环境并读到包版本，不等于当前验收已通过 |
| `package-unconfirmed` | 环境存在，但包版本无法确认 |
| `environment-missing` | 未找到预期的独立环境 |
| `manager-unavailable` | 无法调用 conda，不能判断其环境是否还在 |
| `inspection-error` | 环境查询失败或遇到同名环境歧义 |
| `guidance-only` | 当前没有自动检查该人工安装路线的能力 |

`receipt_version_matches_current` 只比较顶层软件版本，不能证明依赖或文件没有变化。收据是历史记录；损坏、超出读取上限或指向符号链接的收据不会被采信，存储的命令也不会被重放。成功的新安装记录还包含处理器架构、安装器 Python 版本和环境名。

`usage <id>` 在确认包版本后显示 `invocation_argv` 和适合本机终端的 `invocation_command`。Python 库使用隔离环境中的解释器；命令行软件使用其入口。它只展示命令，**不会运行命令或自动开始科研任务**。例如 Vina 的 conda 调用以 `conda run --prefix <实际环境路径> vina` 为前缀。请再按软件维护者文档选择输入文件和参数；若当前状态不明确，命令字段保持空值。

### 终端智能体入口：离线规则或本地模型

明确指定软件名，以及少量无歧义的中英文科研任务，可以直接离线匹配已审核配方，**不需要 Ollama 或模型额度**：

```bash
python scripts/bioagent.py ask "安装 OpenMM"
python scripts/bioagent.py ask "我需要蛋白和 DNA 对接工具"
```

若出现多个软件或任务，入口会要求用户选定，不会擅自替换明确指定的软件。离线词表只是保守入口，不是完整自然语言理解；未命中时可显式传入本机模型。

如需更灵活的任务表述，先按照 [Ollama 官方指南](https://docs.ollama.com/quickstart)在用户电脑上安装 Ollama，并由用户自行选择一个适合本机内存、支持结构化输出的**本地**模型。将以下 `MODEL_NAME` 替换成所选模型的真实名称；下载命令见 [Ollama CLI 文档](https://docs.ollama.com/cli)。本项目不预设模型名称、不自动拉取模型，也不需要云端 API 密钥。

```bash
ollama pull MODEL_NAME
python scripts/bioagent.py models
python scripts/bioagent.py ask --model MODEL_NAME "我需要安装蛋白和 DNA 对接工具"
python scripts/bioagent.py ask "安装 OpenMM" --apply
```

第一条 `ask` 只返回已审核配方和安装预览；`--apply` 也仅对自动安装配方有效，并会在交互式终端要求输入 `INSTALL <软件ID>` 才执行。引导型配方只显示步骤，不能被模型升级为自动执行。只有使用 `--model` 且离线规则未直接识别软件名时，才把请求发送到本机 `127.0.0.1:11434`；模型只能从仓库的任务/软件 ID 中分类，不能向安装器提供任意命令、包名或网址。该入口是首版单轮任务路由器，不支持任意软件、连续对话或自动执行引导型流程。

本地推理可以避免使用本项目的云端模型额度，但模型下载、磁盘、电力和用户电脑的内存/算力并非零成本。模型及软件各自的许可证仍需由使用者核对。

完整的本机执行边界与当前局限见[架构说明](docs/ARCHITECTURE.md)。

对于只提供引导的工具：

```bash
python scripts/bioinstall.py plan gnina
python scripts/bioinstall.py plan boltz2
```

终端智能体应先运行 `list`；面对科研任务而非指定软件时，使用 `tasks`、`suggest <task-id>` 查找候选，再运行 `plan`，把候选软件、方法差异、系统要求、下载内容及来源告诉用户。`suggest` 只按已审核的任务标签匹配，并不证明软件适合具体实验。用户提出安装请求后，智能体才调用适用的安装流程。它只能从已经审核的配方中选择，不应根据模型生成的任意包名或网址直接执行命令。

## 设计依据

- 安装方法以软件维护者的[官方安装文档和发布页](docs/SOURCES.md)为准；论文用于确认工具功能和适用领域，不能代替安装文档。
- 每个软件放在独立环境。conda 配方使用 `conda-forge` 并只对该命令指定渠道；不改用户全局配置。参见 [conda 渠道文档](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-channels.html)。
- 软件与预训练权重分开管理。例如 [Boltz](https://github.com/jwohlwend/boltz/blob/main/README.md)可能在首次预测时下载模型文件；[AlphaFold 3](https://github.com/google-deepmind/alphafold3/blob/main/WEIGHTS_TERMS_OF_USE.md)的参数有单独使用条款。ProteinMPNN、LigandMPNN、RFdiffusion 和 DiffDock 的推理也需核对模型文件。
- 自动安装配方固定了当前核对的顶层软件版本。收据记录实际顶层版本、命令与来源；完整依赖锁定和跨平台安装验证属于下一阶段。不要把本仓库视为对全部平台已经完成实测的声明。
- PDBFixer、Vina、FreeSASA、PROPKA、Open Babel、Meeko、MDTraj、ParmEd、Gemmi、ProLIF、OpenMMForceFields、PDB2PQR 和 APBS 的实际安装冒烟测试配置在 GitHub 临时环境中，验证范围和未覆盖的平台见[安装测试边界](docs/INSTALL_TESTING.md)。单元测试通过不等于软件安装成功。

## 开发与校验

```bash
python scripts/bioinstall.py validate
python scripts/validate_skills.py
python -m unittest discover -s tests -v
python -m pip wheel --no-deps --wheel-dir dist .
```

增加软件时，先读 [配方格式](docs/RECIPE_SCHEMA.md)，核对官方安装来源、操作系统支持、许可和最小验收，再增加 `catalog/<id>.json`。仅当现有流程无法清楚覆盖时新增 Skill。欢迎通过 issue 或 pull request 提交经过验证的安装配方。

原创 Skill、脚本和文档采用 MIT 许可。软件、容器、论文、模型权重和数据库仍遵守各自的许可与使用条款；它们不包含在本仓库中。
