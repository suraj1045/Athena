import asyncio
import json
import urllib.request
from urllib.error import URLError
import websockets

async def test_ws():
    uri = "ws://localhost:8000/ws/control/test-client"
    
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/officers/test_officer_1/location",
        data=json.dumps({
            "latitude": 20.5937,
            "longitude": 78.9629,
            "heading": 90.0,
            "speed_mps": 0.0,
            "on_duty": True
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='PUT'
    )
    from urllib.request import urlopen
    
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket, sending PUT request...")
        try:
            with urlopen(req) as response:
                print(f"PUT Status: {response.status}")
        except URLError as e:
            print(f"PUT Error: {e}")
            return
            
        print("Waiting for WebSocket message...")
        while True:
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(msg)
                print("Received:", data)
                if data.get("type") == "OFFICER_LOCATION_UPDATE":
                    print("SUCCESS: Received OFFICER_LOCATION_UPDATE!")
                    break
            except asyncio.TimeoutError:
                print("Timeout waiting for message.")
                break

if __name__ == "__main__":
    asyncio.run(test_ws())
