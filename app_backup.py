from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__, 
            template_folder='frontend/templates',
            static_folder='static')
app.secret_key = 'super-secret-key-for-edubox'

DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
VIDEOS_FILE = os.path.join(DATA_DIR, 'videos.json')
PROGRESS_FILE = os.path.join(DATA_DIR, 'user_progress.json')

def load_json(filepath):
    if not os.path.exists(filepath):
        return [] if 'progress' not in filepath else {}
    with open(filepath, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return [] if 'progress' not in filepath else {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    videos = load_json(VIDEOS_FILE)
    return render_template('landing.html', courses=videos)

@app.route('/about')
def about():
    return "About Edubox - Personalized Learning Platform"

@app.route('/contact')
def contact():
    return "Contact Us at support@edubox.com"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        users = load_json(USERS_FILE)
        user = next((u for u in users if u['email'] == email and u['password'] == password), None)
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        users = load_json(USERS_FILE)
        if any(u['email'] == email for u in users):
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        new_user = {
            'id': str(len(users) + 1),
            'name': name,
            'email': email,
            'password': password,
            'created_at': datetime.now().isoformat()
        }
        users.append(new_user)
        save_json(USERS_FILE, users)
        
        session['user_id'] = new_user['id']
        session['user_name'] = new_user['name']
        return jsonify({'success': True})
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    videos = load_json(VIDEOS_FILE)
    progress = load_json(PROGRESS_FILE)
    user_progress = progress.get(user_id, {})

    for video in videos:
        video_p = user_progress.get(video['id'], {})
        video['progress'] = video_p.get('watch_percentage', 0)
    
    attempts = load_json(QUIZ_ATTEMPTS_FILE)
    user_attempts = [a for a in attempts if a['user_id'] == user_id]
    
    user_attempts.sort(key=lambda x: x['timestamp'])
    
    topic_counters = {}
    temp_labels = []
    for a in user_attempts:
        topic = a.get('topic_id', 'Quiz').upper()
        topic_counters[topic] = topic_counters.get(topic, 0) + 1
        temp_labels.append(f"{topic} #{topic_counters[topic]}")
    
    relevant_attempts = user_attempts[-10:]
    mastery_history = [round(a['mastery'] * 100, 2) for a in relevant_attempts]
    mastery_labels = temp_labels[-10:]
    
    latest_speed = "Standard"
    latest_cluster = "General Learner"
    speed_message = "Keep up the consistent effort!"
    
    if user_attempts:
        latest_attempt = user_attempts[-1]
        latest_speed = latest_attempt.get('adaptation', {}).get('speed_label', 'Standard')
        latest_cluster = latest_attempt.get('behavior_cluster', 'General Learner')
        
        if latest_speed == 'Fast':
            speed_message = "You are moving quickly through concepts with high accuracy!"
        elif latest_speed == 'Slow':
            speed_message = "Taking your time is great for deep understanding. Keep going!"
        else:
            speed_message = "You are maintaining a steady and optimal learning pace."

    return render_template('dashboard.html', 
                         user_name=session['user_name'], 
                         videos=videos,
                         mastery_history=mastery_history,
                         mastery_labels=mastery_labels,
                         learning_speed=latest_speed,
                         learning_cluster=latest_cluster,
                         speed_message=speed_message)

@app.route('/progress')
def progress_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    attempts = load_json(QUIZ_ATTEMPTS_FILE)
    videos = load_json(VIDEOS_FILE)
    
    topic_map = {v['id']: v['title'] for v in videos}
    
    user_attempts = [a for a in attempts if a['user_id'] == user_id]
    for attempt in user_attempts:
        attempt['topic_name'] = topic_map.get(attempt['topic_id'], attempt['topic_id'])
        
    return render_template('progress.html', attempts=user_attempts)

@app.route('/video/<topic_id>')
def video_page(topic_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    videos = load_json(VIDEOS_FILE)
    video = next((v for v in videos if v['id'] == topic_id), None)
    if not video:
        return redirect(url_for('dashboard'))
    
    return render_template('video.html', video=video)

from backend.adaptation.micro_pattern import mp_manager
from backend.adaptation.recommendation import recommender
from backend.quiz.quiz_generator import quiz_gen
from backend.quiz.quiz_evaluator import evaluator
from backend.adaptation.speed_adaptation import speed_adapter
from backend.bkt.bkt_engine import bkt_engine

QUIZ_ATTEMPTS_FILE = 'data/quiz_attempts.json'

@app.route('/api/video-track', methods=['POST'])
def video_track():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.json
    user_id = session['user_id']
    video_id = data.get('topic_id')
    
    interaction_data = {
        "pause_count": data.get('pause_count', 0),
        "rewatch_count": data.get('rewatch_count', 0),
        "skip_ratio": data.get('skip_ratio', 0),
        "watch_percentage": data.get('watch_percentage', 0)
    }
    
    success = mp_manager.log_interaction(user_id, video_id, interaction_data)
    
    progress = load_json(PROGRESS_FILE)
    if user_id not in progress:
        progress[user_id] = {}
    progress[user_id][video_id] = {
        "last_position": data.get('last_time', 0),
        "watch_percentage": data.get('watch_percentage', 0),
        "timestamp": datetime.now().isoformat()
    }
    save_json(PROGRESS_FILE, progress)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Logging failed'}), 500

@app.route('/api/user-progress/<video_id>', methods=['GET'])
def get_user_progress(video_id):
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    user_id = session['user_id']
    progress = load_json(PROGRESS_FILE)
    
    user_progress = progress.get(user_id, {}).get(video_id, {})
    return jsonify({
        'success': True,
        'last_position': user_progress.get('last_position', 0),
        'watch_percentage': user_progress.get('watch_percentage', 0)
    })

@app.route('/quiz/<topic_id>')
def quiz_page(topic_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    videos = load_json(VIDEOS_FILE)
    video = next((v for v in videos if v['id'] == topic_id), None)
    if not video:
        return redirect(url_for('dashboard'))

    user_id = session['user_id']
    progress = load_json(PROGRESS_FILE)
    user_video_progress = progress.get(user_id, {}).get(topic_id, {})
    watch_time = user_video_progress.get('last_position', 0)

    quiz = quiz_gen.generate_quiz(topic_id, video['title'], video['video_id'], watch_time)
    
    session['current_quiz'] = quiz
    
    return render_template('quiz.html', quiz=quiz)



@app.route('/api/quiz-submit', methods=['POST'])
def quiz_submit():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.json
    user_id = session['user_id']
    topic_id = data.get('topic_id')
    responses = data.get('responses', [])
    current_difficulty = data.get('difficulty', 'medium')
    
    quiz = session.get('current_quiz')
    if not quiz:
        return jsonify({'success': False, 'message': 'Quiz session expired. Please refresh the page.'}), 400

    eval_result = evaluator.evaluate(quiz, responses)
    if not eval_result:
        return jsonify({'success': False, 'message': 'Evaluation error'}), 500
    
    score = eval_result['score']
    avg_time = eval_result['avg_time']
    
    adaptation = speed_adapter.adapt(score, avg_time, current_difficulty)
    
    is_correct_overall = score >= 70
    new_mastery = bkt_engine.update_mastery(user_id, topic_id, is_correct_overall)
    
    try:
        all_patterns = load_json('data/micro_patterns.json')
        if not isinstance(all_patterns, list):
            all_patterns = []
        user_patterns = [p for p in all_patterns if p.get('user_id') == user_id and p.get('video_id') == topic_id]
        latest_pattern = user_patterns[-1] if user_patterns else {}
    except Exception:
        latest_pattern = {}
    cluster = mp_manager.predict_cluster(latest_pattern)
    
    recommendation = recommender.get_recommendation(score, new_mastery, adaptation['speed_label'], cluster)

    
    attempt_log = {
        "user_id": user_id,
        "topic_id": topic_id,
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "avg_time": avg_time,
        "adaptation": adaptation,
        "mastery": new_mastery,
        "behavior_cluster": cluster,
        "recommendation": recommendation
    }
    
    attempts = load_json(QUIZ_ATTEMPTS_FILE) if os.path.exists(QUIZ_ATTEMPTS_FILE) else []
    attempts.append(attempt_log)
    save_json(QUIZ_ATTEMPTS_FILE, attempts)
    
    return jsonify({
        'success': True, 
        'score': score,
        'adaptation': adaptation,
        'mastery': round(new_mastery, 2),
        'cluster': cluster,
        'results': eval_result['question_results'],
        'recommendation': recommendation
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
