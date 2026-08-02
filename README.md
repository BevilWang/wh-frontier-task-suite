# WH Frontier Task Suite

一个可开箱即用的 Codex 多智能体插件，用于创作、独立二审、修复和发布 Frontier-Bench / Harbor 基准任务。

插件已经内置 7 个 Frontier-Bench 参考题，以及任务创作所需的 checks、rubrics、taxonomy 和 task template。GitHub 用户安装插件后无需再单独克隆 Frontier-Bench 仓库。

## 工作流程

```text
Coordinator
  -> isolated author
  -> isolated independent reviewer
  -> isolated repairer (when required)
  -> fresh two-phase re-reviewer
  -> immutable-snapshot release agent
```

整个流程在一个 Codex 任务内完成。协调器通过子智能体和磁盘产物交接工作，不要求用户手动创建多个任务。

## 包含的 Skills

### `$run-wh-frontier-pipeline`

推荐入口。负责调度完整多智能体流水线：

- 使用空继承上下文启动每个阶段智能体；
- 串行执行所有写入阶段，避免多个智能体同时修改提交；
- 使用 `review.json`、源码指纹和 `repair-ledger.json` 作为阶段门；
- 修复后先进行 from-scratch review，再检查旧问题是否真正关闭；
- 只有独立复审为 `PASS` 才能进入发布；
- 发布包必须与通过复审的不可变快照指纹一致。

### `$create-wh-frontier-tasks`

根据一个内置参考题创作、实现、验证并打包 3 个原创任务，包括：

- 新颖性与难度设计；
- `instruction.md`、`task.toml`、`environment/`、`solution/` 和 `tests/`；
- static、oracle、nop、泄漏和抗投机检查；
- 提交目录及 zip 归档。

### `$verify-wh-frontier-tasks`

使用独立 AI 和确定性证据进行只读二审，检查：

- 相对参考题的实质原创性；
- 题面与测试的双向一致性；
- 可解性、oracle/nop 结果及验证器质量；
- 隔离、泄漏、权限安全、确定性和打包规范。

输出 `evidence.json`、`review.json` 和 `review.md`，结论只能是 `PASS`、`FAIL` 或 `PROVISIONAL`。

### `$repair-wh-frontier-tasks`

读取独立二审报告，逐条复现 finding、修复根因、补充回归测试，并生成可验证的 repair ledger。完成的 ledger 必须包含每个任务的 static、oracle 和 nop 回归证据。

## 内置参考题

| 方向 | 参考题 |
| --- | --- |
| Software / Databases | `wal-recovery-ordering` |
| Software / Data Engineering | `ontology-kg-querying` |
| Software / Algorithms | `rs-archive-clone` |
| Science / Math | `lean-midpoint-proof` |
| Science / Physics | `ks-solver-cpp` |
| ML / Inference | `vllm-deepseek-streaming` |
| Science / Robotics | `biped-contact-dynamics` |

参考文件位于：

```text
plugins/wh-frontier-task-suite/assets/frontier-bench/
```

该目录是 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench) 提交 `3d694e919871dbf21ea5ff618782c99a3cb3663f` 的精选快照。

为控制插件体积，快照排除了 `ks-solver-cpp/tests/wheels/**` 中的大型预编译 wheels；题面、元数据、环境源码、solution、tests、checks 和 rubrics 均已保留。详细来源和排除清单见 [PROVENANCE.md](plugins/wh-frontier-task-suite/assets/frontier-bench/PROVENANCE.md)。

上游内容采用 Apache License 2.0，许可证和第三方声明见：

- [Frontier-Bench LICENSE](plugins/wh-frontier-task-suite/assets/frontier-bench/LICENSE)
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

## 安装

需要带有 `plugin` 子命令并支持子智能体协作的 Codex。

```bash
codex plugin marketplace add BevilWang/wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

安装或更新后，新建一个 Codex 任务以载入插件。

更新插件：

```bash
codex plugin marketplace upgrade wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

## 开箱即用

安装完成后，在 Codex 中发送：

```text
Use $run-wh-frontier-pipeline to run the complete Frontier-Bench lifecycle.

Reference: wal-recovery-ordering
Workspace root: /path/to/writable/workspace
Owner: example-owner
Contact: owner@example.com
Submission date: 20260802
Maximum repair rounds: 2

Use the bundled Frontier-Bench snapshot. Do not ask me to open separate tasks.
```

只需提供参考题名称和可写工作目录；参考题路径、checks、rubrics 与模板由插件自动解析。

7 个方向的完整提示词及手工阶段提示词见 [docs/prompts.md](docs/prompts.md)。

## 产物结构

```text
OWNER_submission/
|-- README.md
|-- task-1-short-name/
|-- task-2-short-name/
`-- task-3-short-name/
```

每个任务包含：

```text
instruction.md
task.toml
environment/
solution/
tests/
```

最终归档名称：

```text
OWNER_Category_Subcategory_YYYYMMDD.zip
```

## 运行要求

插件本身及参考题阅读不需要额外下载。完整运行生成任务的容器验证时，仍可能需要：

- Python 3；
- Docker；
- Harbor；
- 参考题或新任务声明的系统依赖。

如果本机缺少 Harbor 或 Docker，Skill 会完成可执行的静态检查，并把未运行项目标为 `PROVISIONAL`，不会伪报为通过。

## 仓库结构

```text
.
|-- .agents/plugins/marketplace.json
|-- docs/prompts.md
|-- THIRD_PARTY_NOTICES.md
`-- plugins/wh-frontier-task-suite/
    |-- .codex-plugin/plugin.json
    |-- assets/frontier-bench/
    `-- skills/
        |-- run-wh-frontier-pipeline/
        |-- create-wh-frontier-tasks/
        |-- verify-wh-frontier-tasks/
        `-- repair-wh-frontier-tasks/
```

## 本地验证

```bash
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/create-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/verify-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/repair-wh-frontier-tasks/scripts -p "test_*.py"
```

参考 bundle 也可单独验证：

```bash
python plugins/wh-frontier-task-suite/skills/create-wh-frontier-tasks/scripts/validate_reference_bundle.py \
  plugins/wh-frontier-task-suite/assets/frontier-bench
```

## 审查完整性

- Reviewer 不接收 Author 的结论或预期 verdict。
- 可能写入文件的审查命令必须在 disposable copy 上运行。
- 源码检查不能代替必须执行的 runtime checks。
- `PROVISIONAL` 不等于通过。
- 修复后的提交必须由新的独立 Reviewer 复审。
- Release 只能打包与最终 `PASS` 指纹一致的不可变快照。
