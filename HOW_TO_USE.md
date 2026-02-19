# How to Use Network Diagnostics Service - Complete Guide

## Step 1: Start the Service

```bash
cd netdiag-service
docker compose up -d
```

Verify it's running:
```bash
docker compose ps
```

You should see:
- `netdiag-service` (healthy) on port 5001
- `netdiag-influxdb` on port 8086

## Step 2: Check Health

```bash
./netdiag health
```

Output:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-19T07:56:33.685838"
}
```

---

## Usage Scenarios

### Scenario 1: Quick Network Diagnostic Check

You suspect connectivity issues. Run an immediate scan:

```bash
./netdiag scan 8.8.8.8,1.1.1.1,1.0.0.1
```

Output shows each host's status, latency, and packet loss.

### Scenario 2: Monitor Specific Service

Your API depends on DNS resolvers. Monitor them continuously:

**Step 1:** Update config to monitor DNS servers
```bash
./netdiag config
```

Edit `config/netdiag.json`:
```json
{
  "targets": [
    "8.8.8.8",        // Google DNS
    "1.1.1.1",        // Cloudflare DNS
    "208.67.222.222"  // OpenDNS
  ],
  "scan_interval_seconds": 30,
  "alert_loss_threshold_pct": 3,
  "alert_latency_threshold_ms": 50
}
```

**Step 2:** Restart service to apply config
```bash
docker compose restart netdiag-service
```

**Step 3:** Watch logs for alerts
```bash
docker compose logs -f netdiag-service | grep ALERT
```

### Scenario 3: Investigate Latency Issue

Your app is slow. Check if it's network-related:

```bash
# Scan your infrastructure
./netdiag scan api-server.internal,db-server.internal,cdn.example.com

# View results
./netdiag results
```

Sample output:
```
Host                    Status     Avg Latency  Loss %   Packets     
api-server.internal     UP         5.23ms       0.0%     4/4        
db-server.internal      UP         12.45ms      0.0%     4/4        
cdn.example.com         UP         85.32ms      0.0%     4/4  ← High latency!
```

**Step 4:** Get historical data for that host
```bash
./netdiag history cdn.example.com 1
```

Returns all measurements from the last hour to see if latency is persistent or intermittent.

### Scenario 4: Alert on Host Failure

Configure the service to alert you immediately when a critical host goes down:

```bash
# Set very low thresholds
./netdiag config set alert_loss_threshold_pct 1
./netdiag config set alert_latency_threshold_ms 150
```

Watch logs:
```bash
docker compose logs -f netdiag-service | grep "WARNING\|ALERT"
```

When host fails:
```
WARNING - ALERT: Host 8.8.8.8 is unreachable
WARNING - ALERT: Host 1.1.1.1 packet loss 100%
```

---

## Real-World Examples

### Example 1: Troubleshoot VPN Connection

```bash
# Test before VPN
./netdiag scan 8.8.8.8

# Connect to VPN, test again
./netdiag scan 8.8.8.8

# Compare results
./netdiag results 8.8.8.8
```

If latency jumps from 10ms to 100ms, VPN is degrading performance.

### Example 2: Monitor Cloud Region Health

Monitor latency to AWS regions:

```bash
./netdiag scan \
  ec2-us-east-1.amazonaws.com,\
  ec2-eu-west-1.amazonaws.com,\
  ec2-ap-southeast-1.amazonaws.com
```

Check which region is fastest/slowest.

### Example 3: Detect Network Jitter

Run the same scan multiple times and compare variance:

```bash
for i in {1..5}; do
  echo "Scan $i:"
  ./netdiag scan 8.8.8.8
  sleep 5
done
```

If latency varies wildly (e.g., 5ms, 50ms, 8ms, 45ms), you have jitter.

### Example 4: Monitor DNS Resolution Time

Test multiple DNS servers to find the fastest:

```bash
./netdiag scan 8.8.8.8,1.1.1.1,9.9.9.9,208.67.222.222,45.33.32.156

