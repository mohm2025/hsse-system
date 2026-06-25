# ASP/CSP Adaptive Quiz Engine

A minimal, runnable backend for a daily study app built on the [Anthropic API](https://docs.claude.com/en/api/overview). Each run it:

1. Loads your knowledge-base text (markdown files / chapter excerpts under `./kb/`).
2. Loads your progress log (per-domain accuracy + recently-seen question IDs).
3. Asks Claude to generate *N* exam-style questions, weighted by the real BCSP blueprint domain percentages **and** your weak domains (spaced repetition).
4. Returns strict JSON the app can render, grade, and track.

The system prompt enforces hard rules: questions are written **only** from your supplied source material — the model never invents standards, CFR numbers, PELs, constants, or statistics.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
```

Add your study material as markdown files under `./kb/`. A placeholder sample is included so the engine runs out of the box — replace it with your own content (10–17 files works well). Rotate which files you include across days for full coverage of a large library.

## Run

```bash
python quiz_engine.py                  # generate ASP, 10 questions (default)
python quiz_engine.py --exam CSP -n 15 # generate CSP, 15 questions
python quiz_engine.py --interactive    # generate, answer interactively, and grade
python quiz_engine.py --grade          # grade today's already-generated quiz
python quiz_engine.py --help           # all flags
```

Generation writes `quizzes/quiz_YYYY-MM-DD.json` and updates `study_log.json`.

| Flag | Meaning |
|------|---------|
| `--exam {ASP,CSP}` | Which BCSP exam to target (default: `ASP`) |
| `-n, --num N` | Number of questions to generate (default: 10) |
| `-i, --interactive` | After generating, present the quiz, collect A/B/C/D answers, and grade |
| `--grade` | Skip generation; grade today's quiz interactively |

## Recording results (for adaptivity)

`--interactive` / `--grade` close the loop for you. To record answers programmatically:

```python
from quiz_engine import record_results

# {question_id: "A" | "B" | "C" | "D"}
accuracy = record_results({"abc123": "B", "def456": "A"})
print(accuracy)   # e.g. {"ASP-D2": 80, "ASP-D4": 50}
```

## Tests & linting

```bash
pip install -r requirements-dev.txt   # ruff
python -m unittest -v                  # tests
ruff check .                           # lint
```

The test suite mocks the Anthropic client, so it runs **without an API key** and covers the full generate → parse → persist → grade path offline. Lint config lives in `ruff.toml`.

## Claude Code on the web

`.claude/hooks/session-start.sh` (registered in `.claude/settings.json`) installs the runtime and dev dependencies on session start in web sessions, so tests, linting, and the engine work out of the box. It runs **asynchronously** (the session starts immediately while deps install in the background) and only in remote sessions.

## Daily schedule (cron, 7am)

```cron
0 7 * * *  cd /path/to/app && python quiz_engine.py
```

## Model

Defaults to `claude-sonnet-4-6` (good accuracy/cost balance). For harder reasoning, set `MODEL = "claude-opus-4-8"` in `quiz_engine.py`. Model strings change over time — confirm the latest in the [Anthropic API docs](https://docs.claude.com/en/api/overview).

## Files

| Path | Purpose |
|------|---------|
| `quiz_engine.py` | The engine: prompt, generation, grading, progress tracking. |
| `kb/` | Your source material (markdown). Questions are grounded only in these files. |
| `study_log.json` | Generated. Per-domain accuracy, recent question IDs, run history. |
| `quizzes/` | Generated. One JSON quiz per day. |

`study_log.json` and `quizzes/` are git-ignored — they are per-environment runtime artifacts.
