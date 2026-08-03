# WH Frontier Task Suite

在 Codex 中创建、审查、修复并发布 Frontier-Bench 任务的插件。

选择一道内置参考题，插件会据此设计恰好 3 道原创任务，完成实现、验证、独立审查和必要修复，并且只在最终复审通过后生成交付压缩包。使用者无需另外克隆 Frontier-Bench，也不需要在多个 Codex 任务之间手动传递文件。

## 主要功能

- 从一个受支持的参考题出发，创建恰好 3 道原创任务；
- 生成完整的 `instruction.md`、`task.toml`、环境、参考解、测试和验证脚本；
- 检查题面、实现和测试是否一致；
- 使用生成式或验证器自有用例，降低公开样例硬编码风险；
- 执行静态检查、oracle、nop、非特权 verifier、CTRF 和 reward 检查；
- 由独立审查流程检查正确性、原创性、难度、泄漏和验证器安全性；
- 默认持续修复和重新复审，直到 `PASS`；
- 仅发布与通过复审的源码指纹一致的最终 zip 和 SHA-256 校验和；
- 支持从保存的运行目录恢复中断流程。

## 支持的参考题

| 方向 | 参考题 |
| --- | --- |
| Software / Databases | `wal-recovery-ordering` |
| Software / Data Engineering | `ontology-kg-querying` |
| Software / Algorithms | `rs-archive-clone` |
| Science / Math | `lean-midpoint-proof` |
| Science / Physics | `ks-solver-cpp` |
| ML / Inference | `vllm-deepseek-streaming` |
| Science / Robotics | `biped-contact-dynamics` |

参考题用于校准能力结构、难度和验证方法。插件会要求新任务更换目标、数据或系统、核心推理和隐藏变化；仅改名、改常数或更换故事背景不算原创。

## 使用前准备

- 支持子代理的 Codex 应用；
- Python 3.12 或更高版本；
- Docker Desktop，并确保 Docker daemon 正在运行；
- Harbor CLI；
- 一个可写工作目录；
- 提交者姓名、联系方式和真实提交日期。

安装 Harbor：

```powershell
python -m pip install --user --upgrade uv
python -m uv tool install harbor
```

运行前确认以下命令成功：

```powershell
docker version
harbor --version
```

中文 Windows 环境建议设置 UTF-8，然后重启 Codex：

```powershell
setx PYTHONUTF8 1
setx PYTHONIOENCODING utf-8
```

## 安装插件

1. 在 Codex 应用中打开本仓库所在项目。
2. 重启 Codex，使项目中的 marketplace 配置生效。
3. 打开 **Plugins**，选择 **WH Frontier Task Suite**。
4. 点击加号安装插件。
5. 安装或更新后新建一个 Codex 任务，以加载最新 Skills。

更详细的安装和分享说明见 [Codex 应用安装指南](docs/app-install.md)。

## 快速开始

在新的 Codex 任务中发送：

```text
Use $run-wh-frontier-pipeline.

Reference: wal-recovery-ordering
Workspace root: E:\path\to\writable-workspace
Owner: Your Name
Contact: name@example.com
Submission date: YYYYMMDD
Repair policy: continue until PASS
```

将 `Reference` 替换为上表中的任一参考题，并把其余字段换成真实信息即可。默认不设置数字修复上限：只要仍能取得可验证的进展，插件会继续修复和复审。

如果希望限制自动修复次数，可显式加入：

```text
Maximum repair rounds: 3
```

## 运行结果

成功完成后，工作目录中会包含：

```text
pipeline-runs/<reference>/<run-id>/
  pipeline-state.json
  author/<owner>_submission/
  hardening/
  reviews/
  repairs/
  release/<owner>_Category_Subcategory_YYYYMMDD.zip
  release/*.sha256
```

最重要的交付物是 `release/` 下的 zip 和 SHA-256 校验和。只有最终独立复审为 `PASS`，且压缩包解压后的内容与已审查内容完全一致时，才会生成可发布归档。

`pipeline-state.json` 保存运行阶段、审查结论、修复次数、源码指纹和阻塞原因，可用于审计和恢复。作者阶段或复审前产生的 zip 均不属于最终交付物。

## 状态说明

| 状态 | 含义 |
| --- | --- |
| `PASS` | 当前独立审查已完成必要检查且没有未解决的重大问题 |
| `FAIL` | 发现可复现的重大问题，插件将进入修复和重新复审 |
| `PROVISIONAL` | Docker、Harbor 或其他必要证据缺失；不能视为通过 |
| `BLOCKED` | 缺少权限、基础设施或有效工件，或显式修复上限已耗尽 |
| `COMPLETE` | 已通过复审，并完成最终打包、校验和与解压回验 |

## 恢复中断运行

如果运行被中断，打开新的 Codex 任务并发送：

```text
Use $run-wh-frontier-pipeline to resume the saved run.

Run root: E:\path\to\pipeline-runs\REFERENCE\RUN_ID
```

插件会读取 `pipeline-state.json` 和已有工件，从安全的阶段继续，不会把旧压缩包误当成最终版本。

## 单独使用某项能力

| Skill | 用途 |
| --- | --- |
| `$run-wh-frontier-pipeline` | 完整创建、审查、修复、复审和发布流程；推荐入口 |
| `$create-wh-frontier-tasks` | 单独创建或校验三题提交包 |
| `$verify-wh-frontier-tasks` | 对现有提交进行只读独立审查 |
| `$repair-wh-frontier-tasks` | 根据匹配源码指纹的审查报告修复提交 |

各参考方向和手动工作流的完整提示词见 [提示词库](docs/prompts.md)。

## 质量与安全边界

- 未实际运行的检查不会被标记为通过。
- `PROVISIONAL` 不会被转换为 `PASS`。
- 审查期间不会修改被审查的源码。
- 修复后必须由新的独立审查重新验证。
- 插件不会为了通过测试而删除检查、泄漏答案或放宽关键容差。
- 最终归档之前的任何内容修改都会触发重新审查。


## 常见问题

### Docker 已安装但运行仍被阻塞

确认 Docker Desktop 已启动，并在当前终端运行 `docker version`。输出必须同时包含 Client 和 Server 信息。

### Windows 上 Harbor 路径过长或输出乱码

先设置上述 UTF-8 环境变量并重启 Codex。插件会在需要时使用较短的临时工作路径和独立 jobs 目录，但不会修改被审查源码。

### 为什么没有生成 zip？

通常是最终复审尚未 `PASS`、运行证据不完整，或发布快照与审查指纹不一致。查看运行目录中的 `pipeline-state.json` 和最新 `reviews/` 报告。

### 可以只使用其中一个 Skill 吗？

可以。已有提交可直接使用审查或修复 Skill；需要完整三题交付时建议使用 `$run-wh-frontier-pipeline`。

## 来源与许可

内置参考资源来自 [harbor-framework/frontier-bench](https://github.com/harbor-framework/frontier-bench)。第三方资源说明见 [PROVENANCE.md](plugins/wh-frontier-task-suite/fb/PROVENANCE.md) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
