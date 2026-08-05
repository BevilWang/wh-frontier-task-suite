# Frontier Task Suite

一个 Codex 插件：用多智能体流水线创作三道原创 Frontier-Bench/Harbor 任务（创作 → 加固 → 独立评审 → 修复 → 不可变发布），内置 7 道参考题与完整 Frontier-Bench 快照，无需另克隆仓库。

## 功能

- **创作三题**：从内置参考题中选一，生成三道原创任务，每题含 `instruction.md`、`task.toml`、`environment/`、`solution/`、`tests/` 与元数据；只保留参考题难度类别，不复制其数据/答案/测试。
- **多智能体流水线**（`$run-wh-frontier-pipeline`）：author → hardener → reviewer(r1) → [repair(rN) → 全新 reviewer(rN+1)] → release，内部评审循环直到 `PASS`（默认最多 5 轮）。
- **四个技能**：`$create-wh-frontier-tasks`（创作/加固/打包）、`$verify-wh-frontier-tasks`（独立评审）、`$repair-wh-frontier-tasks`（按评审修复）、`$run-wh-frontier-pipeline`（编排）。
- **独立评审**：全新上下文的 AI 评审 + oracle/nop/静态检查证据，产出 schema-2 `review.json`；报告无效可复用同一评审员补一次。
- **不可变发布**：只发布与通过内部评审源码指纹一致的 zip（校验和 + 解包冒烟）；官方 `harbor check` 是外部步骤，插件本地不执行。
- **子 agent 规模**：5 种角色；r1 直接 PASS 时 4 个，每轮修复 +2，默认上限 5 轮 → 最多 14 个。

## 设计特点

### 证据与不可变性
- **指纹链**：`review_tool snapshot` 对提交逐文件 SHA-256 并生成树指纹，评审前后 `compare` 比对；评审期间提交被改动即作废该评审。
- **版本化产物**：`evidence.json` / `review.json` / `repair-ledger.json` 均为 schema-2 机器可读格式（要求完成全部四轮 audit_sweeps、`stopped_after_first_blocker=false`），并兼容 schema-1 续跑旧流程。
- **负样本夹具库**：`fb/c/test-tasks/` 内置 65 个故意损坏的任务（`fail-static-*`、`fail-rubric-*`、`fail-validate-*`、`fail-analysis-*`），用于自测校验器、评审工具与修复工具确实能识别每一类失败——工具本身先被测试过。

### 防趋同与原创性
- **设计方向族**：每道参考题有 4 个互斥方向族（`design-pools.json`），`select_variant.py` 用 `SHA-256(reference:seed)` 确定性抽样；seed + variant 自动记入包 README 与 `pipeline-state.json`，流水线会避开最近已用过的族，防止重复运行产出趋同任务。

### 质量闸门与防作弊
- **Canary 防污染**：`harbor-canary GUID 26b5c67b-…` 必须出现在 `instruction.md` 与 `task.toml`，标记基准数据不得进入训练语料。
- **instruction 强制契约**：绝对 `/app/...` 路径、末尾超时句（"You have N seconds…"）与反作弊句，全部由静态校验器强制。
- **静态校验器**（`submission_tool.py validate`）：恰好 3 个 `task-N-<slug>`（编号 1/2/3、目录全名 ≤3 个连字符 token）、无 TODO、无缓存/生成目录（`__pycache__`/`.venv`/`node_modules`/`.lake` 等）、`environment_mode="separate"`、非空 artifacts、元数据字段齐全且专家时间 >0、环境 Dockerfile 不得 COPY/ADD `solution`/`tests`、python 测试须 >3 条或含变体标记（random/parametrize/hidden fixtures）、包 README 必含 Owner/Contact/Reference/Reference link/Modality/Oracle/Nop/Static checks。
- **打包安全**：`package` 先 validate、不过即拒绝打包；经 sanitized staging 清理后再归档；`init`/`package` 都拒绝覆盖已有提交/归档。
- **双环境隔离与验证器安全**：agent 与验证器双容器分离，真相只放验证器；验证器依赖 bake 进 `tests/Dockerfile`（禁止运行时联网安装）；只收窄产物；非特权执行 agent 代码、root 写二进制奖励 0/1、杀进程组、pytest 出 CTRF；对 nop、常量输出、可见样例硬编码、reward 覆盖、后台存活做对抗探测。
- **四轮加固 + 九项评审标准**：契约矩阵、输入/领域全量、验证器对抗、运行时 harness；评审按 9 项标准，结论只有 `PASS`/`FAIL`/`PROVISIONAL`（PROVISIONAL 不能转 PASS）。非确定性任务 oracle 至少跑 5 次。
- **修复 halo**：修复任何 finding 后，须对全部三题（含未被点名的）重做 schema-2 加固矩阵，防止同根因在兄弟路径复发。

### 环境适配与工程保障
- **诚实降级**：Docker/Harbor 不可用时跑完静态/单元检查，把确切 blocker 与替代证据写进包 README，绝不谎称未跑的检查已通过。
- **运行环境适配**：逐阶段 preflight（`harbor --version`、`docker version`；Windows 另需 UTF-8 变量）；Docker 停了先启动再继续，不消耗评审/修复轮次；Windows 长路径用短根 + `subst` + `--jobs-dir`（macOS/Linux 无此问题，如需可同样指定短 `--jobs-dir`），不改动已评审提交；全部参考题 CPU 可验证，创作前用 `runnability_report.py` 评估镜像大小/联网需求/算力/墙钟。
- **跨平台仓库设计**：`fb/` 快照用短目录（`c/d/r/t`、`wr/kg/rs/lm/ks/vs/bd`），在 Windows / macOS / Linux 上都能免 `core.longpaths` 检出；`validate_reference_bundle.py` 同时解析 bundled 短布局与上游标准布局；`validate_windows_paths.py` 拒绝 Windows 保留名（CON/COM1 等）、非法字符、超长路径与大小写碰撞，保证仓库在任何平台都可安全检出。
- **三平台 CI**：GitHub Actions 在 **ubuntu + windows + macOS** 上跑全部单元测试、插件清单/市场校验、参考题解析、runnability 报告、Windows 路径校验；Windows 额外做深路径 git clone 测试。
- **沙箱合规**：不关闭宿主沙箱、不申请 blanket 绕过、Docker/Harbor 只做范围化授权；评审员只读提交，只能写评审目录或一次性副本。

