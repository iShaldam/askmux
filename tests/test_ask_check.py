"""Synthetic transcripts and payloads only, shaped like Claude Code's real ones."""
import json, os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def pre_tool_use():
    with open(os.path.join(ROOT, "hooks", "hooks.json")) as f:
        return json.load(f)["hooks"]["PreToolUse"][0]


HOOK = os.path.join(ROOT, "hooks", "ask_check.py")
sys.path.insert(0, os.path.join(ROOT, "hooks"))
import ask_check as ac  # noqa: E402


def q(text, *labels, **kw):
    return dict({"question": text, "header": "Pick",
                 "options": [{"label": l, "description": "d"} for l in labels]}, **kw)


def asked(*questions, answers=None):
    """The two transcript rows of one answered AskUserQuestion call."""
    use = {"type": "assistant", "message": {"content": [{
        "type": "tool_use", "id": "toolu_1", "name": "AskUserQuestion",
        "input": {"questions": list(questions)}}]}}
    res = {"type": "user", "message": {"content": [{
        "type": "tool_result", "tool_use_id": "toolu_1",
        "content": "Your questions have been answered. You can now continue."}]},
        "toolUseResult": {"questions": list(questions), "answers": answers}}
    return [use, res]


class Hook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.transcript = os.path.join(self.tmp.name, "t.jsonl")
        self.env = dict(os.environ)
        self.env.pop("ASKMUX_CHECK", None)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, *rows):
        with open(self.transcript, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def run_hook(self, *questions, env=None, stdin=None):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "AskUserQuestion",
                   "session_id": "s1", "transcript_path": self.transcript,
                   "tool_input": {"questions": list(questions)}}
        r = subprocess.run([sys.executable, HOOK], capture_output=True, text=True,
                           input=stdin if stdin is not None else json.dumps(payload),
                           env=env or self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout else {}

    def warned(self, *questions):
        return self.run_hook(*questions).get("additionalContext", "")


class Repeat(Hook):
    def test_a_fresh_question_goes_through(self):
        self.write(*asked(q("Database to use?", "a", "b"), answers={"Database to use?": "a"}))
        self.assertEqual(self.run_hook(q("Cache to use?", "x", "y")), {})

    def test_an_answered_question_is_denied_with_the_answer(self):
        self.write(*asked(q("Database to use?", "a", "b"), answers={"Database to use?": "Postgres"}))
        out = self.run_hook(q("Database to use?", "a", "b"))
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("Postgres", out["permissionDecisionReason"])

    def test_case_and_punctuation_dont_dodge_it(self):
        self.write(*asked(q("Database to use?", "a", "b"), answers={"Database to use?": "a"}))
        self.assertEqual(self.run_hook(q("  database TO use ", "a", "b"))["permissionDecision"], "deny")

    def test_a_restated_question_is_still_a_repeat(self):
        self.write(*asked(q("Database to use?", "a", "b"), answers={"Database to use?": "a"}))
        out = self.run_hook(q("Quick check: database to use for the cache layer?", "a", "b"))
        self.assertEqual(out["permissionDecision"], "deny")

    def test_a_short_earlier_question_isnt_found_inside_others(self):
        self.write(*asked(q("Ship it?", "Yes", "No"), answers={"Ship it?": "Yes"}))
        self.assertNotIn("permissionDecision", self.run_hook(q("Ship it to staging first?", "Yes", "No")))

    def test_a_multiselect_answer_is_quoted_whole(self):
        self.write(*asked(q("Pick one?", "a", "b", multiSelect=True), answers={"Pick one?": ["a", "b"]}))
        self.assertIn("a, b", self.run_hook(q("Pick one?", "a", "b"))["permissionDecisionReason"])

    def test_re_asking_because_gets_through(self):
        self.write(*asked(q("Database to use?", "a", "b"), answers={"Database to use?": "a"}))
        out = self.run_hook(q("Database to use? (re-asking because the load numbers changed)", "a", "b"))
        self.assertNotIn("permissionDecision", out)

    def test_one_repeat_in_a_batch_denies_the_batch(self):
        self.write(*asked(q("Database to use?", "a", "b"), answers={"Database to use?": "a"}))
        out = self.run_hook(q("Cache to use?", "x", "y"), q("Database to use?", "a", "b"))
        self.assertEqual(out["permissionDecision"], "deny")

    def test_an_unanswered_question_is_not_a_repeat(self):
        use = asked(q("Database to use?", "a", "b"), answers={})[0]
        self.write(use)
        self.assertEqual(self.run_hook(q("Database to use?", "a", "b")), {})

    def test_no_transcript_means_no_block(self):
        self.transcript = os.path.join(self.tmp.name, "missing.jsonl")
        self.assertEqual(self.run_hook(q("Database to use?", "a", "b")), {})

    def test_junk_rows_are_skipped(self):
        with open(self.transcript, "w") as f:
            f.write('not json "answers"\n{"toolUseResult": 5, "x": "answers"}\n')
        self.assertEqual(self.run_hook(q("Database to use?", "a", "b")), {})


class Hints(Hook):
    def test_recommended_not_first_warns(self):
        self.assertIn("put the recommended option first",
                      self.warned(q("Database to use?", "a", "b (Recommended)")))

    def test_recommended_first_is_quiet(self):
        self.assertNotIn("recommended", self.warned(q("Database to use?", "a (Recommended)", "b")))

    def test_four_options_warn(self):
        self.assertIn("4 options", self.warned(q("Database to use?", "a", "b", "c", "d")))

    def test_three_options_dont(self):
        self.assertNotIn("4 options", self.warned(q("Database to use?", "a", "b", "c")))

    def test_combinable_choice_hints_both(self):
        self.assertIn("'both' option", self.warned(q("Which one first?", "Ship the CLI", "Ship the docs")))

    def test_both_option_or_multiselect_silences_it(self):
        self.assertNotIn("'both'", self.warned(q("Which one first?", "CLI", "Docs", "Both")))
        self.assertNotIn("'both'", self.warned(q("Which one first?", "CLI", "Docs", multiSelect=True)))

    def test_yes_no_is_not_a_choice_between_things(self):
        self.assertNotIn("'both'", self.warned(q("Ship it or hold?", "Yes", "No")))

    def test_fact_question_says_look_it_up(self):
        self.assertIn("look it up first", self.warned(q("What is the deploy region?", "us", "eu")))

    def test_a_check_option_silences_the_fact_hint(self):
        self.assertNotIn("look it up", self.warned(q("What is the deploy region?", "us", "Check the config first")))

    def test_manual_step_without_an_agent_option(self):
        self.assertIn("'agent does it'", self.warned(q("How should the key rotate?", "I'll do it myself", "Wait")))

    def test_agent_option_silences_the_manual_hint(self):
        self.assertNotIn("'agent does it'", self.warned(
            q("How should the key rotate?", "I'll do it myself", "Agent does it")))

    def test_long_preview_warns_but_does_not_block(self):
        o = q("Send this?", "Send", "Hold")
        o["options"][0]["preview"] = "x" * 200
        out = self.run_hook(o)
        self.assertIn("only in its preview", out["additionalContext"])
        self.assertNotIn("permissionDecision", out)

    def test_a_preview_the_question_repeats_is_fine(self):
        o = q("Send this: hello world", "Send", "Hold")
        o["options"][0]["preview"] = "hello world"
        self.assertEqual(self.run_hook(o), {})

    def test_warnings_name_the_question(self):
        self.assertIn("'Pick':", self.warned(q("Database to use?", "a", "b", "c", "d")))


class Safe(Hook):
    def test_off_switch(self):
        env = dict(self.env, ASKMUX_CHECK="off")
        self.write(*asked(q("Database to use?", "a", "b"), answers={"Database to use?": "a"}))
        self.assertEqual(self.run_hook(q("Database to use?", "a", "b"), env=env), {})

    def test_garbage_stdin_is_silent(self):
        self.assertEqual(self.run_hook(stdin="not json"), {})

    def test_odd_payloads_are_silent(self):
        for tool_input in (None, 3, {"questions": "x"}, {"questions": [None, 4, {"options": 7}]}):
            payload = json.dumps({"tool_input": tool_input, "transcript_path": self.transcript})
            self.assertEqual(self.run_hook(stdin=payload), {})

    def test_the_plugin_hook_runs_it(self):
        cmd = pre_tool_use()
        self.assertEqual(cmd["matcher"], "AskUserQuestion")
        self.write(*asked(q("Database to use?", "a", "b"), answers={"Database to use?": "Postgres"}))
        payload = {"tool_input": {"questions": [q("Database to use?", "a", "b")]}, "transcript_path": self.transcript}
        r = subprocess.run(["sh", "-c", cmd["hooks"][0]["command"]], capture_output=True, text=True,
                           input=json.dumps(payload), env=dict(self.env, CLAUDE_PLUGIN_ROOT=ROOT))
        self.assertEqual(r.returncode, 0)
        self.assertIn("deny", r.stdout)

    def test_every_hook_has_a_short_timeout(self):
        cmd = pre_tool_use()
        self.assertLessEqual(cmd["hooks"][0]["timeout"], 5)


if __name__ == "__main__":
    unittest.main()