./netdiag results
```

Pick the server with lowest latency.

---

## Using the Python Client

For scripting and automation:

### Basic Usage

```python
from netdiag_client import NetDiagClient

client = NetDiagClient("http://localhost:5001")

# Scan hosts
results = client.scan(["8.8.8.8", "1.1.1.1"])

# Print formatted results
client.print_results(results)
```

Output:
```
Host            Status     Avg Latency  Loss %   Packets   
8.8.8.8         UP         12.34ms      0.0%     4/4      
1.1.1.1         UP         15.67ms      0.0%     4/4
```

### Example: SLA Monitoring Script

```python
from netdiag_client import NetDiagClient
import sys

client = NetDiagClient()

# SLA: 99.5% uptime, <50ms latency
results = client.scan(["critical-api.example.com"])

for host, data in results["results"].items():
    loss = data["packet_loss_pct"]
    latency = data["avg_ms"]
    
    # Check SLA compliance
    if loss > 0.5:
        print(f"❌ SLA VIOLATION: {host} has {loss}% loss")
        sys.exit(1)
    
    if latency and latency > 50:
        print(f"❌ SLA VIOLATION: {host} latency is {latency}ms (>50ms)")
        sys.exit(1)

print("✓ SLA compliant")
sys.exit(0)
```

Run in CI/CD pipeline:
```bash
python check_sla.py && echo "Deploy OK" || echo "Deploy blocked - network SLA violated"
```

### Example: Auto-Scaling Trigger

```python
from netdiag_client import NetDiagClient

client = NetDiagClient()

# Check if load balancer is responsive
results = client.scan(["load-balancer.internal"])

for host, data in results["results"].items():
    if data["status"] == "down":
        print("Load balancer down - trigger auto-scale!")
        # Call API to scale up
        trigger_autoscale()
    elif data["avg_ms"] and data["avg_ms"] > 200:
        print("Load balancer slow - trigger scale-up")
        trigger_autoscale()
```

---

## REST API Direct Usage

### Using curl

**Check health:**
```bash
curl http://localhost:5001/health
```

**Trigger scan:**
```bash
curl -X POST http://localhost:5001/api/scan \
  -H "Content-Type: application/json" \
  -d '{"targets": ["8.8.8.8", "1.1.1.1"]}'
```

**Get latest results:**
```bash
curl http://localhost:5001/api/results
```

**Get specific host results:**
```bash
curl http://localhost:5001/api/results/8.8.8.8
```

**Get history (last 2 hours):**
```bash
curl "http://localhost:5001/api/results/8.8.8.8?hours=2"
```

**Update configuration:**
```bash
curl -X PUT http://localhost:5001/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "targets": ["8.8.8.8", "1.1.1.1"],
    "alert_loss_threshold_pct": 10
  }'
```

---

## Monitoring in Production

### Continuous Background Scanning

The service automatically scans every 60 seconds (configurable):

```bash
# Watch the logs
docker compose logs -f netdiag-service

# You'll see:
# 2026-02-19 07:56:00 - Starting scan of 4 hosts
# 2026-02-19 07:56:02 - Scan complete: 4 hosts processed
# 2026-02-19 07:56:02 - WARNING - ALERT: Host 8.8.8.8 latency 120ms
```

### Database Queries

Access raw measurement data:

```bash
# Get all measurements for a host
docker exec netdiag-service sqlite3 /data/netdiag.db \
  "SELECT timestamp, status, avg_ms, packet_loss_pct FROM ping_results WHERE host='8.8.8.8' LIMIT 10;"
```

Output:
```
2026-02-19T07:56:00|up|12.34|0.0
2026-02-19T07:56:01|up|11.56|0.0
2026-02-19T07:56:02|up|150.34|5.0  ← Spike!
```

### Export to Monitoring System

```python
# Export recent data to Prometheus
from netdiag_client import NetDiagClient

