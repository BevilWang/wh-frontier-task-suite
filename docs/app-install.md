# Codex 应用安装与发布

WH Frontier Task Suite 的最终用户安装入口是 Codex 应用的 **Plugins** 页面。CLI 只属于底层开发工具，不是本插件的用户安装前提。

## 从 repo marketplace 安装

1. 在 Codex 应用中打开本仓库所在项目。
2. 重启 Codex 应用，让它重新读取项目根目录下的 `.agents/plugins/marketplace.json`。
3. 打开 **Plugins**，选择 **WH Frontier Task Suite**。
4. 打开插件详情并点击加号。
5. 新建任务，再通过 `@wh-frontier-task-suite` 或 `$run-wh-frontier-pipeline` 使用插件。

marketplace entry 使用 GitHub `git-subdir` 源，因此点击安装后由 Codex 下载 `plugins/wh-frontier-task-suite`，而不是依赖当前工作区里的本地插件副本。

## 从分享链接安装

发布者在 Codex 应用中安装并验证插件后，可以打开插件详情，选择 **Share**，向同一 ChatGPT workspace 的成员或群组分享，或复制分享链接。

接收者打开链接后，可在 **Plugins > Shared with me** 中安装。分享不会把插件发布到 OpenAI 的通用公共目录，访问范围仍受 workspace 权限控制。

## 更新

发布者升级 manifest 版本并推送 `main` 后，重新打开插件详情并执行应用提供的更新或重新安装操作。更新完成后新建任务，以确保新版本 Skills 被加载。

## 应用侧验证清单

- 插件展示名、开发者和描述正确；
- 点击加号后安装成功；
- Installed 列表显示新版本；
- 新任务能发现 4 个 Skills；
- `$run-wh-frontier-pipeline` 能解析 7 个内置参考名；
- Windows 安装不要求 `core.longpaths`；
- macOS 使用同一 marketplace 与 bundle resolver，无反斜杠硬编码。

