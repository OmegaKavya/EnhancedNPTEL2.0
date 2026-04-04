from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime
import uuid

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


def build_review_rows(attempts, topic_map):
    rows = []
    for attempt in sorted(attempts, key=lambda x: x.get('timestamp', ''), reverse=True):
        rows.append({
            "attempt_id": attempt.get("attempt_id", ""),
            "topic_id": attempt.get("topic_id"),
            "topic_name": topic_map.get(attempt.get("topic_id"), attempt.get("topic_id", "Topic")),
            "score": attempt.get("score", 0),
            "mastery": attempt.get("mastery", 0),
            "speed_label": attempt.get("adaptation", {}).get("speed_label", "Steady"),
            "timestamp": attempt.get("timestamp", ""),
            "insight_summary": attempt.get("ai_insights", {}).get("summary", "No AI insight available yet.")
        })
    return rows


def build_topic_heatmap_rows(attempts, topic_map):
    rows = []
    for topic_id, topic_name in topic_map.items():
        topic_attempts = [a for a in attempts if a.get('topic_id') == topic_id]
        if topic_attempts:
            count = len(topic_attempts)
            avg_score = round(sum(a.get('score', 0) for a in topic_attempts) / count, 1)
            avg_mastery = round((sum(a.get('mastery', 0) for a in topic_attempts) / count) * 100, 1)
            avg_time = round(sum(a.get('avg_time', 0) for a in topic_attempts) / count, 1)
            speed_values = [a.get('adaptation', {}).get('speed_label', 'Steady') for a in topic_attempts]
            fast_count = len([s for s in speed_values if s == 'Fast'])
            steady_count = len([s for s in speed_values if s == 'Steady'])
            slow_count = len([s for s in speed_values if s == 'Slow'])
            dominant_speed = 'Fast' if fast_count >= steady_count and fast_count >= slow_count else 'Slow' if slow_count >= steady_count else 'Steady'
        else:
            count = 0
            avg_score = 0
            avg_mastery = 0
            avg_time = 0
            dominant_speed = 'N/A'

        rows.append({
            'topic_id': topic_id,
            'topic_name': topic_name,
            'attempts': count,
            'score_value': avg_score,
            'mastery_value': avg_mastery,
            'speed_value': 95 if dominant_speed == 'Fast' else 70 if dominant_speed == 'Steady' else 45 if dominant_speed == 'Slow' else 0,
            'avg_time_value': max(0, min(100, int(100 - min(avg_time, 40) * 2.5))) if count else 0,
            'avg_score': avg_score,
            'avg_mastery': avg_mastery,
            'avg_time': avg_time,
            'dominant_speed': dominant_speed
        })
    return rows


