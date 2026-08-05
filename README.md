# WH Frontier Task Suite

一个用于**创作、加固、评审、修复并发布**三道原创 Frontier-Bench/Harbor 任务的 Codex 插件：从内置参考题出发，经 **内部评审循环 r1、r2、…直到内部 PASS** 后发布不可变压缩包，无需另外克隆 Frontier-Bench 仓库。

## 功能

- **创作（Author）**：生成三道原创任务——目标、Agent 环境、oracle 参考解、验证器与元数据。
- **加固（Harden）**：评审前完成契约、输入域、对抗与运行时四轮扫描。
- **评审（Review）**：由全新独立 AI 执行语义评审，并收集 oracle、nop 与内置静态检查证据，构成内部评审循环的一轮（r1、r2、…）。
- **修复（Repair）**：依据评审发现修复，进入下一轮 `rN+1` 重新评审，直到 **内部 PASS**。
- **发布（Release）**：只发布与通过内部评审源码指纹一致的不可变压缩包。
- **Harbor 官方 check（外部步骤）**：插件不在本地运行官方 `harbor check`；内部 PASS 并发布后，将压缩包**单独交给 Harbor 平台**检查。

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

```bash
codex plugin marketplace add https://github.com/BevilWang/wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

完整安装与验证清单见 [docs/app-install.md](docs/app-install.md)。

## 使用

新开一个 Codex 任务，调用：

```text
使用 $run-wh-frontier-pipeline。

参考题：wal-recovery-ordering
工作目录：E:\path\to\writable-workspace
提交人：Your Name
联系方式：name@example.com
提交日期：20260805
```

默认内部评审循环最多修复并复审 5 轮；如需上限，添加 `Maximum repair rounds: N`。

| 技能 | 用途 |
| --- | --- |
| `$run-wh-frontier-pipeline` | 跑完整流程：创作 → 加固 → 评审 → 修复 → 发布。 |
| `$create-wh-frontier-tasks` | 单独创建或校验三题提交包。 |
| `$verify-wh-frontier-tasks` | 独立审计已有三题提交包。 |
| `$repair-wh-frontier-tasks` | 依据评审发现修复并准备下一轮复审。 |

## 运行要求

- Codex app 或 Codex CLI
- Python 3.12+
- Docker Desktop（daemon 处于运行状态）
- Harbor CLI（`python -m uv tool install harbor`，仅作本地 oracle/nop 运行时；官方 `harbor check` 在外部执行）
- 一个可写的工作目录

Windows 下先设置 UTF-8 变量并重启 Codex：

```powershell
setx PYTHONUTF8 1
setx PYTHONIOENCODING utf-8
```

## 许可证

[MIT License](LICENSE)。内置参考材料来自 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench)，按 Apache-2.0 分发。