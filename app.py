from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
from datetime import datetime
from trivia_parser import TriviaParser
from models import TriviaGame

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trivia-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

game = TriviaGame()

# Team validation helper
def validate_team_membership():
    """Validate that the current session has a valid team membership"""
    player_name = session.get('player_name')
    team_id = session.get('team_id')
    
    if not player_name or not team_id:
        return False
    
    # Check if team exists in current game
    if team_id not in game.teams:
        # Clear invalid session data
        session.pop('team_id', None)
        session.pop('player_name', None)
        return False
    
    # Verify player is still in the team
    current_team_id = game.find_player_team(player_name)
    if current_team_id != team_id:
        # Clear invalid session data
        session.pop('team_id', None)
        session.pop('player_name', None)
        return False
    
    return True

# Team membership required decorator
def team_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_team_membership():
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to invalidate player sessions when team changes
def invalidate_player_sessions(affected_players):
    """Invalidate sessions for players whose teams have changed"""
    # Note: In a production environment, you'd want to track active sessions
    # For now, the client-side validation will handle this when they next interact
    pass

# Helper function to emit question updates to all teams
def emit_question_to_all_teams():
    """Emit the current question to all teams with their specific answer status"""
    base_question = game.get_current_question()
    if not base_question:
        return
    
    for team_id in game.teams:
        team_question = base_question.copy()
        current_index = game.current_question_index
        team_question['already_answered'] = game.has_team_answered_question(team_id, current_index)
        
        if team_question['already_answered']:
            team_question['submitted_answer'] = game.get_team_answer(team_id, current_index)
        
        # Emit to specific team
        socketio.emit('new_question', team_question, room=team_id)

# Admin authentication decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/teams')
def get_teams():
    return jsonify(game.get_teams())

@app.route('/api/teams', methods=['POST'])
def create_team():
    data = request.json
    team_name = data.get('team_name')
    player_name = data.get('player_name')
    
    team_id = game.create_team(team_name, player_name)
    session['team_id'] = team_id
    session['player_name'] = player_name
    
    return jsonify({'team_id': team_id, 'success': True})

@app.route('/api/teams/<team_id>/join', methods=['POST'])
def join_team(team_id):
    data = request.json
    player_name = data.get('player_name')
    
    # Check if player is already on a team
    current_team_id = game.find_player_team(player_name)
    if current_team_id and current_team_id != team_id:
        # Remove from current team first
        game.leave_team(current_team_id, player_name)
    
    success = game.join_team(team_id, player_name)
    if success:
        session['team_id'] = team_id
        session['player_name'] = player_name
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Team not found'})

@app.route('/api/teams/leave', methods=['POST'])
def leave_team():
    player_name = session.get('player_name')
    team_id = session.get('team_id')
    
    if not player_name or not team_id:
        return jsonify({'success': False, 'error': 'No active team membership'})
    
    success = game.leave_team(team_id, player_name)
    if success:
        # Clear session data
        session.pop('team_id', None)
        session.pop('player_name', None)
        
        # Emit team update to all clients
        socketio.emit('teams_update', game.get_teams())
        
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to leave team'})

@app.route('/api/player/status')
def get_player_status():
    if not validate_team_membership():
        return jsonify({'has_team': False})
    
    # If we get here, validation passed
    player_name = session.get('player_name')
    team_id = session.get('team_id')
    team = game.teams[team_id]
    
    return jsonify({
        'has_team': True,
        'team_id': team_id,
        'team_name': team.name,
        'player_name': player_name,
        'teammates': [p for p in team.players if p != player_name]
    })

@app.route('/game')
@team_required
def game_page():
    return render_template('game.html')

@app.route('/api/question')
@team_required
def get_current_question():
    team_id = session.get('team_id')
    question_data = game.get_current_question()
    
    if question_data and team_id:
        # Add team-specific information
        current_index = game.current_question_index
        question_data['already_answered'] = game.has_team_answered_question(team_id, current_index)
        
        if question_data['already_answered']:
            # Include the team's submitted answer
            question_data['submitted_answer'] = game.get_team_answer(team_id, current_index)
    
    return jsonify(question_data)

@app.route('/api/answer', methods=['POST'])
@team_required
def submit_answer():
    data = request.json
    team_id = session.get('team_id')
    answer = data.get('answer')
    
    result = game.submit_answer(team_id, answer)
    
    # Emit score update to all clients
    socketio.emit('score_update', game.get_scoreboard())
    
    return jsonify(result)

