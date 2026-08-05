# Installation guide

## Codex app

1. Open this repository in the Codex app.
2. Restart Codex so it reloads `.agents/plugins/marketplace.json`.
3. Go to **Plugins**, find **Frontier Task Suite**, and click install.

## Codex CLI

Add the repository as a marketplace, then install the plugin:

```bash
codex plugin marketplace add .
codex plugin add frontier-task-suite@frontier-task-suite
```

Or add from the remote URL (after pushing):

```bash
codex plugin marketplace add https://github.com/BevilWang/Frontier-Task-Suite
codex plugin add frontier-task-suite@frontier-task-suite
```

Use `codex plugin marketplace list` to confirm the marketplace name if it differs.

## Platform support

The plugin runs on **Windows, macOS, and Linux**. Task containers are always Linux, so `/app` paths and Docker behavior are identical across hosts.

- **macOS**: Python 3.12+ from [python.org](https://www.python.org/downloads/) or Homebrew; keep Docker Desktop for Mac (Intel / Apple Silicon) running; UTF-8 is the system default, so no encoding variables are needed; the bundled `check-*.sh` scripts are plain bash and run on macOS's bundled bash.
- **Windows**: set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` and restart Codex before running Harbor commands; use a short root + `subst` + `--jobs-dir` if you hit long-path errors (`WinError 206`).
- **Linux**: Docker Engine plus bash is enough; no extra encoding or path configuration.

## Verification checklist

After installing, confirm in a new task:

- The plugin shows four skills: `$run-wh-frontier-pipeline`, `$create-wh-frontier-tasks`, `$verify-wh-frontier-tasks`, `$repair-wh-frontier-tasks`.
- `$run-wh-frontier-pipeline` can resolve all seven supported reference names and runs an internal review loop (r1, r2, …) until internal `PASS`.
- `docker version` and `harbor --version` work in your environment (Harbor is used only as the local oracle/nop runtime harness; the official `harbor check` runs externally).
- CI verifies the repository on Ubuntu, Windows, and macOS (unit tests, plugin manifest, reference resolution, runnability report, Windows-safe path checks).