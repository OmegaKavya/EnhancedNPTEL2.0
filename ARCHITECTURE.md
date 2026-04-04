# Architecture — Enhanced NPTEL Learning Platform

This document describes the full technical architecture of the platform, including system layers, module boundaries, adaptive engine flow, and runtime request pipelines.

## 1) High-level system architecture

```mermaid
flowchart LR
    U[User Browser] -->|HTTP + JSON| F[Flask App: app.py]

    F --> T[Frontend Templates\nJinja + JS + CSS]
    F --> A[Auth + Session Layer]
    F --> QG[Quiz Generator]
    F --> QE[Quiz Evaluator]
    F --> AI[Quiz Insights Engine]
    F --> SA[Speed Adaptation Engine]
    F --> BKT[BKT Mastery Engine]
    F --> MP[Micro-Pattern Manager]
    F --> RE[Recommendation Engine]

    QG --> O[Ollama API\nllama3.2]
    QE --> O
    AI --> O

    QG --> YT[YouTube Transcript API]

    F --> D[(JSON Data Store\nusers/progress/attempts/patterns/videos)]
    MP --> M[(Clustering Model\nKMeans pickle)]
    BKT --> D
```

## 2) Layered architecture

### Presentation layer

- HTML views in `frontend/templates/`.
- CSS and client-side behavior in `static/`.
- Dynamic pages:
  - dashboard,
  - video player with checkpoints,
  - quiz runtime,
  - quiz review history.

### Application layer (`app.py`)

- Owns HTTP routes and orchestration.
- Builds adaptive quiz payloads from:
  - user state,
  - progress history,
  - prior attempt history,
  - behavior profile.
- Persists attempt snapshots and dashboard aggregates.

### Domain services (`backend/`)

- `backend/quiz/quiz_generator.py`:
  - conceptual question generation,
  - dynamic question count and difficulty,
  - non-repetition filtering.
- `backend/quiz/quiz_evaluator.py`:
  - semantic answer validation and feedback.
- `backend/quiz/quiz_insights.py`:
  - summary/focus/revision insights.
- `backend/adaptation/speed_adaptation.py`:
  - score/time-based difficulty policy.
- `backend/bkt/bkt_engine.py`:
  - Bayesian mastery update.
- `backend/adaptation/micro_pattern.py`:
  - behavior logging and KMeans cluster prediction.
- `backend/adaptation/recommendation.py`:
  - final next-step recommendation synthesis.

### Infrastructure layer

- Local LLM runtime: Ollama (`llama3.2`).
- Transcript context fetch via YouTube transcript API.
- JSON-file persistence for deterministic local execution.
- Serialized clustering model under `models/`.

## 3) Module architecture map

```mermaid
flowchart TB
    subgraph APP[app.py Orchestrator]
      R1[/dashboard/]
      R2[/video/<topic_id>/]
      R3[/api/video-track/]
      R4[/quiz/<topic_id>/]
      R5[/api/quiz-data/<topic_id>/]
      R6[/api/quiz-submit/]
      R7[/quiz-review/*/]
    end

    subgraph ADAPT[Adaptation Modules]
      BKT[bkt_engine]
      SPD[speed_adapter]
      MP[mp_manager]
      REC[recommender]
    end

    subgraph QUIZ[Quiz Modules]
      GEN[quiz_gen]
      EVAL[evaluator]
      INS[insights_engine]
    end

    subgraph STORE[Data + Models]
      J1[(data/users.json)]
      J2[(data/user_progress.json)]
      J3[(data/quiz_attempts.json)]
      J4[(data/micro_patterns.json)]
      J5[(data/bkt_states.json)]
      M1[(models/clustering_model.pkl)]
    end

    R3 --> MP
    MP --> J4
    MP --> M1

    R5 --> BKT
    R5 --> GEN
    R5 --> J2
    R5 --> J3

    R6 --> EVAL
    R6 --> SPD
    R6 --> BKT
    R6 --> MP
    R6 --> REC
    R6 --> INS
    R6 --> J3
    BKT --> J5

    R1 --> J2
    R1 --> J3
    R7 --> J3
    R1 --> J1
```

## 4) Adaptive engine pipeline