client = NetDiagClient()
results = client.get_results()

for host, data in results["results"].items():
    if data["status"] == "up":
        # Emit metrics
        print(f'netdiag_latency_ms{{host="{host}"}} {data["avg_ms"]}')
        print(f'netdiag_loss_pct{{host="{host}"}} {data["packet_loss_pct"]}')
    else:
        print(f'netdiag_up{{host="{host}"}} 0')
```

---

## Troubleshooting Guide

### Issue: Hosts showing as "down" but they're actually up

**Cause:** Network restrictions (firewall blocking ICMP)

**Fix:**
```bash
# Test fping directly
docker exec netdiag-service fping 8.8.8.8

# If it times out, ICMP is blocked
# Solution: Allow ICMP in firewall rules
```

### Issue: Service won't start

**Check logs:**
```bash
docker compose logs netdiag-service
```

**Common errors:**
- Port 5001 already in use → Change port in docker-compose.yml
- fping not in PATH → Already included in Dockerfile, should work
- Permission denied → Run with sudo or add user to docker group

### Issue: Results showing very high latency

**Cause 1:** Network congestion
```bash
# Run multiple scans to see variance
./netdiag scan 8.8.8.8
sleep 5
./netdiag scan 8.8.8.8
sleep 5
./netdiag scan 8.8.8.8
```

If latency consistently high, there's congestion.

**Cause 2:** DNS issue
```bash
# Try with IP address instead of hostname
./netdiag scan 8.8.8.8  # vs google-dns.com
```

### Issue: Database getting too large

```bash
# Check database size
docker exec netdiag-service du -sh /data/netdiag.db

# Clean data older than 30 days
docker exec netdiag-service sqlite3 /data/netdiag.db \
  "DELETE FROM ping_results WHERE datetime(timestamp) < datetime('now', '-30 days');"
```

---

## Integration Examples

### Slack Alerts

Set webhook in alert_handler.py and run:

```python
from alert_handler import AlertHandler

handler = AlertHandler("https://hooks.slack.com/services/YOUR/WEBHOOK")

# When service detects alert, send to Slack
handler.send_slack("8.8.8.8", "down", 100.0, 0.0)
```

### GitHub Actions CI/CD Check

```yaml
name: Network Health Check

on: [workflow_dispatch]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check network SLA
        run: |
          # Start service
          docker compose up -d
          sleep 5
          
          # Run check
          python check_sla.py
```

### Cron Job for Regular Reporting

```bash
#!/bin/bash
# monitor.sh - Run nightly

RESULTS=$(curl -s http://localhost:5001/api/results)
echo "Network Health Report - $(date)" > report.txt
echo "$RESULTS" | jq . >> report.txt

# Email report
mail -s "Network Report" ops@example.com < report.txt
```

Schedule in crontab:
```bash
0 6 * * * /path/to/monitor.sh
```

---

## Quick Reference Card

```bash
# Start
docker compose up -d

# Health check
./netdiag health

# Scan now
./netdiag scan 8.8.8.8,1.1.1.1

# View results
./netdiag results
./netdiag results 8.8.8.8

# History
./netdiag history 8.8.8.8 1    # Last 1 hour
./netdiag history 8.8.8.8 24   # Last 24 hours

# Config
./netdiag config
./netdiag config set alert_loss_threshold_pct 10

# Logs
docker compose logs -f netdiag-service

# Stop
docker compose down
```

---

## Next Steps

1. **Start monitoring:** `docker compose up -d`
2. **Run first scan:** `./netdiag scan 8.8.8.8`
3. **Check results:** `./netdiag results`
4. **Set up alerts:** Edit config for your thresholds
5. **Integrate:** Use Python client or API in your automation
6. **Deploy:** Use `docker-compose.prod.yml` for production

You're ready to go! Let me know if you need help with any specific use case.
