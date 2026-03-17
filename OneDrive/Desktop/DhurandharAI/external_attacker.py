#!/usr/bin/env python3
"""
External Attacker Script - Run from any device on the network
Sends attack events to DhurandharAI backend
"""

import requests
import json
import time
import socket
from datetime import datetime

# Configuration - Change this to the backend server IP
BACKEND_URL = "http://192.168.1.10:8000"  # Replace with actual backend IP

def get_local_ip():
    """Get the local IP address of this device"""
    try:
        # Connect to a remote server to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def send_attack(attack_type, target_ip="192.168.1.100"):
    """Send an attack event"""
    local_ip = get_local_ip()
    
    payload = {
        "attack_type": attack_type,
        "source_ip": local_ip,
        "target_ip": target_ip,
        "payload": {
            "attack_id": f"ATT-{int(time.time())}",
            "severity": "high",
            "protocol": "TCP",
            "port": 80,
            "method": "POST",
            "user_agent": "AttackerBot/1.0"
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    try:
        print(f"🚨 Sending {attack_type} attack from {local_ip} to {target_ip}...")
        response = requests.post(f"{BACKEND_URL}/api/attack/receive", json=payload, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Attack received! Alerts generated: {result.get('alerts_generated', 0)}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎯 External Attacker Script")
    print(f"Target: {BACKEND_URL}")
    print(f"Local IP: {get_local_ip()}")
    print("=" * 50)
    
    # Menu of attack types
    attacks = [
        ("ddos", "DDoS Volumetric Attack"),
        ("bruteforce", "Brute Force Login Attack"),
        ("cryptominer", "Cryptocurrency Mining Attack"),
        ("insider", "Insider Threat Attack")
    ]
    
    print("\nSelect attack type:")
    for i, (key, name) in enumerate(attacks, 1):
        print(f"{i}. {name}")
    print("5. Random attack")
    print("6. Continuous attack mode")
    
    try:
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == "6":
            # Continuous mode
            print("🔄 Continuous attack mode started (Ctrl+C to stop)")
            while True:
                attack_type = random.choice([a[0] for a in attacks])
                send_attack(attack_type)
                time.sleep(random.randint(3, 8))
        
        elif choice == "5":
            # Random attack
            attack_type = random.choice([a[0] for a in attacks])
            send_attack(attack_type)
        
        elif choice in ["1", "2", "3", "4"]:
            # Specific attack
            attack_type = attacks[int(choice) - 1][0]
            send_attack(attack_type)
        
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n🛑 Attack stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import random
    main()