```mermaid
sequenceDiagram
    participant C as Client (Quiz UI)
    participant A as Flask app.py
    participant B as BKT Engine
    participant G as Quiz Generator
    participant O as Ollama
    participant E as Quiz Evaluator
    participant S as Speed Adapter
    participant M as Micro-Pattern Manager
    participant R as Recommendation Engine
    participant I as Insights Engine
    participant D as JSON Store

    C->>A: GET /api/quiz-data/<topic_id>
    A->>B: get_mastery(user, topic)
    A->>D: read progress + prior attempts
    A->>G: generate_quiz(topic, mastery, speed, avoid_questions)
    G->>O: prompt (conceptual basic->advanced)
    O-->>G: quiz JSON
    G-->>A: unique/adaptive quiz payload
    A-->>C: quiz + timer + hint metadata

    C->>A: POST /api/quiz-submit (responses)
    A->>E: evaluate(quiz, responses)
    E->>O: semantic verify + feedback
    O-->>E: per-question correctness + feedback
    E-->>A: score + avg_time + results

    A->>S: adapt(score, avg_time, current_difficulty)
    A->>B: update_mastery(user, topic, pass/fail)
    A->>M: predict_cluster(latest interaction)
    A->>R: get_recommendation(score, mastery, speed, cluster)
    A->>I: generate_insights(topic, score, mastery, question_results)

    A->>D: persist attempt snapshot
    A-->>C: score + adaptation + mastery + recommendation + insights
```

## 5) Core runtime engines

### 5.1 Quiz generation engine

Input:

- topic id + title,
- watch-time transcript context,
- current difficulty,
- mastery estimate,
- behavior cluster + speed label,
- recent question stems to avoid.

Output:

- adaptive quiz payload,
- conceptual progression (basic -> advanced),
- unique stem set with hints.

Failure behavior:

- falls back to deterministic conceptual question bank if LLM/transcript fails.

### 5.2 Evaluation engine

- Primary path: LLM semantic verification of selected answer vs expected answer.
- Fallback path: normalized string-match correctness if model unavailable.
- Produces score, average time, and per-question feedback.

### 5.3 Mastery engine (BKT)

- Maintains probability of latent concept mastery per user/topic.
- Updates mastery after each attempt using Bayesian observation update + transition.

### 5.4 Speed adaptation engine

- Computes speed label from response latency thresholds.
- Applies policy-based difficulty transition for the next attempt.

### 5.5 Behavior clustering engine

- Logs micro interactions (pause/rewatch/skip/watch%).
- Predicts behavior archetype using KMeans model.
- Feeds recommendation tone and adaptation context.

### 5.6 Recommendation and insight engines

- Recommendation engine returns action-level learning guidance.
- Insight engine returns AI-authored weak-topic focus and cheat-sheet style next steps.

## 6) API contract overview

### Web pages

- `GET /dashboard`
- `GET /video/<topic_id>`
- `GET /quiz/<topic_id>`
- `GET /quiz-review`
- `GET /quiz-review/<attempt_id>`

### JSON APIs

- `POST /api/video-track`
- `GET /api/user-progress/<video_id>`
- `GET /api/quiz-data/<topic_id>`
- `POST /api/quiz-submit`

## 7) Data model summary (JSON persistence)

- `data/users.json`: user credentials/profile.
- `data/user_progress.json`: watch position + percentage by user/topic.
- `data/quiz_attempts.json`: full attempt snapshots, per-question outcomes, adaptation, insights.
- `data/micro_patterns.json`: interaction telemetry records.
- `data/bkt_states.json`: mastery probability state by user/concept.
- `models/clustering_model.pkl`: serialized KMeans + metadata.

## 8) Request lifecycle snapshots

### A) Video tracking lifecycle

1. Frontend sends interaction snapshot to `POST /api/video-track`.
2. Server logs micro-pattern telemetry.
3. Server updates watch-state progress.
4. Behavior features become available for subsequent cluster prediction.

### B) Quiz generation lifecycle

1. Server loads user mastery + recent attempts.
2. Difficulty/speed context is derived.
3. Generator requests conceptual MCQs from LLM with anti-generic constraints.
4. Duplicate filter enforces novelty.
5. Timers/hints metadata added and returned to UI.

### C) Quiz submission lifecycle

1. Server evaluates each response.
2. Computes score/time metrics.
3. Updates speed profile + mastery estimate.
4. Predicts behavior cluster.
5. Creates recommendation + AI insights.
6. Persists full attempt and returns final response payload.

## 9) Extensibility points

- Replace JSON persistence with PostgreSQL/MongoDB by swapping load/save adapters.
- Add checkpoint-performance persistence endpoint for in-video quizzes.
- Add offline model fallback (rule-based distractor generation) for no-LLM mode.
- Introduce event bus (Redis/Kafka) for analytics decoupling at scale.

## 10) Reliability and fallback strategy

- Transcript retrieval uses multi-strategy attempts.
- LLM generation/evaluation guarded with timeout and exception handling.
- Deterministic fallback quiz/evaluation prevents user-facing hard failure.
- Version-aware model loading retrains clustering model on sklearn mismatch.
