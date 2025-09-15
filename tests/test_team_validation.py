import requests
import json

BASE_URL = 'http://localhost:5001'

def test_team_validation():
    print("Testing team validation functionality...")
    
    # Test 1: Try to access game page without team membership
    print("\n=== Test 1: Access game without team ===")
    session = requests.Session()
    response = session.get(f'{BASE_URL}/game', allow_redirects=False)
    
    if response.status_code == 302 and response.headers.get('Location', '').endswith('/'):
        print("✓ Redirected to home page when no team membership")
    else:
        print(f"❌ Expected redirect but got status {response.status_code}")
        return False
    
    # Test 2: Create a team and verify access works
    print("\n=== Test 2: Create team and access game ===")
    team_response = session.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Test Team',
        'player_name': 'Test Player'
    })
    
    if team_response.json().get('success'):
        print("✓ Team created successfully")
        
        # Now try accessing game page - should work
        game_response = session.get(f'{BASE_URL}/game', allow_redirects=False)
        if game_response.status_code == 200:
            print("✓ Game page accessible with valid team")
        else:
            print(f"❌ Expected 200 but got {game_response.status_code}")
            return False
    else:
        print("❌ Failed to create team")
        return False
    
    # Test 3: Check player status API
    print("\n=== Test 3: Player status validation ===")
    status_response = session.get(f'{BASE_URL}/api/player/status')
    status = status_response.json()
    
    if status.get('has_team') and status.get('team_name') == 'Test Team':
        print("✓ Player status shows valid team membership")
    else:
        print(f"❌ Player status invalid: {status}")
        return False
    
    # Test 4: Try to submit answer (should work)
    print("\n=== Test 4: Submit answer with valid team ===")
    answer_response = session.post(f'{BASE_URL}/api/answer', 
                                 json={'answer': 'test answer'},
                                 allow_redirects=False)
    
    # This might fail due to game logic, but should not redirect
    if answer_response.status_code != 302:
        print("✓ Answer submission handled (not redirected)")
    else:
        print("❌ Answer submission redirected (team validation failed)")
        return False
    
    # Test 5: Simulate team deletion and check validation
    print("\n=== Test 5: Simulate team deletion ===")
    # We'll manually clear the team from the game object
    # This simulates what happens when admin or system deletes teams
    
    # Leave team to simulate deletion
    leave_response = session.post(f'{BASE_URL}/api/teams/leave')
    if leave_response.json().get('success'):
        print("✓ Left team successfully")
        
        # Now try to access game page - should redirect
        game_response2 = session.get(f'{BASE_URL}/game', allow_redirects=False)
        if game_response2.status_code == 302:
            print("✓ Redirected after team membership lost")
        else:
            print(f"❌ Expected redirect but got {game_response2.status_code}")
            return False
        
        # Check player status - should show no team
        status_response2 = session.get(f'{BASE_URL}/api/player/status')
        status2 = status_response2.json()
        
        if not status2.get('has_team'):
            print("✓ Player status correctly shows no team")
        else:
            print(f"❌ Player status still shows team: {status2}")
            return False
    else:
        print("❌ Failed to leave team")
        return False
    
    return True

def test_multiple_sessions():
    print("\n=== Test 6: Multiple session validation ===")
    
    # Create two sessions with same player name
    session1 = requests.Session()
    session2 = requests.Session()
    
    # Create team in session1
    team1_response = session1.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Session1 Team',
        'player_name': 'MultiSessionPlayer'
    })
    
    if not team1_response.json().get('success'):
        print("❌ Failed to create team in session1")
        return False
    
    # Create another team with same player in session2
    team2_response = session2.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Session2 Team', 
        'player_name': 'MultiSessionPlayer'
    })
    
    if not team2_response.json().get('success'):
        print("❌ Failed to create team in session2")
        return False
    
    print("✓ Created teams in both sessions with same player")
    
    # Check status in session1 - should be invalid now
    status1 = session1.get(f'{BASE_URL}/api/player/status').json()
    if not status1.get('has_team'):
        print("✓ Session1 correctly invalidated after player moved")
    else:
        print(f"❌ Session1 still shows team: {status1}")
        return False
    
    # Check status in session2 - should be valid
    status2 = session2.get(f'{BASE_URL}/api/player/status').json()
    if status2.get('has_team') and status2.get('team_name') == 'Session2 Team':
        print("✓ Session2 shows valid team membership")
    else:
        print(f"❌ Session2 invalid status: {status2}")
        return False
    
    return True

if __name__ == '__main__':
    try:
        success1 = test_team_validation()
        success2 = test_multiple_sessions()
        
        if success1 and success2:
            print("\n✅ All team validation tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()