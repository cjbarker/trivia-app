const socket = io();
let currentQuestion = null;
let selectedAnswer = null;

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
    });
    socket.on('game_status_update', updateGameStatus);
    socket.on('game_stopped', function(data) {
        showGameStopped(data.scoreboard);
    });
    socket.on('game_paused', function(data) {
        showGamePaused(data.message);
    });
    socket.on('game_resumed', function(data) {
        hideGameStatus();
        if (currentQuestion) {
            displayQuestion(currentQuestion);
            document.getElementById('question-section').style.display = 'block';
            document.getElementById('answer-result').style.display = 'none';
        }
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
            teamInfo.textContent = `${status.team_name} - ${status.player_name}`;
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
        statusElement.textContent = 'Correct!';
        statusElement.className = 'correct';
    } else {
        statusElement.textContent = 'Incorrect';
        statusElement.className = 'incorrect';
        correctAnswerElement.textContent = `Correct answer: ${result.correct_answer}`;
    }
    
    teamScoreElement.textContent = `Your team score: ${result.team_score}`;
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
    
    scoreboardList.innerHTML = scoreboard.map((team, index) => `
        <div class="score-item">
            <div class="team-details">
                <div class="team-name">${team.team_name}</div>
                <div class="players-list">${team.players.join(', ')}</div>
            </div>
            <div class="team-score">${team.score} points</div>
        </div>
    `).join('');
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