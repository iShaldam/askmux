import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROBE = os.path.join(ROOT, "scripts", "probe.sh")
ECHO = '{"type":"user","text":"...built-in tool for asking the user a question... reply exactly NO_ASK_TOOL."}\n'

# one call event per harness. grok's and cursor's are trimmed from real runs;
# agy's is the shape its other tools log with (it leaves this one unlabelled);
# the rest follow each harness's documented event shape until a probe catches one
CALLS = {
    "claude": '{"type":"tool_use","name":"AskUserQuestion","input":{}}',
    "cursor": '{"type":"tool_call","subtype":"started","tool_call":{"askQuestionToolCall":{"args":{"title":"Pick a color"}}}}',
    "agy": '{"event":"step_update","step_update":{"step_type":"tool","tool_name":"ask_question"}}',
    "copilot": '{"type":"tool.execution_start","data":{"toolName":"ask_user"}}',
    "grok": '{"type":"tool_call","title":"ask_user_question","toolName":"ask_user_question"}',
    # unverified: codex exec never offers the tool; only app-server sends this
    "codex": '{"jsonrpc":"2.0","id":0,"method":"item/tool/requestUserInput","params":{}}',
}
# the name each model sees, as the skill's table lists it
TOOLS = {
    "claude": "AskUserQuestion",
    "cursor": "AskQuestion",
    "agy": "ask_question",
    "copilot": "ask_user",
    "grok": "ask_user_question",
    "codex": "request_user_input",
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

    def test_mention_is_not_called(self):
        # cursor's thinking said "No AskQuestion tool" and the old regex took it as a call
        for h, tool in TOOLS.items():
            log = (ECHO + f'{{"type":"thinking","subtype":"delta","text":"No {tool} tool"}}\n'
                   f'{{"type":"assistant","text":"I would call {tool} but"}}\n')
            self.assertEqual(classify(h, log), 3, h)

    def test_other_harness_call_does_not_count(self):
        self.assertEqual(classify("claude", CALLS["grok"] + "\n"), 3)

    def test_tool_definition_object_is_not_called(self):
        # copilot lists its tools as objects with a "name" key
        log = ECHO + '{"type":"session.tools_updated","data":{"tools":[{"name":"ask_user"}]}}\n'
        self.assertEqual(classify("copilot", log), 3)

    def test_unknown_harness_is_2(self):
        # an empty pattern would match anything
        self.assertEqual(classify("nope", ECHO + CALLS["grok"] + "\n"), 2)
        self.assertEqual(classify("agy-listdir", ""), 2)

    def test_spaced_json_still_counts(self):
        for h, line in CALLS.items():
            spaced = line.replace('":"', '": "').replace('":{', '": {')
            self.assertEqual(classify(h, ECHO + spaced + "\n"), 0, h)


def fake_run(tmp, cli, body, *args, **env):
    # run the probe from a copy of scripts/ with a stand-in cli first on PATH
    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(tmp, "scripts"))
    os.mkdir(os.path.join(tmp, "bin"))
    fake = os.path.join(tmp, "bin", cli)
    with open(fake, "w") as f:
        f.write("#!/bin/sh\n" + body)
    os.chmod(fake, 0o755)
    env = dict(os.environ, PATH=os.path.join(tmp, "bin") + os.pathsep + os.environ["PATH"], **env)
    return subprocess.run(["bash", os.path.join(tmp, "scripts", "probe.sh"), *args],
                          env=env, text=True, capture_output=True)


class Run(unittest.TestCase):
    def test_fake_harness_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = fake_run(tmp, "grok", f"echo '{CALLS['grok']}'\n", "grok")
            self.assertEqual(r.returncode, 0, r.stdout)
            # the summary names the log file, it doesn't dump it
            self.assertRegex(r.stdout, r"^probe: grok\s+-> 0 \(log: runs/[\w-]+-grok\.jsonl\)\n$")
            (log,) = os.listdir(os.path.join(tmp, "runs"))
            self.assertIn("ask_user_question", read_abs(os.path.join(tmp, "runs", log)))

    def test_cursor_default_model_survives(self):
        # cursor-agent --model saves that model as the user's default
        with tempfile.TemporaryDirectory() as tmp:
            cfg = os.path.join(tmp, "home", ".cursor", "cli-config.json")
            os.makedirs(os.path.dirname(cfg))
            with open(cfg, "w") as f:
                f.write('{"model":{"modelId":"grok-4.5"}}\n')
            body = ("echo '{\"model\":{\"modelId\":\"composer-2.5\"}}' > \"$HOME/.cursor/cli-config.json\"\n"
                    f"echo '{CALLS['cursor']}'\n")
            r = fake_run(tmp, "cursor-agent", body, "cursor", "--model", "composer-2.5",
                         HOME=os.path.join(tmp, "home"))
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertEqual(json.loads(read_abs(cfg)), {"model": {"modelId": "grok-4.5"}})

    def test_cursor_restore_keeps_other_settings(self):
        # the config also holds auth and permissions; a run may change those and they must stay
        with tempfile.TemporaryDirectory() as tmp:
            cfg = os.path.join(tmp, "home", ".cursor", "cli-config.json")
            os.makedirs(os.path.dirname(cfg))
            with open(cfg, "w") as f:
                json.dump({"model": {"modelId": "grok-4.5"}, "permissions": {"allow": []}}, f)
            new = {"model": {"modelId": "composer-2.5"}, "selectedModel": "composer-2.5",
                   "permissions": {"allow": ["Shell(ls)"]}}
            body = (f"echo '{json.dumps(new)}' > \"$HOME/.cursor/cli-config.json\"\n"
                    f"echo '{CALLS['cursor']}'\n")
            r = fake_run(tmp, "cursor-agent", body, "cursor", HOME=os.path.join(tmp, "home"))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(json.loads(read_abs(cfg)),
                             {"model": {"modelId": "grok-4.5"}, "permissions": {"allow": ["Shell(ls)"]}})

    def test_cursor_probe_refuses_to_overlap(self):
        # two overlapping probes would restore each other's model
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "home", ".cursor", "askmux-probe.lock"))
            r = fake_run(tmp, "cursor-agent", "echo x\n", "cursor", HOME=os.path.join(tmp, "home"))
            self.assertEqual(r.returncode, 2, r.stdout)
            self.assertIn("another cursor probe", r.stdout)


class Docs(unittest.TestCase):
    def test_every_probed_harness_has_a_matrix_row(self):
        harnesses = re.findall(r"^    (\w+)\)\s+echo", read("scripts/probe.sh"), re.M)
        self.assertEqual(sorted(harnesses), sorted(CALLS))
        matrix = read("MATRIX.md")
        for h in harnesses:
            self.assertRegex(matrix, rf"`{h}\b", h)

    def test_every_skill_tool_is_in_the_matrix(self):
        tools = set(re.findall(r"^\| [^|]+\| `(\w+)`", read("skills/askmux/SKILL.md"), re.M))
        self.assertEqual(tools, set(TOOLS.values()))
        matrix = read("MATRIX.md")
        for t in tools:
            self.assertIn(f"`{t}`", matrix, t)


if __name__ == "__main__":
    unittest.main()
