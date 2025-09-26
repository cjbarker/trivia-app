const socket = io();
let currentQuestion = null;
let selectedAnswer = null;
let timerInterval = null;
let currentTimer = null;

document.addEventListener('DOMContentLoaded', function() {
    checkTeamStatus();
    loadCurrentQuestion();
    loadScoreboard();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('submit-answer').addEventListener('click', submitAnswer);
    document.getElementById('blank-answer').addEventListener('input', function() {
        const submitBtn = document.getElementById('submit-answer');
        submitBtn.disabled = this.value.trim() === '';
    });
    
    // Socket event listeners
    socket.on('score_update', updateScoreboard);
    socket.on('new_question', function(question) {
        currentQuestion = question;
        displayQuestion(question);
        document.getElementById('answer-result').style.display = 'none';
        document.getElementById('question-section').style.display = 'block';
        updateGameStatus(question);
        // Start timer for new question
        if (question.timer) {
            startTimer(question.timer);
        }
    });
    socket.on('game_status_update', updateGameStatus);
    socket.on('game_stopped', function(data) {
        showGameStopped(data.scoreboard);
        stopTimer();
    });
    socket.on('game_paused', function(data) {
        showGamePaused(data.message);
        pauseTimer();
    });
    socket.on('game_resumed', function(data) {
        hideGameStatus();
        if (currentQuestion) {
            displayQuestion(currentQuestion);
            document.getElementById('question-section').style.display = 'block';
            document.getElementById('answer-result').style.display = 'none';
        }
        resumeTimer();
    });
    
    // Timer-specific socket events
    socket.on('timer_update', function(data) {
        updateTimer(data.time_remaining, data.bonus_points, data.expired);
    });
    
    socket.on('timer_expired', function() {
        onTimerExpired();
    });
}

async function checkTeamStatus() {
    try {
        const response = await fetch('/api/player/status');
        const status = await response.json();
        
        if (!status.has_team) {
            // Team no longer exists or player not in team, redirect to home
            window.location.href = '/';
            return;
        }
        
        // Update team info display if available
        const teamInfo = document.getElementById('team-info');
        if (teamInfo) {
            const iconHtml = status.team_icon ? 
                `<img class="team-icon-small" src="${status.team_icon}" alt="${status.team_name} icon" style="width: 20px; height: 20px; object-fit: cover; border-radius: 4px; margin-right: 8px; vertical-align: middle;">` : 
                '<span class="team-icon-placeholder-small" style="display: inline-block; width: 20px; height: 20px; background: #e9ecef; border-radius: 4px; margin-right: 8px; vertical-align: middle; text-align: center; line-height: 20px; font-size: 12px; color: #6c757d;">?</span>';
            teamInfo.innerHTML = `${iconHtml}${status.team_name} - ${status.player_name}`;
        }
        
    } catch (error) {
        console.error('Error checking team status:', error);
        // On error, redirect to home to be safe
        window.location.href = '/';
    }
}

async function loadCurrentQuestion() {
    try {
        const response = await fetch('/api/question');
        const question = await response.json();
        
        if (question) {
            currentQuestion = question;
            displayQuestion(question);
            updateGameStatus(question);
            // Initialize timer if game is started
            if (question.game_started && !question.game_paused && question.timer) {
                startTimer(question.timer);
            }
        } else {
            document.getElementById('question-text').textContent = 'No more questions available.';
        }
    } catch (error) {
        console.error('Error loading question:', error);
    }
}

function displayQuestion(question) {
    document.getElementById('question-counter').textContent = 
        `Question ${question.question_number} of ${question.total_questions}`;
    document.getElementById('question-text').textContent = question.question_text;
    
    const multipleChoiceDiv = document.getElementById('multiple-choice-options');
    const fillInBlankDiv = document.getElementById('fill-in-blank');
    const submitBtn = document.getElementById('submit-answer');
    
    // Reset submit button visibility and enable form elements
    submitBtn.style.display = 'block';
    submitBtn.disabled = true;
    
    // Check if question has already been answered
    if (question.already_answered) {
        displayAnsweredQuestion(question);
        return;
    }
    
    if (question.question_type === 'multiple_choice') {
        multipleChoiceDiv.style.display = 'block';
        fillInBlankDiv.style.display = 'none';
        
        const optionsDiv = multipleChoiceDiv.querySelector('.options');
        optionsDiv.innerHTML = question.options.map((option, index) => `
            <div class="option" onclick="selectOption(${index}, '${option.replace(/'/g, "\\'")}')">
                ${String.fromCharCode(65 + index)}. ${option}
            </div>
        `).join('');
        
        submitBtn.disabled = true;
    } else {
        multipleChoiceDiv.style.display = 'none';
        fillInBlankDiv.style.display = 'block';
        
        const blankAnswer = document.getElementById('blank-answer');
        blankAnswer.value = '';
        blankAnswer.disabled = false;
        blankAnswer.style.opacity = '1';
        blankAnswer.focus();
        
        submitBtn.disabled = true;
    }
    
    selectedAnswer = null;
}

function displayAnsweredQuestion(question) {
    const multipleChoiceDiv = document.getElementById('multiple-choice-options');
    const fillInBlankDiv = document.getElementById('fill-in-blank');
    const submitBtn = document.getElementById('submit-answer');
    
    // Hide submit button for answered questions
    submitBtn.style.display = 'none';
    
    if (question.question_type === 'multiple_choice') {
        multipleChoiceDiv.style.display = 'block';
        fillInBlankDiv.style.display = 'none';
        
        const optionsDiv = multipleChoiceDiv.querySelector('.options');
        optionsDiv.innerHTML = question.options.map((option, index) => {
            const isSelected = option === question.submitted_answer;
            return `
                <div class="option answered ${isSelected ? 'selected' : ''}" style="cursor: default; opacity: 0.7;">
                    ${String.fromCharCode(65 + index)}. ${option}
                    ${isSelected ? ' ← Your Answer' : ''}
                </div>
            `;
        }).join('');
    } else {
        multipleChoiceDiv.style.display = 'none';
        fillInBlankDiv.style.display = 'block';
        
        const blankAnswer = document.getElementById('blank-answer');
        blankAnswer.value = question.submitted_answer || '';
        blankAnswer.disabled = true;
        blankAnswer.style.opacity = '0.7';
    }
    
    // Add a message indicating the question was already answered
    const questionText = document.getElementById('question-text');
    questionText.innerHTML = question.question_text + 
        '<br><small style="color: #666; font-style: italic;">This question has already been answered.</small>';
}

function selectOption(index, optionText) {
    // Remove previous selections
    document.querySelectorAll('.option').forEach(option => {
        option.classList.remove('selected');
    });
    
    // Select current option
    event.target.classList.add('selected');
    selectedAnswer = optionText;
    
    document.getElementById('submit-answer').disabled = false;
}

async function submitAnswer() {
    // Check if game is active
    if (!currentQuestion || !currentQuestion.game_started || currentQuestion.game_paused) {
        alert('Game is not currently active');
        return;
    }
    
    let answer;
    
    if (currentQuestion.question_type === 'multiple_choice') {
        answer = selectedAnswer;
    } else {
        answer = document.getElementById('blank-answer').value.trim();
    }
    
    if (!answer) {
        alert('Please provide an answer');
        return;
    }
    
    try {
        const response = await fetch('/api/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ answer: answer })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Stop timer when answer is submitted
            stopTimer();
            displayResult(result);
        } else {
            alert('Error submitting answer: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert('Error submitting answer');
    }
}

function displayResult(result) {
    document.getElementById('question-section').style.display = 'none';
    document.getElementById('answer-result').style.display = 'block';
    
    const statusElement = document.getElementById('result-status');
    const correctAnswerElement = document.getElementById('correct-answer-display');
    const teamScoreElement = document.getElementById('team-score');
    
    if (result.correct) {
        statusElement.innerHTML = `
            <span class="correct">Correct!</span>
            ${result.bonus_points > 0 ? `<span style="color: #28a745; font-size: 0.9em; display: block;">Bonus: +${result.bonus_points} points (${result.answer_time}s)</span>` : ''}
        `;
        statusElement.className = 'correct';
    } else {
        statusElement.textContent = 'Incorrect';
        statusElement.className = 'incorrect';
        correctAnswerElement.textContent = `Correct answer: ${result.correct_answer}`;
    }
    
    const pointsText = result.correct && result.points_earned > 1 ? 
        `+${result.points_earned} points (1 + ${result.bonus_points} bonus)` :
        result.correct ? '+1 point' : '0 points';
    
    teamScoreElement.innerHTML = `
        <strong>Points earned:</strong> ${pointsText}<br>
        <strong>Team score:</strong> ${result.team_score}
    `;
}

async function nextQuestion() {
    try {
        const response = await fetch('/api/next_question', {
            method: 'POST'
        });
        
        if (response.ok) {
            // The new question will be received via socket
        }
    } catch (error) {
        console.error('Error advancing to next question:', error);
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
                        ${iconHtml}${team.team_name}
                    </div>
                    <div class="players-list">${team.players.join(', ')}</div>
                </div>
                <div class="team-score">${team.score} points</div>
            </div>
        `;
    }).join('');
}

function updateGameStatus(data) {
    if (data && data.hasOwnProperty('game_started') && data.hasOwnProperty('game_paused')) {
        handleGameStatusChange(data.game_started, data.game_paused);
    }
}

function handleGameStatusChange(started, paused) {
    const questionSection = document.getElementById('question-section');
    const answerResult = document.getElementById('answer-result');
    
    if (!started || paused) {
        // Game is stopped or paused - disable interactions
        questionSection.style.display = 'none';
        answerResult.style.display = 'none';
        
        if (!started) {
            showGameStopped();
        } else if (paused) {
            showGamePaused();
        }
    } else {
        // Game is active - show current question
        hideGameStatus();
        if (currentQuestion) {
            displayQuestion(currentQuestion);
        }
    }
}

function showGameStopped(scoreboard = null) {
    const questionSection = document.getElementById('question-section');
    const answerResult = document.getElementById('answer-result');
    
    questionSection.style.display = 'none';
    answerResult.style.display = 'block';
    
    document.getElementById('result-status').innerHTML = `
        <h2 style="color: #dc3545;">Game Stopped</h2>
        <p>The trivia game has been stopped by the administrator.</p>
    `;
    document.getElementById('correct-answer-display').style.display = 'none';
    document.getElementById('team-score').style.display = 'none';
    document.getElementById('next-question').style.display = 'none';
    
    if (scoreboard) {
        loadScoreboard();
    }
}

function showGamePaused(customMessage = null) {
    const questionSection = document.getElementById('question-section');
    const answerResult = document.getElementById('answer-result');
    
    questionSection.style.display = 'none';
    answerResult.style.display = 'block';
    
    const message = customMessage || 'The trivia game has been paused. Please wait for the administrator to resume.';
    
    document.getElementById('result-status').innerHTML = `
        <h2 style="color: #ffc107;">Game Paused</h2>
        <p>${message}</p>
    `;
    document.getElementById('correct-answer-display').style.display = 'none';
    document.getElementById('team-score').style.display = 'none';
    document.getElementById('next-question').style.display = 'none';
}

function hideGameStatus() {
    const resultStatus = document.getElementById('result-status');
    const correctAnswer = document.getElementById('correct-answer-display');
    const teamScore = document.getElementById('team-score');
    const nextButton = document.getElementById('next-question');
    
    resultStatus.innerHTML = '';
    correctAnswer.style.display = 'block';
    teamScore.style.display = 'block';
    nextButton.style.display = 'block';
}

// Timer Functions
function startTimer(timerData) {
    currentTimer = {
        timeRemaining: timerData.time_remaining || 60,
        bonusPoints: timerData.bonus_points || 6,
        totalTime: timerData.total_time || 60
    };
    
    // Show timer section
    document.getElementById('timer-section').style.display = 'block';
    
    // Clear any existing timer
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    
    // Start countdown
    updateTimerDisplay();
    timerInterval = setInterval(function() {
        if (currentTimer.timeRemaining > 0) {
            currentTimer.timeRemaining--;
            // Update bonus points based on remaining time
            const elapsed = currentTimer.totalTime - currentTimer.timeRemaining;
            currentTimer.bonusPoints = getBonusPointsForTime(elapsed);
            updateTimerDisplay();
        } else {
            onTimerExpired();
        }
    }, 1000);
}

function updateTimer(timeRemaining, bonusPoints, expired) {
    if (expired) {
        onTimerExpired();
        return;
    }
    
    currentTimer = {
        timeRemaining: timeRemaining,
        bonusPoints: bonusPoints,
        totalTime: currentTimer ? currentTimer.totalTime : 60
    };
    
    updateTimerDisplay();
}

function updateTimerDisplay() {
    if (!currentTimer) return;
    
    const timerSeconds = document.getElementById('timer-seconds');
    const bonusPoints = document.getElementById('bonus-points');
    const progressCircle = document.getElementById('timer-progress-circle');
    const bonusValue = document.querySelector('.bonus-value');
    
    // Update timer text
    timerSeconds.textContent = currentTimer.timeRemaining;
    bonusPoints.textContent = currentTimer.bonusPoints > 0 ? `+${currentTimer.bonusPoints}` : '0';
    
    // Update progress circle
    const totalTime = currentTimer.totalTime;
    const remaining = currentTimer.timeRemaining;
    const progress = (remaining / totalTime) * 283; // 283 is circumference
    progressCircle.style.strokeDashoffset = 283 - progress;
    
    // Update colors based on time remaining
    const progressBar = document.querySelector('.timer-progress-bar');
    const percentage = (remaining / totalTime) * 100;
    
    progressBar.classList.remove('warning', 'danger');
    bonusValue.classList.remove('warning', 'zero');
    
    if (percentage <= 20) {
        progressBar.classList.add('danger');
        bonusValue.classList.add('zero');
    } else if (percentage <= 50) {
        progressBar.classList.add('warning');
        bonusValue.classList.add('warning');
    }
}

function getBonusPointsForTime(elapsedSeconds) {
    // Start with 6 points, deduct 1 point every 10 seconds
    // 0-10s: 6 points, 10-20s: 5 points, 20-30s: 4 points, 30-40s: 3 points, 40-50s: 2 points, 50-60s: 1 point, 60s+: 0 points
    const points = 6 - Math.floor(elapsedSeconds / 10);
    return Math.max(0, points); // Ensure points never go below 0
}

function pauseTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function resumeTimer() {
    if (currentTimer && currentTimer.timeRemaining > 0) {
        startTimer(currentTimer);
    }
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    
    currentTimer = null;
    document.getElementById('timer-section').style.display = 'none';
}

function onTimerExpired() {
    stopTimer();
    
    // Show timer expired message but keep submission enabled
    const timerSection = document.getElementById('timer-section');
    if (timerSection) {
        timerSection.innerHTML = `
            <div class="timer-display" style="text-align: center; color: #dc3545;">
                <h3>⏰ Bonus Time Expired!</h3>
                <p>You can still submit answers, but no bonus points will be awarded.</p>
            </div>
        `;
    }
}