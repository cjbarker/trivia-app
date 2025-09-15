import requests
import json

BASE_URL = 'http://localhost:5001'

def test_simple_team_management():
    print("Testing basic team management functionality...")
    
    # Setup admin session
    admin_session = requests.Session()
    admin_response = admin_session.post(f'{BASE_URL}/admin/login', 
                                      data={'password': 'admin123'}, 
                                      allow_redirects=False)
    assert admin_response.status_code == 302, "Admin login failed"
    print("✓ Admin logged in")
    
    # Create a test team
    team_session = requests.Session()
    team_response = team_session.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Test Team',
        'player_name': 'Player 1'
    })
    assert team_response.json().get('success'), "Failed to create team"
    team_id = team_response.json()['team_id']
    print("✓ Created test team")
    
    # Test 1: Update team name
    print("\n=== Test 1: Update Team Name ===")
    update_response = admin_session.put(f'{BASE_URL}/admin/api/teams/{team_id}/name',
                                       json={'name': 'Updated Team Name'})
    result = update_response.json()
    print(f"Update result: {result}")
    assert result.get('success'), f"Team name update failed: {result}"
    print("✓ Team name updated")
    
    # Test 2: Add player to team
    print("\n=== Test 2: Add Player ===")
    add_response = admin_session.post(f'{BASE_URL}/admin/api/teams/{team_id}/players',
                                     json={'player_name': 'Player 2'})
    result = add_response.json()
    print(f"Add player result: {result}")
    assert result.get('success'), f"Add player failed: {result}"
    print("✓ Player added")
    
    # Test 3: Check current team state
    print("\n=== Test 3: Check Team State ===")
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    print(f"Current teams: {teams}")
    
    current_team = next((t for t in teams if t['id'] == team_id), None)
    if current_team:
        print(f"Current team state: {current_team}")
        print(f"Team players: {current_team['players']}")
    else:
        print("❌ Team not found!")
        return False
    
    # Test 4: Remove one player
    print("\n=== Test 4: Remove Player ===")
    if len(current_team['players']) > 1:
        player_to_remove = current_team['players'][0]
        remove_response = admin_session.delete(f'{BASE_URL}/admin/api/teams/{team_id}/players/{player_to_remove}')
        result = remove_response.json()
        print(f"Remove player result: {result}")
        assert result.get('success'), f"Remove player failed: {result}"
        print(f"✓ Removed player {player_to_remove}")
    
    # Test 5: Check team state after removal
    print("\n=== Test 5: Check Team State After Removal ===")
    teams_response = admin_session.get(f'{BASE_URL}/api/teams')
    teams = teams_response.json()
    current_team = next((t for t in teams if t['id'] == team_id), None)
    
    if current_team:
        print(f"Team after removal: {current_team}")
        print(f"Remaining players: {current_team['players']}")
    else:
        print("Team was deleted (expected if no players left)")
    
    # Test 6: Delete team if it still exists
    if current_team:
        print("\n=== Test 6: Delete Team ===")
        delete_response = admin_session.delete(f'{BASE_URL}/admin/api/teams/{team_id}')
        result = delete_response.json()
        print(f"Delete team result: {result}")
        assert result.get('success'), f"Delete team failed: {result}"
        print("✓ Team deleted")
    
    return True

if __name__ == '__main__':
    try:
        success = test_simple_team_management()
        if success:
            print("\n✅ Basic team management tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()