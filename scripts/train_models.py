import json
import os
import pickle
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn import __version__ as sklearn_version
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
MODELS_DIR = os.path.join(PROJECT_ROOT, 'models')

MICRO_PATTERNS_FILE = os.path.join(DATA_DIR, 'micro_patterns.json')
QUIZ_ATTEMPTS_FILE = os.path.join(DATA_DIR, 'quiz_attempts.json')
CLUSTERING_MODEL_PATH = os.path.join(MODELS_DIR, 'clustering_model.pkl')
BKT_MODEL_PATH = os.path.join(MODELS_DIR, 'bkt_model.pkl')
FEATURE_COLUMNS = ['pause_count', 'rewatch_count', 'skip_ratio', 'watch_percentage']

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def load_json(filepath):
    if not os.path.exists(filepath):
        print(f"Warning: File not found at {filepath}")
        return []
    with open(filepath, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {filepath}")
            return []

def train_clustering():
    print("--- Training Micro-Pattern Clustering Model ---")
    data = load_json(MICRO_PATTERNS_FILE)
    if len(data) < 5:
        print(f"Insufficient data for clustering (found {len(data)}, need at least 5). Skipping.")
        return

    df = pd.DataFrame(data)
    X = df[FEATURE_COLUMNS]
    
    print(f"Fitting KMeans on {len(data)} interaction records...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    kmeans.fit(X)
    
    ensure_dir(MODELS_DIR)
    with open(CLUSTERING_MODEL_PATH, 'wb') as f:
        pickle.dump({
            'model': kmeans,
            'sklearn_version': sklearn_version,
            'feature_columns': FEATURE_COLUMNS
        }, f)
    print(f"Successfully saved clustering model to {CLUSTERING_MODEL_PATH}")

def train_bkt():
    print("\n--- Training BKT Model ---")
    try:
        from pyBKT.models import Model
    except Exception as e:
        print(f"Could not import pyBKT Model: {e}. Skipping BKT training.")
        return

    data = load_json(QUIZ_ATTEMPTS_FILE)
    if not data:
        print("No quiz attempts found. Skipping BKT training.")
        return

    bkt_data = []
    for attempt in data:
        user_id = attempt.get('user_id')
        concept = attempt.get('topic_id')
        correct = 1 if attempt.get('score', 0) >= 70 else 0
        
        bkt_data.append({
            'user_id': user_id,
            'skill_name': concept,
            'correct': correct
        })
    
    df = pd.DataFrame(bkt_data)
    
    print(f"Fitting pyBKT on {len(df)} response points...")
    model = Model(seed=42, num_fits=1)
    model.fit(data=df)
    
    ensure_dir(MODELS_DIR)
    with open(BKT_MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"Successfully saved BKT model to {BKT_MODEL_PATH}")

if __name__ == "__main__":
    print(f"Model Training Session - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Root: {PROJECT_ROOT}")
    train_clustering()
    train_bkt()
    print("\nAll training tasks completed successfully.")
