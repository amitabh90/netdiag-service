#!/usr/bin/env python3
"""
Network Diagnostics Service - SRE Tool
Base: fping for parallel host monitoring
"""

import subprocess
import json
import time
import re
import threading
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import logging

from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@dataclass
class PingResult:
    timestamp: str
    host: str
    status: str  # "up", "down", "unreachable"
    min_ms: float = None
    avg_ms: float = None
    max_ms: float = None
    stddev_ms: float = None
    packet_loss_pct: float = None
    packets_sent: int = None
    packets_received: int = None

class NetworkDiagnostics:
    def __init__(self, db_path: str = "/data/netdiag.db"):
        self.db_path = db_path
        self.init_db()
        self.last_scan_results = {}
        self.lock = threading.Lock()
    
    def init_db(self):
        """Initialize SQLite database for storing results"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ping_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                host TEXT NOT NULL,
                status TEXT NOT NULL,
                min_ms REAL,
                avg_ms REAL,
                max_ms REAL,
                stddev_ms REAL,
                packet_loss_pct REAL,
                packets_sent INTEGER,
                packets_received INTEGER
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp_host 
            ON ping_results(timestamp, host)
        ''')
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def scan_hosts(self, hosts: List[str], count: int = 4, timeout: int = 5) -> Dict[str, PingResult]:
        """
        Scan a list of hosts using fping
        Returns dict of {host: PingResult}
        """
        if not hosts:
            logger.warning("No hosts provided for scan")
            return {}
        
        logger.info(f"Starting scan of {len(hosts)} hosts")
        
        try:
            # Build fping command - use default output format (not quiet)
            cmd = [
                'fping',
                '-c', str(count),      # Number of pings per host
                '-t', str(timeout * 1000),  # Timeout in ms
            ]
            cmd.extend(hosts)
            
            # Run fping
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10
            )
            
            # Parse results from stdout and stderr
            output = result.stdout + result.stderr
            parsed_results = self._parse_fping_output(output, hosts)
            
            # Store results in database
            self._store_results(parsed_results)
            
            # Cache last results
            with self.lock:
                self.last_scan_results = parsed_results
            
            logger.info(f"Scan complete: {len(parsed_results)} hosts processed")
            return parsed_results
            
        except subprocess.TimeoutExpired:
            logger.error("fping command timed out")
            return {}
        except Exception as e:
            logger.error(f"Error during scan: {e}")
            return {}
    
    def _parse_fping_output(self, output: str, hosts: List[str]) -> Dict[str, PingResult]:
        """Parse fping output and return structured results"""
        results = {}
        timestamp = datetime.now().isoformat()
        
        # Parse summary lines like:
        # "8.8.8.8 : xmt/rcv/%loss = 4/4/0%, min/avg/max = 25.0/28.7/35.1"
        for line in output.split('\n'):
            line = line.strip()
            if not line or 'xmt/rcv' not in line:
                continue
            
            try:
                # Extract host name
                host = line.split(':')[0].strip()
                
                if host not in hosts:
                    continue
                
                # Parse xmt/rcv/%loss = 4/4/0%
                loss_section = line.split('xmt/rcv/%loss =')[1].split(',')[0].strip()
                packets_sent, packets_received, loss_str = loss_section.split('/')
                packets_sent = int(packets_sent)
                packets_received = int(packets_received)
                packet_loss_pct = float(loss_str.rstrip('%'))
                
                # Parse min/avg/max
                stats_section = line.split('min/avg/max =')[1].strip()
                min_ms, avg_ms, max_ms = [float(x) for x in stats_section.split('/')]
                
                if packet_loss_pct == 100.0 or packets_received == 0:
                    results[host] = PingResult(
                        timestamp=timestamp,
                        host=host,
                        status="down",
                        packet_loss_pct=100.0,
                        packets_sent=packets_sent,
                        packets_received=0
                    )
                else:
                    results[host] = PingResult(
                        timestamp=timestamp,
                        host=host,
                        status="up",
                        min_ms=min_ms,
                        avg_ms=avg_ms,
                        max_ms=max_ms,
                        packet_loss_pct=packet_loss_pct,
                        packets_sent=packets_sent,
                        packets_received=packets_received
                    )
                    
            except (IndexError, ValueError) as e:
                logger.debug(f"Could not parse line: {line} - {e}")
                continue
        
        # Mark any hosts not in results as unreachable
        for host in hosts:
            if host not in results:
                results[host] = PingResult(
                    timestamp=timestamp,
                    host=host,
                    status="down",
                    packet_loss_pct=100.0
                )
        
        return results
    
    def _store_results(self, results: Dict[str, PingResult]):
        """Store results in SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for result in results.values():
                cursor.execute('''
                    INSERT INTO ping_results 
                    (timestamp, host, status, min_ms, avg_ms, max_ms, stddev_ms, 
                     packet_loss_pct, packets_sent, packets_received)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    result.timestamp, result.host, result.status,
                    result.min_ms, result.avg_ms, result.max_ms, result.stddev_ms,
                    result.packet_loss_pct, result.packets_sent, result.packets_received
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing results: {e}")
    
    def get_last_results(self) -> Dict[str, PingResult]:
        """Get cached last scan results"""
        with self.lock:
            return self.last_scan_results.copy()
    
    def get_history(self, host: str, hours: int = 1) -> List[Dict]:
        """Get historical results for a host"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute('''
                SELECT * FROM ping_results 
                WHERE host = ? AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (host, cutoff_time))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving history: {e}")
            return []


