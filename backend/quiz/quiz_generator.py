import json
import os
import requests
import random


class QuizGenerator:
    def __init__(self, ollama_url="http://localhost:11434/api/generate", model="llama3.2"):
        self.ollama_url = ollama_url
        self.model = model

    def _get_transcript_text(self, youtube_id, watch_time):
        if not youtube_id:
            return None
            
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = None
            try:
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(youtube_id)
                except:
                    pass
                if not transcript_list:
                    try:
                        transcript_list = YouTubeTranscriptApi().get_transcript(youtube_id)
                    except:
                        pass
                if not transcript_list:
                    try:
                        ts_obj = YouTubeTranscriptApi.list(youtube_id)
                        transcript_list = ts_obj.find_transcript(['en']).fetch()
                    except:
                        try:
                            ts_obj = YouTubeTranscriptApi().list(youtube_id)
                            transcript_list = ts_obj.find_transcript(['en']).fetch()
                        except:
                            pass
                if not transcript_list:
                    import youtube_transcript_api as yta
                    if hasattr(yta, 'get_transcript'):
                        transcript_list = yta.get_transcript(youtube_id)
            except Exception as e:
                print(f"Transcript strategies failed: {e}")

            if not transcript_list or not isinstance(transcript_list, list):
                return None

            relevant_text = []
            for entry in transcript_list:
                if isinstance(entry, dict) and 'start' in entry and 'text' in entry:
                    if entry['start'] <= watch_time:
                        relevant_text.append(entry['text'])
                    else:
                        break
            return " ".join(relevant_text) if relevant_text else None
        except Exception as e:
            print(f"Transcript service error: {e}")
            return None

    def _get_question_count(self, mastery, speed_label):
        speed = (speed_label or "Steady").lower()
        if speed == "slow":
            base_min, base_max = 12, 15
        elif speed == "fast":
            base_min, base_max = 7, 9
        else:
            base_min, base_max = 9, 12

        if mastery < 0.35:
            base_max = min(base_max + 1, 15)
        elif mastery > 0.75:
            base_min = max(base_min - 1, 7)

        return random.randint(base_min, base_max)

    def _get_adaptive_difficulty(self, difficulty, speed_label):
        speed = (speed_label or "Steady").lower()
        if speed == "slow":
            if difficulty == "hard":
                return "medium"
            return random.choice(["easy", "medium"])
        if speed == "fast":
            if difficulty == "easy":
                return "medium"
            return random.choice(["medium", "hard"])
        return difficulty

    def _normalize_text(self, text):
        return " ".join(str(text or "").strip().lower().split())

    def _ensure_unique_questions(self, questions, num_questions, avoid_questions=None):
        avoid = {self._normalize_text(q) for q in (avoid_questions or []) if q}
        seen = set(avoid)
        unique = []

        for question in questions or []:
            text = question.get("text")
            norm = self._normalize_text(text)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            unique.append(question)
            if len(unique) >= num_questions:
                break

        for idx, question in enumerate(unique, start=1):
            question["id"] = idx

        return unique

    def generate_quiz(self, topic_id, topic_name, youtube_id, watch_time=0,
                      difficulty="medium", mastery=0.3, cluster="General Learner", speed_label="Steady", avoid_questions=None):

        num_questions = self._get_question_count(mastery, speed_label)
        adaptive_difficulty = self._get_adaptive_difficulty(difficulty, speed_label)
        print(f"[QuizGen] difficulty={adaptive_difficulty}, questions={num_questions}, mastery={mastery:.2f}, cluster={cluster}, speed={speed_label}")

        transcript_context = self._get_transcript_text(youtube_id, watch_time)

        if transcript_context:
            context_prompt = f"Use the following transcript context from the video (covering up to {watch_time} seconds) to generate questions specifically about this content:\n\n{transcript_context[:3000]}\n\n"
        else:
            context_prompt = f"Generate a quiz for the topic: {topic_name}. (Note: Transcript unavailable, use general knowledge about {topic_name})\n\n"

        questions_template = ""
        for i in range(1, num_questions + 1):
            questions_template += f"""
        {{
            "id": {i},
            "text": "Question {i} text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "Correct Option text exactly",
            "hint": "One concise hint for this question"
        }}{"," if i < num_questions else ""}"""

        if mastery < 0.4:
            mastery_instruction = "Focus on foundational concepts since the learner has low mastery."
        elif mastery > 0.7:
            mastery_instruction = "Include challenging and analytical questions since the learner has high mastery."
        else:
            mastery_instruction = "Balance conceptual and applied questions."

        prompt = f"""{context_prompt}
Generate a {num_questions}-question MCQ quiz.
Difficulty level: {adaptive_difficulty}.
Learner profile: {cluster}.
Current speed pattern: {speed_label}.
{mastery_instruction}

CRITICAL REQUIREMENTS:
1) Every question MUST test conceptual understanding of {topic_name}.
2) Do NOT ask about study habits, exam strategy, motivation, revision techniques, or generic best practices.
3) Questions must progress from basic to advanced across the quiz:
   - First ~30%: core definitions and fundamentals.
   - Middle ~40%: mechanisms, comparisons, cause-effect, and applications.
   - Final ~30%: scenario-based reasoning, edge cases, trade-offs, and advanced analysis.
4) Each question stem must explicitly reference {topic_name} concepts (directly or via topic-specific terminology from the transcript/context).
5) Each question must have one clearly correct option and 3 plausible distractors tied to common misconceptions.
6) Keep hints concise and non-revealing; hints should guide reasoning, not give away the answer.

Use varied wording and avoid repeating past question stems from this list:
{json.dumps((avoid_questions or [])[:20])}
Also ensure each question in this quiz is unique.

Return the result ONLY as a JSON object with this exact structure:
{{
    "topic_id": "{topic_id}",
    "difficulty": "{adaptive_difficulty}",
    "num_questions": {num_questions},
    "questions": [{questions_template}
    ]
}}"""

        try:
            response = requests.post(self.ollama_url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=120)
            if response.status_code == 200:
                quiz_data = json.loads(response.json().get('response', '{}'))
                if quiz_data and 'questions' in quiz_data:
                    cleaned_questions = self._ensure_unique_questions(
                        quiz_data.get('questions', []),
                        num_questions,
                        avoid_questions=avoid_questions
                    )
                    if cleaned_questions:
                        quiz_data['questions'] = cleaned_questions
                        quiz_data['num_questions'] = len(cleaned_questions)
                        print(f"[QuizGen] Generated {len(cleaned_questions)} unique questions")
                        return quiz_data
        except requests.exceptions.ConnectionError:
            print("Ollama not running. Using fallback quiz.")
        except Exception as e:
            print(f"Ollama error: {e}")

        return self._get_fallback_quiz(topic_id, topic_name, adaptive_difficulty, num_questions, avoid_questions=avoid_questions)

    def _get_fallback_quiz(self, topic_id, topic_name, difficulty, num_questions=7, avoid_questions=None):
        all_questions = [
            {
                "id": 1,
                "text": f"Which statement best defines the core purpose of {topic_name}?",
                "options": ["A framework for modeling and solving domain-specific problems", "A memorization-only method with no decision-making", "A topic used only for historical context", "A concept unrelated to system behavior"],
                "answer": "A framework for modeling and solving domain-specific problems",
                "hint": "Pick the option that captures what the topic is fundamentally used for."
            },
            {
                "id": 2,
                "text": f"In {topic_name}, why are foundational concepts introduced before advanced techniques?",
                "options": ["Advanced reasoning depends on core principles", "Because advanced concepts are less useful", "Only beginners need theory", "Order does not affect understanding"],
                "answer": "Advanced reasoning depends on core principles",
                "hint": "Look for the dependency relationship between basics and advanced ideas."
            },
            {
                "id": 3,
                "text": f"Which scenario is the best example of applying {topic_name} conceptually rather than mechanically?",
                "options": ["Choosing an approach based on constraints and explaining why", "Applying the same fixed steps to every problem", "Ignoring assumptions and focusing only on final output", "Selecting options by pattern matching alone"],
                "answer": "Choosing an approach based on constraints and explaining why",
                "hint": "Conceptual use means adapting ideas to context."
            },
            {
                "id": 4,
                "text": f"When comparing two methods in {topic_name}, which criterion most directly reflects conceptual correctness?",
                "options": ["How well assumptions match the problem model", "How quickly the answer was guessed", "How long the option text is", "How familiar the method name sounds"],
                "answer": "How well assumptions match the problem model",
                "hint": "Correctness starts with valid assumptions."
            },
            {
                "id": 5,
                "text": f"A common misconception in {topic_name} is that one rule fits all situations. Why is this incorrect?",
                "options": ["Different constraints require different conceptual choices", "Rules never work in any context", "Concepts are optional for real systems", "All problems in the topic are identical"],
                "answer": "Different constraints require different conceptual choices",
                "hint": "Think about variability in constraints and goals."
            },
            {
                "id": 6,
                "text": f"In {topic_name}, what is the most reliable way to evaluate whether a solution generalizes beyond one example?",
                "options": ["Test reasoning against edge cases and changed assumptions", "Check only one successful case", "Prefer the shortest explanation", "Reuse the previous answer unchanged"],
                "answer": "Test reasoning against edge cases and changed assumptions",
                "hint": "Generalization requires stress-testing the model, not one sample."
            },
            {
                "id": 7,
                "text": f"Which change would most likely break a valid solution approach in {topic_name}?",
                "options": ["Violating a core assumption of the approach", "Renaming variables consistently", "Reordering equivalent explanation steps", "Using clearer notation"],
                "answer": "Violating a core assumption of the approach",
                "hint": "Identify what the approach fundamentally depends on."
            },
            {
                "id": 8,
                "text": f"An advanced decision in {topic_name} usually involves which trade-off?",
                "options": ["Balancing optimality, complexity, and constraints", "Choosing whichever method is newest", "Maximizing steps regardless of outcomes", "Ignoring failure modes"],
                "answer": "Balancing optimality, complexity, and constraints",
                "hint": "Advanced decisions are rarely one-dimensional."
            },
            {
                "id": 9,
                "text": f"In a failure analysis for {topic_name}, what question best targets root cause?",
                "options": ["Which assumption or model condition was violated?", "Who answered fastest?", "Which explanation used more keywords?", "How many times was the solution repeated?"],
                "answer": "Which assumption or model condition was violated?",
                "hint": "Root cause analysis starts from model breakdowns."
            },
            {
                "id": 10,
                "text": f"Which option represents higher-order understanding in {topic_name}?",
                "options": ["Predicting behavior under unseen constraints", "Recalling one definition verbatim", "Selecting by elimination without reasoning", "Repeating a solved example exactly"],
                "answer": "Predicting behavior under unseen constraints",
                "hint": "Higher-order understanding supports prediction in new situations."
            },
            {
                "id": 11,
                "text": f"If two answers in {topic_name} seem plausible, what should decide the correct one?",
                "options": ["Consistency with the topic’s underlying model and constraints", "Whichever sounds more confident", "Whichever is longer", "Whichever appears first"],
                "answer": "Consistency with the topic’s underlying model and constraints",
                "hint": "Choose based on model validity, not style."
            },
            {
                "id": 12,
                "text": f"What makes an advanced question in {topic_name} genuinely difficult?",
                "options": ["It requires integrating multiple concepts under constraints", "It uses uncommon vocabulary only", "It is intentionally ambiguous with no model", "It has very long answer options"],
                "answer": "It requires integrating multiple concepts under constraints",
                "hint": "Difficulty should come from reasoning depth, not wording tricks."
            },
            {
                "id": 13,
                "text": f"Which outcome best demonstrates conceptual mastery of {topic_name}?",
                "options": ["Explaining and defending solution choices for new scenarios", "Memorizing one pipeline perfectly", "Avoiding unfamiliar problem setups", "Optimizing only for speed"],
                "answer": "Explaining and defending solution choices for new scenarios",
                "hint": "Mastery combines explanation, justification, and transfer."
            },
            {
                "id": 14,
                "text": f"In {topic_name}, why are edge cases important in advanced reasoning?",
                "options": ["They reveal limits of assumptions and approach robustness", "They are useful only in exams, not practice", "They always have the same behavior as normal cases", "They can be ignored after one correct example"],
                "answer": "They reveal limits of assumptions and approach robustness",
                "hint": "Edge cases expose where a model stops being reliable."
            },
            {
                "id": 15,
                "text": f"Which advanced evaluation in {topic_name} is strongest?",
                "options": ["Justifying trade-offs with explicit assumptions and expected impact", "Choosing the most popular method by default", "Ignoring model limitations for simpler answers", "Preferring fixed rules over context"],
                "answer": "Justifying trade-offs with explicit assumptions and expected impact",
                "hint": "Strong advanced reasoning makes assumptions and impacts explicit."
            }
        ]
        random.shuffle(all_questions)
        unique_questions = self._ensure_unique_questions(all_questions, num_questions, avoid_questions=avoid_questions)
        if not unique_questions:
            unique_questions = all_questions[:num_questions]
            for idx, question in enumerate(unique_questions, start=1):
                question["id"] = idx

        return {
            "topic_id": topic_id,
            "difficulty": difficulty,
            "num_questions": len(unique_questions),
            "questions": unique_questions
        }


quiz_gen = QuizGenerator()