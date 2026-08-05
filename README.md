# Frontier Task Suite

一个 Codex 插件：用多智能体流水线创作三道原创 Frontier-Bench/Harbor 基准任务，内置 7 道参考题与完整快照，无需另克隆仓库。

## 运行流程

### 1. 创作（Author）

- 确认输入：参考题、可写工作目录、提交人、联系方式、日期。
- 评估参考题可运行性（镜像大小/联网/算力/墙钟），选择设计方向族与确定性种子，并记录到包 README 与运行状态。
- 设计三道原创任务（概念卡），初始化三题提交骨架。
- 逐题实现：`instruction.md`（目标、产物、被评行为、超时与反作弊句）→ `environment/`（仅 agent 可见输入）→ `solution/`（oracle 参考解）→ `tests/`（独立验证器容器）→ `task.toml`（资源与元数据）。
- 验证：构建双容器，oracle 必须得 1、nop 必须得 0（非确定性任务 oracle 至少跑 5 次），跑全部静态检查与结构校验。
- 四轮加固扫描：契约矩阵、输入/领域全量、验证器对抗、运行时 harness。
- 产出未打包的三题提交（本阶段不生成 zip）。

### 2. 预评审加固（Harden）

- 由没有作者上下文的加固者执行对抗性作者门禁（同样做四轮扫描），可修复缺陷并留下加固证据。
- 重新运行结构校验并记录提交指纹；若提交仍无效，返回创作，不消耗评审轮次。

### 3. 内部评审（Review r1）

- 全新独立评审员按 9 项标准逐题审查，并运行静态检查 + oracle + nop 收集证据。
- 完成四项审计扫描：契约测试矩阵、输入/领域全量、验证器对抗、运行时 harness。
- 产出 `evidence.json` / `review.json` / `review.md`，校验报告并比对评审前后提交指纹（提交被改动即作废评审）。
- 结论处理：`PASS` → 进入发布；`FAIL` → 进入修复；`PROVISIONAL` → 只补跑缺失的检查；报告无效 → 同一评审员补一次。

### 4. 修复（Repair rN）

- 校验评审指纹与当前提交一致后导入修复台账。
- 逐条 triage 评审发现（fixed / rejected / not_applicable / blocked），按契约层做根因修复，不为通过测试而削弱题目。
- 修复 halo：对全部三题（含未被点名的）重做加固矩阵，防止同根因在兄弟路径复发。
- 重跑完整回归门禁（静态 + oracle + nop + 结构校验），产出 `repair-ledger.json` / `repair.md` 与新指纹。

### 5. 复审（Review rN+1）

- 全新评审员对修复后提交做 from-scratch 复审（不透露旧结论与修复思路）。
- closure 阶段复用同一评审员核验修复，以 closure 结论为准。
- 仍为 `FAIL` 则进入下一轮修复，默认最多 5 轮；同一 blocker 连续两轮无进展则停止。

### 6. 发布（Release）

- 仅当内部 `PASS`；核对当前提交指纹与通过评审的指纹一致。
- 打包不可变 zip（校验和 + 解包冒烟 + 指纹比对），发布阶段不得再改动内容。
- 将 zip 单独交给 Harbor 平台执行官方 `harbor check`（外部步骤，插件本地不执行）。

## 快速使用

### 运行要求
Codex app/CLI（多智能体协作）、Python 3.12+、Docker（daemon 运行中）、Harbor CLI（`python -m uv tool install harbor`，仅本地 oracle/nop 运行时）、可写工作目录。Windows 需设置 `PYTHONUTF8=1`、`PYTHONIOENCODING=utf-8` 并重启；macOS/Linux 无需额外配置。

### 安装
- **Codex app**：打开本仓库 → 重启 Codex → Plugins 安装 Frontier Task Suite。
- **Codex CLI**：`codex plugin marketplace add .` 后 `codex plugin add frontier-task-suite@frontier-task-suite`。

### 快速开始
新开一个 Codex 任务，调用：

```text
使用 $run-wh-frontier-pipeline。

参考题：wal-recovery-ordering
工作目录：\path\to\writable-workspace
提交人：Your Name
联系方式：name@example.com
提交日期：20260805
```
可选 `Maximum repair rounds: N`（默认 5）。

## 内置参考题

| Category | Reference |
| --- | --- |
| Software / Databases | `wal-recovery-ordering` |
| Software / Data Engineering | `ontology-kg-querying` |
| Software / Algorithms | `rs-archive-clone` |
| Science / Math | `lean-midpoint-proof` |
| Science / Physics | `ks-solver-cpp` |
| ML / Inference | `vllm-deepseek-streaming` |
| Science / Robotics | `biped-contact-dynamics` |

## 许可证
[MIT License](LICENSE)。内置参考材料来自 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench)（Apache-2.0）。
