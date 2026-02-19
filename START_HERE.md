# Quick Start: 5-Minute Walkthrough

## Prerequisites
- Docker and Docker Compose installed
- Service running: `docker compose up -d`

---

## Step 1: Verify Service is Running (30 seconds)

```bash
cd netdiag-service

# Check all containers are healthy
docker compose ps
```

Expected output:
```
NAME               STATUS              PORTS
netdiag-service    Up (healthy)        0.0.0.0:5001->5000/tcp
netdiag-influxdb   Up                  0.0.0.0:8086->8086/tcp
```

---

## Step 2: Run Your First Scan (30 seconds)

```bash
# Scan public DNS servers
./netdiag scan 8.8.8.8,1.1.1.1,1.0.0.1
```

**What happens:**
- Sends 4 ICMP pings to each host in parallel (fping)
- Measures response time (latency)
- Calculates packet loss
- Returns results in JSON format

**Expected output:**
```json
{
  "timestamp": "2026-02-19T08:05:00.123456",
  "results": {
    "8.8.8.8": {
      "status": "up",
      "avg_ms": 12.34,
      "min_ms": 11.2,
      "max_ms": 13.5,
      "packet_loss_pct": 0.0,
      "packets_sent": 4,
      "packets_received": 4
    },
    "1.1.1.1": {
      "status": "up",
      "avg_ms": 15.67,
      ...
    }
  }
}
```

---

## Step 3: View Results (1 minute)

```bash
# View all latest results
./netdiag results

# View results for specific host
./netdiag results 8.8.8.8

# View history from last 2 hours
./netdiag history 8.8.8.8 2
```

---

## Step 4: Update Configuration (1 minute)

Edit `config/netdiag.json`:

```json
{
  "targets": [
    "8.8.8.8",
    "1.1.1.1"
  ],
  "scan_interval_seconds": 60,
  "ping_count": 4,
  "alert_loss_threshold_pct": 5,
  "alert_latency_threshold_ms": 100
}
```

**What each setting means:**
- `targets`: Hosts to monitor continuously
- `scan_interval_seconds`: How often to scan (60 = once per minute)
- `ping_count`: Pings per host per scan
- `alert_loss_threshold_pct`: Alert if packet loss > 5%
- `alert_latency_threshold_ms`: Alert if latency > 100ms

**Apply changes:**
```bash
docker compose restart netdiag-service
```

---

## Step 5: Watch for Alerts (1 minute)

```bash
# Watch logs for alerts
docker compose logs -f netdiag-service | grep ALERT
```

You'll see alerts like:
```
WARNING - ALERT: Host 8.8.8.8 is unreachable
WARNING - ALERT: Host 1.1.1.1 packet loss 15%
WARNING - ALERT: Host 1.0.0.1 latency 250ms
```

---

## Common Commands Reference

| Task | Command |
|------|---------|
| Check health | `./netdiag health` |
| Scan hosts now | `./netdiag scan 8.8.8.8,1.1.1.1` |
| View results | `./netdiag results` |
| View host results | `./netdiag results 8.8.8.8` |
| View history | `./netdiag history 8.8.8.8 1` |
| Show config | `./netdiag config` |
| Change threshold | `./netdiag config set alert_loss_threshold_pct 10` |
| View logs | `docker compose logs -f netdiag-service` |
| Stop service | `docker compose down` |

---

## Real-World Scenarios

### Scenario A: Monitor Your API Server

**1. Update config:**
```json
{
  "targets": ["api.mycompany.com", "db.mycompany.com", "cache.mycompany.com"],
  "scan_interval_seconds": 30,
  "alert_loss_threshold_pct": 1,
  "alert_latency_threshold_ms": 50
}
```

**2. Restart:**
```bash
docker compose restart netdiag-service
```

**3. Watch for issues:**
```bash
docker compose logs -f netdiag-service | grep ALERT
```

### Scenario B: Test Before vs After Network Changes

**Before:**
```bash
./netdiag scan myhost.com
# Note the latency
```

**Make network change (e.g., switch ISP)**

**After:**
```bash
./netdiag scan myhost.com
# Compare latency - improved or degraded?
```

### Scenario C: Debug Slow Application

```bash
# Test connection to critical services
./netdiag scan \
  database-server.internal,\
  cache-server.internal,\
  api-gateway.internal

./netdiag results

# If latency is high, network might be the issue
```

### Scenario D: 24/7 Monitoring

```bash
# Leave running with these settings in config
{
  "targets": ["critical-host.com"],
  "scan_interval_seconds": 60,
  "alert_loss_threshold_pct": 0.1,
  "alert_latency_threshold_ms": 200
}

# Service will:
# - Scan every 60 seconds automatically
# - Alert immediately on any packet loss
# - Alert if latency exceeds 200ms

# Check status anytime:
./netdiag results
```

---

