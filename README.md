# BioAgent Skills

面向**用户自己电脑上的终端智能体**的生物计算软件安装 Skill 包。项目帮助智能体根据科研任务和本机条件选择软件、预览安装方案、安装到隔离环境，并运行基础验收。计算任务仍在用户选择的计算机或集群执行。仓库还提供一个最小化的本地模型终端入口 `scripts/bioagent.py`。

本仓库依据 [Agent Skills 规范](https://agentskills.io/specification)编写，Skill 放在 `.agents/skills/`，软件的具体来源与安装方式放在 `catalog/`。支持读取该目录的终端智能体可以按需加载 Skill；其他智能体需要将这些 Skill 接入其自身的加载机制。Skill 是指令和工作流，需要宿主智能体提供命令执行能力。

## 当前范围

| 流程 | 状态 | 首批软件 |
| --- | --- | --- |
| conda-forge 包安装到独立环境 | 可预览、可执行、可验收 | OpenMM、RDKit、GROMACS、Psi4 |
| PyPI 包安装到独立虚拟环境 | 可预览、可执行、可验收 | MDAnalysis |
| 官方二进制、容器、源码、权重、受限软件及尚未锁定版本的包 | 资料核对与安装引导 | AutoDock Vina、GNINA、PLIP、Boltz-2、AlphaFold 3、ProteinMPNN、LigandMPNN、RFdiffusion、HADDOCK3、LightDock、DiffDock、OpenFE、PDBFixer |

引导流程尚未提供一键安装。它们需要进一步锁定平台专用发布文件、镜像摘要、模型文件或许可条件。`plan` 不会改变电脑；`install` 默认也只预览，只有加 `--apply` 才会执行自动安装。脚本不会安装驱动、修改系统 Python、改动 conda 的全局配置、运行 `curl | sh`、安装受限权重或删除已有环境。

## 使用

需要 Python 3.10+。自动安装 conda 配方还需要用户电脑已经安装 conda；Windows 用户使用 Linux-only 配方前需要先准备 Linux/WSL 环境。以下命令在仓库根目录执行：

```bash
git clone https://github.com/tyb-sdu/bioagent-skills.git
cd bioagent-skills
```

```bash
python scripts/bioinstall.py doctor
python scripts/bioinstall.py list
python scripts/bioinstall.py tasks
python scripts/bioinstall.py suggest protein-nucleic-acid-docking
python scripts/bioinstall.py plan openmm
python scripts/bioinstall.py install openmm
python scripts/bioinstall.py install openmm --apply
python scripts/bioinstall.py verify openmm
```

`install --apply` 将软件装入全新的独立环境，随后运行配方中的基础验收命令。成功时，会在当前用户的 `~/.bioagent-skills/receipts/` 写入安装记录。已有环境不会被脚本清理或覆盖。验收仅证明程序可被调用，不证明科研结果的正确性。

### 本地模型终端入口

先按照 [Ollama 官方指南](https://docs.ollama.com/quickstart)在用户电脑上安装 Ollama，并由用户自行选择一个适合本机内存、支持结构化输出的**本地**模型。将以下 `MODEL_NAME` 替换成所选模型的真实名称；下载命令见 [Ollama CLI 文档](https://docs.ollama.com/cli)。本项目不预设模型名称、不自动拉取模型，也不需要云端 API 密钥。

```bash
ollama pull MODEL_NAME
python scripts/bioagent.py models
python scripts/bioagent.py ask --model MODEL_NAME "我需要安装蛋白和 DNA 对接工具"
python scripts/bioagent.py ask --model MODEL_NAME "安装 OpenMM" --apply
```

第一条 `ask` 只返回已审核配方和安装预览；`--apply` 也仅对自动安装配方有效，并会在交互式终端要求输入 `INSTALL <软件ID>` 才执行。引导型配方只显示步骤，不能被模型升级为自动执行。请求只发送到本机 `127.0.0.1:11434`；模型只能从仓库的任务/软件 ID 中分类，不能向安装器提供任意命令、包名或网址。未安装 Ollama 时仍可直接使用上面的 `bioinstall.py` 命令。该入口是首版单轮任务路由器，不支持任意软件、连续对话或自动执行引导型流程。

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

## 开发与校验

```bash
python scripts/bioinstall.py validate
python scripts/validate_skills.py
python -m unittest discover -s tests -v
```

增加软件时，先读 [配方格式](docs/RECIPE_SCHEMA.md)，核对官方安装来源、操作系统支持、许可和最小验收，再增加 `catalog/<id>.json`。仅当现有流程无法清楚覆盖时新增 Skill。欢迎通过 issue 或 pull request 提交经过验证的安装配方。

原创 Skill、脚本和文档采用 MIT 许可。软件、容器、论文、模型权重和数据库仍遵守各自的许可与使用条款；它们不包含在本仓库中。
