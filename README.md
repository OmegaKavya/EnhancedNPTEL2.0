# Enhanced NPTEL Learning Platform

A Flask-based adaptive learning platform that combines structured video learning, AI-generated quizzes, conceptual review, learner adaptation, and personalized revision support.

## Architecture

For full system architecture, module boundaries, adaptive-engine pipeline, and request lifecycle diagrams, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Why this project stands out

- Adaptive intelligence stack: BKT mastery + speed adaptation + behavior clustering.
- Concept-first assessment quality: basic-to-advanced question progression with anti-generic prompt constraints.
- Reliability by design: graceful fallback paths for transcript and LLM failures.
- End-to-end product depth: video checkpoints, adaptive quiz engine, review analytics, and heatmap-driven insights.

## What this project does

This application is designed to turn a topic into a guided learning flow:

1. Watch a topic video.
2. Study topic-specific submodules and quick revision checkpoints.
3. Take an adaptive conceptual quiz.
4. Review answers with explanations, insights, and performance feedback.
5. Track progress over time with dashboard analytics and heatmaps.

The project is built for topic mastery, not generic study-habit questions. Quizzes are intended to move from basic concepts to advanced reasoning.

## Core features

### 1. Adaptive quiz generation

- Generates topic-based MCQ quizzes using local Ollama models.
- Questions adapt to learner mastery and speed.
- Quiz length can vary from 7 to 15 questions.
- Difficulty is adjusted based on learner behavior.
- Question repetition is minimized across attempts.

### 2. Conceptual question quality

- Questions are generated to test understanding of the topic itself.
- The quiz flow is designed to move from:
  - basic definitions and foundations,
  - to intermediate mechanisms and applications,
  - to advanced reasoning, edge cases, and trade-offs.
- Study-habit or generic best-practice style questions are intentionally avoided.

### 3. Quiz review and explanations

- Every attempt can be reviewed later.
- Shows correct answer, user answer, score, and performance details.
- Includes AI-generated insights and focus areas.
- Helps the learner understand where reasoning broke down.

### 4. AI insights and revision support

- Generates topic-wise revision support after a quiz.
- Highlights focus concepts.
- Builds a quick cheat-sheet style summary.
- Suggests related learning resources.

### 5. Video learning with submodules

- Each topic page is structured into submodules.
- Submodules provide a more guided learning path instead of a single video-only experience.
- Includes checkpoint mini-quizzes during video playback.
- Checkpoints help reinforce concepts before moving ahead.

### 6. Timer and hint behavior

- Quiz questions use per-question timing.
- Hints unlock during the question flow.
- When time expires, the quiz advances instead of terminating.

### 7. Dashboard analytics

- Tracks progress and quiz history.
- Shows review links for past attempts.
- Displays topic-wise heatmaps.
- Surfaces mastery, score, timing, and learning trends.

### 8. Local Ollama integration

- Uses Ollama for quiz generation and evaluation.
- Default model is `llama3.2`.
- Falls back safely when the model is unavailable.

## Tech stack

- Python 3.12
- Flask
- Jinja templates
- JavaScript
- Ollama local LLM API
- scikit-learn
- pandas
- numpy
- pyBKT
- YouTube transcript extraction

## Project structure

- `app.py` - Main Flask application and route handling.
- `backend/` - Quiz generation, evaluation, adaptation, and recommendation logic.
- `frontend/templates/` - HTML templates for landing, dashboard, video, quiz, review, login, and register pages.
- `static/` - Shared CSS and other static assets.
- `data/` - JSON data used by the app for users, progress, quiz attempts, and video metadata.
- `models/` - Saved learning/adaptation models.
- `scripts/` - Utility scripts for training models.
- `utils/` - Ollama client and helper utilities.

## Setup

### 1. Clone the repository

