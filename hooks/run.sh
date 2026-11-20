#!/bin/sh
# runs ask_check.py with the first python that works; any failure is silence.
# a script, not an inline loop, so the hook command in hooks.json is a plain path
i=$(cat)
for p in python3 'py -3' python; do
  # $p unquoted on purpose: 'py -3' is a command plus a flag
  o=$(printf %s "$i" | $p "$(dirname "$0")/ask_check.py" 2>/dev/null) && { printf %s "$o"; exit 0; }
done
exit 0
