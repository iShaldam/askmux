# matrix

Which ask-the-user tool each harness offers, by mode and model, and how we
know. Evidence:

- **probe exit N** — `scripts/probe.sh` on that date, and the log was read
  to confirm the code wasn't a classifier mistake
- **reported** — a public source, linked; not run here
- **manual** — used by hand in a live session
- **Unanswered, when the tool is offered but nobody answers:**
  - `blocks` (the run waits)
  - `times out` (an empty or "proceed anyway" answer comes back after a fixed wait)
  - `skipped` (the harness answers "skipped" on its own)
  - `no operator` (the tool returns an error result)
  - `auto-picks` (the harness settles the choice itself)
  - `n/a` (tool not offered)
  - `unknown` (not measured yet)

A weekly Action re-checks every cited issue and pinned source line and opens an issue when one moves; `make watch` runs it locally.

<!-- matrix:start -->
| harness | tool | surface / mode | model | result | unanswered | evidence |
|---|---|---|---|---|---|---|
| `claude` | `AskUserQuestion` | desktop app, interactive | claude-opus-5-5 | works | times out: after 60s the tool returns "No response after 60s ... proceed using your best judgment" | manual, 2026-09-25, [anthropics/claude-code#73125](https://github.com/anthropics/claude-code/issues/73125) |
| `claude` | `AskUserQuestion` | `claude -p` | claude-sonnet-5 | not offered: tool search finds nothing, replies NO_ASK_TOOL | n/a | probe exit 1, 2026-09-25 |
| `claude` | `AskUserQuestion` | `claude -p --permission-mode plan` | claude-sonnet-5 | not offered | n/a | probe exit 1, 2026-09-25 |
| `claude` | `AskUserQuestion` | Agent SDK, with a permission handler attached | — | offered; plain `-p` hides it since 2.1.187 | unknown | reported, [anthropics/claude-code#77994](https://github.com/anthropics/claude-code/issues/77994) |
| `cursor` | `AskQuestion` | IDE agent | varies | works in Plan mode, varies by model | unknown | reported (community), [forum](https://forum.cursor.com/t/allow-askquestion-tool-calls-in-agent-mode-or-any-mode/152517) |
| `cursor` | `AskQuestion` | `cursor-agent -p` | Grok 4.5 High | not offered (two runs) | n/a | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --mode plan` | Grok 4.5 High | not offered | n/a | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --model auto` | Auto (routed model not shown) | not offered | n/a | probe exit 1, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p` | Composer 2.5 | called (`askQuestionToolCall`); headless answers it with "Questions skipped by the user" | skipped | probe exit 0, 2026-09-25 |
| `cursor` | `AskQuestion` | `cursor-agent -p --mode plan` | Composer 2.5 | called | skipped | probe exit 0, 2026-09-25 |
| `agy` | `ask_question` | `agy -p` | not reported | inconclusive: in the tool list, one unlabelled step ran, and the model says it asked | auto-picks | probe exit 3, 2026-09-25 |
| `agy` | `ask_question` | `agy -p --mode plan` | not reported | inconclusive, same pattern | auto-picks | probe exit 3, 2026-09-25 |
| `agy` | `ask_question` | interactive | — | offered; headless runs settle the choice themselves | unknown | reported, releases [1.2.7](https://github.com/google-antigravity/antigravity-cli/releases/tag/1.2.7), [1.1.12](https://github.com/google-antigravity/antigravity-cli/releases/tag/1.1.12) |
| `copilot` | `ask_user` | `copilot -p` (1.0.88) | mai-code-1.1-flash | not offered | n/a | probe exit 1, 2026-09-25 |
| `copilot` | `ask_user` | interactive | — | offered; `--no-ask-user` turns it off | unknown | reported, [CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference), [github/copilot-cli#2929](https://github.com/github/copilot-cli/issues/2929) |
| `grok` | `ask_user_question` | `grok -p` | grok-4.7 | called | no operator | probe exit 0, 2026-09-25 |
| `grok` | `ask_user_question` | interactive | — | offered; in `-p` an unanswered question returns a "no operator" result | unknown | reported, [source](https://github.com/xai-org/grok-build/blob/f0e3be1100ef5252488e3be8bb0e91cf68d8c305/crates/codegen/xai-grok-tools/src/implementations/grok_build/ask_user_question/mod.rs#L101-L105) |
| `codex` | `request_user_input` | `codex exec` | — | not offered; exec rejects the request as "not supported in exec mode" | n/a | reported, [source](https://github.com/openai/codex/blob/25270df2615eb4da5b9d4a9a392226933fb096c5/codex-rs/exec/src/lib.rs#L2038-L2048) |
| `codex` | `request_user_input` | TUI, Plan mode | — | offered; Default mode says it's unavailable unless `[features] default_mode_request_user_input = true` (under development, off by default); Default mode auto-resolves after about a minute with an empty answer | blocks | reported, [openai/codex#29104](https://github.com/openai/codex/issues/29104), [#11536](https://github.com/openai/codex/issues/11536), [flag](https://github.com/openai/codex/blob/0fbf0bedc25d0effec4b758030772468339d315c/codex-rs/features/src/lib.rs#L1613-L1618), [openai/codex#34455](https://github.com/openai/codex/issues/34455), [#37472](https://github.com/openai/codex/issues/37472) |
| `codex` | `request_user_input` | `codex app-server` | — | sent as the JSON-RPC request `item/tool/requestUserInput` (experimental) | unknown | reported, [source](https://github.com/openai/codex/blob/25270df2615eb4da5b9d4a9a392226933fb096c5/codex-rs/app-server-protocol/src/protocol/common.rs#L1777-L1781) |
| `codex` | `request_user_input_async` | Default mode, models whose catalog lists it | — | offered to the main agent, not subagents | unknown | reported, [source](https://github.com/openai/codex/blob/0fbf0bedc25d0effec4b758030772468339d315c/codex-rs/core/src/tools/spec_plan.rs#L1178-L1193) |
| `gemini` | `ask_user` | interactive | — | offered: pauses until answered or dismissed | blocks: waits for an answer; dismissing returns "User dismissed ask_user dialog without answering." | reported, [docs](https://geminicli.com/docs/tools/ask-user/), [ask-user.ts](https://github.com/google-gemini/gemini-cli/blob/40d4dccfa9aec692b27798ca819b918609e2bc60/packages/core/src/tools/ask-user.ts#L190-L193) |
| `gemini` | `ask_user` | `gemini -p` | — | not offered: excluded when not interactive, and in ACP mode | n/a | reported, [config.ts](https://github.com/google-gemini/gemini-cli/blob/40d4dccfa9aec692b27798ca819b918609e2bc60/packages/cli/src/config/config.ts#L795-L803) |
| `opencode` | `question` | TUI, or `opencode run --mini` | — | offered, on by default | blocks: no timeout | reported, [docs](https://opencode.ai/docs/tools/#question), [question/index.ts](https://github.com/anomalyco/opencode/blob/2fa3363c924c5c3e367b84a87ae478296a0ed59b/packages/opencode/src/question/index.ts#L96-L107) |
| `opencode` | `question` | `opencode run` | — | denied: a `question: deny` rule is added unless `--mini` | unknown: denied, but whether the model gets an error or never sees the tool isn't verified | reported, [run.ts](https://github.com/anomalyco/opencode/blob/2fa3363c924c5c3e367b84a87ae478296a0ed59b/packages/opencode/src/cli/cmd/run.ts#L430-L437) |
| `cline` | `ask_question` | CLI, in a terminal | — | offered and auto-approved | blocks: reads the answer from the terminal, no timeout | reported, [run-agent.ts](https://github.com/cline/cline/blob/fef9de1665d098ef13327656669cc43783151e0b/apps/cli/src/runtime/run-agent.ts#L163-L166), [approval.ts](https://github.com/cline/cline/blob/fef9de1665d098ef13327656669cc43783151e0b/apps/cli/src/utils/approval.ts#L128-L145) |
| `cline` | `ask_question` | CLI, stdin or stdout not a terminal | — | offered | auto-picks: returns the first option without asking | reported, [approval.ts](https://github.com/cline/cline/blob/fef9de1665d098ef13327656669cc43783151e0b/apps/cli/src/utils/approval.ts#L120-L126) |
| `pi` | `ask_user_question` | TUI, with the ghoseb/pi-askuserquestion extension | — | not built in; the extension adds it | blocks: waits on the TUI; cancel returns "User cancelled" | reported, [built-in tools](https://github.com/earendil-works/pi/blob/1b347794e2a630e4359f2584f4eea388145d0ddf/packages/coding-agent/src/core/tools/index.ts#L95), [extension](https://github.com/ghoseb/pi-askuserquestion/blob/e58609c9e9c8c4e8a0348c96eaad38dd7e6f0578/src/index.ts#L65-L71) |
| `pi` | `ask_user_question` | print / JSON mode, with the extension | — | loaded, but returns an error and turns itself off | no operator: error result, and the tool is off for the rest of the session | reported, [extension](https://github.com/ghoseb/pi-askuserquestion/blob/e58609c9e9c8c4e8a0348c96eaad38dd7e6f0578/src/index.ts#L40-L56) |
<!-- matrix:end -->

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

**Nobody answering is the other gap.** The harnesses that do offer the tool
disagree on what an unanswered question does: Claude Code returns a "proceed"
message after 60 seconds, Codex Default mode submits an empty answer after
about a minute while Plan mode waits, Cursor headless skips it, and Grok
headless returns "no operator". That's why the skill treats a skipped, empty,
or no-operator result as headless.
