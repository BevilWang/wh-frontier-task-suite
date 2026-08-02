# WH Frontier Task Suite

面向 Codex 应用的 Frontier-Bench 多智能体插件。它从一个内置参考题出发，在同一个 Codex 任务中完成 3 道原创任务的创作、独立二审、问题修复、重新复审和最终打包。

插件内置 7 个 Frontier-Bench 参考资源及所需 checks、rubrics、taxonomy 和 task template。用户无需另行克隆 Frontier-Bench，也无需配置 Git 的 `core.longpaths`。

## 在 Codex 应用中安装

本插件以 Codex repo marketplace 发布，插件条目直接指向 GitHub 的 `git-subdir` 源。安装和更新都在 Codex 应用的 **Plugins** 页面完成，不要求用户运行 Codex CLI。

1. 在 Codex 应用中打开包含本仓库的项目，然后重启一次 Codex 应用，让它发现 `.agents/plugins/marketplace.json`。
2. 打开 **Plugins**，选择 **WH Frontier Task Suite** marketplace。
3. 打开插件详情，点击加号安装。
4. 新建一个 Codex 任务；已安装的 Skills 会在新任务中加载。

如果发布者通过 Codex 应用分享了插件，接收者也可以直接打开分享链接，在 **Shared with me** 中点击加号安装，无需本地仓库。完整的应用安装、更新和分享说明见 [docs/app-install.md](docs/app-install.md)。

## 运行完整流水线

在新任务中发送：

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
- `Workspace root`：保存任务、审核记录和发布包的可写目录；
- `Owner`、`Contact`、`Submission date`：写入提交元数据；
- `Maximum repair rounds`：可省略，默认值为 `2`。

插件会在磁盘产物之间进行隔离交接，并依次运行：

```text
Coordinator
  -> Author
  -> Independent Reviewer
  -> Repairer（需要时）
  -> Fresh Re-reviewer
  -> Release Agent
```

只有最终独立复审为 `PASS`，且发布快照与已审核内容指纹一致时，才会生成 zip 和校验和。

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

更完整的提示词见 [docs/prompts.md](docs/prompts.md)。

## 可单独调用的 Skills

| Skill | 用途 |
| --- | --- |
| `$run-wh-frontier-pipeline` | 推荐入口；协调完整多智能体流水线 |
| `$create-wh-frontier-tasks` | 创作、验证并打包 3 道任务 |
| `$verify-wh-frontier-tasks` | 独立、只读地二审任务提交 |
| `$repair-wh-frontier-tasks` | 复现并修复二审报告中的问题 |

## 运行环境与权限

读取内置参考资源只需要已安装插件。完整执行某些参考方向时还可能需要 Python 3、Docker、Harbor 或题目声明的系统依赖。

Codex 应用仍会对插件发起的命令应用当前项目的 sandbox 与审批策略。请把 `Workspace root` 设为当前项目内的可写目录；Docker 或 Harbor 需要访问宿主服务时，Codex 可能请求一次有范围的命令批准。插件不会要求关闭 sandbox。

如果必要基础设施不可用，流程会完成仍可执行的静态检查，并把缺失的运行证据标记为 `PROVISIONAL`，不会伪装成通过。

## Windows 与 macOS 兼容性

内置参考包使用短物理路径，公开的参考名保持不变。解析器基于 `pathlib` 和宿主系统原生路径语义，同时支持 Windows、macOS 和 Linux。

仓库 CI 在三种系统上执行单元测试、参考包解析、插件发布校验和 Windows 路径预算检查。所有待发布相对路径限制在 115 个字符以内，并以关闭 `core.longpaths` 的深目录干净下载作为 Windows 发布门，为 Codex 插件缓存和默认 Windows `MAX_PATH` 留出余量。

## 本地发布验证

```bash
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/create-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/verify-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s plugins/wh-frontier-task-suite/skills/repair-wh-frontier-tasks/scripts -p "test_*.py"
python -m unittest discover -s scripts -p "test_*.py"
python scripts/validate_plugin_release.py
python scripts/validate_windows_paths.py
```

## 来源与许可

内置参考包来自 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench)。为控制插件体积，参考包排除了 `ks-solver-cpp/tests/wheels/**` 下的大型预编译 wheels，其余所需题面、源码、solution、tests、checks 和 rubrics 均已保留。

- [参考包来源、短路径映射和排除清单](plugins/wh-frontier-task-suite/fb/PROVENANCE.md)
- [Frontier-Bench Apache-2.0 LICENSE](plugins/wh-frontier-task-suite/fb/LICENSE)
- [第三方声明](THIRD_PARTY_NOTICES.md)
