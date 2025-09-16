import uuid
from datetime import datetime, timedelta
import time
import threading

class Team:
    def __init__(self, name, team_id=None):
        self.id = team_id or str(uuid.uuid4())
        self.name = name
        self.players = []
        self.score = 0
        self.answers = {}
        self.created_at = datetime.now()
    
    def add_player(self, player_name):
        if player_name not in self.players:
            self.players.append(player_name)
            return True
        return False
    
    def remove_player(self, player_name):
        if player_name in self.players:
            self.players.remove(player_name)
            return True
        return False
    
    def is_empty(self):
        return len(self.players) == 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'players': self.players,
            'score': self.score,
            'player_count': len(self.players)
        }

class Question:
    def __init__(self, question_text, question_type, options=None, correct_answer=None):
        self.question_text = question_text
        self.question_type = question_type  # 'multiple_choice' or 'fill_in_blank'
        self.options = options or []
        self.correct_answer = correct_answer
    
    def to_dict(self, include_answer=False):
        data = {
            'question_text': self.question_text,
            'question_type': self.question_type,
            'options': self.options
        }
        if include_answer:
            data['correct_answer'] = self.correct_answer
        return data

class TriviaGame:
    def __init__(self):
        self.teams = {}
        self.questions = []
        self.current_question_index = 0
        self.game_started = False
        self.game_paused = False
        # Timer functionality
        self.question_timer_duration = 60  # seconds
        self.question_start_time = None
        self.timer_thread = None
        self.timer_callbacks = []  # For WebSocket updates
        self.timer_expired_callbacks = []  # Called when timer expires
        self.answer_times = {}  # Store when each team answered: {question_index: {team_id: timestamp}}
    
    def create_team(self, team_name, player_name):
        team = Team(team_name)
        team.add_player(player_name)
        self.teams[team.id] = team
        return team.id
    
    def join_team(self, team_id, player_name):
        if team_id in self.teams:
            return self.teams[team_id].add_player(player_name)
        return False
    
    def leave_team(self, team_id, player_name):
        if team_id in self.teams:
            team = self.teams[team_id]
            success = team.remove_player(player_name)
            
            # Remove empty teams
            if team.is_empty():
                del self.teams[team_id]
            
            return success
        return False
    
    def find_player_team(self, player_name):
        for team_id, team in self.teams.items():
            if player_name in team.players:
                return team_id
        return None
    
    def get_teams(self):
        return [team.to_dict() for team in self.teams.values()]
    
    def load_questions(self, questions):
        self.questions = questions
    
    def get_current_question(self):
        if self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            return {
                'question_number': self.current_question_index + 1,
                'total_questions': len(self.questions),
                'game_started': self.game_started,
                'game_paused': self.game_paused,
                **question.to_dict()
            }
        return None
    
    def has_team_answered_question(self, team_id, question_index):
        """Check if a team has already answered a specific question"""
        if team_id not in self.teams:
            return False
        return question_index in self.teams[team_id].answers
    
    def get_team_answer(self, team_id, question_index):
        """Get a team's answer for a specific question"""
        if team_id not in self.teams:
            return None
        return self.teams[team_id].answers.get(question_index)
    
    def submit_answer(self, team_id, answer):
        if team_id not in self.teams:
            return {'success': False, 'error': 'Team not found'}
        
        if self.current_question_index >= len(self.questions):
            return {'success': False, 'error': 'No current question'}
        
        # Check if team has already answered this question
        if self.has_team_answered_question(team_id, self.current_question_index):
            return {'success': False, 'error': 'Question already answered'}
        
        # Calculate answer time and bonus points
        answer_time_seconds = 60  # Default if no timer
        bonus_points = 0
        
        if self.question_start_time:
            answer_time_seconds = time.time() - self.question_start_time
            bonus_points = self.get_bonus_points(answer_time_seconds)
            
            # Store answer time
            if self.current_question_index not in self.answer_times:
                self.answer_times[self.current_question_index] = {}
            self.answer_times[self.current_question_index][team_id] = answer_time_seconds
        
        question = self.questions[self.current_question_index]
        team = self.teams[team_id]
        
        # Store the answer
        team.answers[self.current_question_index] = answer
        
        # Check if answer is correct
        is_correct = self._check_answer(answer, question.correct_answer)
        
        # Calculate points (1 for correct + bonus)
        points_earned = 0
        if is_correct:
            points_earned = 1 + bonus_points
            team.score += points_earned
        
        return {
            'success': True,
            'correct': is_correct,
            'points_earned': points_earned,
            'bonus_points': bonus_points,
            'answer_time': round(answer_time_seconds, 1),
            'correct_answer': question.correct_answer,
            'team_score': team.score
        }
    
    def _check_answer(self, submitted_answer, correct_answer):
        if isinstance(submitted_answer, str) and isinstance(correct_answer, str):
            return submitted_answer.strip().lower() == correct_answer.strip().lower()
        return submitted_answer == correct_answer
    
    def next_question(self):
        self.current_question_index += 1
        # Start timer for new question
        if self.game_started and not self.game_paused:
            self.start_question_timer()
    
    def get_scoreboard(self):
        scoreboard = []
        for team in self.teams.values():
            scoreboard.append({
                'team_name': team.name,
                'score': team.score,
                'players': team.players
            })
        
        # Sort by score descending
        scoreboard.sort(key=lambda x: x['score'], reverse=True)
        return scoreboard
    
    def start_game(self):
        self.game_started = True
        self.game_paused = False
        # Start timer for first question
        self.start_question_timer()
        return {'success': True, 'message': 'Game started'}
    
    def stop_game(self):
        self.game_started = False
        self.game_paused = True
        self.question_start_time = None  # Stop timer
        return {'success': True, 'message': 'Game stopped'}
    
    def pause_game(self):
        if self.game_started:
            self.game_paused = True
            return {'success': True, 'message': 'Game paused'}
        return {'success': False, 'message': 'Game is not started'}
    
    def resume_game(self):
        if self.game_started:
            self.game_paused = False
            return {'success': True, 'message': 'Game resumed'}
        return {'success': False, 'message': 'Game is not started'}
    
    def set_question(self, question_index):
        if 0 <= question_index < len(self.questions):
            self.current_question_index = question_index
            return {'success': True, 'message': f'Set to question {question_index + 1}'}
        return {'success': False, 'message': 'Invalid question index'}
    
    def get_game_status(self):
        status = {
            'started': self.game_started,
            'paused': self.game_paused,
            'current_question': self.current_question_index + 1,
            'total_questions': len(self.questions),
            'teams_count': len(self.teams),
            # Timer information
            'timer': {
                'time_remaining': self.get_time_remaining(),
                'total_time': self.question_timer_duration,
                'bonus_points': self.get_bonus_points(self.question_timer_duration - self.get_time_remaining())
            }
        }
        
        # Add current question details if game is started
        if self.game_started and self.current_question_index < len(self.questions):
            current_question = self.questions[self.current_question_index]
            status['question_details'] = {
                'question_text': current_question.question_text,
                'question_type': current_question.question_type,
                'correct_answer': current_question.correct_answer,
                'options': current_question.options if hasattr(current_question, 'options') else None
            }
            
            # Add team answer status
            team_answers = []
            for team_id, team in self.teams.items():
                has_answered = self.has_team_answered_question(team_id, self.current_question_index)
                answer_data = {
                    'team_id': team_id,
                    'team_name': team.name,
                    'has_answered': has_answered,
                    'submitted_answer': None,
                    'is_correct': None
                }
                
                if has_answered:
                    submitted_answer = self.get_team_answer(team_id, self.current_question_index)
                    answer_data['submitted_answer'] = submitted_answer
                    answer_data['is_correct'] = (submitted_answer.lower().strip() == 
                                               current_question.correct_answer.lower().strip())
                
                team_answers.append(answer_data)
            
            status['team_answers'] = team_answers
            
            # Add summary stats
            answered_count = sum(1 for t in team_answers if t['has_answered'])
            correct_count = sum(1 for t in team_answers if t['is_correct'])
            
            status['answer_summary'] = {
                'teams_answered': answered_count,
                'teams_total': len(self.teams),
                'correct_answers': correct_count,
                'completion_percentage': round((answered_count / len(self.teams)) * 100) if self.teams else 0
            }
        
        return status
    
    def add_timer_callback(self, callback):
        """Add callback function for timer updates (WebSocket events)"""
        self.timer_callbacks.append(callback)
    
    def get_time_remaining(self):
        """Get remaining time for current question in seconds"""
        if not self.question_start_time or self.game_paused:
            return self.question_timer_duration
        
        elapsed = time.time() - self.question_start_time
        remaining = max(0, self.question_timer_duration - elapsed)
        return int(remaining)
    
    def get_bonus_points(self, answer_time_seconds):
        """Calculate bonus points based on answer time - deduct 1 point every 10 seconds"""
        # Start with 6 points, deduct 1 point every 10 seconds
        # 0-10s: 6 points, 10-20s: 5 points, 20-30s: 4 points, 30-40s: 3 points, 40-50s: 2 points, 50-60s: 1 point, 60s+: 0 points
        points = 6 - int(answer_time_seconds // 10)
        return max(0, points)  # Ensure points never go below 0
    
    def start_question_timer(self):
        """Start the timer for the current question"""
        if self.game_paused:
            return
            
        self.question_start_time = time.time()
        
        # Initialize answer times for current question if not exists
        if self.current_question_index not in self.answer_times:
            self.answer_times[self.current_question_index] = {}
        
        # Start timer thread for WebSocket updates
        if self.timer_thread and self.timer_thread.is_alive():
            return  # Timer already running
            
        self.timer_thread = threading.Thread(target=self._timer_worker, daemon=True)
        self.timer_thread.start()
    
    def _timer_worker(self):
        """Background worker for timer updates"""
        while self.question_start_time and not self.game_paused:
            remaining = self.get_time_remaining()
            
            # Notify callbacks (WebSocket updates)
            for callback in self.timer_callbacks:
                try:
                    callback(remaining, self.get_bonus_points(60 - remaining))
                except Exception as e:
                    print(f"Timer callback error: {e}")
            
            if remaining <= 0:
                # Timer expired - notify expired callbacks
                for callback in self.timer_expired_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        print(f"Timer expired callback error: {e}")
                break
                
            time.sleep(1)  # Update every second
    
    def pause_question_timer(self):
        """Pause the current question timer"""
        if self.question_start_time:
            # Store elapsed time
            elapsed = time.time() - self.question_start_time
            self.question_start_time = None
            return elapsed
        return 0
    
    def resume_question_timer(self, elapsed_time=0):
        """Resume the question timer with previous elapsed time"""
        self.question_start_time = time.time() - elapsed_time
        self.start_question_timer()
    
    def update_team_name(self, team_id, new_name):
        """Update a team's name"""
        if team_id not in self.teams:
            return {'success': False, 'error': 'Team not found'}
        
        if not new_name or not new_name.strip():
            return {'success': False, 'error': 'Team name cannot be empty'}
        
        self.teams[team_id].name = new_name.strip()
        return {'success': True, 'message': f'Team name updated to "{new_name.strip()}"'}
    
    def add_player_to_team(self, team_id, player_name):
        """Add a player to a team (admin function)"""
        if team_id not in self.teams:
            return {'success': False, 'error': 'Team not found'}
        
        if not player_name or not player_name.strip():
            return {'success': False, 'error': 'Player name cannot be empty'}
        
        player_name = player_name.strip()
        
        # Check if player is already in this team
        if player_name in self.teams[team_id].players:
            return {'success': False, 'error': 'Player already in this team'}
        
        # Remove player from any other team first
        current_team_id = self.find_player_team(player_name)
        if current_team_id:
            self.teams[current_team_id].remove_player(player_name)
            # Remove team if it becomes empty
            if self.teams[current_team_id].is_empty():
                del self.teams[current_team_id]
        
        # Add to new team
        self.teams[team_id].add_player(player_name)
        return {'success': True, 'message': f'Added "{player_name}" to team'}
    
    def remove_player_from_team(self, team_id, player_name):
        """Remove a player from a team (admin function)"""
        if team_id not in self.teams:
            return {'success': False, 'error': 'Team not found'}
        
        if not player_name or player_name not in self.teams[team_id].players:
            return {'success': False, 'error': 'Player not found in this team'}
        
        self.teams[team_id].remove_player(player_name)
        
        # Remove team if it becomes empty
        if self.teams[team_id].is_empty():
            del self.teams[team_id]
            return {'success': True, 'message': f'Removed "{player_name}" and deleted empty team'}
        
        return {'success': True, 'message': f'Removed "{player_name}" from team'}
    
    def delete_team(self, team_id):
        """Delete an entire team (admin function)"""
        if team_id not in self.teams:
            return {'success': False, 'error': 'Team not found'}
        
        team_name = self.teams[team_id].name
        del self.teams[team_id]
        return {'success': True, 'message': f'Deleted team "{team_name}"'}