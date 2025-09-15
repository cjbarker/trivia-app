const socket = io();
let gameStatus = null;

document.addEventListener('DOMContentLoaded', function() {
    loadGameStatus();
    loadScoreboard();
    loadTeams();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('start-game').addEventListener('click', () => controlGame('start'));
    document.getElementById('pause-game').addEventListener('click', () => controlGame('pause'));
    document.getElementById('resume-game').addEventListener('click', () => controlGame('resume'));
    document.getElementById('stop-game').addEventListener('click', () => controlGame('stop'));
    
    document.getElementById('next-question').addEventListener('click', nextQuestion);
    document.getElementById('prev-question').addEventListener('click', prevQuestion);
    document.getElementById('set-question').addEventListener('click', setQuestion);
    
    // Team management listeners
    document.getElementById('update-team-name').addEventListener('click', updateTeamName);
    document.getElementById('add-player').addEventListener('click', addPlayerToTeam);
    document.getElementById('delete-team').addEventListener('click', deleteTeam);
    document.getElementById('close-modal').addEventListener('click', closeTeamModal);
    document.getElementById('new-player-name').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') addPlayerToTeam();
    });
    
    // Socket listeners
    socket.on('game_status_update', updateGameStatus);
    socket.on('score_update', updateScoreboard);
    socket.on('teams_update', updateTeams);
    socket.on('new_question', function(question) {
        loadGameStatus(); // Refresh status when question changes
    });
}

async function loadGameStatus() {
    try {
        const response = await fetch('/admin/api/status');
        const status = await response.json();
        updateGameStatus(status);
    } catch (error) {
        console.error('Error loading game status:', error);
    }
}

function updateGameStatus(status) {
    gameStatus = status;
    const statusDiv = document.getElementById('game-status');
    
    statusDiv.innerHTML = `
        <p><strong>Game Started:</strong> ${status.started ? 'Yes' : 'No'}</p>
        <p><strong>Game Paused:</strong> ${status.paused ? 'Yes' : 'No'}</p>
        <p><strong>Current Question:</strong> ${status.current_question} of ${status.total_questions}</p>
        <p><strong>Active Teams:</strong> ${status.teams_count}</p>
    `;
    
    // Update button states
    const startBtn = document.getElementById('start-game');
    const pauseBtn = document.getElementById('pause-game');
    const resumeBtn = document.getElementById('resume-game');
    const stopBtn = document.getElementById('stop-game');
    
    startBtn.disabled = status.started;
    pauseBtn.disabled = !status.started || status.paused;
    resumeBtn.disabled = !status.started || !status.paused;
    stopBtn.disabled = !status.started;
    
    // Update question input max
    document.getElementById('question-number').max = status.total_questions;
}

