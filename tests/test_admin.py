import requests
import json

BASE_URL = 'http://localhost:5001'

def test_admin_login():
    print("Testing admin login...")
    
    # Test invalid login
    response = requests.post(f'{BASE_URL}/admin/login', data={'password': 'wrong'})
    assert 'Invalid password' in response.text
    print("✓ Invalid login rejected")
    
    # Test valid login
    session = requests.Session()
    response = session.post(f'{BASE_URL}/admin/login', data={'password': 'admin123'}, allow_redirects=False)
    print(f"Login response status: {response.status_code}")
    assert response.status_code == 302  # Redirect after successful login
    print("✓ Valid login accepted")
    
    return session

def test_game_controls(session):
    print("\nTesting game controls...")
    
    # Get initial status
    response = session.get(f'{BASE_URL}/admin/api/status')
    status = response.json()
    print(f"Initial status: {status}")
    
    # Start game
    response = session.post(f'{BASE_URL}/admin/api/game/start')
    result = response.json()
    assert result['success'] == True
    print("✓ Game started successfully")
    
    # Check status after start
    response = session.get(f'{BASE_URL}/admin/api/status')
    status = response.json()
    assert status['started'] == True
    print("✓ Game status shows started")
    
    # Pause game
    response = session.post(f'{BASE_URL}/admin/api/game/pause')
    result = response.json()
    assert result['success'] == True
    print("✓ Game paused successfully")
    
    # Resume game
    response = session.post(f'{BASE_URL}/admin/api/game/resume')
    result = response.json()
    assert result['success'] == True
    print("✓ Game resumed successfully")
    
    # Stop game
    response = session.post(f'{BASE_URL}/admin/api/game/stop')
    result = response.json()
    assert result['success'] == True
    print("✓ Game stopped successfully")
    
    # Check final status
    response = session.get(f'{BASE_URL}/admin/api/status')
    status = response.json()
    assert status['started'] == False
    print("✓ Game status shows stopped")

def test_question_controls(session):
    print("\nTesting question controls...")
    
    # Start game first
    session.post(f'{BASE_URL}/admin/api/game/start')
    
    # Set specific question
    response = session.post(f'{BASE_URL}/admin/api/set_question', 
                          json={'question_number': 2})
    result = response.json()
    assert result['success'] == True
    print("✓ Successfully set to question 2")
    
    # Advance to next question
    response = session.post(f'{BASE_URL}/admin/api/next_question')
    result = response.json()
    assert result['success'] == True
    print("✓ Successfully advanced to next question")

if __name__ == '__main__':
    try:
        # Test admin functionality
        session = test_admin_login()
        test_game_controls(session)
        test_question_controls(session)
        
        print("\n✅ All admin functionality tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()