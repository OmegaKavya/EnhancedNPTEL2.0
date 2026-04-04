# Enhanced NPTEL Learning Platform

A Flask-based adaptive learning platform that combines structured video learning, AI-generated quizzes, conceptual review, learner adaptation, and personalized revision support.

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

## License

Add a license if you plan to publish the repository publicly.
