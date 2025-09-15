import requests
import json

BASE_URL = 'http://localhost:5001'

def test_team_management():
    print("Testing admin team management functionality...")
    
    # Setup admin session
    admin_session = requests.Session()
    admin_response = admin_session.post(f'{BASE_URL}/admin/login', 
                                      data={'password': 'admin123'}, 
                                      allow_redirects=False)
    assert admin_response.status_code == 302, "Admin login failed"
    print("✓ Admin logged in")
    
    # Create initial teams for testing
    team_session1 = requests.Session()
    team_session2 = requests.Session()
    
    # Create first team
    team1_response = team_session1.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Original Team 1',
        'player_name': 'Player A'
    })
    assert team1_response.json().get('success'), "Failed to create team 1"
    team1_id = team1_response.json()['team_id']
    print("✓ Created Team 1")
    
    # Add another player to team 1
    team_session1.post(f'{BASE_URL}/api/teams/{team1_id}/join', json={
        'player_name': 'Player B'
    })
    print("✓ Added Player B to Team 1")
    
    # Create second team
    team2_response = team_session2.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Original Team 2',
        'player_name': 'Player C'
    })
    assert team2_response.json().get('success'), "Failed to create team 2"
    team2_id = team2_response.json()['team_id']
    print("✓ Created Team 2")
    
    # Test 1: Update team name
    print("\n=== Test 1: Update Team Name ===")
    update_name_response = admin_session.put(f'{BASE_URL}/admin/api/teams/{team1_id}/name',
                                           json={'name': 'Updated Team 1'})
    result = update_name_response.json()
    assert result.get('success'), f"Team name update failed: {result}"
    print("✓ Team name updated successfully")
    
    # Verify name change
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    team1 = next((t for t in teams if t['id'] == team1_id), None)
    assert team1 and team1['name'] == 'Updated Team 1', "Team name not updated"
    print("✓ Team name change verified")
    
    # Test 2: Add player to existing team
    print("\n=== Test 2: Add Player to Team ===")
    add_player_response = admin_session.post(f'{BASE_URL}/admin/api/teams/{team1_id}/players',
                                           json={'player_name': 'Player D'})
    result = add_player_response.json()
    assert result.get('success'), f"Add player failed: {result}"
    print("✓ Player D added to team")
    
    # Verify player added
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    team1 = next((t for t in teams if t['id'] == team1_id), None)
    assert team1 and 'Player D' in team1['players'], "Player D not found in team"
    print("✓ Player addition verified")
    
    # Test 3: Move player between teams
    print("\n=== Test 3: Move Player Between Teams ===")
    move_player_response = admin_session.post(f'{BASE_URL}/admin/api/teams/{team2_id}/players',
                                            json={'player_name': 'Player B'})
    result = move_player_response.json()
    assert result.get('success'), f"Move player failed: {result}"
    print("✓ Player B moved to Team 2")
    
    # Verify player moved
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    team1 = next((t for t in teams if t['id'] == team1_id), None)
    team2 = next((t for t in teams if t['id'] == team2_id), None)
    
    assert team1 and 'Player B' not in team1['players'], "Player B still in Team 1"
    assert team2 and 'Player B' in team2['players'], "Player B not in Team 2"
    print("✓ Player move verified")
    
    # Test 4: Remove player from team
    print("\n=== Test 4: Remove Player from Team ===")
    remove_player_response = admin_session.delete(f'{BASE_URL}/admin/api/teams/{team1_id}/players/Player%20A')
    result = remove_player_response.json()
    assert result.get('success'), f"Remove player failed: {result}"
    print("✓ Player A removed from team")
    
    # Verify player removed
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    team1 = next((t for t in teams if t['id'] == team1_id), None)
    assert team1 and 'Player A' not in team1['players'], "Player A still in team"
    print("✓ Player removal verified")
    
    # Test 5: Remove remaining players (should delete team)
    print("\n=== Test 5: Remove Remaining Players (Delete Team) ===")
    
    # Check current state of team1
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    team1 = next((t for t in teams if t['id'] == team1_id), None)
    
    if team1 and team1['players']:
        print(f"Team 1 has players: {team1['players']}")
        # Remove remaining players one by one
        for player in team1['players'][:]:  # Create copy of list to iterate safely
            remove_response = admin_session.delete(f'{BASE_URL}/admin/api/teams/{team1_id}/players/{player}')
            result = remove_response.json()
            if result.get('success'):
                print(f"✓ Removed player {player}")
            else:
                print(f"Failed to remove player {player}: {result}")
    else:
        print("Team 1 has no players or was already deleted")
    
    # Verify team deleted
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    team1 = next((t for t in teams if t['id'] == team1_id), None)
    assert team1 is None, "Team 1 should be deleted"
    print("✓ Empty team deletion verified")
    
    # Test 6: Delete entire team
    print("\n=== Test 6: Delete Entire Team ===")
    delete_team_response = admin_session.delete(f'{BASE_URL}/admin/api/teams/{team2_id}')
    result = delete_team_response.json()
    assert result.get('success'), f"Delete team failed: {result}"
    print("✓ Team 2 deleted successfully")
    
    # Verify team deleted
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    team2 = next((t for t in teams if t['id'] == team2_id), None)
    assert team2 is None, "Team 2 should be deleted"
    print("✓ Team deletion verified")
    
    # Test 7: Error handling
    print("\n=== Test 7: Error Handling ===")
    
    # Try to update non-existent team
    error_response = admin_session.put(f'{BASE_URL}/admin/api/teams/fake-id/name',
                                     json={'name': 'New Name'})
    result = error_response.json()
    assert not result.get('success'), "Should fail for non-existent team"
    print("✓ Non-existent team update correctly failed")
    
    # Try to add player with empty name
    team_session3 = requests.Session()
    team3_response = team_session3.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Test Team 3',
        'player_name': 'Player E'
    })
    team3_id = team3_response.json()['team_id']
    
    empty_name_response = admin_session.post(f'{BASE_URL}/admin/api/teams/{team3_id}/players',
                                           json={'player_name': ''})
    result = empty_name_response.json()
    assert not result.get('success'), "Should fail for empty player name"
    print("✓ Empty player name correctly rejected")
    
    return True

if __name__ == '__main__':
    try:
        success = test_team_management()
        if success:
            print("\n✅ All team management tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()