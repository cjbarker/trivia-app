const socket = io();
let currentQuestion = null;
let selectedAnswer = null;

document.addEventListener('DOMContentLoaded', function() {
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
    });
}

async function loadCurrentQuestion() {
    try {
        const response = await fetch('/api/question');
        const question = await response.json();
        
        if (question) {
            currentQuestion = question;
            displayQuestion(question);
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
        blankAnswer.focus();
        
        submitBtn.disabled = true;
    }
    
    selectedAnswer = null;
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