## 参考题

| 参考题 | 方向 | 难度机制（抽象保留） |
| --- | --- | --- |
| `wal-recovery-ordering` | 软件/数据库 | 存储管线耦合 bug、崩溃一致性/并发可见性不变量 |
| `ontology-kg-querying` | 软件/数据工程 | 逆向 schema、异构记录对齐、隐藏未来批次 |
| `rs-archive-clone` | 软件/算法 | 黑盒探测行为重实现、二进制格式、纠错 |
| `lean-midpoint-proof` | 科学/数学 | 稀疏公理形式化阶梯、禁止未证假设 |
| `ks-solver-cpp` | 科学/物理 | 高精度非线性 PDE、oracle-only 边界、隐藏误差容限 |
| `vllm-deepseek-streaming` | ML/推理 | 多层服务栈间歇性协议 bug、流式分块边界 |
| `biped-contact-dynamics` | 科学/机器人 | 混合模式轨迹、隐藏构型、多体一致性 |

## 使用

### 运行要求
支持平台：**Windows / macOS / Linux**（任务容器统一为 Linux，`/app` 路径与宿主系统无关）。需要 Codex app/CLI（多智能体协作）、Python 3.12+、Docker（Windows/macOS 用 Docker Desktop，Linux 用 Docker Engine，daemon 运行中）、Harbor CLI（`python -m uv tool install harbor`，仅本地 oracle/nop 运行时）、可写工作目录。

平台差异：

- **macOS**：Python 3.12+ 用 [python.org](https://www.python.org/downloads/) 或 Homebrew 安装；Docker Desktop for Mac（Intel / Apple Silicon）需保持运行；系统默认 UTF-8，无需设置编码变量；`check-*.sh` 均为普通 bash，macOS 自带 bash 即可运行。
- **Windows**：先 `setx PYTHONUTF8 1`、`setx PYTHONIOENCODING utf-8` 并重启 Codex。
- **Linux**：Docker Engine + bash 即可，无额外编码/路径配置。

### 安装
- **Codex app**：打开本仓库 → 重启 Codex 加载 `.agents/plugins/marketplace.json` → Plugins 中安装 Frontier Task Suite。
- **Codex CLI**：`codex plugin marketplace add .` 后 `codex plugin add frontier-task-suite@frontier-task-suite`（或推送到远端后加远端 URL）。完整清单见 [docs/app-install.md](docs/app-install.md)。

### 完整流水线
新开一个 Codex 任务：

```text
使用 $run-wh-frontier-pipeline。

参考题：wal-recovery-ordering
工作目录：E:\path\to\writable-workspace
提交人：Your Name
联系方式：name@example.com
提交日期：20260805
```

可选 `Maximum repair rounds: N`（默认 5）。运行根 `WORKSPACE_ROOT/pipeline-runs/REFERENCE/DATE-TIME/` 记录全部产物与 `pipeline-state.json`。

### 单独使用技能

| 需求 | 技能 | 关键输入 |
| --- | --- | --- |
| 创作/校验三题提交包 | `$create-wh-frontier-tasks` | 参考题、工作目录、提交人、联系方式、日期 |
| 独立审计已有提交包 | `$verify-wh-frontier-tasks` | 提交目录、参考题、评审输出目录 |
| 依据评审修复 | `$repair-wh-frontier-tasks` | 提交目录、`review.json`、`evidence.json`、参考题 |

### 常用命令（仓库根目录）

```bash
# 参考题可运行性画像
python skills/create-wh-frontier-tasks/scripts/runnability_report.py fb --reference REFERENCE [--json]

# 提交初始化 / 静态校验 / 打包
python skills/create-wh-frontier-tasks/scripts/submission_tool.py init|validate|package ...

# 评审证据：快照 / 初始化报告 / 校验报告 / 指纹比对
python skills/verify-wh-frontier-tasks/scripts/review_tool.py {snapshot,init-report,validate-report,compare} ...

# 修复台账
python skills/repair-wh-frontier-tasks/scripts/repair_tool.py {intake,validate-ledger,stamp-ledger} ...

# 仓库级自检
python scripts/run_all_tests.py
python scripts/validate_plugin_release.py
python scripts/validate_windows_paths.py

# 恢复 ks-solver-cpp 参考题被排除的 wheels（仅执行上游参考题校准时需要）
python scripts/restore_ks_wheels.py [--check]
```

### 交付物
`OWNER_submission/`（包 README + 三个 `task-N-<slug>`）、`OWNER_Category_Subcategory_YYYYMMDD.zip`、`evidence.json`/`review.json`/`review.md`、`repair-ledger.json`/`repair.md`，以及发布校验和与指纹。

### 安装后验证
四技能可见；7 个参考题名可解析；`docker version` / `harbor --version` 可用；仓库自检脚本全部通过。

## 许可证
[MIT License](LICENSE)。内置参考材料来自 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench)（Apache-2.0，见 [fb/PROVENANCE.md](fb/PROVENANCE.md)）。