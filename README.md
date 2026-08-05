# WH Frontier Task Suite

一个用于**创作、加固、内部评审并发布**三道原创 Frontier-Bench/Harbor 任务的 Codex 插件：以内置的一道参考题为校准基准，经 **内部评审循环 r1、r2、…直到内部 PASS** 后发布不可变压缩包。

## 工作流程

插件把单个参考题转化为一份完整的三题提交包：

- **创作（Author）**：为每道任务生成原创目标、Agent 环境、oracle 参考解、验证器与元数据。
- **加固（Harden）**：在评审前完成契约、输入域、对抗与运行时四轮扫描。
- **内部评审循环（r1、r2、…）**：由全新独立 AI 执行语义评审，并收集确定性 oracle、nop 与内置静态检查证据；`FAIL` 则依据评审发现修复并进入下一轮 `rN+1` 重新评审，直到 **内部 PASS**。
- **发布（Release）**：只发布与通过内部评审的源码指纹完全一致的不可变压缩包。

插件内置参考任务、校验脚本与评审工具，无需另外克隆 Frontier-Bench 仓库。

## Harbor 官方 check（外部步骤）

插件只负责本地内部评审循环并产出发布包，**不在本地运行官方 `harbor check`**。内部 PASS 并发布后，请把压缩包**单独交给 Harbor 平台**运行官方检查（rubric 静态校验与后续评测）。该外部步骤不在本插件中实现，具体提交方式遵循 Harbor 平台流程。

## 支持的参考题

| 方向 | 参考题 |
| --- | --- |
| 软件 / 数据库 | `wal-recovery-ordering` |
| 软件 / 数据工程 | `ontology-kg-querying` |
| 软件 / 算法 | `rs-archive-clone` |
| 科学 / 数学 | `lean-midpoint-proof` |
| 科学 / 物理 | `ks-solver-cpp` |
| 机器学习 / 推理 | `vllm-deepseek-streaming` |
| 科学 / 机器人 | `biped-contact-dynamics` |

## 安装

### Codex app

1. 在 Codex 应用中打开本仓库。
2. 重启 Codex，使其加载 `.agents/plugins/marketplace.json`。
3. 打开 **Plugins**，找到 **WH Frontier Task Suite** 并安装。

### Codex CLI

添加仓库为市场并安装插件：

```bash
codex plugin marketplace add .
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

或推送后在远端安装：

```bash
codex plugin marketplace add https://github.com/BevilWang/wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

如果市场名不同，用 `codex plugin marketplace list` 确认。

完整指引与安装后验证清单见 [docs/app-install.md](docs/app-install.md)。

## 技能

安装后新开一个 Codex 任务，调用以下四个技能：

| 技能 | 适用场景 |
| --- | --- |
| `$run-wh-frontier-pipeline` | 跑完整生命周期：创作 → 内部评审循环 → 发布。 |
| `$create-wh-frontier-tasks` | 单独创建或校验三题提交包。 |
| `$verify-wh-frontier-tasks` | 独立审计已有三题提交包。 |
| `$repair-wh-frontier-tasks` | 依据内部评审发现修复并准备下一轮复审。 |

## 快速开始

```text
使用 $run-wh-frontier-pipeline。

参考题：wal-recovery-ordering
工作目录：E:\path\to\writable-workspace
提交人：Your Name
联系方式：name@example.com
提交日期：20260805
```

默认内部评审循环最多修复并复审 5 轮；如需上限，添加 `Maximum repair rounds: N`。

## 运行要求

- Codex app 或 Codex CLI
- Python 3.12+
- Docker Desktop 且 daemon 处于运行状态（本地 oracle/nop 运行时）
- Harbor CLI（`python -m uv tool install harbor`，仅用作本地 oracle/nop 运行时工具；官方 `harbor check` 在外部执行）
- 一个可写的工作目录

Windows 下先设置 UTF-8 变量并重启 Codex：

```powershell
setx PYTHONUTF8 1
setx PYTHONIOENCODING utf-8
```

## 参考题可运行性

七道内置参考题各自有可运行性画像，帮助你选择当前硬件能真正构建并验证的参考题：

```text
python skills/create-wh-frontier-tasks/scripts/runnability_report.py fb --reference REFERENCE
```

要点：

- 七道题都可在 **CPU** 上验证，无需 GPU 或模型权重。
- 每道题的镜像构建都需要网络。`lean-midpoint-proof` 还会下载 Lean 工具链，`biped-contact-dynamics` 会安装较大的 drake 依赖，`vllm-deepseek-streaming` 会拉取数 GB 的 vLLM CPU 镜像。
- `ks-solver-cpp` 是唯一不自包含的参考题：其 verifier wheels 按设计从快照中排除。创作新题不需要它们；如需运行该参考题做校准，先还原：`python scripts/restore_ks_wheels.py`（详见 [fb/PROVENANCE.md](fb/PROVENANCE.md)）。
- 完整可行性表与逐类创作指南：[reference-profiles.md](skills/create-wh-frontier-tasks/references/reference-profiles.md)。

## 设计多样性

同一参考题多次运行容易收敛到相似的选题。为避免重复，每次运行都从参考题的**设计方向族池**中采样一个方向族，并在该方向族内创作：

```text
python skills/create-wh-frontier-tasks/scripts/select_variant.py --reference REFERENCE --seed SEED
python skills/create-wh-frontier-tasks/scripts/select_variant.py --reference REFERENCE --variant FAMILY_ID
```

`submission_tool.py init --seed/--variant` 会把种子与方向族写入包 README 的 `## Design provenance`。方向族定义见 `references/design-pools.json`。

## 开发与测试

仓库仅依赖 Python 标准库即可自测：

```powershell
python scripts/run_all_tests.py                                # 全部单元测试
python scripts/validate_plugin_release.py                      # 清单 + 市场 + 仓库卫生
python scripts/validate_windows_paths.py                       # Windows 路径预算
python skills/create-wh-frontier-tasks/scripts/validate_reference_bundle.py fb  # 内置参考题
```

GitHub Actions 会在每次 push / pull request 时于 Windows 与 Ubuntu 上运行以上全部检查。

## 仓库结构

```text
.
├── .codex-plugin/plugin.json   # 插件清单
├── .agents/plugins/marketplace.json  # Codex app 市场条目
├── .github/workflows/ci.yml    # Windows + Ubuntu CI 矩阵
├── .gitattributes              # 脚本与配置统一 LF 行尾
├── skills/                     # 四个 Codex 技能
├── fb/                         # 内置 Frontier-Bench 快照
├── docs/                       # 安装与使用文档
├── scripts/                    # 仓库校验辅助脚本
├── LICENSE                     # 本项目 MIT 许可证
├── README.md                   # 本文件
└── THIRD_PARTY_NOTICES.md      # 第三方声明
```

## 许可证与出处

本项目（插件代码、技能与工具）采用 [MIT License](LICENSE)。

内置参考材料来自 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench)，按 Apache License 2.0 分发。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [fb/PROVENANCE.md](fb/PROVENANCE.md)。