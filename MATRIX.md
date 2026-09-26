# matrix

Which ask-the-user tool each harness offers, by mode and model, and how we
know. Evidence:

- **probe exit N** — `scripts/probe.sh` on that date, and the log was read
  to confirm the code wasn't a classifier mistake
- **reported** — a public source, linked; not run here
- **manual** — used by hand in a live session

| harness | tool | surface / mode | model | result | evidence |
|---|---|---|---|---|---|
| `claude` | `AskUserQuestion` | desktop app, interactive | claude-opus-5-5 | works | manual, 2026-09-25 |
| `claude` | `AskUserQuestion` | `claude -p` | claude-sonnet-5 | not offered: tool search finds nothing, replies NO_ASK_TOOL | probe exit 1, 2026-09-25 |
| `claude` | `AskUserQuestion` | `claude -p --permission-mode plan` | claude-sonnet-5 | not offered | probe exit 1, 2026-09-25 |
| `claude` | `AskUserQuestion` | Agent SDK, with a permission handler attached | — | offered; plain `-p` hides it since 2.1.187 | reported, [anthropics/claude-code#77994](https://github.com/anthropics/claude-code/issues/77994) |
| `cursor` | `AskQuestion` | IDE agent | varies | works in Plan mode, varies by model | reported (community), [forum](https://forum.cursor.com/t/allow-askquestion-tool-calls-in-agent-mode-or-any-mode/152517) |
| `cursor` | `AskQuestion` | `cursor-agent -p` | Grok 4.5 High | not offered (two runs) | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --mode plan` | Grok 4.5 High | not offered | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --model auto` | Auto (routed model not shown) | not offered | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p` | Composer 2.5 | called (`askQuestionToolCall`); headless answers it with "Questions skipped by the user" | probe exit 0, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --mode plan` | Composer 2.5 | called | probe exit 0, 2026-09-25 |
| `agy` | `ask_question` | `agy -p` | not reported | inconclusive: in the tool list, one unlabelled step ran, and the model says it asked | probe exit 3, 2026-09-25 |
| `agy` | `ask_question` | `agy -p --mode plan` | not reported | inconclusive, same pattern | probe exit 3, 2026-09-25 |
| `agy` | `ask_question` | interactive | — | offered; headless runs settle the choice themselves | reported, releases [1.2.7](https://github.com/google-antigravity/antigravity-cli/releases/tag/1.2.7), [1.1.12](https://github.com/google-antigravity/antigravity-cli/releases/tag/1.1.12) |
| `copilot` | `ask_user` | `copilot -p` (1.0.88) | mai-code-1.1-flash | not offered | probe exit 1, 2026-09-25 |
| `copilot` | `ask_user` | interactive | — | offered; `--no-ask-user` turns it off | reported, [CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference), [github/copilot-cli#2929](https://github.com/github/copilot-cli/issues/2929) |
| `grok` | `ask_user_question` | `grok -p` | grok-4.7 | called | probe exit 0, 2026-09-25 |
| `grok` | `ask_user_question` | interactive | — | offered; in `-p` an unanswered question returns a "no operator" result | reported, [source](https://github.com/xai-org/grok-build/blob/f0e3be1100ef5252488e3be8bb0e91cf68d8c305/crates/codegen/xai-grok-tools/src/implementations/grok_build/ask_user_question/mod.rs#L101-L105) |
| `codex` | `request_user_input` | `codex exec` | — | not offered; exec rejects the request as "not supported in exec mode" | reported, [source](https://github.com/openai/codex/blob/25270df2615eb4da5b9d4a9a392226933fb096c5/codex-rs/exec/src/lib.rs#L2038-L2048) |
| `codex` | `request_user_input` | TUI, Plan mode | — | offered; Default mode says it's unavailable | reported, [openai/codex#29104](https://github.com/openai/codex/issues/29104), [#11536](https://github.com/openai/codex/issues/11536) |
| `codex` | `request_user_input` | `codex app-server` | — | sent as the JSON-RPC request `item/tool/requestUserInput` (experimental) | reported, [source](https://github.com/openai/codex/blob/25270df2615eb4da5b9d4a9a392226933fb096c5/codex-rs/app-server-protocol/src/protocol/common.rs#L1777-L1781) |

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

**Codex wasn't probed** (not installed here). The tool is Plan-mode only,
Plan mode has no headless flag
([openai/codex#13377](https://github.com/openai/codex/issues/13377), closed
as not planned), and exec rejects the request anyway. So the probe's pattern
is the app-server request, and it's unverified.

**Headless is the common gap.** Claude Code, Copilot CLI and Codex exec all
drop the tool in print mode, and Cursor's Composer gets it but can't be
answered. That's why the skill's fallback for a headless run is to take the
recommended option and say so, not to ask.
