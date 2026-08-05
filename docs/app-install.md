# Installation guide

## Codex app

1. Open this repository in the Codex app.
2. Restart Codex so it reloads `.agents/plugins/marketplace.json`.
3. Go to **Plugins**, find **WH Frontier Task Suite**, and click install.

## Codex CLI

Add the repository as a marketplace, then install the plugin:

```bash
codex plugin marketplace add .
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

Or add from the remote URL (after pushing):

```bash
codex plugin marketplace add https://github.com/BevilWang/wh-frontier-task-suite
codex plugin add wh-frontier-task-suite@wh-frontier-task-suite
```

Use `codex plugin marketplace list` to confirm the marketplace name if it differs.

## Verification checklist

After installing, confirm in a new task:

- The plugin shows four skills: `$run-wh-frontier-pipeline`, `$create-wh-frontier-tasks`, `$verify-wh-frontier-tasks`, `$repair-wh-frontier-tasks`.
- `$run-wh-frontier-pipeline` can resolve all seven supported reference names and runs an internal review loop (r1, r2, …) until internal `PASS`.
- `docker version` and `harbor --version` work in your environment (Harbor is used only as the local oracle/nop runtime harness; the official `harbor check` runs externally).