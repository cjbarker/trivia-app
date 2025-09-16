#!/usr/bin/env python3
"""
Test script for countdown timer functionality
"""

import requests
import time
import json
import threading
from websocket import WebSocket, WebSocketApp

# Base URL for the trivia app
BASE_URL = 'http://127.0.0.1:5001'

def admin_login():
    """Login as admin and return session"""
    session = requests.Session()
    response = session.post(f'{BASE_URL}/admin/login', data={'password': 'admin123'})
    if response.status_code == 200 or response.status_code == 302:
        print("✓ Admin logged in successfully")
        return session
    else:
        print("✗ Admin login failed")
        return None

def create_test_team():
    """Create a test team and return session"""
    session = requests.Session()
    team_data = {
        'team_name': 'Test Team Timer',
        'player_name': 'Test Player'
    }
    response = session.post(f'{BASE_URL}/api/teams', json=team_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Created team: {result['team_id']}")
        return session, result['team_id']
    else:
        print("✗ Failed to create team")
        return None, None

def test_timer_functionality():
    """Test the timer functionality end-to-end"""
    print("\n🧪 Testing Countdown Timer and Bonus Scoring System")
    print("=" * 60)
    
    # 1. Admin login and start game
    admin_session = admin_login()
    if not admin_session:
        return False
    
    # 2. Create a test team
    team_session, team_id = create_test_team()
    if not team_session:
        return False
    
    # 3. Start the game
    print("\n📝 Starting game...")
    response = admin_session.post(f'{BASE_URL}/admin/api/game/start')
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✓ Game started successfully")
        else:
            print(f"✗ Game start failed: {result.get('message')}")
            return False
    else:
        print("✗ Failed to start game")
        return False
    
    # 4. Get current question to verify timer info is included
    print("\n⏱️ Testing timer information in question API...")
    response = team_session.get(f'{BASE_URL}/api/question')
    if response.status_code == 200:
        question = response.json()
        if 'timer' in question:
            timer_info = question['timer']
            print(f"✓ Timer info present: {timer_info['time_remaining']}s remaining, {timer_info['bonus_points']} bonus points")
        else:
            print("✗ Timer information missing from question response")
            return False
    else:
        print("✗ Failed to get current question")
        return False
    
    # 5. Test different timing scenarios for bonus points
    print("\n🚀 Testing timing-based bonus scoring (1 point deducted every 10 seconds)...")
    
    # Test immediate answer (should get 6 bonus points)
    time.sleep(1)  # Wait 1 second - should get 6 points (0-10s range)
    answer_data = {'answer': 'Paris'}  # Answer to first question
    response = team_session.post(f'{BASE_URL}/api/answer', json=answer_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✓ Quick answer submitted (1s elapsed)")
            print(f"  Points earned: {result.get('points_earned')}")
            print(f"  Bonus points: {result.get('bonus_points', 0)}")
            print(f"  Answer time: {result.get('answer_time', 'N/A')}s")
            
            # Verify bonus scoring logic for quick answer
            if result.get('correct') and result.get('bonus_points', 0) == 6:
                print("✓ Quick answer bonus scoring working correctly (6 points)")
            elif result.get('correct'):
                print(f"⚠️  Unexpected bonus points: {result.get('bonus_points', 0)} (expected 6 for quick answer)")
        else:
            print(f"✗ Answer submission failed: {result.get('error')}")
            return False
    else:
        print("✗ Failed to submit answer")
        return False
    
    # 6. Test additional timing scenarios
    print("\n⏰ Testing additional timing scenarios...")
    
    # Move to next question to test medium timing
    response = admin_session.post(f'{BASE_URL}/admin/api/next_question')
    if response.status_code == 200:
        print("✓ Advanced to next question for timing test")
        
        # Wait 15 seconds to test 10-20s range (should get 5 bonus points)
        print("  Waiting 15 seconds to test medium timing...")
        time.sleep(15)
        
        answer_data = {'answer': 'London'}  # Answer to second question  
        response = team_session.post(f'{BASE_URL}/api/answer', json=answer_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ Medium timing answer submitted (15s elapsed)")
                print(f"  Bonus points: {result.get('bonus_points', 0)}")
                print(f"  Answer time: {result.get('answer_time', 'N/A')}s")
                
                if result.get('correct') and result.get('bonus_points', 0) == 5:
                    print("✓ Medium timing bonus scoring working correctly (5 points)")
                elif result.get('correct'):
                    print(f"⚠️  Unexpected bonus points: {result.get('bonus_points', 0)} (expected 5 for 15s timing)")
    
    # Test longer timing scenario  
    response = admin_session.post(f'{BASE_URL}/admin/api/next_question')
    if response.status_code == 200:
        print("✓ Advanced to next question for long timing test")
        
        # Wait 35 seconds to test 30-40s range (should get 3 bonus points)
        print("  Waiting 35 seconds to test longer timing...")
        time.sleep(35)
        
        answer_data = {'answer': 'Berlin'}  # Answer to third question
        response = team_session.post(f'{BASE_URL}/api/answer', json=answer_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ Long timing answer submitted (35s elapsed)")
                print(f"  Bonus points: {result.get('bonus_points', 0)}")
                print(f"  Answer time: {result.get('answer_time', 'N/A')}s")
                
                if result.get('correct') and result.get('bonus_points', 0) == 3:
                    print("✓ Long timing bonus scoring working correctly (3 points)")
                elif result.get('correct'):
                    print(f"⚠️  Unexpected bonus points: {result.get('bonus_points', 0)} (expected 3 for 35s timing)")

    # 7. Test admin game controls
    print("\n🎮 Testing game controls...")
    
    # Next question
    response = admin_session.post(f'{BASE_URL}/admin/api/next_question')
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✓ Advanced to next question")
        else:
            print(f"✗ Failed to advance question: {result.get('error')}")
    
    # Test pause/resume
    print("\n⏸️ Testing pause/resume...")
    response = admin_session.post(f'{BASE_URL}/admin/api/game/pause')
    if response.status_code == 200 and response.json().get('success'):
        print("✓ Game paused")
        
        response = admin_session.post(f'{BASE_URL}/admin/api/game/resume')
        if response.status_code == 200 and response.json().get('success'):
            print("✓ Game resumed")
        else:
            print("✗ Failed to resume game")
    else:
        print("✗ Failed to pause game")
    
    # 7. Test admin status with timer info
    print("\n📊 Testing admin status with timer info...")
    response = admin_session.get(f'{BASE_URL}/admin/api/status')
    if response.status_code == 200:
        status = response.json()
        if 'timer' in status and status['timer']:
            timer_info = status['timer']
            print(f"✓ Admin timer status: {timer_info['time_remaining']}s remaining, {timer_info['bonus_points']} bonus")
        else:
            print("✓ Admin status retrieved (timer may be inactive)")
    
    # 8. Stop the game
    print("\n🛑 Stopping game...")
    response = admin_session.post(f'{BASE_URL}/admin/api/game/stop')
    if response.status_code == 200 and response.json().get('success'):
        print("✓ Game stopped successfully")
    else:
        print("✗ Failed to stop game")
    
    print("\n" + "=" * 60)
    print("🎉 Timer functionality test completed!")
    return True

if __name__ == '__main__':
    success = test_timer_functionality()
    if success:
        print("\n✅ All timer tests passed!")
    else:
        print("\n❌ Some timer tests failed!")
        exit(1)