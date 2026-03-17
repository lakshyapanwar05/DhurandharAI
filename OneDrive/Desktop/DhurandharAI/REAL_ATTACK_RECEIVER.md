# Real Attack Receiver - DhurandharAI

## Overview
The Real Attack Receiver allows external attacker devices on the same network to send attack events directly to the DhurandharAI backend. This enables realistic hackathon demonstrations with actual attack traffic.

## Features

### 🔥 Real Attack Detection
- **External Attack Input**: Accepts attack events from any device on the network
- **Instant Correlation**: Runs correlation engine immediately on real attacks
- **Source IP Tracking**: Logs and displays actual attacker IP addresses
- **Visual Indicators**: Shows "⚠ REAL ATTACK FROM [IP]" banner in dashboard

### 📡 API Endpoints

#### POST /api/attack/receive
Accepts real attack events from external devices.

**Request Body:**
```json
{
  "attack_type": "ddos|bruteforce|cryptominer|insider",
  "source_ip": "192.168.1.50",
  "target_ip": "192.168.1.100", 
  "payload": {
    "attack_id": "ATT-12345",
    "severity": "high",
    "protocol": "TCP"
  },
  "timestamp": "2026-03-17T10:00:00Z"
}
```

**Response:**
```json
{
  "status": "received",
  "attack_type": "ddos",
  "source_ip": "192.168.1.50",
  "alerts_generated": 3,
  "timestamp": "2026-03-17T10:00:00Z"
}
```

#### GET /api/attack/status
Returns current attack status and connected attacker IPs.

**Response:**
```json
{
  "last_attack": {
    "attack_type": "ddos",
    "source_ip": "192.168.1.50",
    "target_ip": "192.168.1.100",
    "timestamp": "2026-03-17T10:00:00Z",
    "payload": {...}
  },
  "connected_ips": ["192.168.1.50", "10.0.0.15"],
  "total_attacks_received": 5,
  "active_scenario": "ddos"
}
```

## 🎯 Usage Examples

### Method 1: Python Test Script
```bash
python test_real_attack.py
```

### Method 2: External Attacker Script
```bash
# Edit BACKEND_URL in external_attacker.py
python external_attacker.py
```

### Method 3: curl Command
```bash
curl -X POST http://localhost:8000/api/attack/receive \
  -H "Content-Type: application/json" \
  -d '{
    "attack_type": "ddos",
    "source_ip": "192.168.1.99",
    "target_ip": "192.168.1.100",
    "payload": {"test": true},
    "timestamp": "2026-03-17T10:00:00Z"
  }'
```

### Method 4: JavaScript (Browser)
```javascript
fetch('http://localhost:8000/api/attack/receive', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    attack_type: 'ddos',
    source_ip: '192.168.1.99',
    target_ip: '192.168.1.100',
    payload: { test: true },
    timestamp: new Date().toISOString()
  })
})
.then(response => response.json())
.then(data => console.log('Attack sent:', data));
```

## 🚨 Dashboard Indicators

### Real Attack Banner
When a real attack is received, the dashboard shows:
- **Red pulsing banner**: "⚠ REAL ATTACK FROM [IP]"
- **Different styling** from simulated attacks
- **Real source IP** displayed prominently

### Incident Logging
- **Root cause**: "Real attack from [source_ip]"
- **Supabase logging**: Real attacks logged with actual IP addresses
- **Correlation**: Immediate threat correlation across domains

## 🛠️ Attack Type Mapping

| Attack Type | Scenario | Description |
|-------------|----------|-------------|
| `ddos` | DDoS Attack | Volumetric flood detection |
| `bruteforce` | Brute Force | Login pattern attacks |
| `cryptominer` | Cryptomining | CPU/memory anomalies |
| `insider` | Insider Threat | User behavior anomalies |

## 🔧 Configuration

### CORS Settings
For hackathon demo purposes, CORS allows all origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Network Requirements
- **Same Network**: Attacker devices must be on the same network as backend
- **Port Access**: Backend port 8000 must be accessible
- **No Authentication**: Open endpoint for demo purposes

## 📱 Mobile Device Support

### Android (Termux)
```bash
pkg install python3
pip install requests
python external_attacker.py
```

### iOS (Shortcuts)
Create a shortcut that sends HTTP POST to the attack endpoint.

### Cross-Platform
Any device that can make HTTP requests can send attacks:
- Web browsers
- Mobile apps
- IoT devices
- Command line tools

## 🎭 Hackathon Demo Ideas

### Multi-Device Attack
1. **Multiple attackers**: Run script on different devices
2. **Coordinated attack**: Synchronized attacks from multiple IPs
3. **Attack patterns**: Different attack types from different sources

### Live Demonstration
1. **Audience participation**: Let attendees send attacks from phones
2. **Real-time visualization**: Watch attacks appear on dashboard
3. **Geographic distribution**: Show attacks from different network segments

### Attack Scenarios
1. **Botnet simulation**: Multiple devices attacking simultaneously
2. **Insider threat**: Attack from internal IP range
3. **External threat**: Attack from outside network

## 🔍 Monitoring

### Attack Status
```bash
curl http://localhost:8000/api/attack/status
```

### Real-time Logs
Backend logs show:
```
🚨 REAL ATTACK RECEIVED: ddos from 192.168.1.50 to 192.168.1.100
🔍 Real attack correlation: 3 alerts found
📡 Broadcasting REAL ATTACK: ddos, source=192.168.1.50, alerts=3
```

### WebSocket Events
Frontend receives real attack data with:
```json
{
  "attack_mode": "real",
  "real_attack": {
    "source_ip": "192.168.1.50",
    "target_ip": "192.168.1.100",
    "payload": {...},
    "timestamp": "2026-03-17T10:00:00Z"
  }
}
```

## 🚀 Advanced Features

### Custom Payloads
Send custom attack data in the payload field:
```json
{
  "attack_type": "ddos",
  "source_ip": "10.0.0.15",
  "target_ip": "192.168.1.100",
  "payload": {
    "packets_per_second": 50000,
    "attack_duration": 300,
    "signature": "SYN_FLOOD",
    "botnet_size": 1000
  }
}
```

### Continuous Attack Mode
The external attacker script supports continuous mode:
```bash
python external_attacker.py
# Choose option 6 for continuous attacks
```

### Integration with Other Tools
- **Metasploit**: Post-exploitation scripts can send attack events
- **Nmap**: Custom scripts can report scan results
- **SIEM Systems**: Forward alerts to DhurandharAI
- **IoT Devices**: Embedded devices can report anomalies

## 🎯 Security Considerations

### Production Deployment
For production use, consider:
- **Authentication**: Add API key validation
- **Rate Limiting**: Prevent abuse
- **IP Whitelisting**: Restrict to trusted sources
- **HTTPS**: Encrypt traffic in production

### Demo Safety
- **Network Isolation**: Use dedicated network for demo
- **Firewall Rules**: Limit exposure during demo
- **Monitoring**: Watch for unexpected attack traffic

---

**🎉 The Real Attack Receiver transforms DhurandharAI from a simulation tool into a live threat detection platform!**
