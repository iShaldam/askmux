#!/usr/bin/env bash
# probe one harness headless: does the model reach for its native
# ask-the-user tool? the prompt never names the tool, so finding it is the test.
#   probe.sh <harness> [extra cli args]    e.g. probe.sh cursor --model composer-2.5
#   probe.sh --classify <harness> < log    classify a saved run
# exit: 0 tool called | 1 model says it has no such tool | 2 cli missing
#       3 neither (asked in plain text, or the call isn't visible; read the log)
#       124 timed out
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
PROMPT='Ask me one multiple-choice question using your built-in tool for asking the user a question (not plain text): "Pick a color" with options Red and Blue. If you have no such tool, reply exactly NO_ASK_TOOL.'

called() {  # a pattern only a real call event matches
  case "$1" in
    claude)  echo '"name":"AskUserQuestion"' ;;
    cursor)  echo '"askQuestionToolCall":' ;;
    agy)     echo '"tool_name":"ask_question"' ;;
    copilot) echo '"type":"tool\.execution_start".*"toolName":"ask_user"' ;;  # not its tool list
    grok)    echo '"toolName":"ask_user_question"' ;;
    codex)   echo '"method":"item/tool/requestUserInput"' ;;  # app-server only; exec never offers it
    *) return 1 ;;
  esac
}

classify() {
  local log; log="$(cat)"
  grep -qE "$(called "$1")" <<<"$log" && return 0
  # some harnesses echo the prompt back; its NO_ASK_TOOL doesn't count
  grep -v 'built-in tool for asking' <<<"$log" | grep -q NO_ASK_TOOL && return 1
  return 3
}

if [ "${1:-}" = --classify ]; then
  called "${2:?harness}" >/dev/null || exit 2  # no pattern would match anything
  classify "$2"; exit
fi

h="${1:?usage: probe.sh <harness> [extra cli args]}"; shift
called "$h" >/dev/null || { echo "probe: unknown harness '$h'"; exit 2; }
w="$(mktemp -d)"   # run outside the repo so an agent can't touch it
# cursor-agent --model saves that model as your default; put yours back after
snap="$(mktemp)"; cfg="$HOME/.cursor/cli-config.json"
[ "$h" = cursor ] && cp "$cfg" "$snap" 2>/dev/null
trap '[ -s "$snap" ] && cp "$snap" "$cfg"; rm -rf "$w" "$snap"' EXIT
case "$h" in
  claude)  cmd=(claude -p "$PROMPT" --output-format stream-json --verbose) ;;
  cursor)  cmd=(cursor-agent -p "$PROMPT" --output-format stream-json --trust --workspace "$w") ;;
  agy)     cmd=(agy -p "$PROMPT" --output-format stream-json --print-timeout 2m) ;;
  copilot) cmd=(copilot -p "$PROMPT" --output-format json -s) ;;
  grok)    cmd=(grok -p "$PROMPT" --output-format streaming-json) ;;
  codex)   cmd=(codex exec --json "$PROMPT") ;;
esac
command -v "${cmd[0]}" >/dev/null || { echo "probe: $h -> 2 (${cmd[0]} not installed)"; exit 2; }
mkdir -p "$root/runs"
log="$root/runs/$(date +%Y%m%d-%H%M%S)-$h.jsonl"
(cd "$w" && timeout "${PROBE_TIMEOUT:-150}" "${cmd[@]}" "$@") > "$log" 2>&1
rc=$?
[ $rc = 124 ] || { classify "$h" < "$log"; rc=$?; }
echo "probe: $h $* -> $rc (log: ${log#"$root"/})"
exit $rc