@app.route('/api/scoreboard')
def get_scoreboard():
    return jsonify(game.get_scoreboard())

@app.route('/api/next_question', methods=['POST'])
def next_question():
    game.next_question()
    emit_question_to_all_teams()
    socketio.emit('game_status_update', game.get_game_status())
    return jsonify({'success': True})

@app.route('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    password = request.form.get('password')
    # Simple password check - in production, use proper hashing
    if password == 'admin123':  # Change this to a secure password
        session['admin_logged_in'] = True
        return redirect(url_for('admin_panel'))
    else:
        return render_template('admin_login.html', error='Invalid password')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html')

@app.route('/admin/api/status')
@admin_required
def admin_get_status():
    return jsonify(game.get_game_status())

@app.route('/admin/api/game/start', methods=['POST'])
@admin_required
def admin_start_game():
    result = game.start_game()
    if result['success']:
        socketio.emit('game_status_update', game.get_game_status())
        emit_question_to_all_teams()
    return jsonify(result)

@app.route('/admin/api/game/stop', methods=['POST'])
@admin_required
def admin_stop_game():
    result = game.stop_game()
    if result['success']:
        socketio.emit('game_status_update', game.get_game_status())
        socketio.emit('game_stopped', {'scoreboard': game.get_scoreboard()})
    return jsonify(result)

@app.route('/admin/api/game/pause', methods=['POST'])
@admin_required
def admin_pause_game():
    result = game.pause_game()
    if result['success']:
        socketio.emit('game_status_update', game.get_game_status())
        socketio.emit('game_paused', {'message': 'Game has been paused by the administrator'})
    return jsonify(result)

@app.route('/admin/api/game/resume', methods=['POST'])
@admin_required
def admin_resume_game():
    result = game.resume_game()
    if result['success']:
        socketio.emit('game_status_update', game.get_game_status())
        socketio.emit('game_resumed', {'message': 'Game has been resumed'})
        emit_question_to_all_teams()
    return jsonify(result)

@app.route('/admin/api/next_question', methods=['POST'])
@admin_required
def admin_next_question():
    if game.current_question_index < len(game.questions) - 1:
        game.next_question()
        emit_question_to_all_teams()
        socketio.emit('game_status_update', game.get_game_status())
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'No more questions available'})

@app.route('/admin/api/set_question', methods=['POST'])
@admin_required
def admin_set_question():
    data = request.json
    question_number = data.get('question_number', 1)
    result = game.set_question(question_number - 1)  # Convert to 0-based index
    if result['success']:
        emit_question_to_all_teams()
        socketio.emit('game_status_update', game.get_game_status())
    return jsonify(result)

@app.route('/admin/api/teams/<team_id>/name', methods=['PUT'])
@admin_required
def admin_update_team_name(team_id):
    data = request.json
    new_name = data.get('name')
    
    result = game.update_team_name(team_id, new_name)
    
    if result['success']:
        # Emit team update to all clients
        socketio.emit('teams_update', game.get_teams())
    
    return jsonify(result)

@app.route('/admin/api/teams/<team_id>/players', methods=['POST'])
@admin_required
def admin_add_player(team_id):
    data = request.json
    player_name = data.get('player_name')
    
    result = game.add_player_to_team(team_id, player_name)
    
    if result['success']:
        # Emit team update to all clients
        socketio.emit('teams_update', game.get_teams())
    
    return jsonify(result)

@app.route('/admin/api/teams/<team_id>/players/<player_name>', methods=['DELETE'])
@admin_required
def admin_remove_player(team_id, player_name):
    result = game.remove_player_from_team(team_id, player_name)
    
    if result['success']:
        # Emit team update to all clients
        socketio.emit('teams_update', game.get_teams())
    
    return jsonify(result)

@app.route('/admin/api/teams/<team_id>', methods=['DELETE'])
@admin_required
def admin_delete_team(team_id):
    result = game.delete_team(team_id)
    
    if result['success']:
        # Emit team update to all clients
        socketio.emit('teams_update', game.get_teams())
    
    return jsonify(result)

@socketio.on('connect')
def on_connect():
    if 'team_id' in session:
        join_room(session['team_id'])

@socketio.on('disconnect')
def on_disconnect():
    if 'team_id' in session:
        leave_room(session['team_id'])

if __name__ == '__main__':
    # Load questions from markdown file
    if os.path.exists('questions.md'):
        parser = TriviaParser('questions.md')
        questions = parser.parse()
        game.load_questions(questions)
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)