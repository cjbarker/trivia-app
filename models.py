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
                **question.to_dict()
            }
        return None
    
    def submit_answer(self, team_id, answer):
        if team_id not in self.teams:
            return {'success': False, 'error': 'Team not found'}
        
        if self.current_question_index >= len(self.questions):
            return {'success': False, 'error': 'No current question'}
        
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