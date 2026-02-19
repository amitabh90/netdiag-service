# Network Diagnostics Service - Quick Reference

## Start Service

```bash
cd netdiag-service
docker compose up -d
```

## CLI Examples

```bash
# Check health
./netdiag health

# Scan specific hosts
./netdiag scan 8.8.8.8,1.1.1.1,1.0.0.1

# Get latest results
./netdiag results

# Get host-specific results
./netdiag results 8.8.8.8

# View 2-hour history for a host
./netdiag history 8.8.8.8 2

# Show config
./netdiag config

# Update alert threshold
./netdiag config set alert_loss_threshold_pct 10
```

## Python Client Examples

```python
from netdiag_client import NetDiagClient

client = NetDiagClient()

# Basic scan
results = client.scan(["8.8.8.8", "1.1.1.1"])
client.print_results(results)

# Get history
history = client.get_history("8.8.8.8", hours=1)
print(history)

# Update config
client.set_config_value("alert_latency_threshold_ms", 150)
```

## Docker Commands

```bash
# View logs
docker compose logs -f netdiag-service

# Run command inside container
docker exec netdiag-service fping 8.8.8.8

# Access database
docker exec netdiag-service sqlite3 /data/netdiag.db \
  "SELECT COUNT(*) FROM ping_results;"

# Stop service
docker compose down

# Stop and remove data
docker compose down -v
```

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

After changes, restart:
```bash
docker compose restart netdiag-service
```

## API Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Service health |
| POST | `/api/scan` | Trigger scan |
| GET | `/api/results` | Latest results |
| GET | `/api/results/<host>` | Host results |
| GET | `/api/config` | Get config |
| PUT | `/api/config` | Update config |

## Result Status

```
"up"   - Host reachable, latency measured
"down" - Host unreachable (100% packet loss)
```

## Common Issues

**Port already in use:**
```bash
# Use different port in docker-compose.yml
ports:
  - "5002:5000"
```

**Network access denied:**
```bash
# Check if fping can reach hosts
docker exec netdiag-service fping 8.8.8.8
```

**Database growing too large:**
```bash
# Clean data older than 30 days
docker exec netdiag-service sqlite3 /data/netdiag.db \
  "DELETE FROM ping_results WHERE datetime(timestamp) < datetime('now', '-30 days');"
```

## Environment Variables

Set in docker-compose.yml:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - LOG_LEVEL=INFO
```

## Metrics

Stored in SQLite with:
- min/avg/max latency (ms)
- packet loss percentage
- packets sent/received
- timestamp of measurement

## Example: Monitor DNS Resolvers

```bash
./netdiag scan 8.8.8.8,1.1.1.1,9.9.9.9,208.67.222.222
./netdiag results
```

## Example: Alert on High Latency

```bash
# Set latency threshold to 50ms
./netdiag config set alert_latency_threshold_ms 50
```

Service will log alerts like:
```
WARNING - ALERT: Host 8.8.8.8 latency 75ms
```

## Deployment

**Development (single host):**
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

## Data Retention

By default, all data is kept. To implement retention:

```bash
# Keep only last 30 days of data
docker exec netdiag-service bash -c \
  'while true; do
     sqlite3 /data/netdiag.db "DELETE FROM ping_results WHERE datetime(timestamp) < datetime(\"now\", \"-30 days\");"
     sleep 86400
   done'
```

## Next Steps

- Integrate with Prometheus for metrics
- Add Slack/PagerDuty alerts
- Export to InfluxDB for long-term storage
- Build web dashboard
- Add email notifications