## Understanding the Results

```json
{
  "8.8.8.8": {
    "status": "up",              // "up" = reachable, "down" = unreachable
    "avg_ms": 12.34,             // Average latency in milliseconds
    "min_ms": 11.2,              // Minimum latency of 4 pings
    "max_ms": 13.5,              // Maximum latency of 4 pings
    "packet_loss_pct": 0.0,      // Percentage of pings lost (0-100)
    "packets_sent": 4,           // Number of pings sent
    "packets_received": 4        // Number of pings that came back
  }
}
```

**Interpreting results:**

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| Status | `up` | `up` but slow | `down` |
| Latency | <50ms | 50-100ms | >100ms |
| Loss | 0% | 0-5% | >5% |

---

## Using the REST API

For scripts and automation:

### Health Check
```bash
curl http://localhost:5001/health
```

### Trigger Scan
```bash
curl -X POST http://localhost:5001/api/scan \
  -H "Content-Type: application/json" \
  -d '{"targets": ["8.8.8.8", "1.1.1.1"]}'
```

### Get Results
```bash
curl http://localhost:5001/api/results
curl http://localhost:5001/api/results/8.8.8.8
curl "http://localhost:5001/api/results/8.8.8.8?hours=2"
```

### Update Config
```bash
curl -X PUT http://localhost:5001/api/config \
  -H "Content-Type: application/json" \
  -d '{"alert_latency_threshold_ms": 150}'
```

---

## Using Python Client

```python
from netdiag_client import NetDiagClient

client = NetDiagClient()

# Health check
print(client.health())

# Trigger scan
results = client.scan(["8.8.8.8", "1.1.1.1"])

# Print formatted results
client.print_results(results)

# Get history
history = client.get_history("8.8.8.8", hours=2)
for entry in history:
    print(f"{entry['timestamp']}: {entry['avg_ms']}ms")

# Get and update config
config = client.get_config()
config['alert_loss_threshold_pct'] = 10
client.update_config(config)
```

---

## Troubleshooting

### Q: Why are hosts showing as "down"?
**A:** 
- ICMP (ping) might be blocked by firewall
- Try a public host: `./netdiag scan 1.1.1.1`
- If still down, network is isolated or ICMP is blocked

### Q: Why is latency very high?
**A:**
- Network congestion
- Try scanning again in a few seconds
- Check if it's consistent or temporary
- Run: `./netdiag history <host> 1` to see trends

### Q: How do I see all the data?
**A:**
```bash
# Access SQLite database directly
docker exec netdiag-service sqlite3 /data/netdiag.db \
  "SELECT timestamp, host, status, avg_ms, packet_loss_pct FROM ping_results LIMIT 20;"
```

### Q: Service won't start?
**A:**
```bash
# Check logs
docker compose logs netdiag-service

# If port 5001 already in use, edit docker-compose.yml:
# Change: ports: ["5001:5000"]
# To:     ports: ["5002:5000"]
```

### Q: How do I reset everything?
**A:**
```bash
# Stop and remove all data
docker compose down -v

# Restart fresh
docker compose up -d
```

---

## Next Steps

1. ✅ Service is running and tested
2. ✅ You've run your first scan
3. ✅ You understand the output format

**What to do next:**

- **For monitoring:** Set up continuous scans (edit config, set `scan_interval_seconds`)
- **For alerting:** Lower thresholds and watch logs (grep ALERT)
- **For integration:** Use Python client or REST API in your scripts
- **For production:** Use `docker-compose.prod.yml` with resource limits
- **For persistence:** Data is stored in `/data/netdiag.db` (SQLite)

---

## File Structure

```
netdiag-service/
├── netdiag                 ← Use this for CLI commands
├── netdiag_client.py       ← Use for Python scripts
├── alert_handler.py        ← Send alerts to Slack/Discord
├── app.py                  ← Service code (don't modify)
├── docker-compose.yml      ← Development setup
├── docker-compose.prod.yml ← Production setup
├── config/
│   └── netdiag.json        ← EDIT THIS for configuration
├── HOW_TO_USE.md           ← Full documentation
├── QUICKSTART.md           ← Quick reference
└── OPERATIONS.md           ← Operational guide
```

**You only need to:**
1. Run `./netdiag` commands for CLI use
2. Edit `config/netdiag.json` for settings
3. Import `netdiag_client.py` for Python scripts

Everything else is already configured and running!

---

## Need Help?

**Check logs:**
```bash
docker compose logs -f netdiag-service
```

**Test fping directly:**
```bash
docker exec netdiag-service fping 8.8.8.8
```

**Access database:**
```bash
docker exec netdiag-service sqlite3 /data/netdiag.db "SELECT COUNT(*) FROM ping_results;"
```

**Restart service:**
```bash
docker compose restart netdiag-service
```

You're all set! Start monitoring your network now. 🚀
