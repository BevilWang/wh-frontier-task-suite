# WH Frontier Task Suite

一个面向 Frontier-Bench / Harbor 任务生产的 Codex 插件，提供“创作 → 独立二审 → 报告驱动修复 → 独立复审”的完整工作流。

插件内置任务规范和 7 个参考方向的能力画像，**不需要读取 Fellow 认领表、claim sheet 或其他 assignment PDF**。

## Skills

### `$create-wh-frontier-tasks`

从一个受支持的 Frontier-Bench 参考题中提炼难度机制，创作、实现、验证并打包 3 个原创任务。它负责：

- 新颖性与难度设计；
- `instruction.md`、`task.toml`、`environment/`、`solution/`、`tests/`；
- oracle/nop、静态检查、泄漏与抗投机检查；
- 提交目录和 zip 打包。

### `$verify-wh-frontier-tasks`

让一个没有继承创作上下文的新 AI 对候选任务进行只读二审。它负责：

- 记录提交与参考题指纹；
- 运行静态、oracle、nop 和必要的攻击测试；
- 检查原创性、可解性、题面—测试一致性、验证器质量和隔离安全；
- 生成 `review.json`、`review.md` 和 `PASS` / `FAIL` / `PROVISIONAL` 结论。

### `$repair-wh-frontier-tasks`

读取独立二审报告，逐条复现 finding，修复根因并建立 repair ledger。修复完成后必须交给另一个新的 AI 使用 `$verify-wh-frontier-tasks` 复审，不能自行宣布通过。

## 支持的 7 个参考方向

| 方向 | 参考题 |
| --- | --- |
| Software / Databases | `wal-recovery-ordering` |
| Software / Data Engineering | `ontology-kg-querying` |
| Software / Algorithms | `rs-archive-clone` |
| Science / Math | `lean-midpoint-proof` |
| Science / Physics | `ks-solver-cpp` |
| ML / Inference | `vllm-deepseek-streaming` |
| Science / Robotics | `biped-contact-dynamics` |

7 个方向的可复制中文提示词，以及二审、修复、复审和最终打包提示词，见 [docs/prompts.zh-CN.md](docs/prompts.zh-CN.md)。

## 安装

需要带有 `plugin` 子命令的 Codex CLI。

```bash
codex plugin marketplace add BevilWang/wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

安装或更新后请新建一个 Codex 任务，使新 skills 进入上下文。

更新 marketplace 和插件：

```bash
codex plugin marketplace upgrade wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

## 推荐工作流

1. 新建任务 A，用 `$create-wh-frontier-tasks` 生成候选任务。
2. 新建任务 B，只提供原始候选目录、参考题目录和输出目录，用 `$verify-wh-frontier-tasks` 独立二审。
3. 若结论不是 `PASS`，在可写任务中用 `$repair-wh-frontier-tasks` 修复。
4. 新建任务 C，用 `$verify-wh-frontier-tasks` 独立复审。
5. 只有复审为 `PASS` 才能打包；`PROVISIONAL` 不等于通过。

## 仓库结构

```text
.
├── .agents/plugins/marketplace.json
├── docs/prompts.zh-CN.md
└── plugins/wh-frontier-task-suite/
    ├── .codex-plugin/plugin.json
    └── skills/
        ├── create-wh-frontier-tasks/
        ├── verify-wh-frontier-tasks/
        └── repair-wh-frontier-tasks/
```

## 本地验证

三个技能都带有确定性辅助脚本和单元测试：

```bash
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/create-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/verify-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/repair-wh-frontier-tasks/scripts -p "test_*.py"
```

插件开发源由 `plugin-creator` 的 `validate_plugin.py` 验证；每个 skill 由 `skill-creator` 的 `quick_validate.py` 验证。

## 隐私与安全

- 插件不会要求读取认领表或 assignment PDF。
- 独立二审默认不修改候选任务。
- 不应把隐藏测试、oracle 真值或私密数据发送到外部服务。
- 所有“通过”结论都必须对应实际运行证据，未运行的必需检查不能标为通过。
