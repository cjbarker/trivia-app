import requests

BASE_URL = 'http://localhost:5001'

def test_basic_team_validation():
    print("Testing basic team validation...")
    
    session = requests.Session()
    
    # Test 1: Access game without team should redirect
    print("1. Testing access without team...")
    response = session.get(f'{BASE_URL}/game', allow_redirects=False)
    assert response.status_code == 302, f"Expected redirect but got {response.status_code}"
    print("   ✓ Redirected to home when no team")
    
    # Test 2: Create team and verify access
    print("2. Creating team and testing access...")
    team_response = session.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Validation Test Team',
        'player_name': 'Validation Player'
    })
    assert team_response.json().get('success'), "Failed to create team"
    print("   ✓ Team created successfully")
    
    # Now access should work
    game_response = session.get(f'{BASE_URL}/game', allow_redirects=False)
    assert game_response.status_code == 200, f"Expected 200 but got {game_response.status_code}"
    print("   ✓ Game page accessible with valid team")
    
    # Test 3: Verify player status API works
    print("3. Testing player status validation...")
    status_response = session.get(f'{BASE_URL}/api/player/status')
    status = status_response.json()
    assert status.get('has_team') == True, f"Player should have team: {status}"
    assert status.get('team_name') == 'Validation Test Team', f"Wrong team name: {status}"
    print("   ✓ Player status correctly shows team membership")
    
    # Test 4: Test answer submission (should not redirect)
    print("4. Testing answer submission with valid team...")
    answer_response = session.post(f'{BASE_URL}/api/answer', 
                                 json={'answer': 'test'}, 
                                 allow_redirects=False)
    # Should get a response, not a redirect (even if answer fails game logic)
    assert answer_response.status_code != 302, f"Answer submission redirected: {answer_response.status_code}"
    print("   ✓ Answer submission processed (not redirected)")
    
    # Test 5: Leave team and verify validation fails
    print("5. Testing validation after leaving team...")
    leave_response = session.post(f'{BASE_URL}/api/teams/leave')
    assert leave_response.json().get('success'), "Failed to leave team"
    print("   ✓ Left team successfully")
    
    # Now access should redirect again
    game_response2 = session.get(f'{BASE_URL}/game', allow_redirects=False)
    assert game_response2.status_code == 302, f"Expected redirect but got {game_response2.status_code}"
    print("   ✓ Redirected after losing team membership")
    
    # Player status should show no team
    status_response2 = session.get(f'{BASE_URL}/api/player/status')
    status2 = status_response2.json()
    assert status2.get('has_team') == False, f"Player should not have team: {status2}"
    print("   ✓ Player status correctly shows no team")
    
    return True

if __name__ == '__main__':
    try:
        success = test_basic_team_validation()
        if success:
            print("\n✅ All basic team validation tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()