import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE = os.path.join(ROOT, "scripts", "probe.sh")
ECHO = '{"type":"user","text":"...built-in tool for asking the user a question... reply exactly NO_ASK_TOOL."}\n'

# one call event per harness. grok's is trimmed from a real run; the rest
# follow each harness's documented event shape until a probe catches one
CALLS = {
    "claude": '{"type":"tool_use","name":"AskUserQuestion","input":{}}',
    "cursor": '{"type":"tool_call","tool_call":{"askQuestionToolCall":{}}}',
    "agy": '{"event":"step_update","step_update":{"step_type":"ask_question"}}',
    "copilot": '{"type":"tool.execution_start","data":{"toolName":"ask_user"}}',
    "grok": '{"type":"tool_call","title":"ask_user_question","toolName":"ask_user_question"}',
    "codex": '{"type":"item.started","item":{"type":"function_call","name":"request_user_input"}}',
}


def classify(harness, log):
    return subprocess.run(["bash", PROBE, "--classify", harness], input=log,
                          text=True, capture_output=True).returncode


def read_abs(path):
    with open(path) as f:
        return f.read()


def read(path):
    return read_abs(os.path.join(ROOT, path))


class Classify(unittest.TestCase):
    def test_call_is_0(self):
        for h, line in CALLS.items():
            self.assertEqual(classify(h, ECHO + line + "\n"), 0, h)

    def test_no_tool_reply_is_1(self):
        for h in CALLS:
            self.assertEqual(classify(h, ECHO + '{"result":"NO_ASK_TOOL"}\n'), 1, h)

    def test_echoed_prompt_alone_is_3(self):
        for h in CALLS:
            self.assertEqual(classify(h, ECHO + '{"result":"Pick a color: Red or Blue?"}\n'), 3, h)

    def test_listed_is_not_called(self):
        # a tool list naming the tool is not a call
        log = ECHO + '{"init":{"tools":["AskUserQuestion","ask_question","ask_user"]}}\n'
        for h in ("claude", "agy", "copilot"):
            self.assertEqual(classify(h, log), 3, h)

    def test_other_harness_call_does_not_count(self):
        self.assertEqual(classify("claude", CALLS["grok"] + "\n"), 3)


class Run(unittest.TestCase):
    def test_fake_harness_run(self):
        # a stand-in grok cli on PATH; the probe runs it and logs under runs/
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
            os.mkdir(os.path.join(tmp, "bin"))
            fake = os.path.join(tmp, "bin", "grok")
            with open(fake, "w") as f:
                f.write(f"#!/bin/sh\necho '{CALLS['grok']}'\n")
            os.chmod(fake, 0o755)
            env = dict(os.environ, PATH=os.path.join(tmp, "bin") + os.pathsep + os.environ["PATH"])
            r = subprocess.run(["bash", os.path.join(tmp, "scripts", "probe.sh"), "grok"],
                               env=env, text=True, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stdout)
            # the summary names the log file, it doesn't dump it
            self.assertRegex(r.stdout, r"^probe: grok\s+-> 0 \(log: runs/[\w-]+-grok\.jsonl\)\n$")
            (log,) = os.listdir(os.path.join(tmp, "runs"))
            self.assertIn("ask_user_question", read_abs(os.path.join(tmp, "runs", log)))


class Docs(unittest.TestCase):
    def test_every_probed_harness_has_a_matrix_row(self):
        harnesses = re.findall(r"^    (\w+)\)\s+echo", read("scripts/probe.sh"), re.M)
        self.assertEqual(sorted(harnesses), sorted(CALLS))
        matrix = read("MATRIX.md")
        for h in harnesses:
            self.assertRegex(matrix, rf"`{h}\b", h)

    def test_every_skill_tool_is_in_the_matrix(self):
        tools = set(re.findall(r"^\| [^|]+\| `(\w+)`", read("skills/askmux/SKILL.md"), re.M))
        self.assertTrue(tools)
        matrix = read("MATRIX.md")
        for t in tools:
            self.assertIn(f"`{t}`", matrix, t)


if __name__ == "__main__":
    unittest.main()
