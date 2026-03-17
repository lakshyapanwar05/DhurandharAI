#!/usr/bin/env python3
"""
Enhanced Real Attack Test - Demonstrates visual effects and database tracking
"""

import requests
import time
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

def test_real_attack_with_visual_effects():
    """Test real attack with visual effects like simulated attacks"""
    
    print("🎯 ENHANCED REAL ATTACK RECEIVER TEST")
    print("=" * 60)
    
    # Test different attack types with visual effects
    attack_scenarios = [
        {
            "type": "ddos",
            "source_ip": "10.100.1.10",
            "description": "DDoS Volumetric Attack",
            "expected_effects": ["High network traffic", "CPU spike", "Firewall alerts"]
        },
        {
            "type": "bruteforce", 
            "source_ip": "10.100.2.20",
            "description": "Brute Force Login Attack",
            "expected_effects": ["Failed logins", "User anomalies", "Security alerts"]
        },
        {
            "type": "cryptominer",
            "source_ip": "10.100.3.30", 
            "description": "Cryptocurrency Mining Attack",
            "expected_effects": ["High CPU", "Memory usage", "Network anomalies"]
        },
        {
            "type": "insider",
            "source_ip": "10.100.4.40",
            "description": "Insider Threat Attack", 
            "expected_effects": ["User anomalies", "Data access", "Security alerts"]
        }
    ]
    
    for i, scenario in enumerate(attack_scenarios, 1):
        print(f"\n📡 Test {i}/{len(attack_scenarios)}: {scenario['description']}")
        print(f"   Source IP: {scenario['source_ip']}")
        print(f"   Expected Effects: {', '.join(scenario['expected_effects'])}")
        
        # Send attack
        payload = {
            "attack_type": scenario["type"],
            "source_ip": scenario["source_ip"],
            "target_ip": "192.168.1.100",
            "payload": {
                "test_id": i,
                "visual_effects": True,
                "database_tracking": True,
                "timestamp": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/api/attack/receive", json=payload)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Attack received: {result['alerts_generated']} alerts generated")
                print(f"   📊 Status: {result['status']}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Wait between attacks
    
    print("\n" + "=" * 60)
    print("🔍 CHECKING ATTACK STATUS")
    
    # Check attack status
    try:
        response = requests.get(f"{BACKEND_URL}/api/attack/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   Total attacks received: {status.get('total_attacks_received', 0)}")
            print(f"   Connected attacker IPs: {status.get('connected_ips', [])}")
            print(f"   Recent real attacks: {status.get('real_attack_count', 0)}")
            if status.get('last_attack'):
                last = status['last_attack']
                print(f"   Last attack: {last.get('attack_type')} from {last.get('source_ip')}")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking status: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 TEST COMPLETE!")
    print("\n📋 WHAT TO CHECK:")
    print("   1. Frontend Dashboard: http://localhost:3000")
    print("   2. Look for red '⚠ REAL ATTACK FROM [IP]' banner")
    print("   3. Check domain cards for visual changes:")
    print("      - Network: High traffic, anomalies")
    print("      - Hardware: CPU/Memory spikes") 
    print("      - User: Failed logins, anomalies")
    print("      - Security: Firewall hits, IDS alerts")
    print("   4. Network topology should show attack paths")
    print("   5. Incident panel should show real incidents")
    print("   6. Browser console (F12) should show WebSocket data")
    
    print("\n🗄️ DATABASE TRACKING:")
    print("   - Run SQL scripts in Supabase:")
    print("     * create_real_attacks_table.sql")
    print("     * update_incidents_table.sql")
    print("   - Real attacks stored in 'real_attacks' table")
    print("   - Enhanced incident logging with real attack fields")
    
    print("\n🎯 KEY FEATURES ENABLED:")
    print("   ✅ Visual effects matching simulated attacks")
    print("   ✅ Real-time database tracking")
    print("   ✅ Enhanced incident logging")
    print("   ✅ Attack history API endpoints")
    print("   ✅ Source IP tracking and attribution")
    print("   ✅ WebSocket real-time updates")

if __name__ == "__main__":
    test_real_attack_with_visual_effects()
