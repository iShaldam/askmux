# askmux

Your skill says "ask me", and half your coding agents have no tool to ask with. askmux is one skill that tells the model which question tool its harness has, plus a tested matrix of who offers one, by mode and model.

14 harnesses, last re-checked 2026-11-05: six by a live probe, the rest from their source code, pinned to the line.

## install

Any harness, with the [skills CLI](https://github.com/vercel-labs/skills) (needs Node 22.20+):

```
npx skills add iShaldam/askmux
```

Claude Code, as a plugin:

```
/plugin marketplace add iShaldam/askmux
/plugin install askmux@askmux
```

Or copy `skills/askmux/` into your harness's skills folder by hand.

<!-- matrix:start -->
| harness | tool | interactive | headless | notes |
|---|---|---|---|---|
| Claude Code | `AskUserQuestion` | ✓ | ✗ `claude -p` | ✓ in the Agent SDK with a permission handler, or a PreToolUse hook that answers it |
| Cursor | `AskQuestion` | ✓ model-gated | ~ Composer 2.5 calls it, the answer comes back "skipped" | ✗ on Grok 4.5 High and Auto, both modes |
| Antigravity | `ask_question` | ✓ | ~ listed, the call can't be proven | headless picks for you |
| Codex | `request_user_input` | ✓ Plan mode only | ✗ `codex exec` | Default mode needs the `default_mode_request_user_input` feature; some models get `request_user_input_async` |
| Copilot CLI | `ask_user` | ✓ | ✗ `copilot -p` | `--no-ask-user` turns it off |
| Grok CLI | `ask_user_question` | ✓ | ~ called, but no operator answers | |
| Gemini CLI | `ask_user` | ✓ | ✗ `gemini -p` | same tool name as Copilot CLI |
| OpenCode | `question` | ✓ | ✗ `opencode run` denies it | `--mini` allows it; `"permission": {"question": "deny"}` turns it off |
| Cline | `ask_question` | ✓ | ~ offered, picks the first option | older builds and the VS Code extension call it `ask_followup_question` |
| pi | `ask_user_question` | ~ extension only | ✗ print / JSON mode | same tool name as Grok CLI |
| Qwen Code | `ask_user_question` | ✓ | ~ `qwen -p` errors without an ACP host | same tool name as Grok CLI and pi |
| Crush | `question` | ✓ | ✗ dropped when not interactive | same tool name as OpenCode, different schema |
| Zed | `ask_user` | ~ off in the default profiles | ✗ editor only | needs 2+ options or `allow_free_text` |
| Kilo CLI | `question` | ✓ | ✗ `kilo run` denies it | OpenCode fork; the VS Code extension uses `ask_followup_question` |
<!-- matrix:end -->

✓ offered and answered · ✗ not offered · ~ offered, but nobody answers or the call can't be proven

No native tool found in Amp, Goose, Windsurf / Devin for Terminal, Junie or Augment (checked 2026-11-05). Warp and Factory Droid have one, but I couldn't confirm its name, so they aren't rows yet.

[MATRIX.md](MATRIX.md) has every run: mode, model, result, what happens when nobody answers, and where the evidence comes from.

## what it does

Every harness names its tool differently, and whether the model actually gets it depends on the harness, the mode, and sometimes the model. A skill that just says "use your question tool" breaks the moment the tool isn't there, and the model either invents a name or pretends it asked.

The skill tells the model:

1. which tool its harness has, from the table above, so it never guesses a name,
2. what to do when the tool is missing: in a headless run, take the recommended option and say so in one line; otherwise ask once in plain text with lettered options,
3. what to do when the tool is there but nobody answers (skipped, empty, "no operator"): treat it as headless,
4. how to shape the call for that tool (Codex wants 2 or 3 options, Crush wants a type per question, Zed needs `allow_free_text` for typed answers),
5. how to write the options so people don't end up typing their own.

On Claude Code the plugin also checks each question before it's asked ([below](#the-ask-check-hook-claude-code)).

It picks one of two modes from context. **Requirements** ("ask me what you need") asks only what changes what gets built, 4 questions at most. **Study** ("quiz me on this") asks one question at a time, says right or wrong with a one-line why, and scores you at the end.

## what 2,119 real questions taught it

I counted every `AskUserQuestion` call in my own Claude Code sessions over 45 days: 2,119 calls, 3,476 answered questions.

| options offered | picked the first | typed their own | picked the last |
|---|---|---|---|
| 2 | 66% | 23% | 10% |
| 3 | 56% | 27% | 4% |
| 4 | 36% | 41% | 2% |

A fourth option almost never wins, and four-option questions got the most typed-in answers. Nearly half of my typed answers were "both", "check it yourself first" or "you do it". So the skill asks for three options, a "both" or multi-select when two can happen together, and a lookup before any question about a fact. That's one heavy user, so read it as a lead, not a law.

## the ask-check hook (Claude Code)

The Claude Code plugin also adds a `PreToolUse` hook on `AskUserQuestion`. It blocks one thing: a question the user already answered earlier in the same session, either word for word or restated inside a longer one. The call is denied and the model gets the earlier answer back, so it uses it instead of asking twice. Put "re-asking because <what changed>" in the question to get past it.

Everything else is a warning the model reads, never a block:

- "(Recommended)" on an option that isn't first
- four options (see the table above)
- a "which" or "or" choice with no "both" option and no multi-select
- a question about a fact with no "check it first" option
- an option that's the user's manual step, with no "agent does it" option
- an option preview holding more than 80 characters the question doesn't, since not every surface shows previews

It's stdlib Python with a 5-second timeout, and any error means silence, so it never stops a question by accident. It reads the session's own transcript and stores nothing.

Turn it off with `ASKMUX_CHECK=off` in your environment, or install the skill alone with `npx skills add`, which brings no hook.

## no tool, or nobody there

- Claude Code headless: the Agent SDK gets the tool with a permission handler, and a `PreToolUse` hook can answer it by returning `updatedInput` ([changelog](https://github.com/anthropics/claude-code/blob/646b74189c735abbccf78ef5cb7ddd38a07a36eb/CHANGELOG.md#L7392)).
- Cursor headless: Cursor suggests having the agent write the question as plain text and stop, then answering with `cursor-agent -p --resume <session_id> "<answer>"` ([forum](https://forum.cursor.com/t/cursor-agent-p-askquestion-is-auto-skipped-in-headless-mode-and-only-some-models-get-the-tool/173657)).
- No native tool at all: an MCP server can stand in. [mcp-feedback-enhanced](https://github.com/Minidoracat/mcp-feedback-enhanced) opens a feedback UI from any MCP client, and a harness that renders MCP elicitation forms, like Copilot CLI, can ask through one.

askmux stays a skill, plus one optional hook on Claude Code: no server, nothing to run.

## the probe

`scripts/probe.sh <harness> [cli args]` runs one harness headless in a temp folder with a prompt that asks for a multiple-choice question without naming the tool. Finding it is the test. The log goes to `runs/` (gitignored) and the exit code is the result:

| exit | meaning |
|---|---|
| 0 | the tool was called |
| 1 | the model says it has no such tool |
| 2 | the CLI isn't installed |
| 3 | neither: it asked in plain text, or the call isn't visible in the log |
| 124 | timed out |

```
bash scripts/probe.sh cursor --model composer-2.5
bash scripts/probe.sh --classify cursor < runs/<log>   # re-read a saved run
make probe                                             # every harness
```

![probe.sh on OpenCode: exit 1, the model answers NO_ASK_TOOL](docs/probe-demo.gif)

The gif is a re-render of one real run's output (OpenCode on its free model), not a live recording.

Each probe is one real model call on your account. Cursor's `--model` flag saves that model as your default; the probe puts your config back after. macOS users need `brew install coreutils` (for `gtimeout`).

## keeping it current

A weekly Action re-checks every cited issue and pinned source line. When one moves, it opens a draft PR that refreshes the baseline and lists what moved, so the matching rows get a look before the merge. `make watch` runs the same check locally. If your harness changed, the [issue template](.github/ISSUE_TEMPLATE/harness-changed.md) asks for the version and a probe log.

## development

```
make check      # manifest validation, tests, and a canary that plants bugs
make leakscan   # run before any push
make demo-gif   # re-render docs/probe-demo.gif from a fresh opencode probe (needs Pillow)
```

MIT licensed.
