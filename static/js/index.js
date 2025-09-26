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
    
    // Set up icon upload functionality
    document.getElementById('team-icon-upload').addEventListener('change', handleIconUpload);
    document.getElementById('remove-icon').addEventListener('click', removeIcon);
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
            <div class="team-header">
                ${team.icon ? `<img class="team-icon" src="${team.icon}" alt="${team.name} icon">` : '<div class="team-icon-placeholder"></div>'}
                <div class="team-name">${team.name}</div>
            </div>
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
    const iconPreviewImg = document.getElementById('icon-preview-image');
    const teamIcon = iconPreviewImg.src && iconPreviewImg.src.startsWith('data:') ? iconPreviewImg.src : null;
    
    try {
        const response = await fetch('/api/teams', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                team_name: teamName,
                player_name: playerName,
                team_icon: teamIcon
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = '/game';
        } else {
            alert('Error creating team: ' + (result.error || 'Unknown error'));
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
    const teamNameElement = document.getElementById('current-team-name');
    
    // Create team name with icon
    const iconHtml = status.team_icon ? 
        `<img class="team-icon-small" src="${status.team_icon}" alt="${status.team_name} icon" style="width: 24px; height: 24px; object-fit: cover; border-radius: 4px; margin-right: 8px; vertical-align: middle;">` : 
        '<span class="team-icon-placeholder-small" style="display: inline-block; width: 24px; height: 24px; background: #e9ecef; border-radius: 4px; margin-right: 8px; vertical-align: middle; text-align: center; line-height: 24px; font-size: 14px; color: #6c757d;">?</span>';
    
    teamNameElement.innerHTML = `${iconHtml}${status.team_name}`;
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

function handleIconUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file.');
        event.target.value = '';
        return;
    }
    
    // Validate file size (max 2MB)
    const maxSize = 2 * 1024 * 1024; // 2MB
    if (file.size > maxSize) {
        alert('Image file size must be less than 2MB.');
        event.target.value = '';
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const iconPreview = document.getElementById('icon-preview');
        const iconPreviewImage = document.getElementById('icon-preview-image');
        
        iconPreviewImage.src = e.target.result;
        iconPreview.style.display = 'block';
    };
    reader.readAsDataURL(file);
}

function removeIcon() {
    const iconUpload = document.getElementById('team-icon-upload');
    const iconPreview = document.getElementById('icon-preview');
    const iconPreviewImage = document.getElementById('icon-preview-image');
    
    iconUpload.value = '';
    iconPreviewImage.src = '';
    iconPreview.style.display = 'none';
}