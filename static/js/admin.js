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
    socket.on('score_update', function(scoreboard) {
        updateScoreboard(scoreboard);
        loadGameStatus(); // Refresh status when scores update (answers submitted)
    });
    socket.on('teams_update', updateTeams);
    socket.on('new_question', function(question) {
        loadGameStatus(); // Refresh status when question changes
    });
    
    // Timer-specific socket events for real-time updates
    socket.on('timer_update', function(data) {
        updateAdminTimerRealtime(data.time_remaining, data.bonus_points, data.expired);
    });
    
    socket.on('timer_expired', function() {
        showAdminTimerExpired();
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
    
    // Update question display section
    updateQuestionDisplay(status);
}

function updateQuestionDisplay(status) {
    const questionSection = document.getElementById('current-question-section');
    
    if (status.started && status.question_details) {
        questionSection.style.display = 'block';
        
        // Update question text
        const questionTextDiv = document.getElementById('question-text-display');
        questionTextDiv.innerHTML = `<strong>Q${status.current_question}:</strong> ${status.question_details.question_text}`;
        
        // Update question options or answer type
        const optionsDiv = document.getElementById('question-options-display');
        if (status.question_details.question_type === 'multiple_choice' && status.question_details.options) {
            optionsDiv.innerHTML = '<h5>Options:</h5>' + 
                status.question_details.options.map((option, index) => {
                    const isCorrect = option === status.question_details.correct_answer;
                    return `<div class="question-option ${isCorrect ? 'correct' : ''}">${String.fromCharCode(65 + index)}) ${option}</div>`;
                }).join('');
        } else {
            optionsDiv.innerHTML = '<p><em>Fill-in-the-blank question</em></p>';
        }
        
        // Update correct answer display
        const correctAnswerDiv = document.getElementById('correct-answer-display');
        correctAnswerDiv.innerHTML = `<strong>Correct Answer:</strong> ${status.question_details.correct_answer}`;
        
        // Update answer progress
        updateAnswerProgress(status.answer_summary);
        
        // Update team answers
        updateTeamAnswers(status.team_answers);
        
        // Update timer display
        updateAdminTimer(status.timer);
        
    } else {
        questionSection.style.display = 'none';
        // Hide timer section when game is not active
        document.getElementById('admin-timer-status').style.display = 'none';
    }
}

function updateAnswerProgress(summary) {
    if (!summary) return;
    
    const progressSummary = document.getElementById('progress-summary');
    const progressBar = document.getElementById('progress-bar');
    
    progressSummary.innerHTML = `
        <span>Teams Answered: ${summary.teams_answered}/${summary.teams_total}</span>
        <span>Correct: ${summary.correct_answers}</span>
        <span>${summary.completion_percentage}% Complete</span>
    `;
    
    progressBar.style.width = `${summary.completion_percentage}%`;
}

function updateTeamAnswers(teamAnswers) {
    if (!teamAnswers) return;
    
    const teamAnswersList = document.getElementById('team-answers-list');
    
    if (teamAnswers.length === 0) {
        teamAnswersList.innerHTML = '<p>No teams in game</p>';
        return;
    }
    
    teamAnswersList.innerHTML = teamAnswers.map(team => {
        let statusClass = '';
        let statusIcon = '⏳';
        let statusText = 'Waiting';
        let answerText = '';
        
        if (team.has_answered) {
            answerText = `Answer: "${team.submitted_answer}"`;
            if (team.is_correct) {
                statusClass = 'correct';
                statusIcon = '✓';
                statusText = 'Correct';
            } else {
                statusClass = 'incorrect';
                statusIcon = '✗';
                statusText = 'Incorrect';
            }
        }
        
        const iconHtml = team.team_icon ? 
            `<img class="team-icon-small" src="${team.team_icon}" alt="${team.team_name} icon" style="width: 20px; height: 20px; object-fit: cover; border-radius: 4px; margin-right: 8px;">` : 
            '<span class="team-icon-placeholder-small" style="display: inline-block; width: 20px; height: 20px; background: #e9ecef; border-radius: 4px; margin-right: 8px; text-align: center; line-height: 20px; font-size: 12px; color: #6c757d;">?</span>';
            
        return `
            <div class="team-answer-item ${statusClass}">
                <div class="team-answer-info">
                    <div class="team-answer-name" style="display: flex; align-items: center;">
                        ${iconHtml}${team.team_name}
                    </div>
                    ${answerText ? `<div class="team-answer-response">${answerText}</div>` : ''}
                </div>
                <div class="team-answer-status">
                    <div class="answer-status-icon status-${team.has_answered ? (team.is_correct ? 'correct' : 'incorrect') : 'waiting'}">
                        ${statusIcon}
                    </div>
                    <span>${statusText}</span>
                </div>
            </div>
        `;
    }).join('');
}

function updateAdminTimer(timerData) {
    if (!timerData) {
        document.getElementById('admin-timer-status').style.display = 'none';
        return;
    }
    
    document.getElementById('admin-timer-status').style.display = 'block';
    
    const timeRemaining = timerData.time_remaining;
    const bonusPoints = timerData.bonus_points;
    const totalTime = timerData.total_time || 60;
    
    // Update display text
    document.getElementById('admin-time-remaining').textContent = `${timeRemaining}s`;
    document.getElementById('admin-bonus-points').textContent = `+${bonusPoints}`;
    
    // Update progress bar
    const timerBar = document.getElementById('admin-timer-bar');
    const percentage = (timeRemaining / totalTime) * 100;
    timerBar.style.width = `${percentage}%`;
    
    // Update colors based on time remaining
    timerBar.classList.remove('warning', 'danger');
    
    if (percentage <= 20) {
        timerBar.classList.add('danger');
    } else if (percentage <= 50) {
        timerBar.classList.add('warning');
    }
}

function updateAdminTimerRealtime(timeRemaining, bonusPoints, expired) {
    if (expired) {
        showAdminTimerExpired();
        return;
    }
    
    // Only update if timer section is visible
    const timerSection = document.getElementById('admin-timer-status');
    if (timerSection.style.display === 'none') {
        timerSection.style.display = 'block';
    }
    
    const totalTime = 60; // Default timer duration
    
    // Update display text
    const timeRemainingElement = document.getElementById('admin-time-remaining');
    const bonusPointsElement = document.getElementById('admin-bonus-points');
    
    if (timeRemainingElement) {
        timeRemainingElement.textContent = `${timeRemaining}s`;
    }
    if (bonusPointsElement) {
        bonusPointsElement.textContent = `+${bonusPoints}`;
    }
    
    // Update progress bar
    const timerBar = document.getElementById('admin-timer-bar');
    if (timerBar) {
        const percentage = (timeRemaining / totalTime) * 100;
        timerBar.style.width = `${percentage}%`;
        
        // Update colors based on time remaining
        timerBar.classList.remove('warning', 'danger');
        
        if (percentage <= 20) {
            timerBar.classList.add('danger');
        } else if (percentage <= 50) {
            timerBar.classList.add('warning');
        }
    }
}

function showAdminTimerExpired() {
    const timerSection = document.getElementById('admin-timer-status');
    if (timerSection) {
        timerSection.innerHTML = `
            <div class="timer-status-header">
                <h5>⏰ Bonus Timer</h5>
            </div>
            <div class="timer-display" style="text-align: center; color: #dc3545; padding: 15px;">
                <h6>Bonus Time Expired!</h6>
                <p style="margin: 0; font-size: 0.9em;">Teams can still submit answers, but no bonus points will be awarded.</p>
            </div>
        `;
    }
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
    
    scoreboardList.innerHTML = scoreboard.map((team, index) => {
        const iconHtml = team.team_icon ? 
            `<img class="team-icon-small" src="${team.team_icon}" alt="${team.team_name} icon" style="width: 24px; height: 24px; object-fit: cover; border-radius: 4px; margin-right: 10px;">` : 
            '<span class="team-icon-placeholder-small" style="display: inline-block; width: 24px; height: 24px; background: #e9ecef; border-radius: 4px; margin-right: 10px; text-align: center; line-height: 24px; font-size: 14px; color: #6c757d; flex-shrink: 0;">?</span>';
            
        return `
            <div class="score-item">
                <div class="team-details">
                    <div class="team-name" style="display: flex; align-items: center;">
                        ${iconHtml}#${index + 1} ${team.team_name}
                    </div>
                    <div class="players-list">${team.players.join(', ')}</div>
                </div>
                <div class="team-score">${team.score} points</div>
            </div>
        `;
    }).join('');
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
    
    teamsList.innerHTML = teams.map(team => {
        const iconHtml = team.icon ? 
            `<img class="team-icon-small" src="${team.icon}" alt="${team.name} icon" style="width: 32px; height: 32px; object-fit: cover; border-radius: 4px; margin-right: 12px;">` : 
            '<span class="team-icon-placeholder-small" style="display: inline-block; width: 32px; height: 32px; background: #e9ecef; border-radius: 4px; margin-right: 12px; text-align: center; line-height: 32px; font-size: 16px; color: #6c757d; flex-shrink: 0;">?</span>';
            
        return `
            <div class="team-info" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="display: flex; align-items: flex-start; flex-grow: 1;">
                        ${iconHtml}
                        <div>
                            <strong>${team.name}</strong> (${team.player_count} players)
                            <br><em>Players: ${team.players.join(', ')}</em>
                        </div>
                    </div>
                    <button onclick="openTeamModal('${team.id}', '${team.name}', ${JSON.stringify(team.players).replace(/"/g, '&quot;')}, '${team.icon || ''}')" 
                            class="btn btn-primary" style="font-size: 12px; padding: 5px 10px; margin-left: 10px;">Manage</button>
                </div>
            </div>
        `;
    }).join('');
}

// Team management variables
let currentTeamId = null;

function openTeamModal(teamId, teamName, players, teamIcon = '') {
    currentTeamId = teamId;
    const modalTitle = document.getElementById('modal-title');
    const iconHtml = teamIcon ? 
        `<img src="${teamIcon}" alt="${teamName} icon" style="width: 20px; height: 20px; object-fit: cover; border-radius: 4px; margin-right: 8px; vertical-align: middle;">` : 
        '<span style="display: inline-block; width: 20px; height: 20px; background: #e9ecef; border-radius: 4px; margin-right: 8px; vertical-align: middle; text-align: center; line-height: 20px; font-size: 12px; color: #6c757d;">?</span>';
        
    modalTitle.innerHTML = `${iconHtml}Manage Team: ${teamName}`;
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