#!/usr/bin/env bash
# canary for the test suite: plant known bugs in a copy of the probe and make
# sure the tests catch every one. a green suite that misses a plant means nothing.
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
missed=0
plant() {  # name, sed expression
  tmp="$(mktemp -d)"
  cp -R "$root/scripts" "$root/tests" "$root/skills" "$root/MATRIX.md" "$tmp/"
  sed -i.bak "$2" "$tmp/scripts/probe.sh"
  if cmp -s "$tmp/scripts/probe.sh" "$tmp/scripts/probe.sh.bak"; then
    echo "selftest: plant '$1' did not apply -- the canary is stale"; missed=1
  elif (cd "$tmp" && python3 -m unittest discover -s tests >/dev/null 2>&1); then
    echo "selftest: MISSED '$1'"; missed=1
  else
    echo "selftest: caught '$1'"
  fi
  rm -rf "$tmp"
}
plant "call check skipped"        's/<<<"\$log" \&\& return 0/<<<"" \&\& return 0/'
plant "echoed prompt counts"      "s/grep -v 'built-in tool for asking'/grep -v 'zzz'/"
plant "inconclusive as no tool"   's/^  return 3$/  return 1/'
plant "claude matches tool list"  's/"name":"AskUserQuestion"/AskUserQuestion/'
plant "harness dropped"           '/^    codex)   echo/d'
exit $missed
