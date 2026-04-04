import json
import re
import requests


class QuizInsightsEngine:
    def __init__(self, ollama_url="http://localhost:11434/api/generate", model="llama3.2"):
        self.ollama_url = ollama_url
        self.model = model

    def _extract_keywords(self, text):
        tokens = re.findall(r"[A-Za-z]{4,}", (text or "").lower())
        stop = {
            "which", "what", "when", "where", "while", "about", "their", "there", "these", "those",
            "option", "question", "correct", "answer", "following", "primary", "topic", "student"
        }
        words = [w for w in tokens if w not in stop]
        ranked = []
        seen = set()
        for word in words:
            if word not in seen:
                seen.add(word)
                ranked.append(word)
            if len(ranked) >= 5:
                break
        return ranked

    def _fallback(self, topic_name, incorrect_questions):
        joined = " ".join(q.get("text", "") for q in incorrect_questions)
        keywords = self._extract_keywords(joined)
        if not keywords:
            keywords = [topic_name.lower(), "core concepts", "problem solving"]

        focus_concepts = [k.replace("_", " ").title() for k in keywords[:3]]
        cheat_sheet = [
            f"Define {focus_concepts[0]} in one line and write one example.",
            "Create a compare/contrast table for two closely related ideas.",
            "Practice 5 short MCQs and explain each answer in one sentence."
        ]
        resources = [
            {"title": f"{topic_name} - GeeksforGeeks", "url": f"https://www.geeksforgeeks.org/search/?q={topic_name.replace(' ', '+')}"},
            {"title": f"{topic_name} - Tutorialspoint", "url": f"https://www.tutorialspoint.com/search/{topic_name.replace(' ', '-')}.htm"},
            {"title": f"{topic_name} - YouTube quick revision", "url": f"https://www.youtube.com/results?search_query={topic_name.replace(' ', '+')}+revision"}
        ]
        return {
            "focus_concepts": focus_concepts,
            "cheat_sheet": cheat_sheet,
            "resources": resources,
            "summary": "Focus on concept clarity and short iterative practice before the next quiz."
        }

    def generate_insights(self, topic_name, score, mastery, question_results):
        incorrect = [q for q in question_results if not q.get("is_correct")]
        if not incorrect:
            return {
                "focus_concepts": ["Advanced Application", "Speed + Accuracy", "Concept Transfer"],
                "cheat_sheet": [
                    "Attempt mixed-difficulty questions with a strict timer.",
                    "Teach one concept aloud in 2 minutes from memory.",
                    "Solve one unseen problem and write your reasoning steps."
                ],
                "resources": [
                    {"title": f"Advanced {topic_name} practice sets", "url": f"https://www.google.com/search?q=advanced+{topic_name.replace(' ', '+')}+practice"},
                    {"title": f"{topic_name} interview questions", "url": f"https://www.google.com/search?q={topic_name.replace(' ', '+')}+interview+questions"}
                ],
                "summary": "Strong attempt. Shift toward advanced and transfer-based practice."
            }

        prompt = f"""
You are an expert learning coach.
Topic: {topic_name}
Score: {score}
Mastery: {mastery}
Incorrect question signals: {json.dumps(incorrect)[:2500]}

Return ONLY JSON with this exact structure:
{{
  "focus_concepts": ["concept 1", "concept 2", "concept 3"],
  "cheat_sheet": ["short bullet 1", "short bullet 2", "short bullet 3", "short bullet 4"],
  "resources": [
    {{"title": "resource 1", "url": "https://..."}},
    {{"title": "resource 2", "url": "https://..."}},
    {{"title": "resource 3", "url": "https://..."}}
  ],
  "summary": "one concise paragraph"
}}

Constraints:
- Keep all items concise and practical.
- Focus on weak concepts from the mistakes.
- Resource links should be broadly accessible learning links.
"""

        try:
            response = requests.post(self.ollama_url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=25)
            if response.status_code == 200:
                parsed = json.loads(response.json().get("response", "{}"))
                if parsed.get("focus_concepts") and parsed.get("cheat_sheet") and parsed.get("resources"):
                    return parsed
        except Exception as e:
            print(f"AI insight generation error: {e}")

        return self._fallback(topic_name, incorrect)


insights_engine = QuizInsightsEngine()
