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
    player_name = session.get('player_name')
    team_id = session.get('team_id')
    
    if not player_name:
        return jsonify({'has_team': False})
    
    # Verify player is still in the team (in case team was deleted)
    current_team_id = game.find_player_team(player_name)
    if current_team_id != team_id:
        # Clear invalid session data
        session.pop('team_id', None)
        session.pop('player_name', None)
        return jsonify({'has_team': False})
    
    if team_id and team_id in game.teams:
        team = game.teams[team_id]
        return jsonify({
            'has_team': True,
            'team_id': team_id,
            'team_name': team.name,
            'player_name': player_name,
            'teammates': [p for p in team.players if p != player_name]
        })
    
    return jsonify({'has_team': False})

@app.route('/game')
def game_page():
    if 'team_id' not in session:
        return redirect(url_for('index'))
    return render_template('game.html')

@app.route('/api/question')
def get_current_question():
    return jsonify(game.get_current_question())

@app.route('/api/answer', methods=['POST'])
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
    socketio.emit('new_question', game.get_current_question())
    return jsonify({'success': True})

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