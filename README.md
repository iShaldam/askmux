# askmux

Your skill says "ask me", and half your coding agents have no tool to ask with. askmux is one skill that tells the model which question tool its harness has, plus a tested matrix of who offers one, by mode and model.

Install in Claude Code:

```
/plugin marketplace add iShaldam/askmux
/plugin install askmux@askmux
```

Other harnesses: copy `skills/askmux/` into that harness's skills folder (Cursor: `~/.cursor/skills/`).

<!-- matrix:start -->
| harness | tool | interactive | headless | notes |
|---|---|---|---|---|
| Claude Code | `AskUserQuestion` | ✓ | ✗ `claude -p` | ✓ in the Agent SDK with a permission handler |
| Cursor | `AskQuestion` | ✓ model-gated | ~ Composer 2.5 calls it, the answer comes back "skipped" | ✗ on Grok 4.5 High and Auto, both modes |
| Antigravity | `ask_question` | ✓ | ~ listed, the call can't be proven | headless picks for you |
| Codex | `request_user_input` | ✓ Plan mode only | ✗ `codex exec` | Default mode needs the `default_mode_request_user_input` feature; some models get `request_user_input_async` |
| Copilot CLI | `ask_user` | ✓ | ✗ `copilot -p` | `--no-ask-user` turns it off |
| Grok CLI | `ask_user_question` | ✓ | ~ called, but no operator answers | |
| Gemini CLI | `ask_user` | ✓ | ✗ `gemini -p` | same tool name as Copilot CLI |
| OpenCode | `question` | ✓ | ✗ `opencode run` denies it | `--mini` allows it; `"permission": {"question": "deny"}` turns it off |
| Cline | `ask_question` | ✓ | ~ offered, picks the first option | older builds and the VS Code extension call it `ask_followup_question` |
| pi | `ask_user_question` | ~ extension only | ✗ print / JSON mode | same tool name as Grok CLI |
<!-- matrix:end -->

✓ offered and answered · ✗ not offered · ~ offered, but nobody answers or the call can't be proven

[MATRIX.md](MATRIX.md) has every run: mode, model, result, and where the evidence comes from.

Every harness has its own tool for asking you a multiple-choice question:
`AskUserQuestion` in Claude Code, `AskQuestion` in Cursor, `ask_question` in
Antigravity, `request_user_input` in Codex, `ask_user` in Copilot CLI,
`ask_user_question` in Grok CLI. Whether the model actually gets it depends
on the harness, the mode, and sometimes the model. A skill that just says
"use your question tool" breaks the moment the tool isn't there, and the
model either invents a name or pretends it asked.

## what it does

The skill tells the model:

1. which tool its harness has, from a table, so it never guesses a name,
2. what to do when the tool is missing: in a headless run, take the
   recommended option and say so in one line; otherwise ask once in plain
   text with lettered options,
3. how to write the question: 2 to 4 options, the recommended one first,
   each saying what that choice costs.

It picks one of two modes from context. **Requirements** ("ask me what you
need") asks only what changes what gets built, 4 questions at most.
**Study** ("quiz me on this") asks one question at a time, says right or
wrong with a one-line why, and scores you at the end.

## the probe

`scripts/probe.sh <harness> [cli args]` runs one harness headless in a temp
folder with a prompt that asks for a multiple-choice question without naming
the tool. Finding it is the test. The log goes to `runs/` (gitignored) and
the exit code is the result:

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

Each probe is one real model call on your account. Cursor's `--model` flag
saves that model as your default; the probe puts your config back after.

## development

```
make check      # manifest validation, tests, and a canary that plants bugs
make leakscan   # run before any push
```

MIT licensed.
