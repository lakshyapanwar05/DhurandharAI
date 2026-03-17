#!/usr/bin/env python3
"""
Quick WebSocket Test - Verify connection and real attack data
"""

import asyncio
import websockets
import json
import requests

async def quick_test():
    """Quick test to verify WebSocket and real attack data"""
    
    print("🔍 QUICK WEBSOCKET TEST")
    print("=" * 40)
    
    # Test WebSocket connection
    try:
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            print("✅ WebSocket connected!")
            
            # Send real attack
            print("🚨 Sending real attack...")
            attack_data = {
                "attack_type": "ddos",
                "source_ip": "10.500.500.500",
                "target_ip": "192.168.1.100",
                "payload": {"quick_test": True},
                "timestamp": "2026-03-17T13:10:00Z"
            }
            
            response = requests.post("http://localhost:8000/api/attack/receive", json=attack_data)
            print(f"📡 Attack response: {response.status_code}")
            
            # Listen for messages
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    print(f"\n🔥 Message {i+1}:")
                    print(f"   Attack mode: {data.get('attack_mode')}")
                    print(f"   Real attacker IP: {data.get('real_attacker_ip')}")
                    print(f"   Scenario active: {data.get('scenario_active')}")
                    
                    if data.get('attack_mode') == 'real':
                        print("🎉 REAL ATTACK DATA RECEIVED!")
                        print("🎯 Check frontend dashboard for banner!")
                        break
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout - no message received")
                    break
            
            print("\n✅ Test complete!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
