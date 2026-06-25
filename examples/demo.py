"""
Offline end-to-end demo of the quiz engine — no ANTHROPIC_API_KEY required.

The Anthropic client is mocked, so this exercises the real engine/CLI plumbing
(generate -> answer -> grade -> stats -> review -> export) against a temp
workspace. It proves the wiring, not live question quality.

Run:  python examples/demo.py
"""

import json
import os
import sys
import tempfile
from unittest import mock

# Make the repo root importable when run as `python examples/demo.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import quiz_engine as qe  # noqa: E402  (import follows the sys.path tweak above)

# A realistic 3-question quiz the mocked model "returns".
QUIZ = {
    "exam": "ASP",
    "selection_rationale": "Blueprint default mix with extra weight on D2 (25%).",
    "questions": [
        {"id": "h1", "domain": "ASP-D2", "domain_name": "Safety Programs",
         "type": "recall", "difficulty": "easy",
         "stem": "Which control is most effective in the hierarchy of controls?",
         "options": {"A": "PPE", "B": "Elimination", "C": "Administrative", "D": "Engineering"},
         "correct": "B",
         "explanation": "Elimination removes the hazard at the source; PPE is least effective.",
         "source": "sample_domain2_safety_programs.md"},
        {"id": "h2", "domain": "ASP-D2", "domain_name": "Safety Programs",
         "type": "recall", "difficulty": "medium",
         "stem": "Which is a LEADING indicator?",
         "options": {"A": "Lost-time rate", "B": "Recordable rate",
                     "C": "Audits completed on time", "D": "Days away from work"},
         "correct": "C",
         "explanation": "Leading indicators are proactive (audits, training); the rest are lagging.",
         "source": "sample_domain2_safety_programs.md"},
        {"id": "h3", "domain": "ASP-D2", "domain_name": "Safety Programs",
         "type": "scenario", "difficulty": "medium",
         "stem": "In PDCA, monitoring results against objectives is which phase?",
         "options": {"A": "Plan", "B": "Do", "C": "Check", "D": "Act"},
         "correct": "C",
         "explanation": "'Check' monitors and measures results against objectives.",
         "source": "sample_domain2_safety_programs.md"},
    ],
}


class _FakeStream:
    """Mimics the context manager returned by client.messages.stream(...)."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        block = mock.Mock()
        block.type = "text"
        block.text = json.dumps(QUIZ)
        return mock.Mock(content=[block])


def main():
    workspace = tempfile.mkdtemp()
    kb = os.path.join(workspace, "kb")
    os.makedirs(kb)
    with open(os.path.join(kb, "sample.md"), "w") as f:
        f.write("The hierarchy of controls ranks elimination first.")

    with mock.patch.object(qe, "KB_GLOB", os.path.join(kb, "*.md")), \
         mock.patch.object(qe, "LOG_PATH", os.path.join(workspace, "study_log.json")), \
         mock.patch.object(qe, "OUT_DIR", os.path.join(workspace, "quizzes")):

        fake = mock.Mock()
        fake.messages.stream.return_value = _FakeStream()

        print("\n===== 1) GENERATE  (quiz_engine.py --exam ASP -n 3) =====")
        with mock.patch.object(qe, "get_client", return_value=fake):
            quiz = qe.generate_quiz(exam="ASP", n=3)
        print(f"Generated {len(quiz['questions'])} questions -> {qe._quiz_path()}")
        print("Rationale:", quiz["selection_rationale"])

        print("\n===== 2) ANSWER + GRADE  (--interactive) =====")
        print("Simulated answers: h1=B (correct), h2=A (WRONG), h3=C (correct)")
        qe.grade_and_report(quiz=quiz, answers={"h1": "B", "h2": "A", "h3": "C"})

        print("\n===== 3) STATS  (--stats) =====")
        qe.print_stats()

        print("\n===== 4) REVIEW  (--review) =====")
        print("The missed question (h2) returns; simulated answer this time: h2=C (correct)")
        qe.review_missed(answers={"h2": "C"})

        print("\n===== 5) EXPORT MARKDOWN  (--export-md) =====")
        path = qe.export_markdown(quiz)
        print(f"Wrote {path}\n--- file contents ---")
        print(open(path).read())


if __name__ == "__main__":
    main()