STATIC_CHEAT_SHEETS = {
    'os': {
        'title': 'Operating Systems Rapid Revision',
        'estimated_minutes': 5,
        'core': [
            'Kernel is the privileged core that schedules processes and manages memory/devices.',
            'Process = program in execution; thread = lightweight execution unit inside a process.',
            'CPU scheduling goals: throughput, response time, fairness, and utilization.',
            'Memory management basics: paging, virtual memory, page faults, and replacement.',
            'Concurrency primitives: mutex, semaphore, monitor; use to avoid race conditions.',
            'Deadlock conditions (Coffman): mutual exclusion, hold-and-wait, no preemption, circular wait.'
        ],
        'pitfalls': [
            'Confusing process context switch with thread switch overhead.',
            'Mixing starvation and deadlock — they are not the same failure mode.',
            'Ignoring critical-section boundaries in synchronization questions.'
        ],
        'drills': [
            'Explain FCFS vs Round Robin in 2 lines with one use-case each.',
            'Write one scenario where paging helps and one where it hurts.',
            'State one deadlock prevention strategy and trade-off.'
        ]
    },
    'ds': {
        'title': 'Data Structures Rapid Revision',
        'estimated_minutes': 5,
        'core': [
            'Pick structure by operation profile: lookup, insert, delete, traversal.',
            'Array: O(1) index access, costly middle insert/delete.',
            'Linked list: easy insert/delete with pointer, no O(1) random access.',
            'Stack (LIFO) and queue (FIFO) power many algorithmic patterns.',
            'Trees support hierarchical queries; BST/search costs depend on balance.',
            'Graphs require choosing BFS/DFS based on shortest-path and traversal needs.'
        ],
        'pitfalls': [
            'Using recursion without checking base conditions and stack depth.',
            'Assuming average-case complexity when question asks worst-case.',
            'Forgetting visited tracking in graph traversal problems.'
        ],
        'drills': [
            'Give one real-world stack and queue example each.',
            'Compare BST vs hash table for dynamic lookup workloads.',
            'List BFS and DFS time complexity in terms of V and E.'
        ]
    },
    'dbms': {
        'title': 'DBMS Rapid Revision',
        'estimated_minutes': 5,
        'core': [
            'Primary key uniquely identifies rows; foreign key enforces relationships.',
            'Normalization reduces redundancy and update anomalies.',
            'Transactions obey ACID for reliable concurrent operations.',
            'Indexes speed reads but add write overhead and storage cost.',
            'JOIN types determine row inclusion logic across tables.',
            'Isolation levels trade strict consistency for performance.'
        ],
        'pitfalls': [
            'Confusing candidate key with primary key selection.',
            'Applying too many indexes on write-heavy tables.',
            'Missing NULL behavior in joins and conditions.'
        ],
        'drills': [
            'Explain INNER JOIN vs LEFT JOIN with one mini example.',
            'State one anomaly fixed by 3NF.',
            'Give one case where denormalization is acceptable.'
        ]
    },
    'cn': {
        'title': 'Computer Networks Rapid Revision',
        'estimated_minutes': 5,
        'core': [
            'Layered design separates concerns: link, network, transport, application.',
            'IP handles addressing/routing; TCP/UDP handle end-to-end delivery behavior.',
            'TCP offers reliability, flow + congestion control; UDP favors low latency.',
            'Routing decides path between networks; switching forwards within local network.',
            'Common protocols: HTTP/HTTPS, DNS, DHCP, ARP, ICMP.',
            'Subnetting partitions address space for scalable routing and control.'
        ],
        'pitfalls': [
            'Mixing OSI conceptual layers with exact protocol placement.',
            'Confusing flow control with congestion control.',
            'Ignoring handshake/teardown sequence in TCP questions.'
        ],
        'drills': [
            'Contrast TCP and UDP in one sentence each.',
            'Trace packet flow from browser request to server response.',
            'Define subnet mask purpose in plain language.'
        ]
    }
}


def get_static_cheat_sheet(topic_id, topic_name):
    if topic_id in STATIC_CHEAT_SHEETS:
        return STATIC_CHEAT_SHEETS[topic_id]
    return {
        'title': f'{topic_name} Rapid Revision',
        'estimated_minutes': 4,
        'core': [
            f'Review core definitions and terminology of {topic_name}.',
            'Recall key process/flow from memory once.',
            'Revisit one example and one edge case.',
            'Summarize the most important comparison/trade-off.'
        ],
        'pitfalls': [
            'Mixing similarly named concepts.',
            'Skipping assumptions before solving.',
            'Answering from memory without checking context.'
        ],
        'drills': [
            'Explain one core concept in 2 lines.',
            'Write one common mistake and correction.',
            'Solve one quick practice prompt mentally.'
        ]
    }


def build_topic_submodules(video):
    cheat = get_static_cheat_sheet(video.get('id'), video.get('title', 'Topic'))
    core = cheat.get('core', [])
    drills = cheat.get('drills', [])

    def pick(items, index, fallback):
        if items:
            return items[index % len(items)]
        return fallback

    segments = [
        ("Module 1: Foundations", "Build conceptual clarity and key vocabulary.", 0, 420),
        ("Module 2: Deep Dive", "Strengthen understanding through mechanisms and flow.", 420, 900),
        ("Module 3: Exam Prep", "Focus on high-yield points, pitfalls, and drills.", 900, None)
    ]

    submodules = []
    for idx, (title, objective, start_sec, end_sec) in enumerate(segments):
        focus_line = pick(core, idx, f"Revise foundational concepts in {video.get('title', 'this topic')}.")
        drill_line = pick(drills, idx, "Attempt one quick recall drill before moving ahead.")

        checkpoints = [
            {
                "id": f"cp-{idx+1}-1",
                "trigger_pct": 30,
                "question": f"Checkpoint: Which statement best matches this module focus?",
                "options": [
                    focus_line,
                    "Skip basics and directly memorize final answers.",
                    "Ignore conceptual flow and only read examples.",
                    "Avoid revision until final quiz."
                ],
                "correct_index": 0,
                "explanation": "Correct — this aligns with the current revision objective."
            },
            {
                "id": f"cp-{idx+1}-2",
                "trigger_pct": 65,
                "question": "Checkpoint: What is the best next revision action?",
                "options": [
                    "State one key concept and one edge case from this module.",
                    "Skip all weak areas and move to new topics.",
                    "Memorize without understanding.",
                    "Avoid practice questions."
                ],
                "correct_index": 0,
                "explanation": "Correct — active recall plus edge-case checking improves retention."
            },
            {
                "id": f"cp-{idx+1}-3",
                "trigger_pct": 85,
                "question": "Final checkpoint for this module:",
                "options": [
                    drill_line,
                    "Do nothing until the final graded quiz.",
                    "Only rewatch without testing yourself.",
                    "Skip all pitfall review."
                ],
                "correct_index": 0,
                "explanation": "Correct — quick drills before moving on improve transfer and confidence."
            }
        ]

        submodules.append({
            "id": f"{video.get('id', 'topic')}-m{idx+1}",
            "title": title,
            "objective": objective,
            "video_id": video.get('video_id'),
            "start_sec": start_sec,
            "end_sec": end_sec,
            "checkpoints": checkpoints
        })

    return submodules


