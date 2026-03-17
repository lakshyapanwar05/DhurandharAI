#!/usr/bin/env python3
"""
WebSocket Test Script - Test if WebSocket is receiving real attack data
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    print(f"🔌 Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Send a test attack first
            import requests
            attack_data = {
                "attack_type": "ddos",
                "source_ip": "10.99.99.99", 
                "target_ip": "192.168.1.100",
                "payload": {"websocket_test": True},
                "timestamp": "2026-03-17T12:05:00Z"
            }
            
            print("🚨 Sending test attack...")
            response = requests.post("http://localhost:8000/api/attack/receive", json=attack_data)
            print(f"📡 Attack response: {response.status_code} - {response.json()}")
            
            # Listen for WebSocket messages
            print("👂 Listening for WebSocket messages...")
            message_count = 0
            
            while message_count < 5:  # Listen for 5 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    print(f"\n🔥 WebSocket Message {message_count + 1}:")
                    print(f"   Attack mode: {data.get('attack_mode')}")
                    print(f"   Real attack: {data.get('real_attack')}")
                    print(f"   Scenario active: {data.get('scenario_active')}")
                    print(f"   Correlated alerts: {len(data.get('correlated_alerts', []))}")
                    
                    if data.get('attack_mode') == 'real':
                        print("🎉 REAL ATTACK DATA RECEIVED!")
                        break
                    
                    message_count += 1
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            print("🔌 WebSocket test complete")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
