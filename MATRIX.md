# matrix

Which ask-the-user tool each harness offers, by mode and model, and how we
know. Evidence:

- **probe exit N** — `scripts/probe.sh` on that date, and the log was read
  to confirm the code wasn't a classifier mistake
- **reported** — a public source, linked; not run here
- **manual** — used by hand in a live session

| harness | tool | surface / mode | model | result | evidence |
|---|---|---|---|---|---|
| `claude` | `AskUserQuestion` | desktop app, interactive | — | works | manual, 2026-09-25 |
| `claude` | `AskUserQuestion` | `claude -p` | claude-sonnet-5 | not offered: tool search finds nothing, replies NO_ASK_TOOL | probe exit 1, 2026-09-25 |
| `claude` | `AskUserQuestion` | `claude -p --permission-mode plan` | claude-sonnet-5 | not offered | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p` | Grok 4.5 High | not offered (two runs) | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --mode plan` | Grok 4.5 High | not offered | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --model auto` | Auto (routed model not shown) | not offered | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p` | Composer 2.5 | called (`askQuestionToolCall`); headless answers it with "Questions skipped by the user" | probe exit 0, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --mode plan` | Composer 2.5 | called | probe exit 0, 2026-09-25 |
| `agy` | `ask_question` | `agy -p` | not reported | inconclusive: in the tool list, one unlabelled step ran, and the model says it asked | probe exit 3, 2026-09-25 |
| `agy` | `ask_question` | `agy -p --mode plan` | not reported | inconclusive, same pattern | probe exit 3, 2026-09-25 |
| `copilot` | `ask_user` | `copilot -p` | mai-code-1.1-flash | not offered | probe exit 1, 2026-09-25 |
| `grok` | `ask_user_question` | `grok -p` | grok-4.7 | called | probe exit 0, 2026-09-25 |
| `codex` | `request_user_input` | `codex exec` | — | not offered | reported, [openai/codex#24613](https://github.com/openai/codex/pull/24613) |
| `codex` | `request_user_input` | TUI, Plan mode | — | offered | reported, [#29104](https://github.com/openai/codex/issues/29104), [#11536](https://github.com/openai/codex/issues/11536) |
| `codex` | `request_user_input` | `codex app-server` | — | sent as the JSON-RPC request `item/tool/requestUserInput` | reported, [#12560](https://github.com/openai/codex/pull/12560) |

## notes

**Cursor is model-gated.** The same headless command gets the tool on
Composer 2.5 and not on Grok 4.5 High, in both default and plan mode. Auto
didn't get it either, but its init event only says "Auto", so which model
it routed to is unknown. `--mode plan` doesn't show up in the init event;
the mode comes from the flag. Plain-text mentions ("No AskQuestion tool")
turn up in Grok's thinking stream, so only the `askQuestionToolCall` event
counts as a call.

**Antigravity doesn't label the call.** Its stream-json logs a tool as
`"step_type":"tool"` with a `tool_name` (a control run that listed files
showed `view_file` and `run_command` that way). The ask run instead has one
step with `"step_type":"unknown"` and no name, right after the model's first
response. That's probably `ask_question`, but a probe can't prove it, so it
stays at 3.

**Codex wasn't probed** (not installed here). `codex exec --json` item types
have no tool-name field for this, and exec doesn't offer the tool, so the
probe's pattern is the app-server request; it's unverified.

**Headless is the common gap.** Claude Code, Copilot CLI and Codex exec all
drop the tool in print mode, and Cursor's Composer gets it but can't be
answered. That's why the skill's fallback for a headless run is to take the
recommended option and say so, not to ask.
