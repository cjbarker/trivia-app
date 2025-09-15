document.addEventListener('DOMContentLoaded', function() {
    checkPlayerStatus();
    loadTeams();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('create-team-form').addEventListener('submit', createTeam);
    document.getElementById('join-team-form').addEventListener('submit', joinTeam);
    document.getElementById('cancel-join').addEventListener('click', cancelJoin);
    document.getElementById('leave-team').addEventListener('click', leaveTeam);
}

async function loadTeams() {
    try {
        const response = await fetch('/api/teams');
        const teams = await response.json();
        displayTeams(teams);
    } catch (error) {
        console.error('Error loading teams:', error);
    }
}

function displayTeams(teams) {
    const teamsList = document.getElementById('teams-list');
    
    if (teams.length === 0) {
        teamsList.innerHTML = '<p>No teams created yet. Be the first to create one!</p>';
        return;
    }
    
    teamsList.innerHTML = teams.map(team => `
        <div class="team-item" onclick="selectTeam('${team.id}', '${team.name}')">
            <div class="team-name">${team.name}</div>
            <div class="team-info">${team.player_count} player(s): ${team.players.join(', ')}</div>
        </div>
    `).join('');
}

function selectTeam(teamId, teamName) {
    // Remove previous selections
    document.querySelectorAll('.team-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Select current team
    event.target.closest('.team-item').classList.add('selected');
    
    // Show join form
    document.getElementById('selected-team-id').value = teamId;
    document.getElementById('selected-team-name').textContent = `Join team: ${teamName}`;
    document.getElementById('join-team-section').style.display = 'block';
}

function cancelJoin() {
    document.getElementById('join-team-section').style.display = 'none';
    document.querySelectorAll('.team-item').forEach(item => {
        item.classList.remove('selected');
    });
}

async function createTeam(event) {
    event.preventDefault();
    
    const teamName = document.getElementById('new-team-name').value;
    const playerName = document.getElementById('new-player-name').value;
    
    try {
        const response = await fetch('/api/teams', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                team_name: teamName,
                player_name: playerName
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = '/game';
        } else {
            alert('Error creating team');
        }
    } catch (error) {
        console.error('Error creating team:', error);
        alert('Error creating team');
    }
}

async function joinTeam(event) {
    event.preventDefault();
    
    const teamId = document.getElementById('selected-team-id').value;
    const playerName = document.getElementById('join-player-name').value;
    
    try {
        const response = await fetch(`/api/teams/${teamId}/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                player_name: playerName
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = '/game';
        } else {
            alert('Error joining team: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error joining team:', error);
        alert('Error joining team');
    }
}

async function checkPlayerStatus() {
    try {
        const response = await fetch('/api/player/status');
        const status = await response.json();
        
        if (status.has_team) {
            showCurrentTeamStatus(status);
        } else {
            showTeamSelection();
        }
    } catch (error) {
        console.error('Error checking player status:', error);
        showTeamSelection();
    }
}

function showCurrentTeamStatus(status) {
    document.getElementById('current-team-name').textContent = status.team_name;
    document.getElementById('current-player-name').textContent = status.player_name;
    document.getElementById('current-teammates').textContent = 
        status.teammates.length > 0 ? status.teammates.join(', ') : 'None';
    
    document.getElementById('current-team-status').style.display = 'block';
    document.getElementById('team-selection').style.display = 'none';
}

function showTeamSelection() {
    document.getElementById('current-team-status').style.display = 'none';
    document.getElementById('team-selection').style.display = 'block';
}

async function leaveTeam() {
    if (!confirm('Are you sure you want to leave your current team?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/teams/leave', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showTeamSelection();
            loadTeams(); // Refresh the teams list
        } else {
            alert('Error leaving team: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error leaving team:', error);
        alert('Error leaving team');
    }
}