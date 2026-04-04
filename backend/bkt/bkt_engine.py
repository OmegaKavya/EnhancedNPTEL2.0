import json
import os

class BKTEngine:
    def __init__(self, storage_path='data/bkt_states.json'):
        self.storage_path = storage_path
        self.p_init = 0.3    
        self.p_learn = 0.2   
        self.p_guess = 0.2   
        self.p_slip = 0.1 
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)

    def get_mastery(self, user_id, concept_id):
        try:
            with open(self.storage_path, 'r') as f:
                states = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            states = {}
        
        user_state = states.get(user_id, {})
        return user_state.get(concept_id, self.p_init)

    def update_mastery(self, user_id, concept_id, is_correct):
        p_known_prev = self.get_mastery(user_id, concept_id)


        if is_correct:
            p_known_ev = (p_known_prev * (1 - self.p_slip)) / \
                         (p_known_prev * (1 - self.p_slip) + (1 - p_known_prev) * self.p_guess)
        else:
            p_known_ev = (p_known_prev * self.p_slip) / \
                         (p_known_prev * self.p_slip + (1 - p_known_prev) * (1 - self.p_guess))

        p_known_new = p_known_ev + (1 - p_known_ev) * self.p_learn

        self._save_state(user_id, concept_id, p_known_new)
        return p_known_new

    def _save_state(self, user_id, concept_id, mastery_prob):
        try:
            with open(self.storage_path, 'r') as f:
                states = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            states = {}

        if user_id not in states:
            states[user_id] = {}
        states[user_id][concept_id] = round(mastery_prob, 4)
        
        with open(self.storage_path, 'w') as f:
            json.dump(states, f, indent=4)

bkt_engine = BKTEngine()
