import uuid
from datetime import datetime

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
        
        question = self.questions[self.current_question_index]
        team = self.teams[team_id]
        
        # Store the answer
        team.answers[self.current_question_index] = answer
        
        # Check if answer is correct
        is_correct = self._check_answer(answer, question.correct_answer)
        
        if is_correct:
            team.score += 1
        
        return {
            'success': True,
            'correct': is_correct,
            'correct_answer': question.correct_answer,
            'team_score': team.score
        }
    
    def _check_answer(self, submitted_answer, correct_answer):
        if isinstance(submitted_answer, str) and isinstance(correct_answer, str):
            return submitted_answer.strip().lower() == correct_answer.strip().lower()
        return submitted_answer == correct_answer
    
    def next_question(self):
        self.current_question_index += 1
    
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
        return {'success': True, 'message': 'Game started'}
    
    def stop_game(self):
        self.game_started = False
        self.game_paused = True
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
            'teams_count': len(self.teams)
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