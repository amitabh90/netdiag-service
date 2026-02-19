# Network Diagnostics Service - SRE Tool

A Docker-based network monitoring service built on **fping** to help SREs quickly diagnose and track network issues across multiple hosts.

## Features

- **Parallel Host Monitoring** — Ping multiple targets simultaneously using fping
- **Configurable Alerts** — Set thresholds for packet loss and latency
- **Periodic Scanning** — Automatic background scans at configured intervals
- **SQLite Storage** — Persistent historical data with time-based queries
- **REST API** — Full API for on-demand scans and result retrieval
- **CLI Client** — Bash script for quick command-line operations
- **Python Client** — Programmatic access via Python library
- **InfluxDB Ready** — Optional integration for metrics collection

## Quick Start

### Prerequisites

- Docker
- Docker Compose
- curl (for CLI testing)

### 1. Start the Service

```bash
cd netdiag-service
docker compose up -d
```

This starts:
- **netdiag-service** on `http://localhost:5001`
- **InfluxDB** on `http://localhost:8086` (optional)

### 2. Verify Health

```bash
./netdiag health
# Output: {"status": "healthy", "timestamp": "..."}
```

### 3. Run a Scan

```bash
./netdiag scan 8.8.8.8,1.1.1.1,1.0.0.1
```

### 4. View Results

```bash
./netdiag results
./netdiag results 8.8.8.8
```

## Configuration

Config file: `config/netdiag.json`

```json
{
  "targets": ["8.8.8.8", "1.1.1.1", "1.0.0.1", "9.9.9.9"],
  "scan_interval_seconds": 60,
  "ping_count": 4,
  "alert_loss_threshold_pct": 5,
  "alert_latency_threshold_ms": 100
}
```

- **targets**: List of hosts to monitor (IPs or hostnames)
- **scan_interval_seconds**: Background scan interval
- **ping_count**: Number of pings per host per scan
- **alert_loss_threshold_pct**: Alert if packet loss exceeds this
- **alert_latency_threshold_ms**: Alert if avg latency exceeds this

## API Endpoints

### Health Check
```bash
GET /health
# Response: {"status": "healthy", "timestamp": "..."}
```

### Trigger Scan
```bash
POST /api/scan
# Body: {"targets": ["8.8.8.8", "1.1.1.1"]}
# Response: {"timestamp": "...", "results": {...}}
```

### Get Latest Results
```bash
GET /api/results
# Response: {"timestamp": "...", "results": {...}}

GET /api/results/<host>
# Response: {"host": "8.8.8.8", "history": [...]}
```

### Get Historical Data
```bash
GET /api/results/<host>?hours=2
# Returns results from the last 2 hours
```

### Get Configuration
```bash
GET /api/config
# Response: {...current config...}

PUT /api/config
# Body: {...new config...}
```

## CLI Usage

### Check Health
```bash
./netdiag health
```

### Run On-Demand Scan
```bash
./netdiag scan 8.8.8.8,1.1.1.1,google.com
```

### View Results
```bash
./netdiag results              # All hosts
./netdiag results 8.8.8.8     # Specific host
```

### View History
```bash
./netdiag history 8.8.8.8     # Last 1 hour (default)
./netdiag history 8.8.8.8 6   # Last 6 hours
```

### View/Update Config
```bash
./netdiag config                                    # Show current config
./netdiag config set alert_loss_threshold_pct 10  # Update threshold
```

## Python Client Usage

```python
from netdiag_client import NetDiagClient

client = NetDiagClient()

# Check health
print(client.health())

# Trigger scan
results = client.scan(["8.8.8.8", "1.1.1.1"])

# Get latest results
results = client.get_results()
client.print_results(results)

# Get results for specific host
history = client.get_history("8.8.8.8", hours=2)

# Update config
client.set_config_value("alert_loss_threshold_pct", 10)
```

## Docker Compose Stack

### Volumes
- `netdiag-data`: Stores SQLite database
- `influxdb-data`: Stores InfluxDB metrics (optional)