# Initialize diagnostics service
diagnostics = NetworkDiagnostics()

# Load configuration
def load_config() -> Dict:
    """Load configuration from file or environment"""
    config_path = Path("/config/netdiag.json")
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    
    # Default config
    return {
        "targets": ["8.8.8.8", "1.1.1.1", "localhost"],
        "scan_interval_seconds": 60,
        "ping_count": 4,
        "alert_loss_threshold_pct": 5,
        "alert_latency_threshold_ms": 100
    }

config = load_config()

# === API Routes ===

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()}), 200

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger an on-demand scan"""
    data = request.get_json() or {}
    targets = data.get('targets', config.get('targets', []))
    
    if not targets:
        return jsonify({"error": "No targets provided"}), 400
    
    results = diagnostics.scan_hosts(targets)
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "results": {host: asdict(result) for host, result in results.items()}
    }), 200

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get last scan results"""
    results = diagnostics.get_last_results()
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "results": {host: asdict(result) for host, result in results.items()}
    }), 200

@app.route('/api/results/<host>', methods=['GET'])
def get_host_results(host):
    """Get results for a specific host"""
    hours = request.args.get('hours', 1, type=int)
    history = diagnostics.get_history(host, hours)
    return jsonify({
        "host": host,
        "history": history
    }), 200

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    return jsonify(config), 200

@app.route('/api/config', methods=['PUT'])
def update_config():
    """Update configuration"""
    global config
    config.update(request.get_json())
    logger.info(f"Config updated: {config}")
    return jsonify(config), 200

# === Background Scheduler ===

def periodic_scan():
    """Run periodic scan based on config"""
    targets = config.get('targets', [])
    if targets:
        try:
            results = diagnostics.scan_hosts(targets)
            
            # Check for alerts
            alert_loss = config.get('alert_loss_threshold_pct', 5)
            alert_latency = config.get('alert_latency_threshold_ms', 100)
            
            for host, result in results.items():
                if result.status == "down":
                    logger.warning(f"ALERT: Host {host} is unreachable")
                elif result.packet_loss_pct and result.packet_loss_pct > alert_loss:
                    logger.warning(f"ALERT: Host {host} packet loss {result.packet_loss_pct}%")
                elif result.avg_ms and result.avg_ms > alert_latency:
                    logger.warning(f"ALERT: Host {host} latency {result.avg_ms}ms")
        except Exception as e:
            logger.error(f"Error in periodic scan: {e}")

def start_scheduler():
    """Start background scheduler"""
    scheduler = BackgroundScheduler()
    interval = config.get('scan_interval_seconds', 60)
    
    scheduler.add_job(
        periodic_scan,
        'interval',
        seconds=interval,
        id='periodic_scan',
        name='Periodic network scan'
    )
    
    scheduler.start()
    logger.info(f"Scheduler started with {interval}s interval")

if __name__ == '__main__':
    start_scheduler()
    app.run(host='0.0.0.0', port=5000, debug=False)
