import requests
import json

BASE_URL = 'http://localhost:5001'

def test_answer_restrictions():
    print("Testing answer submission restrictions...")
    
    # Setup
    team_session = requests.Session()
    admin_session = requests.Session()
    
    # Admin login
    admin_response = admin_session.post(f'{BASE_URL}/admin/login', 
                                      data={'password': 'admin123'}, 
                                      allow_redirects=False)
    assert admin_response.status_code == 302, "Admin login failed"
    print("✓ Admin logged in")
    
    # Start game
    admin_session.post(f'{BASE_URL}/admin/api/game/start')
    print("✓ Game started")
    
    # Create team
    team_response = team_session.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Answer Test Team',
        'player_name': 'Test Player'
    })
    assert team_response.json().get('success'), "Failed to create team"
    print("✓ Team created")
    
    # Test 1: First answer submission should work
    print("\n=== Test 1: First answer submission ===")
    answer_response1 = team_session.post(f'{BASE_URL}/api/answer', 
                                        json={'answer': 'first answer'})
    result1 = answer_response1.json()
    assert result1.get('success'), f"First answer failed: {result1}"
    print("✓ First answer submitted successfully")
    
    # Test 2: Second answer submission to same question should fail
    print("\n=== Test 2: Duplicate answer submission ===")
    answer_response2 = team_session.post(f'{BASE_URL}/api/answer', 
                                        json={'answer': 'second answer'})
    result2 = answer_response2.json()
    assert not result2.get('success'), f"Second answer should fail: {result2}"
    assert 'already answered' in result2.get('error', '').lower(), f"Wrong error message: {result2}"
    print("✓ Second answer correctly rejected")
    
    # Test 3: Get current question should show answer status
    print("\n=== Test 3: Question status shows answered ===")
    question_response = team_session.get(f'{BASE_URL}/api/question')
    question_data = question_response.json()
    assert question_data.get('already_answered') == True, f"Question should show answered: {question_data}"
    assert question_data.get('submitted_answer') == 'first answer', f"Should show submitted answer: {question_data}"
    print("✓ Question correctly shows as answered with submitted answer")
    
    # Test 4: Move to next question via admin
    print("\n=== Test 4: Move to next question ===")
    admin_response = admin_session.post(f'{BASE_URL}/admin/api/next_question')
    assert admin_response.json().get('success'), "Failed to advance question"
    print("✓ Advanced to next question")
    
    # Test 5: New question should allow answers
    print("\n=== Test 5: New question allows answers ===")
    question_response2 = team_session.get(f'{BASE_URL}/api/question')
    question_data2 = question_response2.json()
    assert question_data2.get('already_answered') != True, f"New question should not be answered: {question_data2}"
    print("✓ New question shows as unanswered")
    
    answer_response3 = team_session.post(f'{BASE_URL}/api/answer', 
                                        json={'answer': 'answer to question 2'})
    result3 = answer_response3.json()
    assert result3.get('success'), f"Answer to new question failed: {result3}"
    print("✓ Answer to new question submitted successfully")
    
    # Test 6: Go back to previous question via admin
    print("\n=== Test 6: Go back to answered question ===")
    set_response = admin_session.post(f'{BASE_URL}/admin/api/set_question', 
                                     json={'question_number': 1})
    assert set_response.json().get('success'), "Failed to set question"
    print("✓ Set back to question 1")
    
    # Test 7: Previous question should show as answered
    print("\n=== Test 7: Previous question shows answered ===")
    question_response3 = team_session.get(f'{BASE_URL}/api/question')
    question_data3 = question_response3.json()
    assert question_data3.get('already_answered') == True, f"Previous question should show answered: {question_data3}"
    assert question_data3.get('submitted_answer') == 'first answer', f"Should show original answer: {question_data3}"
    print("✓ Previous question correctly shows as answered with original answer")
    
    # Test 8: Cannot submit new answer to previous question
    print("\n=== Test 8: Cannot resubmit to previous question ===")
    answer_response4 = team_session.post(f'{BASE_URL}/api/answer', 
                                        json={'answer': 'trying to change answer'})
    result4 = answer_response4.json()
    assert not result4.get('success'), f"Should not allow answer change: {result4}"
    assert 'already answered' in result4.get('error', '').lower(), f"Wrong error message: {result4}"
    print("✓ Cannot change answer to previous question")
    
    return True

if __name__ == '__main__':
    try:
        success = test_answer_restrictions()
        if success:
            print("\n✅ All answer restriction tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()