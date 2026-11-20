# contributing

The matrix is the product, so the most useful PR is a row that's wrong, missing or newly checked. Code and doc fixes are welcome too; `make check` has to pass either way.

## fix or add a harness row

Everything lives in `matrix.json`. Never edit the tables in `README.md`, `MATRIX.md` or `skills/askmux/SKILL.md` by hand: they're rendered from it.

1. **Add a run** to `rows`, one object per harness, surface/mode and model you checked:
   - `harness`: the key from `harnesses` (`claude`, `cursor`, `gemini`, ...)
   - `tool`: the exact name the model sees
   - `surface`, `model`: where you ran it, like `CLI, stdin or stdout not a terminal`, and the model id
   - `result`: what happened when the model was asked to use it
   - `unanswered`: what happens when nobody answers. It starts with one of `blocks`, `times out`, `skipped`, `no operator`, `auto-picks`, `n/a`, `unknown`
   - `evidence`: how you know. `manual, <date>` or `probe exit <code>, ...` for a run you did, or `reported, ` plus a link for a row read from source or docs
   - `date` (`YYYY-MM-DD`) and `cli_version` (a string, or `null` for a manual app check)
2. **If the summary changed**, edit that harness's entry under `harnesses`: `tool`, `where` (the SKILL.md table) and `grid` (the README table). `grid.interactive` and `grid.headless` start with ✓, ✗ or ~.
3. **Render and check:**
   ```
   python3 scripts/matrix.py render
   make check
   ```

A new harness also needs its tool name in `TOOLS` or `REPORTED` at the top of `tests/test_probe.py`. A reported harness needs at least two rows, each with a link.

## pin a source line

When a row comes from code, link the exact lines at a commit, not a branch:

```
https://github.com/<owner>/<repo>/blob/<40-char sha>/<path>#L10-L20
```

Then refresh the baseline so the weekly watch knows what those lines say today:

```
GITHUB_TOKEN=... python3 scripts/watch.py update   # token optional, avoids rate limits
make watch                                         # exits 0 when nothing moved
```

Commit `watch.json` with the row. Issue links in `evidence` get watched too: the watch notices when one opens or closes.

## attach a probe log

If the harness is one `scripts/probe.sh` knows, run it and attach the log from `runs/` to the PR or issue:

```
bash scripts/probe.sh <harness> [cli args]
```

The exit codes are in the README. Look through the log before you attach it: it's the model's raw output and can include paths from your machine.

To teach the probe a new harness, add its call pattern to `called()` and its command to the `case` in `scripts/probe.sh`, a sample call event to `CALLS` in `tests/test_probe.py`, and the harness to the `probe` loop in the `Makefile`.

## before you open the PR

```
make check      # manifest, tests, rendered tables, planted-bug canary
make leakscan
```