```bash
git clone <your-github-repo-url>
cd UpdatedEnancedNPTEL-main
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and start Ollama

Make sure Ollama is installed and running locally.

Check available models:

```bash
ollama list
```

If needed, pull the default model:

```bash
ollama pull llama3.2
```

### 5. Run the app

```bash
python app.py
```

Then open the local address shown in the terminal, usually:

```bash
http://127.0.0.1:5000
```

## How the learning flow works

### Landing and authentication

- Users can register and log in.
- Session data is used to manage access.

### Dashboard

- Shows the learner’s progress.
- Displays attempts, topic mastery, and heatmap-style insights.
- Provides quick access to video review and quiz review pages.

### Topic video page

- Presents the video lesson.
- Breaks the topic into submodules.
- Adds checkpoint quizzes during playback.
- Encourages active learning instead of passive watching.

### Quiz page

- Loads a topic-specific adaptive quiz.
- Shows a revision helper while the quiz is being prepared.
- Uses timed questions and adaptive difficulty.
- Unlocks hints during the quiz.

### Quiz submission and review

- Calculates score and mastery.
- Saves detailed attempt snapshots.
- Generates AI insights.
- Allows later review from the dashboard or the review page.

## Technical deep dive

This section summarizes the core algorithms and computational logic used by the platform.

### 1) Bayesian Knowledge Tracing (BKT)

The mastery engine maintains per-user, per-concept latent knowledge probability and updates it after each quiz attempt.

Default parameters:

- Initial mastery: \(P(L_0)=0.3\)
- Learning transition: \(P(T)=0.2\)
- Guess probability: \(P(G)=0.2\)
- Slip probability: \(P(S)=0.1\)

Posterior update for correct response \((Correct=1)\):

\[
P(L_n|Correct)=\frac{P(L_n)(1-P(S))}{P(L_n)(1-P(S)) + (1-P(L_n))P(G)}
\]

Posterior update for incorrect response \((Correct=0)\):

\[
P(L_n|Incorrect)=\frac{P(L_n)P(S)}{P(L_n)P(S) + (1-P(L_n))(1-P(G))}
\]

Learning transition after evidence update:

\[
P(L\_{n+1})=P(L_n|Obs) + (1-P(L_n|Obs))P(T)
\]

Where Obs is either Correct or Incorrect.

### 2) Quiz scoring and time metrics

For each quiz attempt:

\[
Score(\%)=\frac{CorrectCount}{QuestionCount} \times 100
\]

\[
AvgTime=\frac{\sum\_{i=1}^{Q} t_i}{Q}
\]

where \(t_i\) is time spent on question \(i\), and \(Q\) is number of questions in that attempt.

### 3) Speed-adaptive difficulty policy

Speed labels are computed from average response time using thresholds:

- Fast if \(AvgTime < 10s\)
- Slow if \(AvgTime > 25s\)
- Steady otherwise

Difficulty transition rules:

- If score \(\ge 80\) and Fast, increase one level.
- If score \(< 50\) and Slow, decrease one level.
- Else keep current level.

Difficulty levels are ordinal: easy \(\rightarrow\) medium \(\rightarrow\) hard.

### 4) Dynamic question-count policy (7 to 15)

Question count is sampled from a range determined by speed and adjusted by mastery:

- Slow: base range [12, 15]
- Steady: base range [9, 12]
- Fast: base range [7, 9]

Mastery refinement:

- If mastery \(< 0.35\), upper bound increases by 1 (capped at 15).
- If mastery \(> 0.75\), lower bound decreases by 1 (floored at 7).

Final question count is selected uniformly at random from the final integer interval.

### 5) Behavior clustering (micro-pattern modeling)

The interaction clustering model uses KMeans with:

- Number of clusters: 3
- Initialization runs: \(n_init=10\)
- Random seed: 42

Feature vector:

- pause_count
- rewatch_count
- skip_ratio
- watch_percentage

Cluster outputs are mapped to behavior labels:

- Steady Learner
- Detail-Oriented
- Fast-Paced

This cluster label is then fed into recommendation messaging and adaptation context.

### 6) Conceptual quiz generation constraints

The generator enforces these constraints in prompt policy:

- Topic-concept focus only (no study-habit or exam-strategy questions).
- Basic \(\rightarrow\) intermediate \(\rightarrow\) advanced progression.
- One correct answer + 3 plausible distractors tied to misconceptions.
- Hint quality constraints: concise and non-revealing.
- Duplicate suppression against recent question stems.

Duplicate suppression is done by normalizing stems (trim + lowercase + whitespace collapse) and filtering seen/avoided items before finalizing the attempt.

### 7) AI-assisted semantic evaluation

For each response, the evaluator asks the local LLM to verify semantic correctness and generate one-line feedback. If LLM verification fails, a deterministic fallback compares normalized strings.

This hybrid strategy provides:

- semantic robustness when wording differs,
- deterministic safety when model calls fail.

### 8) Heatmap feature engineering

Per-topic dashboard heatmap rows are aggregated from historical attempts:

- mean score,
- mean mastery,
- mean response time,
- dominant speed label frequency.

The visualization uses derived normalized values, including:

\[
SpeedValue=
\begin{cases}
95 & \text{Fast}\\
70 & \text{Steady}\\
45 & \text{Slow}\\
0 & \text{N/A}
\end{cases}
\]

\[
AvgTimeValue = clamp(100 - 2.5\cdot min(AvgTime, 40), 0, 100)
\]

### 9) System design patterns in use

- Layered backend modules:
  - generation,
  - evaluation,
  - adaptation,
  - recommendation,
  - presentation routes.
- Graceful fallback architecture for transcript fetch and LLM calls.
- JSON-based persistence for rapid prototyping and deterministic local execution.
- Session-scoped user flow with historical attempt replay and review.

### 10) Practical complexity notes

- Duplicate filtering in quiz assembly is linear in generated question count: \(O(n)\).
- Topic heatmap aggregation is linear in number of stored attempts per render: \(O(m)\).
- KMeans inference is constant-time per request with a fixed small feature vector.
- Most expensive operations are external model/transcript calls (network + model latency), not local CPU math.

## Data files

The app stores learning state in JSON files inside `data/`.
If you want a clean reset, you can clear the relevant JSON files before starting the app.

## Notes for development

- Keep Ollama running before launching the Flask app.
- Use `llama3.2` unless you intentionally change the model configuration.
- If you retrain or replace models, make sure the files under `models/` stay compatible with the app.
- The app is designed to work best with the provided topic metadata and transcript-enabled videos.

## Troubleshooting

### Ollama is not responding

- Confirm Ollama is running locally.
- Check `http://127.0.0.1:11434/api/tags`.
- Make sure `llama3.2` is installed.

### Quiz generation feels generic

- Ensure the topic has correct metadata.
- If transcript data is unavailable, the app uses fallback context.
- The quiz generator is tuned for conceptual topic questions, not generic learning tips.

### Missing Python packages

- Reinstall dependencies with `pip install -r requirements.txt`.