def build_quiz_payload(user_id, topic_id, video, watch_time):
    current_mastery = bkt_engine.get_mastery(user_id, topic_id)
    attempts = load_json(QUIZ_ATTEMPTS_FILE) if os.path.exists(QUIZ_ATTEMPTS_FILE) else []
    user_topic_attempts = [a for a in attempts if a['user_id'] == user_id and a['topic_id'] == topic_id]
    if user_topic_attempts:
        last_attempt = user_topic_attempts[-1]
        current_difficulty = last_attempt.get('adaptation', {}).get('new_difficulty', 'medium')
        current_cluster = last_attempt.get('behavior_cluster', 'General Learner')
        current_speed = last_attempt.get('adaptation', {}).get('speed_label', 'Steady')
    else:
        current_difficulty = 'medium'
        current_cluster = 'General Learner'
        current_speed = 'Steady'

    recent_question_texts = []
    for attempt in user_topic_attempts[-5:]:
        for q in attempt.get('question_results', []):
            text = q.get('text')
            if text:
                recent_question_texts.append(text)

    seen = set()
    avoid_questions = []
    for text in recent_question_texts:
        norm = text.strip().lower()
        if norm and norm not in seen:
            seen.add(norm)
            avoid_questions.append(text)

    avoid_questions = avoid_questions[:30]

    quiz = quiz_gen.generate_quiz(
        topic_id,
        video['title'],
        video['video_id'],
        watch_time,
        difficulty=current_difficulty,
        mastery=current_mastery,
        cluster=current_cluster,
        speed_label=current_speed,
        avoid_questions=avoid_questions
    )

    question_count = len(quiz.get('questions', []))
    question_time_seconds = 15 if quiz.get('difficulty') == 'easy' else 12 if quiz.get('difficulty') == 'medium' else 10
    quiz['question_time_seconds'] = question_time_seconds
    quiz['hint_unlock_seconds'] = max(5, question_time_seconds // 2)
    quiz['topic_name'] = video['title']
    quiz['topic_id'] = topic_id
    quiz['question_count'] = question_count

    return quiz


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
    topic_map = {v['id']: v['title'] for v in videos}
    topic_heatmap_rows = build_topic_heatmap_rows(user_attempts, topic_map)
    review_rows = build_review_rows(user_attempts, topic_map)
    recent_reviews = review_rows[:5]
    latest_ai_insight = recent_reviews[0].get('insight_summary') if recent_reviews else None
    latest_review_by_topic = {}
    for row in review_rows:
        topic_id = row.get('topic_id')
        if topic_id and topic_id not in latest_review_by_topic and row.get('attempt_id'):
            latest_review_by_topic[topic_id] = row.get('attempt_id')
    
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
                         speed_message=speed_message,
                         recent_reviews=recent_reviews,
                         latest_ai_insight=latest_ai_insight,
                         latest_review_by_topic=latest_review_by_topic,
                         topic_heatmap_rows=topic_heatmap_rows)

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

    submodules = build_topic_submodules(video)
    return render_template('video.html', video=video, submodules=submodules)

from backend.adaptation.micro_pattern import mp_manager
from backend.adaptation.recommendation import recommender
from backend.quiz.quiz_generator import quiz_gen
from backend.quiz.quiz_evaluator import evaluator
from backend.quiz.quiz_insights import insights_engine
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

    cheat_sheet = get_static_cheat_sheet(topic_id, video['title'])
    return render_template(
        'quiz.html',
        loading=True,
        topic_id=topic_id,
        topic_name=video['title'],
        static_cheat_sheet=cheat_sheet
    )


