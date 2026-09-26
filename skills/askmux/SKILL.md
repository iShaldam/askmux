---
name: askmux
description: >-
  Use when you need decisions from the user before starting work, or when the
  user says "quiz me", "ask me what you need", or wants options to pick from.
  Asks multiple-choice questions through the host harness's native question
  tool (Claude Code, Cursor, Antigravity, Codex, Copilot CLI, Grok CLI), with
  a fallback when the tool is missing.
---

# askmux

The user taps an option instead of typing an answer. Use the harness's own
question tool; never invent a tool name.

## Which tool

| Harness | Tool | Where it works |
|---|---|---|
| Claude Code | `AskUserQuestion` | interactive, and the Agent SDK; not in `claude -p` |
| Cursor | `AskQuestion` | model-gated: Composer 2.5 has it, Grok 4.5 and Auto didn't; headless skips the answer |
| Antigravity | `ask_question` | interactive; listed in `agy -p`, but headless picks for you |
| Codex | `request_user_input` | Plan mode in the TUI only; not in `codex exec` |
| Copilot CLI | `ask_user` | interactive; not in `copilot -p` |
| Grok CLI | `ask_user_question` | interactive and `grok -p` |

`MATRIX.md` in this repo has the tested detail per mode and model.

## If the tool is missing

1. Check your tool list once. If it isn't there, don't pretend it is.
2. Headless run (no one watching)? Don't ask. Take the recommended option,
   say so in one line, and keep going.
3. Otherwise say in one line what's missing and how to get it (Codex: switch
   to Plan mode; Cursor: pick a model that has `AskQuestion`), then ask once
   in plain text with the same options, labelled A, B, C, recommended first.

## Two modes

Pick from context; don't ask which.

**Requirements** ("ask me what you need"): ask only what changes what you
build. Obvious defaults: take them in one line, no question. Max 4
questions, one round. A second round only if an answer opened a real fork.

**Study** ("quiz me on this"): four options, one right, wrong ones plausible
(real confusions from the conversation). After each pick: right or wrong,
one line why. Score at the end. One question at a time; stop when they stop.
Only quiz what they read or decided, never internals they never saw.

## Writing options

- 2 to 4 options that lead to genuinely different outcomes.
- Labels 5 words or fewer. Put `(Recommended)` on the one you'd pick, first.
- Each description says what that choice costs: the trade-off, not a
  restatement of the label.
- Don't make one option obviously right in requirements mode.

## Don't

- Ask what you could find by reading a file.
- Re-ask something already answered.
- Ask them to reply with a number from a list.
