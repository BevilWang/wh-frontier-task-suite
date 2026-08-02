# WH Frontier Task Suite

一个面向 Codex 的 Frontier-Bench 多智能体插件：从一个参考题出发，自动完成 **3 道原创任务的创作、独立二审、问题修复、重新复审和最终打包**。

插件内置 7 个 Frontier-Bench 参考题，以及 checks、rubrics、taxonomy 和 task template。用户无需手动克隆 Frontier-Bench，也无需为不同阶段单独创建 Codex 任务。

## 核心功能

- **自动创作**：生成 3 道原创任务及完整的 `instruction.md`、`task.toml`、环境、solution 和 tests。
- **独立二审**：由隔离的 Reviewer 检查原创性、可解性、题面与测试一致性、泄漏及 verifier 质量。
- **自动修复**：复现二审问题、修复根因并补充回归测试。
- **重新复审**：使用新的 Reviewer 从头审查，避免 Author 或 Repairer 的上下文影响结论。
- **安全发布**：只有最终复审为 `PASS` 时，才会从已审查的不可变快照生成 zip 和校验和。

```text
Coordinator
  -> Author
  -> Independent Reviewer
  -> Repairer（需要时）
  -> Fresh Re-reviewer
  -> Release Agent
```

## 安装

需要带有 `plugin` 子命令并支持子智能体的 Codex。

```bash
codex plugin marketplace add BevilWang/wh-frontier-task-suite --ref main
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

安装完成后，新建一个 Codex 任务以加载插件。

Marketplace 由 GitHub 仓库提供，Codex 会自动获取插件内容；用户不需要手动执行 `git clone`。

更新插件：

```bash
codex plugin marketplace upgrade wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

## 一条提示词运行完整流程

在新的 Codex 任务中发送：

```text
Use $run-wh-frontier-pipeline.

Reference: wal-recovery-ordering
Workspace root: /path/to/writable/workspace
Owner: example-owner
Contact: owner@example.com
Submission date: <YYYYMMDD>
Maximum repair rounds: 2
```

其中：

- `Reference`：从下方 7 个内置参考题中选择一个；
- `Workspace root`：保存任务、审查记录和发布包的可写目录；
- `Owner`、`Contact`、`Submission date`：写入提交元数据；
- `Maximum repair rounds`：可省略，默认值为 `2`。

随后插件会自动启动各阶段子智能体并通过磁盘产物交接，不需要用户手动切换任务。流程结束后会报告每个阶段的状态、验证证据、最终归档路径和校验和。

## 内置参考题

| 方向 | `Reference` |
| --- | --- |
| Software / Databases | `wal-recovery-ordering` |
| Software / Data Engineering | `ontology-kg-querying` |
| Software / Algorithms | `rs-archive-clone` |
| Science / Math | `lean-midpoint-proof` |
| Science / Physics | `ks-solver-cpp` |
| ML / Inference | `vllm-deepseek-streaming` |
| Science / Robotics | `biped-contact-dynamics` |

7 个方向的完整提示词和手工阶段提示词见 [docs/prompts.md](docs/prompts.md)。

## 质量门与结果

Reviewer 只能给出以下结论：

- `PASS`：所有必要检查均有通过证据，可以发布；
- `FAIL`：存在可复现的问题，进入自动修复；
- `PROVISIONAL`：缺少必要的运行证据，不能视为通过。

若修复轮数耗尽、基础设施不可用或仍存在实质问题，插件会停止并报告 blocker，而不会绕过审查生成发布包。

最终提交包含 3 个任务：

```text
OWNER_submission/
|-- README.md
|-- task-1-short-name/
|-- task-2-short-name/
`-- task-3-short-name/
```

发布归档命名为：

```text
OWNER_Category_Subcategory_YYYYMMDD.zip
```

## 可单独调用的 Skills

| Skill | 用途 |
| --- | --- |
| `$run-wh-frontier-pipeline` | 推荐入口，自动协调完整多智能体流水线 |
| `$create-wh-frontier-tasks` | 只执行任务创作、验证和打包 |
| `$verify-wh-frontier-tasks` | 只执行独立、只读二审 |
| `$repair-wh-frontier-tasks` | 根据二审报告检查并修复问题 |

## 运行要求

安装完成后，读取内置参考题无需再下载 Frontier-Bench。执行完整容器验证时可能需要：

- Python 3；
- Docker；
- Harbor；
- 任务声明的其他系统依赖。

缺少必要运行环境时，插件会执行仍可完成的检查，并将缺失证据标记为 `PROVISIONAL`。

## 参考资料与许可

内置参考包来自 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench)，具体版本与收录范围记录在来源清单中。

为控制插件体积，参考包排除了 `ks-solver-cpp/tests/wheels/**` 中的大型预编译 wheels，其余所需题面、源码、solution、tests、checks 和 rubrics 均已保留。

- [参考包来源和排除清单](plugins/wh-frontier-task-suite/assets/frontier-bench/PROVENANCE.md)
- [Frontier-Bench Apache-2.0 LICENSE](plugins/wh-frontier-task-suite/assets/frontier-bench/LICENSE)
- [第三方声明](THIRD_PARTY_NOTICES.md)

## 本地验证

```bash
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/create-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/verify-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/repair-wh-frontier-tasks/scripts -p "test_*.py"
```

验证内置参考包：

```bash
python plugins/wh-frontier-task-suite/skills/create-wh-frontier-tasks/scripts/validate_reference_bundle.py \
  plugins/wh-frontier-task-suite/assets/frontier-bench
```
