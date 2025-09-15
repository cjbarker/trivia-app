import requests
import json
import time

BASE_URL = 'http://localhost:5001'

def test_admin_question_display():
    print("Testing admin question display functionality...")
    
    # Setup admin session
    admin_session = requests.Session()
    admin_response = admin_session.post(f'{BASE_URL}/admin/login', 
                                      data={'password': 'admin123'}, 
                                      allow_redirects=False)
    assert admin_response.status_code == 302, "Admin login failed"
    print("✓ Admin logged in")
    
    # Create test teams
    team_session1 = requests.Session()
    team1_response = team_session1.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Test Team 1',
        'player_name': 'Alice'
    })
    assert team1_response.json().get('success'), "Failed to create team 1"
    team1_id = team1_response.json()['team_id']
    
    team_session2 = requests.Session()
    team2_response = team_session2.post(f'{BASE_URL}/api/teams', json={
        'team_name': 'Test Team 2', 
        'player_name': 'Bob'
    })
    assert team2_response.json().get('success'), "Failed to create team 2"
    team2_id = team2_response.json()['team_id']
    print("✓ Created test teams")
    
    # Test 1: Stop game if running and check status
    print("\n=== Test 1: Ensure Game is Stopped ===")
    # Stop game if it's running
    stop_response = admin_session.post(f'{BASE_URL}/admin/api/game/stop')
    print(f"Stop game result: {stop_response.json()}")
    
    time.sleep(0.5)
    
    status_response = admin_session.get(f'{BASE_URL}/admin/api/status')
    status = status_response.json()
    print(f"Status after stop: {status}")
    
    if not status['started']:
        assert 'question_details' not in status or not status['question_details'], "Should not have question details when stopped"
        print("✓ Game correctly stopped, no question details")
    else:
        print("⚠️  Game still running (may have been started by another test)")
    
    # Test 2: Start game and check status
    print("\n=== Test 2: Start Game and Check Status ===")
    start_response = admin_session.post(f'{BASE_URL}/admin/api/game/start')
    assert start_response.json().get('success'), "Failed to start game"
    
    time.sleep(0.5)  # Give time for status to update
    
    status_response = admin_session.get(f'{BASE_URL}/admin/api/status')
    status = status_response.json()
    print(f"Status after start: {json.dumps(status, indent=2)}")
    
    assert status['started'], "Game should be started"
    assert 'question_details' in status, "Should have question details after start"
    assert 'team_answers' in status, "Should have team answers data"
    assert 'answer_summary' in status, "Should have answer summary"
    
    question_details = status['question_details']
    print(f"✓ Current question: {question_details['question_text']}")
    print(f"✓ Question type: {question_details['question_type']}")
    print(f"✓ Correct answer: {question_details['correct_answer']}")
    
    # Test 3: Check team answer status (should be all waiting)
    print("\n=== Test 3: Team Answer Status (Waiting) ===")
    team_answers = status['team_answers']
    assert len(team_answers) == 2, "Should have 2 team answers"
    
    for team_answer in team_answers:
        assert not team_answer['has_answered'], f"Team {team_answer['team_name']} should not have answered yet"
        assert team_answer['submitted_answer'] is None, "Should not have submitted answer"
        assert team_answer['is_correct'] is None, "Should not have correctness status"
        print(f"✓ Team {team_answer['team_name']}: Waiting")
    
    # Check answer summary
    summary = status['answer_summary']
    assert summary['teams_answered'] == 0, "No teams should have answered"
    assert summary['teams_total'] == 2, "Should have 2 total teams"
    assert summary['correct_answers'] == 0, "No correct answers yet"
    assert summary['completion_percentage'] == 0, "Should be 0% complete"
    print("✓ Answer summary correct (0% complete)")
    
    # Test 4: Submit an answer and check status
    print("\n=== Test 4: Submit Answer and Check Status ===")
    # Submit correct answer from team 1
    if question_details['question_type'] == 'multiple_choice':
        answer = question_details['correct_answer']
    else:
        answer = question_details['correct_answer']
    
    answer_response = team_session1.post(f'{BASE_URL}/api/answer', 
                                       json={'answer': answer})
    assert answer_response.json().get('success'), "Failed to submit answer"
    print(f"✓ Team 1 submitted answer: {answer}")
    
    time.sleep(0.5)  # Give time for status to update
    
    # Check updated status
    status_response = admin_session.get(f'{BASE_URL}/admin/api/status')
    status = status_response.json()
    
    team_answers = status['team_answers']
    team1_answer = next(t for t in team_answers if t['team_name'] == 'Test Team 1')
    team2_answer = next(t for t in team_answers if t['team_name'] == 'Test Team 2')
    
    # Team 1 should have answered correctly
    assert team1_answer['has_answered'], "Team 1 should have answered"
    assert team1_answer['submitted_answer'] == answer, "Should have correct submitted answer"
    assert team1_answer['is_correct'], "Answer should be correct"
    print("✓ Team 1 status: Answered correctly")
    
    # Team 2 should still be waiting
    assert not team2_answer['has_answered'], "Team 2 should still be waiting"
    print("✓ Team 2 status: Still waiting")
    
    # Check updated summary
    summary = status['answer_summary']
    assert summary['teams_answered'] == 1, "Should have 1 team answered"
    assert summary['correct_answers'] == 1, "Should have 1 correct answer"
    assert summary['completion_percentage'] == 50, "Should be 50% complete"
    print("✓ Answer summary updated (50% complete)")
    
    # Test 5: Submit incorrect answer and check status
    print("\n=== Test 5: Submit Incorrect Answer ===")
    wrong_answer = "Wrong Answer"
    if question_details['question_type'] == 'multiple_choice' and question_details['options']:
        # Pick a wrong option
        options = question_details['options']
        correct = question_details['correct_answer']
        wrong_answer = next(opt for opt in options if opt != correct)
    
    answer_response = team_session2.post(f'{BASE_URL}/api/answer',
                                       json={'answer': wrong_answer})
    assert answer_response.json().get('success'), "Failed to submit answer"
    print(f"✓ Team 2 submitted wrong answer: {wrong_answer}")
    
    time.sleep(0.5)  # Give time for status to update
    
    # Check final status
    status_response = admin_session.get(f'{BASE_URL}/admin/api/status')
    status = status_response.json()
    
    team_answers = status['team_answers']
    team2_answer = next(t for t in team_answers if t['team_name'] == 'Test Team 2')
    
    assert team2_answer['has_answered'], "Team 2 should have answered"
    assert team2_answer['submitted_answer'] == wrong_answer, "Should have wrong submitted answer"
    assert not team2_answer['is_correct'], "Answer should be incorrect"
    print("✓ Team 2 status: Answered incorrectly")
    
    # Check final summary
    summary = status['answer_summary']
    assert summary['teams_answered'] == 2, "Should have 2 teams answered"
    assert summary['correct_answers'] == 1, "Should still have 1 correct answer"
    assert summary['completion_percentage'] == 100, "Should be 100% complete"
    print("✓ Final answer summary (100% complete)")
    
    print("\n✅ All admin question display tests passed!")
    return True

if __name__ == '__main__':
    try:
        success = test_admin_question_display()
        if success:
            print("\n🎉 Admin question display functionality working correctly!")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()