@app.route('/api/quiz-data/<topic_id>', methods=['GET'])
def api_quiz_data(topic_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    videos = load_json(VIDEOS_FILE)
    video = next((v for v in videos if v['id'] == topic_id), None)
    if not video:
        return jsonify({'success': False, 'message': 'Topic not found'}), 404

    user_id = session['user_id']
    progress = load_json(PROGRESS_FILE)
    user_video_progress = progress.get(user_id, {}).get(topic_id, {})
    watch_time = user_video_progress.get('last_position', 0)

    quiz = build_quiz_payload(user_id, topic_id, video, watch_time)
    session['current_quiz'] = quiz

    return jsonify({
        'success': True,
        'quiz': quiz,
        'static_cheat_sheet': get_static_cheat_sheet(topic_id, video['title'])
    })



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

    videos = load_json(VIDEOS_FILE)
    video = next((v for v in videos if v['id'] == topic_id), {'title': topic_id})
    ai_insights = insights_engine.generate_insights(
        video.get('title', topic_id),
        score,
        round(new_mastery, 2),
        eval_result.get('question_results', [])
    )

    answer_map = {
        str(r.get('question_id')): {
            'selected_answer': r.get('selected_answer'),
            'time_taken': r.get('time_taken'),
            'used_hint': r.get('used_hint', False)
        }
        for r in responses
    }
    reviewed_questions = []
    for q_res in eval_result.get('question_results', []):
        qid = str(q_res.get('question_id'))
        q_data = next((q for q in quiz.get('questions', []) if str(q.get('id')) == qid), {})
        user_data = answer_map.get(qid, {})
        reviewed_questions.append({
            'id': qid,
            'text': q_data.get('text'),
            'options': q_data.get('options', []),
            'correct_answer': q_data.get('answer'),
            'selected_answer': user_data.get('selected_answer'),
            'is_correct': q_res.get('is_correct', False),
            'feedback': q_res.get('feedback', ''),
            'hint': q_data.get('hint', ''),
            'used_hint': user_data.get('used_hint', False),
            'time_taken': user_data.get('time_taken', q_res.get('time_taken', 0))
        })

    attempt_id = f"{user_id}-{uuid.uuid4().hex[:10]}"

    
    attempt_log = {
        "attempt_id": attempt_id,
        "user_id": user_id,
        "topic_id": topic_id,
        "topic_name": video.get('title', topic_id),
        "timestamp": datetime.now().isoformat(),
        "score": score,
        "avg_time": avg_time,
        "total_time": eval_result.get('total_time', 0),
        "adaptation": adaptation,
        "mastery": new_mastery,
        "behavior_cluster": cluster,
        "recommendation": recommendation,
        "quiz_meta": {
            "difficulty": quiz.get('difficulty', current_difficulty),
            "num_questions": len(quiz.get('questions', [])),
            "timer_seconds": quiz.get('timer_seconds', 0),
            "hint_unlock_seconds": quiz.get('hint_unlock_seconds', 0)
        },
        "question_results": reviewed_questions,
        "ai_insights": ai_insights
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
        'recommendation': recommendation,
        'attempt_id': attempt_id,
        'ai_insights': ai_insights
    })


@app.route('/quiz-review')
def quiz_review_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    attempts = load_json(QUIZ_ATTEMPTS_FILE) if os.path.exists(QUIZ_ATTEMPTS_FILE) else []
    videos = load_json(VIDEOS_FILE)
    topic_map = {v['id']: v['title'] for v in videos}
    user_attempts = [a for a in attempts if a.get('user_id') == user_id]
    review_rows = build_review_rows(user_attempts, topic_map)

    return render_template('quiz_review.html', review_rows=review_rows, selected_attempt=None)


@app.route('/quiz-review/<attempt_id>')
def quiz_review_page(attempt_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    attempts = load_json(QUIZ_ATTEMPTS_FILE) if os.path.exists(QUIZ_ATTEMPTS_FILE) else []
    videos = load_json(VIDEOS_FILE)
    topic_map = {v['id']: v['title'] for v in videos}

    user_attempts = [a for a in attempts if a.get('user_id') == user_id]
    review_rows = build_review_rows(user_attempts, topic_map)
    selected_attempt = next((a for a in user_attempts if a.get('attempt_id') == attempt_id), None)

    if not selected_attempt:
        return redirect(url_for('quiz_review_list'))

    return render_template('quiz_review.html', review_rows=review_rows, selected_attempt=selected_attempt)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
