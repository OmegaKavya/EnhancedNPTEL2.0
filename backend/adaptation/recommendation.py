class RecommendationEngine:
    def __init__(self):
        pass

    def get_recommendation(self, score, mastery, speed_label, behavior_cluster):
        
        decision = {
            "action": "Proceed to next topic",
            "message": "Great job! You're showing steady progress.",
            "next_difficulty": "medium"
        }

        if mastery < 0.4:
            decision["action"] = "Revision Recommended"
            decision["message"] = "You might want to review this concept again. We've unlocked some simpler resources for you."
            decision["next_difficulty"] = "easy"
        elif mastery > 0.8:
            decision["action"] = "Concept Mastered"
            decision["message"] = "Impressive mastery! Ready for more challenging content?"
            decision["next_difficulty"] = "hard"
        
        if behavior_cluster == "Detail-Oriented":
            decision["message"] += " We noticed you take your time—that's great for deep understanding!"
        elif behavior_cluster == "Fast-Paced":
            decision["message"] += " You're moving fast! Don't forget to double-check the tricky details."

        return decision

recommender = RecommendationEngine()
