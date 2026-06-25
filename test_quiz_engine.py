"""
Tests for the ASP/CSP quiz engine.

Run:  python -m unittest -v

No ANTHROPIC_API_KEY required — the Anthropic client is mocked, so these cover
the full generate -> parse -> persist -> grade path offline.
"""

import json
import os
import tempfile
import unittest
from unittest import mock

import quiz_engine


SAMPLE_QUIZ = {
    "exam": "ASP",
    "selection_rationale": "Blueprint default mix with extra D2 weight.",
    "questions": [
        {
            "id": "q1",
            "domain": "ASP-D2",
            "domain_name": "Safety Programs & Concepts",
            "type": "recall",
            "difficulty": "easy",
            "stem": "Most effective control in the hierarchy?",
            "options": {"A": "PPE", "B": "Elimination", "C": "Admin", "D": "Engineering"},
            "correct": "B",
            "explanation": "Elimination removes the hazard at the source.",
            "source": "sample_domain2_safety_programs.md",
        },
        {
            "id": "q2",
            "domain": "ASP-D2",
            "domain_name": "Safety Programs & Concepts",
            "type": "recall",
            "difficulty": "medium",
            "stem": "Which is a leading indicator?",
            "options": {"A": "Lost-time rate", "B": "Recordable rate",
                        "C": "Audits completed", "D": "Days away"},
            "correct": "C",
            "explanation": "Leading indicators are proactive measures.",
            "source": "sample_domain2_safety_programs.md",
        },
    ],
}


class ParseQuizTests(unittest.TestCase):
    def test_parses_plain_json(self):
        self.assertEqual(quiz_engine._parse_quiz('{"exam": "ASP"}'), {"exam": "ASP"})

    def test_strips_markdown_fences(self):
        fenced = '```json\n{"exam": "CSP"}\n```'
        self.assertEqual(quiz_engine._parse_quiz(fenced), {"exam": "CSP"})

    def test_invalid_json_exits_cleanly(self):
        with self.assertRaises(SystemExit):
            quiz_engine._parse_quiz("not json at all")


class LoadSourcesTests(unittest.TestCase):
    def test_empty_kb_exits(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(quiz_engine, "KB_GLOB", os.path.join(d, "*.md")):
                with self.assertRaises(SystemExit):
                    quiz_engine.load_sources()

    def test_reads_and_labels_sources(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.md"), "w") as f:
                f.write("hello world")
            with mock.patch.object(quiz_engine, "KB_GLOB", os.path.join(d, "*.md")):
                blob = quiz_engine.load_sources()
        self.assertIn("### SOURCE: a.md", blob)
        self.assertIn("hello world", blob)


class _FakeStream:
    """Mimics the context-manager returned by client.messages.stream(...)."""
    def __init__(self, text):
        self._text = text

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        block = mock.Mock()
        block.type = "text"
        block.text = self._text
        return mock.Mock(content=[block])


class EndToEndTests(unittest.TestCase):
    """Full generate -> persist -> grade loop with a mocked client and temp dirs."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        d = self._tmp.name
        # Redirect all filesystem touchpoints into the temp dir.
        kb = os.path.join(d, "kb")
        os.makedirs(kb)
        with open(os.path.join(kb, "sample.md"), "w") as f:
            f.write("The hierarchy of controls ranks elimination first.")
        self._patches = [
            mock.patch.object(quiz_engine, "KB_GLOB", os.path.join(kb, "*.md")),
            mock.patch.object(quiz_engine, "LOG_PATH", os.path.join(d, "study_log.json")),
            mock.patch.object(quiz_engine, "OUT_DIR", os.path.join(d, "quizzes")),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        self._tmp.cleanup()

    def test_generate_persists_quiz_and_updates_log(self):
        fake_client = mock.Mock()
        fake_client.messages.stream.return_value = _FakeStream(json.dumps(SAMPLE_QUIZ))
        with mock.patch.object(quiz_engine, "get_client", return_value=fake_client):
            quiz = quiz_engine.generate_quiz(exam="ASP", n=2)

        self.assertEqual(len(quiz["questions"]), 2)
        self.assertTrue(os.path.exists(quiz_engine._quiz_path()))

        log = quiz_engine.load_log()
        self.assertIn("q1", log["recent_ids"])
        self.assertEqual(log["history"][-1]["exam"], "ASP")

    def test_record_results_accuracy_math(self):
        # Seed today's quiz file directly.
        os.makedirs(quiz_engine.OUT_DIR, exist_ok=True)
        with open(quiz_engine._quiz_path(), "w") as f:
            json.dump(SAMPLE_QUIZ, f)

        # One correct (q1->B), one wrong (q2->A, correct is C) => D2 = 50%.
        accuracy = quiz_engine.record_results({"q1": "B", "q2": "A"})
        self.assertEqual(accuracy["ASP-D2"], 50)

    def test_grade_and_report_with_injected_answers(self):
        os.makedirs(quiz_engine.OUT_DIR, exist_ok=True)
        with open(quiz_engine._quiz_path(), "w") as f:
            json.dump(SAMPLE_QUIZ, f)

        lines = []
        accuracy = quiz_engine.grade_and_report(
            quiz=SAMPLE_QUIZ,
            answers={"q1": "B", "q2": "C"},   # both correct
            output_fn=lines.append,
        )
        self.assertEqual(accuracy["ASP-D2"], 100)
        self.assertTrue(any("2/2" in line for line in lines))


class PromptAnswersTests(unittest.TestCase):
    def test_collects_and_skips(self):
        # q1 answered 'b' (lowercased -> B), q2 skipped via empty Enter.
        replies = iter(["b", ""])
        answers = quiz_engine.prompt_answers(
            SAMPLE_QUIZ,
            input_fn=lambda _prompt: next(replies),
            output_fn=lambda _msg: None,
        )
        self.assertEqual(answers, {"q1": "B"})


if __name__ == "__main__":
    unittest.main()
