#!/usr/bin/env python3
"""PreToolUse(AskUserQuestion): stop a repeat question, nudge weak ones.

One block: a question whose text matches one already answered earlier in this
session is denied, quoting the answer, so the model uses it instead of asking
again. Escape hatch: "re-asking because <what changed>" in the question text.

Everything else is a warning added to the model's context, never a block:
a "(Recommended)" label that isn't on the first option, four options, a choice
whose options could combine, a fact question with no "look it up" option, a
manual step with no "agent does it" option, and a long option preview (not
every surface shows previews). Stdlib only, and any failure means silence: an
error must never stop a question. ASKMUX_CHECK=off turns the whole hook off.
"""
import json, os, re, sys

MIN_CONTAINED = 12  # an earlier question this long found inside a new one is a repeat
PREVIEW_MAX = 80   # characters an option preview may hold that the question text doesn't
UNION = re.compile(r"\b(both|all (three|of (them|it)|\d+)|everything)\b", re.I)
CHOICE = re.compile(r"\b(which|or)\b", re.I)
YESNO = re.compile(r"^(yes|no|not|skip|leave|drop|none|stop|hold|wait|keep as is|explain)\b", re.I)
FACT_Q = re.compile(r"^(did|was|were|has|have|is there|are there|do you (know|have|remember))\b|"
                    r"\b(what is (your|the)|what's (your|the)|who is|when is|what date)\b", re.I)
LOOKUP = re.compile(r"\b(check|look (it )?up|read|search|find|verify)\b", re.I)
MANUAL = re.compile(r"\b(i'll|i will|myself|by hand|manual(ly)?|you (do|run|click|send|type)|"
                    r"i (do|run|click|send|type) it)\b", re.I)
AGENT = re.compile(r"\b(agent|automate\w*|script|you (do|take) it|do it for me|take over)\b", re.I)
REASK = re.compile(r"\bre-?asking\b.*\bbecause\b", re.I | re.S)


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).split())


def answered(transcript):
    """{normalized question: answer} for every question this session had answered.
    The answers ride on the tool_result row as toolUseResult.answers."""
    out = {}
    try:
        with open(transcript, "rb") as f:
            for raw in f:
                if b'"answers"' not in raw:
                    continue   # most rows, and every big tool result, skip the parse
                try:
                    ans = json.loads(raw).get("toolUseResult", {}).get("answers")
                except (ValueError, AttributeError):
                    continue
                if isinstance(ans, dict):
                    for q, a in ans.items():
                        out[norm(q)] = a
    except OSError:
        pass
    return out


def said(a):
    return ", ".join(a) if isinstance(a, list) else str(a)


def repeat(qs, transcript):
    """The deny reason for the first question already answered here, else ''."""
    if not transcript:
        return ""
    done = answered(transcript)
    for q in qs:
        text = q.get("question", "")
        if REASK.search(text):
            continue
        n = norm(text)
        # the same words, or an earlier question restated with more around it
        hit = next((d for d in done if n == d or len(d) >= MIN_CONTAINED and d in n), None)
        if n and hit:
            return (f"askmux: you already asked this and the user answered: "
                    f"\"{said(done[hit])[:200]}\". Use that answer and keep going. If it really "
                    "changed, ask again with 're-asking because <what changed>' in the question text.")
    return ""


def hints(q):
    """Warnings for one question; quiet unless it fits one."""
    opts = q.get("options") or []
    labels = [str(o.get("label", "")) for o in opts]
    text = q.get("question", "")
    out = []
    for i, l in enumerate(labels):
        if i and "(recommended)" in l.lower():
            out.append(f"'(Recommended)' is on option {i + 1}; put the recommended option first")
    if len(labels) >= 4:
        out.append("4 options: the 4th rarely wins and people type their own more; cut to 3 or merge two")
    plain = [l for l in labels if not YESNO.search(l.replace("(Recommended)", "").strip())]
    if (not q.get("multiSelect") and not any(UNION.search(l) for l in labels)
            and len(plain) >= 2 and CHOICE.search(text)):
        out.append("if two options could both happen, add a 'both' option or set multiSelect")
    if FACT_Q.search(text) and not any(LOOKUP.search(l) for l in labels):
        out.append("this asks a fact: look it up first (files, search, accounts), or add 'check X first'")
    if any(MANUAL.search(l) for l in labels) and not any(AGENT.search(l) for l in labels):
        out.append("an option is the user's manual step: add 'agent does it' if an agent could")
    for o in opts:
        shown = norm(text)
        hidden = sum(len(l) for l in (norm(x) for x in str(o.get("preview") or "").splitlines())
                     if l and l not in shown)
        if hidden > PREVIEW_MAX:
            out.append(f"option '{o.get('label', '')}' has {hidden} characters only in its preview, and "
                       "not every surface shows previews: put what must be read in the question text")
            break
    return out


def main():
    if os.environ.get("ASKMUX_CHECK", "").lower() == "off":
        return 0
    try:
        p = json.load(sys.stdin)
        qs = [q for q in (p.get("tool_input") or {}).get("questions") or [] if isinstance(q, dict)]
        reason = repeat(qs, p.get("transcript_path"))
        if reason:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": reason}}))
            return 0
        notes = []
        for q in qs:
            name = q.get("header") or str(q.get("question", ""))[:30]
            notes += [f"'{name}': {h}" for h in hints(q)]
        if notes:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": "askmux (warn only): " + " | ".join(notes)}}))
    except Exception:
        pass   # silence over a blocked question, always
    return 0


if __name__ == "__main__":
    sys.exit(main())