### Networks
- `netdiag-network`: Isolated network for services

### Environment Variables
Set `NETDIAG_URL=http://netdiag-service:5000` for in-network access.

## Monitoring & Alerts

### Automatic Alerts
Service logs alert events when:
- Host becomes unreachable (100% packet loss)
- Packet loss exceeds configured threshold
- Latency exceeds configured threshold

View logs:
```bash
docker compose logs -f netdiag-service
```

### Alert Output Example
```
WARNING - ALERT: Host 8.8.8.8 is unreachable
WARNING - ALERT: Host 1.1.1.1 packet loss 15%
WARNING - ALERT: Host 1.0.0.1 latency 250ms
```

## Data Storage

### SQLite Database
Located at `/data/netdiag.db` (persisted via volume)

Schema:
```sql
CREATE TABLE ping_results (
  id INTEGER PRIMARY KEY,
  timestamp TEXT,
  host TEXT,
  status TEXT,           -- "up" or "down"
  min_ms REAL,
  avg_ms REAL,
  max_ms REAL,
  stddev_ms REAL,
  packet_loss_pct REAL,
  packets_sent INTEGER,
  packets_received INTEGER
);
```

Query examples:
```bash
# Inside container
sqlite3 /data/netdiag.db "SELECT * FROM ping_results WHERE host='8.8.8.8' LIMIT 10;"

# Or via volume mount on host
sqlite3 netdiag-data:/netdiag.db "SELECT COUNT(*) FROM ping_results;"
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker compose logs netdiag-service

# Verify network access
docker exec netdiag-service fping 8.8.8.8

# Test API
curl http://localhost:5001/health
```

### Port Already in Use
Edit `docker-compose.yml` and change port mapping:
```yaml
ports:
  - "5002:5000"  # Use different host port
```

### High Memory Usage
SQLite database grows over time. Clean old data:
```bash
docker exec netdiag-service sqlite3 /data/netdiag.db \
  "DELETE FROM ping_results WHERE datetime(timestamp) < datetime('now', '-30 days');"
```

### fping Timeout Issues
fping requires network access. In restricted environments:
- Enable ICMP traffic outbound
- Check firewall rules
- Verify hosts are reachable: `ping 8.8.8.8`

## Production Deployment

### Single Host (Docker)
```bash
docker compose up -d --pull always
```

### Docker Swarm
```bash
docker stack deploy -c docker-compose.yml netdiag
```

### Kubernetes
Create secrets for config:
```bash
kubectl create configmap netdiag-config \
  --from-file=config/netdiag.json
```

### Best Practices
- Set resource limits:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 256M
  ```
- Use readonly config: `volumes: ['./config:/config:ro']`
- Implement log rotation for alerts
- Monitor database size and archive old data
- Run behind reverse proxy (e.g., nginx)

## Integration Examples

### Prometheus Export
Add to service to export metrics as Prometheus format.

### Slack Alerts
Add alert handler to send to Slack webhook.

### InfluxDB Integration
Configure service to write metrics to InfluxDB for long-term storage.

## Logs

View all service logs:
```bash
docker compose logs -f
```

View netdiag service logs only:
```bash
docker compose logs -f netdiag-service
```

Filter by level:
```bash
docker compose logs netdiag-service | grep ALERT
```

## Cleanup

Stop and remove all containers:
```bash
docker compose down
```

Remove volumes (deletes data):
```bash
docker compose down -v
```

## File Structure

```
netdiag-service/
├── app.py                 # Main Flask service
├── netdiag_client.py     # Python client library
├── netdiag               # Bash CLI client
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container image definition
├── docker-compose.yml   # Multi-service orchestration
├── .dockerignore        # Build context exclusions
└── config/
    └── netdiag.json     # Service configuration
```

## License

Docker Demo Tool - Use freely for network diagnostics.

## Support

For issues or feature requests, check logs and verify fping is working:
```bash
docker exec netdiag-service fping -h
```
