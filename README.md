# Network Diagnostics Service - SRE Tool

A production-ready Docker-based network monitoring service for SREs. Built on **fping** for parallel host scanning with real-time alerts, historical data storage, and REST API.

## Quick Start (2 minutes)

```bash
docker compose up -d              # Start service
./netdiag health                  # Verify running
./netdiag scan 8.8.8.8,1.1.1.1   # Run your first scan
./netdiag results                 # View results
```

**Service is ready at:** http://localhost:5001

## Documentation Guide

Start here based on your needs:

| Guide | For | Time |
|-------|-----|------|
| [START_HERE.md](START_HERE.md) | First-time users | 5 min |
| [CHEAT_SHEET.txt](CHEAT_SHEET.txt) | Quick reference | 2 min |
| [HOW_TO_USE.md](HOW_TO_USE.md) | Real-world examples | 15 min |
| [QUICKSTART.md](QUICKSTART.md) | Common commands | 5 min |
| [OPERATIONS.md](OPERATIONS.md) | Full reference | 30 min |

## What's Included

✅ **fping-based monitoring** — Parallel scanning of multiple hosts  
✅ **REST API** — Full HTTP API for automation  
✅ **CLI tool** — Easy-to-use command-line interface  
✅ **Python client** — Programmatic access for scripts  
✅ **SQLite storage** — Historical data with time-based queries  
✅ **Alerts** — Configurable thresholds for loss & latency  
✅ **Background scanning** — Automatic periodic checks  
✅ **Production ready** — Resource limits, logging, health checks  

## Basic Commands

```bash
# Scan hosts
./netdiag scan 8.8.8.8,1.1.1.1,1.0.0.1

# View results
./netdiag results                 # All hosts
./netdiag results 8.8.8.8        # Specific host

# View history
./netdiag history 8.8.8.8 1      # Last 1 hour
./netdiag history 8.8.8.8 24     # Last 24 hours

# Configuration
./netdiag config                 # Show config
./netdiag config set alert_loss_threshold_pct 10
```

## Common Use Cases

### Monitor DNS Servers
```bash
./netdiag scan 8.8.8.8,1.1.1.1,9.9.9.9,208.67.222.222
./netdiag results  # See which is fastest
```

### 24/7 Network Monitoring
```bash
# Edit config/netdiag.json with your hosts
# Set scan_interval_seconds: 30
# Restart: docker compose restart netdiag-service
# Watch: docker compose logs -f netdiag-service | grep ALERT
```

### Troubleshoot Latency Issues
```bash
./netdiag scan critical-service.internal
./netdiag results                    # Check latency
./netdiag history critical-service.internal 1  # See trends
```

### SLA Compliance Check
```python
from netdiag_client import NetDiagClient

client = NetDiagClient()
results = client.scan(["critical-host.com"])

for host, data in results["results"].items():
    if data["packet_loss_pct"] > 0.5 or data["avg_ms"] > 50:
        print(f"SLA VIOLATION: {host}")
```

## REST API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/scan` | POST | Trigger scan |
| `/api/results` | GET | Get all results |
| `/api/results/<host>` | GET | Get host results |
| `/api/config` | GET/PUT | Get/update config |

## File Structure

```
netdiag-service/
├── netdiag                      ← Use this for CLI
├── netdiag_client.py            ← Use for Python scripts
├── alert_handler.py             ← Slack/Discord alerts
├── app.py                       ← Service (don't edit)
├── docker-compose.yml           ← Development
├── docker-compose.prod.yml      ← Production
├── config/netdiag.json          ← Edit this for settings
├── START_HERE.md                ← Read first
├── CHEAT_SHEET.txt              ← Quick reference
├── HOW_TO_USE.md                ← Examples
└── OPERATIONS.md                ← Full reference
```

## Requirements

- Docker
- Docker Compose
- Network connectivity to target hosts

## Configuration

Edit `config/netdiag.json`:

```json
{
  "targets": ["8.8.8.8", "1.1.1.1"],
  "scan_interval_seconds": 60,
  "ping_count": 4,
  "alert_loss_threshold_pct": 5,
  "alert_latency_threshold_ms": 100
}
```

Apply changes:
```bash
docker compose restart netdiag-service
```

## Monitoring & Logs

```bash
# Watch all logs
docker compose logs -f netdiag-service

# Watch alerts only
docker compose logs -f netdiag-service | grep ALERT

# Watch scans
docker compose logs -f netdiag-service | grep "scan complete"
```

## Data Storage

All measurements are stored in SQLite at `/data/netdiag.db`:

```bash
# Query measurements
docker exec netdiag-service sqlite3 /data/netdiag.db \
  "SELECT * FROM ping_results WHERE host='8.8.8.8' LIMIT 10;"

# Clean old data (>30 days)
docker exec netdiag-service sqlite3 /data/netdiag.db \
  "DELETE FROM ping_results WHERE datetime(timestamp) < datetime('now', '-30 days');"
```

## Deployment

**Development:**
```bash
docker compose up -d
```

**Production (with resource limits):**
```bash
docker compose -f docker-compose.prod.yml up -d
```

**Docker Swarm:**
```bash
docker stack deploy -c docker-compose.yml netdiag
```

## Troubleshooting

**Service won't start:**
```bash
docker compose logs netdiag-service
```

**Hosts showing as "down":**
```bash
# Check if ICMP is blocked
docker exec netdiag-service fping 8.8.8.8
```

**High latency spike:**
```bash
./netdiag history <host> 1  # Check if consistent or temporary
```

## Integration Examples

### Slack Alerts
```python
from alert_handler import AlertHandler

handler = AlertHandler("https://hooks.slack.com/services/YOUR/WEBHOOK")
handler.send_slack("8.8.8.8", "down", 100.0, 0.0)
```

### GitHub Actions
```yaml
- name: Network SLA Check
  run: |
    docker compose up -d
    python check_sla.py
```

### Cron Job
```bash
0 6 * * * cd netdiag-service && \
  curl -s http://localhost:5001/api/results | \
  jq . > /tmp/network_report.json && \
  mail -s "Network Report" ops@example.com < /tmp/network_report.json
```

## Support

**Read documentation:**
- [START_HERE.md](START_HERE.md) - First steps
- [HOW_TO_USE.md](HOW_TO_USE.md) - Real examples
- [OPERATIONS.md](OPERATIONS.md) - Full guide

**Check logs:**
```bash
docker compose logs -f netdiag-service
```

**Test fping:**
```bash
docker exec netdiag-service fping 8.8.8.8
```

## Architecture

```
┌─────────────────────────────────────┐
│   REST API (Flask on port 5001)     │
├─────────────────────────────────────┤
│  Background Scheduler (APScheduler) │
│  Periodic Scan (60s interval)       │
├─────────────────────────────────────┤
│  fping Process (parallel pings)     │
├─────────────────────────────────────┤
│  SQLite Database (/data/netdiag.db) │
└─────────────────────────────────────┘
```

## Performance

- **Latency:** <2s to scan 10 hosts
- **Memory:** ~100MB base (scales with history)
- **CPU:** Minimal (ping I/O bound)
- **Storage:** ~1KB per measurement

## License

Open source - use freely for network diagnostics

---

**Ready to start?** → Read [START_HERE.md](START_HERE.md)

**Need quick reference?** → See [CHEAT_SHEET.txt](CHEAT_SHEET.txt)

**Want examples?** → Check [HOW_TO_USE.md](HOW_TO_USE.md)