async function controlGame(action) {
    try {
        const response = await fetch(`/admin/api/game/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        showMessage(result.message, result.success ? 'success' : 'error');
        
        if (result.success) {
            loadGameStatus();
        }
    } catch (error) {
        console.error(`Error ${action} game:`, error);
        showMessage(`Error ${action} game`, 'error');
    }
}

async function nextQuestion() {
    try {
        const response = await fetch('/admin/api/next_question', {
            method: 'POST'
        });
        
        const result = await response.json();
        if (result.success) {
            showMessage('Advanced to next question', 'success');
            loadGameStatus();
        } else {
            showMessage(result.error || 'Error advancing question', 'error');
        }
    } catch (error) {
        console.error('Error advancing question:', error);
        showMessage('Error advancing question', 'error');
    }
}

async function prevQuestion() {
    if (!gameStatus || gameStatus.current_question <= 1) {
        showMessage('Already at first question', 'error');
        return;
    }
    
    try {
        const response = await fetch('/admin/api/set_question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question_number: gameStatus.current_question - 1 })
        });
        
        const result = await response.json();
        showMessage(result.message, result.success ? 'success' : 'error');
        
        if (result.success) {
            loadGameStatus();
        }
    } catch (error) {
        console.error('Error going to previous question:', error);
        showMessage('Error going to previous question', 'error');
    }
}

async function setQuestion() {
    const questionNumber = parseInt(document.getElementById('question-number').value);
    
    if (!questionNumber || questionNumber < 1) {
        showMessage('Please enter a valid question number', 'error');
        return;
    }
    
    try {
        const response = await fetch('/admin/api/set_question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question_number: questionNumber })
        });
        
        const result = await response.json();
        showMessage(result.message, result.success ? 'success' : 'error');
        
        if (result.success) {
            loadGameStatus();
            document.getElementById('question-number').value = '';
        }
    } catch (error) {
        console.error('Error setting question:', error);
        showMessage('Error setting question', 'error');
    }
}

async function loadScoreboard() {
    try {
        const response = await fetch('/api/scoreboard');
        const scoreboard = await response.json();
        updateScoreboard(scoreboard);
    } catch (error) {
        console.error('Error loading scoreboard:', error);
    }
}

function updateScoreboard(scoreboard) {
    const scoreboardList = document.getElementById('scoreboard-list');
    
    if (scoreboard.length === 0) {
        scoreboardList.innerHTML = '<p>No teams yet</p>';
        return;
    }
    
    scoreboardList.innerHTML = scoreboard.map((team, index) => `
        <div class="score-item">
            <div class="team-details">
                <div class="team-name">#${index + 1} ${team.team_name}</div>
                <div class="players-list">${team.players.join(', ')}</div>
            </div>
            <div class="team-score">${team.score} points</div>
        </div>
    `).join('');
}

async function loadTeams() {
    try {
        const response = await fetch('/api/teams');
        const teams = await response.json();
        updateTeams(teams);
    } catch (error) {
        console.error('Error loading teams:', error);
    }
}

function updateTeams(teams) {
    const teamsList = document.getElementById('teams-management-list');
    
    if (teams.length === 0) {
        teamsList.innerHTML = '<p>No active teams</p>';
        return;
    }
    
    teamsList.innerHTML = teams.map(team => `
        <div class="team-info" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <strong>${team.name}</strong> (${team.player_count} players)
                    <br><em>Players: ${team.players.join(', ')}</em>
                </div>
                <button onclick="openTeamModal('${team.id}', '${team.name}', ${JSON.stringify(team.players).replace(/"/g, '&quot;')})" 
                        class="btn btn-primary" style="font-size: 12px; padding: 5px 10px;">Manage</button>
            </div>
        </div>
    `).join('');
}

// Team management variables
let currentTeamId = null;

function openTeamModal(teamId, teamName, players) {
    currentTeamId = teamId;
    document.getElementById('modal-title').textContent = `Manage Team: ${teamName}`;
    document.getElementById('modal-team-name').value = teamName;
    
    const playersContainer = document.getElementById('modal-players-list');
    playersContainer.innerHTML = players.map(player => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid #eee;">
            <span>${player}</span>
            <button onclick="removePlayer('${player}')" class="btn btn-danger" style="font-size: 12px; padding: 2px 8px;">Remove</button>
        </div>
    `).join('');
    
    document.getElementById('team-modal').style.display = 'block';
}

function closeTeamModal() {
    document.getElementById('team-modal').style.display = 'none';
    document.getElementById('new-player-name').value = '';
    currentTeamId = null;
}

async function updateTeamName() {
    const newName = document.getElementById('modal-team-name').value.trim();
    if (!newName) {
        showMessage('Team name cannot be empty', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/teams/${currentTeamId}/name`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name: newName})
        });
        
        const result = await response.json();
        showMessage(result.message, result.success ? 'success' : 'error');
        
        if (result.success) {
            document.getElementById('modal-title').textContent = `Manage Team: ${newName}`;
        }
    } catch (error) {
        console.error('Error updating team name:', error);
        showMessage('Error updating team name', 'error');
    }
}

async function addPlayerToTeam() {
    const playerName = document.getElementById('new-player-name').value.trim();
    if (!playerName) {
        showMessage('Player name cannot be empty', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/teams/${currentTeamId}/players`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({player_name: playerName})
        });
        
        const result = await response.json();
        showMessage(result.message, result.success ? 'success' : 'error');
        
        if (result.success) {
            document.getElementById('new-player-name').value = '';
            // Refresh teams to update the modal
            loadTeams();
        }
    } catch (error) {
        console.error('Error adding player:', error);
        showMessage('Error adding player', 'error');
    }
}

async function removePlayer(playerName) {
    if (!confirm(`Remove "${playerName}" from the team?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/teams/${currentTeamId}/players/${encodeURIComponent(playerName)}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        showMessage(result.message, result.success ? 'success' : 'error');
        
        if (result.success) {
            // If team was deleted (became empty), close modal
            if (result.message.includes('deleted empty team')) {
                closeTeamModal();
            }
        }
    } catch (error) {
        console.error('Error removing player:', error);
        showMessage('Error removing player', 'error');
    }
}

async function deleteTeam() {
    if (!confirm('Are you sure you want to delete this entire team?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/teams/${currentTeamId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        showMessage(result.message, result.success ? 'success' : 'error');
        
        if (result.success) {
            closeTeamModal();
        }
    } catch (error) {
        console.error('Error deleting team:', error);
        showMessage('Error deleting team', 'error');
    }
}

function showMessage(message, type) {
    const messagesDiv = document.getElementById('admin-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    messagesDiv.appendChild(messageDiv);
    
    // Remove message after 5 seconds
    setTimeout(() => {
        messagesDiv.removeChild(messageDiv);
    }, 5000);
}