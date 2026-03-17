#!/usr/bin/env python3
"""
Simple Frontend Test - Test if real attack data reaches frontend
"""

import asyncio
import websockets
import json
import requests

async def test_frontend_visualization():
    """Test if frontend receives real attack data correctly"""
    
    print("🔍 FRONTEND VISUALIZATION TEST")
    print("=" * 50)
    
    # Connect to WebSocket
    uri = "ws://localhost:8000/ws"
    print(f"🔌 Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            # Send a real attack
            print("\n🚨 Sending real attack...")
            attack_data = {
                "attack_type": "ddos",
                "source_ip": "10.222.222.222",
                "target_ip": "192.168.1.100", 
                "payload": {"frontend_test": True},
                "timestamp": "2026-03-17T12:55:00Z"
            }
            
            response = requests.post("http://localhost:8000/api/attack/receive", json=attack_data)
            print(f"📡 Attack response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Attack received: {result['alerts_generated']} alerts")
            
            # Listen for WebSocket messages
            print("\n👂 Listening for WebSocket messages...")
            
            message_count = 0
            real_attack_received = False
            
            while message_count < 10:  # Listen for 10 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    
                    print(f"\n🔥 Message {message_count + 1}:")
                    print(f"   Timestamp: {data.get('timestamp')}")
                    print(f"   Attack mode: {data.get('attack_mode')}")
                    print(f"   Real attack: {data.get('real_attack')}")
                    print(f"   Scenario active: {data.get('scenario_active')}")
                    
                    # Check for real attack data
                    if data.get('attack_mode') == 'real':
                        real_attack_received = True
                        real_attack = data.get('real_attack', {})
                        print(f"🎉 REAL ATTACK DETECTED!")
                        print(f"   Source IP: {real_attack.get('source_ip')}")
                        print(f"   Attack type: {attack_data['attack_type']}")
                        
                        # Check domain visual effects
                        domains = data.get('domains', {})
                        print(f"\n🎨 VISUAL EFFECTS:")
                        print(f"   Network packets/sec: {domains.get('network', {}).get('packets_per_second', 'N/A')}")
                        print(f"   Network anomaly: {domains.get('network', {}).get('anomaly', False)}")
                        print(f"   Hardware CPU: {domains.get('hardware', {}).get('cpu_percent', 'N/A')}%")
                        print(f"   Hardware anomaly: {domains.get('hardware', {}).get('anomaly', False)}")
                        print(f"   Security firewall hits: {domains.get('security', {}).get('firewall_hits', 'N/A')}")
                        print(f"   Security anomaly: {domains.get('security', {}).get('anomaly', False)}")
                        
                        break
                    
                    message_count += 1
                    
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            if real_attack_received:
                print("\n✅ SUCCESS: Real attack data received with visual effects!")
                print("🎯 Check the frontend dashboard at http://localhost:3000")
                print("🔍 Look for:")
                print("   - Red '⚠ REAL ATTACK FROM [IP]' banner")
                print("   - Yellow debug banner with attack details")
                print("   - Domain cards showing anomalies")
                print("   - Browser console (F12) for debug logs")
            else:
                print("\n❌ ISSUE: No real attack data received in WebSocket messages")
                print("🔧 Troubleshooting:")
                print("   1. Check browser console for WebSocket errors")
                print("   2. Refresh the frontend page")
                print("   3. Check if WebSocket is connected")
            
            print("\n🔌 WebSocket test complete")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_frontend_visualization())
