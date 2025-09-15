import requests
import socketio
import time
import threading

BASE_URL = 'http://localhost:5001'

class SocketIOTestClient:
    def __init__(self):
        self.sio = socketio.Client()
        self.events_received = []
        
        @self.sio.on('game_paused')
        def on_game_paused(data):
            print(f"✓ Received game_paused event: {data}")
            self.events_received.append(('game_paused', data))
            
        @self.sio.on('game_resumed')
        def on_game_resumed(data):
            print(f"✓ Received game_resumed event: {data}")
            self.events_received.append(('game_resumed', data))
            
        @self.sio.on('game_status_update')
        def on_game_status_update(data):
            print(f"✓ Received game_status_update event: {data}")
            self.events_received.append(('game_status_update', data))
    
    def connect(self):
        self.sio.connect(BASE_URL)
        print("✓ Connected to WebSocket")
    
    def disconnect(self):
        self.sio.disconnect()
        print("✓ Disconnected from WebSocket")
    
    def wait_for_events(self, timeout=5):
        time.sleep(timeout)

def test_pause_websocket():
    print("Testing WebSocket pause functionality...")
    
    # Setup admin session
    session = requests.Session()
    login_response = session.post(f'{BASE_URL}/admin/login', 
                                data={'password': 'admin123'}, 
                                allow_redirects=False)
    assert login_response.status_code == 302
    print("✓ Admin logged in")
    
    # Start the game first
    session.post(f'{BASE_URL}/admin/api/game/start')
    print("✓ Game started")
    
    # Setup WebSocket client
    client = SocketIOTestClient()
    client.connect()
    
    # Test pause
    print("\n--- Testing Pause ---")
    session.post(f'{BASE_URL}/admin/api/game/pause')
    print("✓ Pause request sent")
    
    # Wait for events
    client.wait_for_events(2)
    
    # Check if pause events were received
    pause_events = [event for event in client.events_received if event[0] == 'game_paused']
    status_updates = [event for event in client.events_received if event[0] == 'game_status_update']
    
    assert len(pause_events) > 0, "game_paused event not received"
    assert len(status_updates) > 0, "game_status_update event not received"
    
    # Check pause event contains correct message
    pause_data = pause_events[0][1]
    assert 'paused by the administrator' in pause_data['message']
    print("✓ Pause events received correctly")
    
    # Clear events for resume test
    client.events_received.clear()
    
    # Test resume
    print("\n--- Testing Resume ---")
    session.post(f'{BASE_URL}/admin/api/game/resume')
    print("✓ Resume request sent")
    
    # Wait for events
    client.wait_for_events(2)
    
    # Check if resume events were received
    resume_events = [event for event in client.events_received if event[0] == 'game_resumed']
    new_question_events = [event for event in client.events_received if event[0] == 'new_question']
    
    assert len(resume_events) > 0, "game_resumed event not received"
    print("✓ Resume events received correctly")
    
    client.disconnect()
    print("\n✅ All WebSocket pause/resume tests passed!")

if __name__ == '__main__':
    try:
        test_pause_websocket()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()