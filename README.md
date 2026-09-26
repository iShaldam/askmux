# askmux

One ask-the-user skill for every coding agent harness, and a tested matrix
of which question tool actually shows up where.

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

## where it works

Short version, from headless probes and reported sources:

- **Grok CLI** calls it, even in `grok -p`.
- **Cursor** depends on the model: Composer 2.5 calls it, Grok 4.5 doesn't
  have it.
- **Claude Code** and **Copilot CLI** don't offer it in print mode (`-p`).
- **Codex** only offers it in Plan mode, which is TUI-only.
- **Antigravity** lists it, but its stream doesn't label the call, so a
  headless run can't prove it happened.

[`MATRIX.md`](MATRIX.md) has every run: mode, model, result, and where the
evidence comes from.

## install

Claude Code:

```
/plugin marketplace add iShaldam/askmux
/plugin install askmux@askmux
```

Other harnesses: copy `skills/askmux/` into that harness's skills folder
(Cursor: `~/.cursor/skills/`).

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

Each probe is one real model call on your account. Cursor's `--model` flag
saves that model as your default; the probe puts your config back after.

## development

```
make check      # manifest validation, tests, and a canary that plants bugs
make leakscan   # run before any push
```

MIT licensed.
