import json
import os
from datetime import datetime
import warnings
import numpy as np
import pandas as pd
try:
    from sklearn.cluster import KMeans
    from sklearn import __version__ as sklearn_version
    from sklearn.exceptions import InconsistentVersionWarning
    import pickle
except ImportError:
    KMeans = None
    sklearn_version = None
    InconsistentVersionWarning = Warning

class MicroPatternManager:
    FEATURE_COLUMNS = ['pause_count', 'rewatch_count', 'skip_ratio', 'watch_percentage']

    def __init__(self, storage_path='data/micro_patterns.json', model_path='models/clustering_model.pkl'):
        self.storage_path = storage_path
        self.model_path = model_path
        os.makedirs('models', exist_ok=True)
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w') as f:
                json.dump([], f)

    def log_interaction(self, user_id, video_id, interaction_data):
        log_entry = {
            "user_id": user_id,
            "video_id": video_id,
            "timestamp": datetime.now().isoformat(),
            **interaction_data
        }
        try:
            with open(self.storage_path, 'r+') as f:
                data = json.load(f)
                data.append(log_entry)
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            return True
        except Exception as e:
            print(f"Error logging micro-pattern: {e}")
            return False

    def train_model(self):
        if not KMeans or not os.path.exists(self.storage_path):
            return False
        with open(self.storage_path, 'r') as f:
            data = json.load(f)
        if len(data) < 5:
            return False
        
        df = pd.DataFrame(data)
        X = df[self.FEATURE_COLUMNS]
        
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(X)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                "model": kmeans,
                "sklearn_version": sklearn_version,
                "feature_columns": self.FEATURE_COLUMNS
            }, f)
        return True

    def _load_model(self):
        if not os.path.exists(self.model_path):
            return None

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", InconsistentVersionWarning)
            with open(self.model_path, 'rb') as f:
                loaded = pickle.load(f)

        has_version_warning = any(
            issubclass(w.category, InconsistentVersionWarning) for w in caught
        )

        model = loaded.get("model") if isinstance(loaded, dict) else loaded

        if has_version_warning:
            if self.train_model():
                with open(self.model_path, 'rb') as f:
                    refreshed = pickle.load(f)
                return refreshed.get("model") if isinstance(refreshed, dict) else refreshed
            return None

        return model

    def predict_cluster(self, interaction_data):
        if not os.path.exists(self.model_path):
            return "General Learner"
        
        try:
            model = self._load_model()
            if model is None:
                return "General Learner"

            vec_df = pd.DataFrame([{
                'pause_count': interaction_data.get('pause_count', 0),
                'rewatch_count': interaction_data.get('rewatch_count', 0),
                'skip_ratio': interaction_data.get('skip_ratio', 0),
                'watch_percentage': interaction_data.get('watch_percentage', 0)
            }], columns=self.FEATURE_COLUMNS)

            prediction = model.predict(vec_df)[0]
            labels = {
                0: "Steady Learner",
                1: "Detail-Oriented",
                2: "Fast-Paced"
            }
            return labels.get(prediction, "General Learner")
        except Exception as e:
            print(f"Clustering prediction error: {e}")
            return "General Learner"

mp_manager = MicroPatternManager()
