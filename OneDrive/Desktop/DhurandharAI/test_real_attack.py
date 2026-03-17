#!/usr/bin/env python3
"""
Real Attack Simulator for DhurandharAI
Use this script to send fake attack events to the backend
"""

import requests
import json
import time
import random
from datetime import datetime

# Backend configuration
BACKEND_URL = "http://localhost:8000"

def send_real_attack(attack_type, source_ip, target_ip="192.168.1.100"):
    """Send a real attack event to the backend"""
    
    payload = {
        "attack_type": attack_type,
        "source_ip": source_ip,
        "target_ip": target_ip,
        "payload": {
            "packet_size": random.randint(64, 1500),
            "packets_per_second": random.randint(1000, 50000),
            "duration": random.randint(10, 300),
            "signature": random.choice(["SQLi", "XSS", "CMD_INJECTION", "PATH_TRAVERSAL"]),
            "user_agent": random.choice([
                "Mozilla/5.0 (compatible; scanner/1.0)",
                "Python-requests/2.28.1",
                "curl/7.68.0"
            ])
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/attack/receive", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Attack sent successfully!")
            print(f"   Type: {attack_type}")
            print(f"   Source: {source_ip}")
            print(f"   Alerts generated: {result.get('alerts_generated', 0)}")
            return True
        else:
            print(f"❌ Failed to send attack: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending attack: {e}")
        return False

def get_attack_status():
    """Get current attack status"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/attack/status")
        if response.status_code == 200:
            status = response.json()
            print(f"\n📊 Attack Status:")
            print(f"   Total attacks received: {status.get('total_attacks_received', 0)}")
            print(f"   Connected attacker IPs: {status.get('connected_ips', [])}")
            if status.get('last_attack'):
                last = status['last_attack']
                print(f"   Last attack: {last.get('attack_type')} from {last.get('source_ip')}")
            print(f"   Active scenario: {status.get('active_scenario')}")
        else:
            print(f"❌ Failed to get status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting status: {e}")

def main():
    print("🚀 DhurandharAI Real Attack Simulator")
    print("=" * 50)
    
    # Test different attack types
    attack_types = ["ddos", "bruteforce", "cryptominer", "insider"]
    fake_ips = [
        "10.0.0.15", "192.168.1.50", "172.16.0.25", 
        "10.1.1.100", "192.168.0.75", "172.20.0.10"
    ]
    
    print("\n🎯 Sending test attacks...")
    
    for i, attack_type in enumerate(attack_types):
        source_ip = random.choice(fake_ips)
        print(f"\n--- Attack {i+1}/{len(attack_types)} ---")
        
        if send_real_attack(attack_type, source_ip):
            print(f"⏳ Waiting 2 seconds...")
            time.sleep(2)
        else:
            print("⚠️  Skipping next attack due to error")
            break
    
    # Show final status
    print("\n" + "=" * 50)
    get_attack_status()
    print("\n✨ Demo complete! Check the dashboard for real attack indicators.")

if __name__ == "__main__":
    main()
