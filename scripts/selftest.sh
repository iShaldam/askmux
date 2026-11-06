#!/usr/bin/env bash
# canary for the test suite: plant known bugs in a copy of the probe and make
# sure the tests catch every one. a green suite that misses a plant means nothing.
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
missed=0
plant() {  # name, sed expression, file to plant in (default: the probe)
  f="${3:-scripts/probe.sh}"
  tmp="$(mktemp -d)"
  cp -R "$root/scripts" "$root/tests" "$root/skills" "$root/hooks" "$root/MATRIX.md" "$root/README.md" "$root/matrix.json" "$root/watch.json" "$tmp/"
  sed -i.bak "$2" "$tmp/$f"
  if cmp -s "$tmp/$f" "$tmp/$f.bak"; then
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
plant "cursor config not restored" 's/if k in old: new\[k\] = old\[k\]/if 0: pass/'
plant "cursor matches thinking"   's/"askQuestionToolCall":/[Aa]sk[Qq]uestion/'
plant "codex matches prose"       's|"method":"item/tool/requestUserInput"|request_user_input|'
plant "summary dumps the log"     's/local log; log=/log=/'
hook=hooks/ask_check.py
plant "repeat check dropped"      's/if n and n in done:/if False:/' $hook
plant "re-asking escape ignored"  's/^        if REASK.search(text):/        if False:/' $hook
plant "restated question missed"  's/n == d or len(d) >= MIN_CONTAINED and d in n/n == d/' $hook
plant "question not normalized"   's/^    return " ".join(re.sub.*/    return str(s or "")/' $hook
plant "answers never read"        's/isinstance(ans, dict)/False/' $hook
plant "recommended anywhere warns" 's/if i and "(recommended)"/if "(recommended)"/' $hook
plant "four options silent"       's/if len(labels) >= 4:/if False:/' $hook
plant "both hint always on"       's/and CHOICE.search(text)):/):/' $hook
plant "fact hint ignores lookups" 's/ and not any(LOOKUP.search(l) for l in labels)//' $hook
plant "preview limit ignored"     's/if hidden > PREVIEW_MAX:/if hidden > 10**9:/' $hook
plant "off switch ignored"        's/== "off":/== "zzz":/' $hook
plant "errors escape"             's/        pass   # silence over/        raise  # silence over/' $hook
exit $missed
