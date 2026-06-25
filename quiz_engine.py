"""
ASP/CSP Adaptive Quiz Engine
----------------------------
A minimal, runnable backend for a daily study app built on the Anthropic API.

What it does each run:
  1. Loads your knowledge-base text (the markdown files / chapter excerpts).
  2. Loads your progress log (per-domain accuracy + recently-seen question IDs).
  3. Asks Claude to generate N exam-style questions, weighted by the real
     blueprint domain percentages AND your weak domains (spaced repetition).
  4. Returns strict JSON the app can render, grade, and track.

Install:  pip install -r requirements.txt
Run:      ANTHROPIC_API_KEY=sk-... python quiz_engine.py
Schedule: add a cron line (bottom of file) to run it daily.

Model strings change over time — confirm the latest at https://docs.claude.com/en/api/overview
"""

import os
import json
import datetime
import glob

from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from env
MODEL = "claude-sonnet-4-6"   # good accuracy/cost balance; "claude-opus-4-8" for harder reasoning

# ---------------------------------------------------------------------------
# THE PROMPT — this is the part that matters. It encodes the blueprint weights,
# the no-fabrication rule, grounding, adaptivity, and the output contract.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are an exam-item writer for the BCSP ASP and CSP certification exams (blueprints ASP11 / CSP11, V.2024.04.24).
Your job is to generate high-quality practice questions from supplied source material — never from memory.

== HARD RULES (non-negotiable) ==
1. GROUNDING: Write questions ONLY from the SOURCE MATERIAL in the user message. Do not introduce any
   standard, regulation, numeric value, threshold, or formula that is not present in the source. If a value
   you'd need is not in the source, do not write a question that depends on it.
2. NO FABRICATION: Never invent citations, CFR numbers, PELs, constants, or statistics. If unsure, omit.
3. ACCURACY > VARIETY: Distractors must be plausible but unambiguously wrong. Exactly one correct option.
4. Each question cites the source it came from (file name and/or standard section shown in the source).
5. Distinguish fact vs. best practice in the explanation where relevant.

== EXAM BLUEPRINT WEIGHTS (use these to distribute questions) ==
ASP11: D1 Math 10% | D2 Safety Programs & Concepts 25% | D3 Ergonomics 8% | D4 Fire 12% |
       D5 Emergency Prep & Response 10% | D6 Industrial Hygiene & Occ Health 12% |
       D7 Environmental 7% | D8 Training/Education/Comm 11% | D9 Legal 5%
CSP11: D1 Advanced Application 25% | D2 Program Management 25% | D3 Risk Management 15% |
       D4 Emergency Management 9% | D5 Environmental 6% | D6 Occ Health & Applied Science 10% | D7 Training 10%

== ADAPTIVITY ==
The user message includes PERFORMANCE state: per-domain accuracy and a list of recently-seen question IDs.
- Default the domain mix to the blueprint weights for the requested exam.
- Then SHIFT extra weight toward domains where accuracy is low (< 70%).
- Include 1-2 spaced-repetition items revisiting previously-missed topics.
- Never reuse a stem that matches a recently-seen ID's topic; vary angle and numbers.
- Mix item types: recall, calculation, and scenario/application. Calculations must be solvable from the source.

== OUTPUT CONTRACT ==
Return ONLY valid JSON (no markdown, no prose) matching exactly:
{
  "exam": "ASP" | "CSP",
  "selection_rationale": "one sentence on why these domains/weights today",
  "questions": [
    {
      "id": "<short stable hash you generate from the stem>",
      "domain": "<e.g. ASP-D2>",
      "domain_name": "<e.g. Safety Programs & Concepts>",
      "type": "recall" | "calculation" | "scenario",
      "difficulty": "easy" | "medium" | "hard",
      "stem": "<the question>",
      "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
      "correct": "A" | "B" | "C" | "D",
      "explanation": "<why correct; note the trap if any>",
      "source": "<file / standard section from the source material>"
    }
  ]
}
"""

# ---------------------------------------------------------------------------
# Plumbing
# ---------------------------------------------------------------------------
KB_GLOB   = "./kb/*.md"          # put your 10-17 markdown files (and chapter text) here
LOG_PATH  = "./study_log.json"
OUT_DIR   = "./quizzes"


def load_sources(max_chars=60000):
    """Load KB text. For a big library, retrieve a rotating subset instead of all of it."""
    text = []
    for path in sorted(glob.glob(KB_GLOB)):
        with open(path, encoding="utf-8") as f:
            text.append(f"### SOURCE: {os.path.basename(path)}\n{f.read()}")
    if not text:
        raise SystemExit(
            f"No source files found matching {KB_GLOB}. "
            "Add your markdown study material under ./kb/ and run again."
        )
    blob = "\n\n".join(text)
    return blob[:max_chars]  # keep within a sane context budget; rotate files across days for full coverage


def load_log():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"domain_accuracy": {}, "recent_ids": [], "history": []}


def save_log(log):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def _parse_quiz(raw: str) -> dict:
    """Strip any accidental markdown fencing and parse the model's JSON response."""
    raw = raw.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"Model did not return valid JSON ({e}).\n"
            f"--- first 500 chars of response ---\n{raw[:500]}"
        )


def generate_quiz(exam="ASP", n=10):
    sources = load_sources()
    log = load_log()

    performance = {
        "domain_accuracy": log["domain_accuracy"],
        "recent_ids": log["recent_ids"][-50:],
    }
    user_msg = (
        f"EXAM: {exam}\n"
        f"GENERATE: {n} questions.\n"
        f"PERFORMANCE:\n{json.dumps(performance, indent=2)}\n\n"
        f"SOURCE MATERIAL:\n{sources}"
    )

    # Stream so a long JSON payload (10+ detailed questions) can't trip the SDK
    # HTTP timeout; get_final_message() gives us the assembled response.
    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        temperature=0.7,                 # variety of phrasing; grounding rule keeps facts fixed
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        resp = stream.get_final_message()

    raw = "".join(b.text for b in resp.content if b.type == "text")
    quiz = _parse_quiz(raw)

    # persist quiz + update log so tomorrow's run is adaptive
    os.makedirs(OUT_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    with open(f"{OUT_DIR}/quiz_{today}.json", "w", encoding="utf-8") as f:
        json.dump(quiz, f, indent=2)

    log["recent_ids"] += [q["id"] for q in quiz["questions"]]
    log["history"].append({"date": today, "exam": exam,
                           "domains": [q["domain"] for q in quiz["questions"]]})
    save_log(log)
    return quiz


def record_results(answers: dict):
    """answers = {question_id: 'A'/'B'/... }. Call after the user answers; updates per-domain accuracy."""
    today = datetime.date.today().isoformat()
    with open(f"{OUT_DIR}/quiz_{today}.json", encoding="utf-8") as f:
        quiz = json.load(f)
    log = load_log()
    acc = log["domain_accuracy"]
    for q in quiz["questions"]:
        d = q["domain"]
        got = answers.get(q["id"])
        if got is None:
            continue
        rec = acc.setdefault(d, {"correct": 0, "total": 0})
        rec["total"] += 1
        rec["correct"] += int(got == q["correct"])
    save_log(log)
    return {d: round(100 * v["correct"] / v["total"]) for d, v in acc.items() if v["total"]}


if __name__ == "__main__":
    quiz = generate_quiz(exam="ASP", n=10)
    print(json.dumps(quiz, indent=2)[:1500], "...")

# ---------------------------------------------------------------------------
# Daily schedule (cron, runs 7am): 0 7 * * *  cd /path/to/app && python quiz_engine.py
# ---------------------------------------------------------------------------
