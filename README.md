# WH Frontier Task Suite

一个面向 Codex 应用的 Frontier-Bench/Harbor 多智能体插件：从一道人选参考题出发，创建恰好 3 道原创任务，并完成预审加固、独立复审、问题修复、重新复审和不可变发布。

插件内置 7 道 Frontier-Bench 参考题及配套 checks、rubric、taxonomy 和 task template，无需另行克隆 Frontier-Bench。

## 安装插件

在 Codex 应用中打开本仓库所在项目并重启应用，然后进入 **Plugins**，选择 **WH Frontier Task Suite** 并点击加号安装。安装或更新后请新建 Codex 任务，使新版 Skills 生效。完整说明见 [docs/app-install.md](docs/app-install.md)。

## 一次完整运行会做什么

```text
环境预检
  -> 作者：创建 3 道任务，不提前打 zip
  -> 加固者：在正式审查前消除可预防缺陷
  -> 独立审查者：从零审查全部任务和全部质量项
  -> 修复者：修复根因并检查三题相邻边界
  -> 新审查者：先从零复审，再核验旧问题闭环
  -> 发布者：冻结已通过内容，打包、校验和、解压回验
```

只有权威复审为 `PASS`，且源码、审核快照和解压后归档指纹一致时，才会生成最终 zip。作者阶段或修复前产生的 zip 都视为过期，不会发布。

## 支持的参考题

| Category / Subcategory | Reference |
| --- | --- |
| Software / Databases | `wal-recovery-ordering` |
| Software / Data Engineering | `ontology-kg-querying` |
| Software / Algorithms | `rs-archive-clone` |
| Science / Math | `lean-midpoint-proof` |
| Science / Physics | `ks-solver-cpp` |
| ML / Inference | `vllm-deepseek-streaming` |
| Science / Robotics | `biped-contact-dynamics` |

## 使用前准备

- 支持子代理的 Codex 应用任务；
- 当前项目内的可写工作目录；
- Python 3.12+、Docker Desktop 和 Harbor CLI；
- 姓名、联系方式、真实提交日期及所选参考题。

安装 Harbor：

```powershell
python -m pip install --user --upgrade uv
python -m uv tool install harbor
```

中文 Windows 建议设置后重启 Codex：

```powershell
setx PYTHONUTF8 1
setx PYTHONIOENCODING utf-8
```

运行前确认 `docker version` 和 `harbor --version` 均成功。Docker Desktop 必须保持运行。

## 推荐用法

在新 Codex 任务中发送：

```text
Use $run-wh-frontier-pipeline.

Reference: wal-recovery-ordering
Workspace root: E:\path\to\writable-workspace
Owner: 真实姓名或提交名
Contact: name@example.com
Submission date: YYYYMMDD
Repair policy: continue until PASS
```

默认没有数字修复上限：只要每轮仍有可验证进展，流水线就会持续修复和独立复审，直到 `PASS`。只有真实的权限/基础设施阻塞、连续无效阶段工件，或用户显式设置的安全上限耗尽时才停止。流水线会自行创建隔离的作者、加固、审查、修复、复审和发布子代理；用户无需手动切换 Codex 任务。

## 强制质量门

每道题都必须完成：

- 题面要求与测试行为的双向映射；
- 输入/领域完整性检查：按参考题覆盖结构字段、形式声明、数值参数域、协议状态转换或物理模式；
- accepted input/state 到 normalization、recovery、compilation、simulation、serialization 和 output 的适用路径一致性；
- seeded/generated 或 verifier-owned hidden variation；
- 常量输出、可见样例硬编码、输入修改、奖励覆盖、残留进程等反捷径探测；
- 原样运行最终非特权 verifier wrapper，确认 CTRF、reward、oracle=`1`、nop=`0`；
- Frontier-Bench 静态检查和独立复审。

审查者即使发现首个 blocker，也必须继续完成三题全部质量项。修复者不能只补一个回归测试，还要检查同类字段、相邻代码路径和另外两道题。

## 状态含义

| 状态 | 含义 |
| --- | --- |
| `PASS` | 当前审核轮全部质量门和运行证据通过 |
| `FAIL` | 存在可复现的 blocker/major 问题，进入修复 |
| `PROVISIONAL` | 未发现已证实的大问题，但 Docker/Harbor 等必需证据缺失；不是通过 |
| `BLOCKED` | 权限、基础设施、连续无效工件，或用户显式修复上限耗尽，需要外部条件或用户授权 |
| `COMPLETE` | 复审 PASS，且最终归档、校验和、指纹和解压回验成功 |

中断或 `BLOCKED` 后可从原运行目录恢复：

```text
Use $run-wh-frontier-pipeline to resume the saved run.

Run root: E:\path\to\pipeline-runs\REFERENCE\RUN_ID
Remove or raise the explicit repair cap if the saved run stopped at that cap.
```

## 运行产物

```text
pipeline-runs/<reference>/<run-id>/
  pipeline-state.json
  author/<owner>_submission/
  hardening/
  reviews/r1/
  reviews/rN/from-scratch/
  reviews/rN/closure/
  repairs/rN/repair-ledger.json
  release/<owner>_Category_Subcategory_YYYYMMDD.zip
  release/*.sha256
```

`pipeline-state.json` 记录所有代理、阶段、指纹、审查结论、修复轮次、阻塞原因和发布结果，可脱离聊天记录审计或恢复。

## 可单独调用的 Skills

| Skill | 用途 |
| --- | --- |
| `$run-wh-frontier-pipeline` | 推荐入口；完整多智能体流水线和恢复 |
| `$create-wh-frontier-tasks` | 单独创建、验证或发布 3 道任务 |
| `$verify-wh-frontier-tasks` | 对现有三题提交做只读独立审查 |
| `$repair-wh-frontier-tasks` | 根据匹配指纹的审查报告修复并生成账本 |

完整提示词见 [docs/prompts.md](docs/prompts.md)，Codex 应用安装说明见 [docs/app-install.md](docs/app-install.md)。

## 边界

插件负责本地任务工件、验证、审查、修复和 zip 发布；Task Desk 认领、负责人确认、口令备注和最终上传仍需人工完成。没有运行过的检查不会被写成通过。

## 开发验证

```powershell
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/create-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/verify-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/repair-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_plugin_release.py
python scripts/validate_windows_paths.py
```

内置参考资源来自 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench)，详见 [PROVENANCE.md](plugins/wh-frontier-task-suite/fb/PROVENANCE.md) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
