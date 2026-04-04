class SpeedAdaptation:
    def __init__(self, fast_threshold=10, slow_threshold=25):
        self.fast_threshold = fast_threshold
        self.slow_threshold = slow_threshold

    def adapt(self, score, avg_time, current_difficulty):
        new_difficulty = current_difficulty

        if score >= 80:
            if avg_time < self.fast_threshold:
                new_difficulty = self._increase_difficulty(current_difficulty)
        elif score < 50:
            if avg_time > self.slow_threshold:
                new_difficulty = self._decrease_difficulty(current_difficulty)
        
        return {
            "new_difficulty": new_difficulty,
            "speed_label": self._get_speed_label(avg_time)
        }

    def _increase_difficulty(self, difficulty):
        levels = ["easy", "medium", "hard"]
        idx = levels.index(difficulty)
        return levels[min(idx + 1, 2)]

    def _decrease_difficulty(self, difficulty):
        levels = ["easy", "medium", "hard"]
        idx = levels.index(difficulty)
        return levels[max(idx - 1, 0)]

    def _get_speed_label(self, avg_time):
        if avg_time < self.fast_threshold: return "Fast"
        if avg_time > self.slow_threshold: return "Slow"
        return "Steady"

speed_adapter = SpeedAdaptation()
