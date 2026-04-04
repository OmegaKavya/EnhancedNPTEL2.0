import json
import requests

class QuizEvaluator:
    def __init__(self, ollama_url="http://localhost:11434/api/generate"):
        self.ollama_url = ollama_url
        self.model = "llama3.2"

    def _ai_verify_and_explain(self, question, selected, correct_answer):
        prompt = f"""
        Question: {question}
        Student's Answer: {selected}
        Correct Answer: {correct_answer}
        
        Act as an expert tutor. 
        1. Determine if the Student's Answer is semantically identical or correct regarding the Question.
        2. Provide a 1-sentence supportive explanation of WHY it is correct or incorrect.
        
        Return the result ONLY as a JSON object with this structure:
        {{
            "is_correct": true/false,
            "feedback": "Your explanation here"
        }}
        """
        try:
            response = requests.post(self.ollama_url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=15)
            
            if response.status_code == 200:
                return json.loads(response.json().get('response', '{}'))
        except Exception as e:
            print(f"AI Evaluation error: {e}")
        
        is_correct = str(selected).strip().lower() == str(correct_answer).strip().lower()
        return {
            "is_correct": is_correct,
            "feedback": "Great focus on the core concept!" if is_correct else "Review the key principles of this topic."
        }

    def evaluate(self, quiz, responses):
        try:
            if not quiz:
                return None

            correct_count = 0
            total_time = 0
            question_results = []

            for resp in responses:
                q_id = resp['question_id']
                selected = resp['selected_answer']
                time_taken = resp['time_taken']
                total_time += time_taken

                question_data = next((q for q in quiz['questions'] if str(q['id']) == str(q_id)), None)
                
                if question_data:
                    ai_result = self._ai_verify_and_explain(
                        question_data['text'], 
                        selected, 
                        question_data['answer']
                    )
                    
                    is_correct = ai_result.get('is_correct', False)
                    if is_correct:
                        correct_count += 1
                    
                    question_results.append({
                        "question_id": q_id,
                        "is_correct": is_correct,
                        "time_taken": time_taken,
                        "feedback": ai_result.get('feedback', "")
                    })
                else:
                    question_results.append({
                        "question_id": q_id,
                        "is_correct": False,
                        "time_taken": time_taken,
                        "feedback": "Question not found."
                    })

            q_count = len(quiz.get('questions', []))
            score = (correct_count / q_count) * 100 if q_count > 0 else 0
            avg_time = total_time / q_count if q_count > 0 else 0

            return {
                "score": round(score, 2),
                "avg_time": round(avg_time, 2),
                "total_time": round(total_time, 2),
                "question_results": question_results
            }
        except Exception as e:
            print(f"Evaluation error: {e}")
            return None


evaluator = QuizEvaluator()
