#!/usr/bin/env python3
"""
Example alert handler for netdiag service
Sends alerts to Slack, Discord, or webhook endpoint
"""

import requests
import json
import sys
from typing import Dict, Optional


class AlertHandler:
    def __init__(self, webhook_url: str, service_name: str = "netdiag"):
        self.webhook_url = webhook_url
        self.service_name = service_name
    
    def send_slack(self, host: str, alert_type: str, value: float, threshold: float):
        """Send alert to Slack webhook"""
        color = "danger" if alert_type == "down" else "warning"
        
        payload = {
            "attachments": [
                {
                    "fallback": f"{self.service_name}: {host} {alert_type}",
                    "color": color,
                    "title": f"Network Alert: {host}",
                    "text": f"{alert_type.title()} - Value: {value}",
                    "fields": [
                        {
                            "title": "Host",
                            "value": host,
                            "short": True
                        },
                        {
                            "title": "Alert Type",
                            "value": alert_type,
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": str(threshold),
                            "short": True
                        },
                        {
                            "title": "Current Value",
                            "value": str(value),
                            "short": True
                        }
                    ],
                    "footer": self.service_name,
                    "ts": int(__import__('time').time())
                }
            ]
        }
        
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=5)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending Slack alert: {e}", file=sys.stderr)
            return False
    
    def send_discord(self, host: str, alert_type: str, value: float, threshold: float):
        """Send alert to Discord webhook"""
        embed = {
            "title": f"Network Alert: {host}",
            "description": f"{alert_type.title()} detected",
            "color": 16711680 if alert_type == "down" else 16776960,  # Red or Yellow
            "fields": [
                {
                    "name": "Host",
                    "value": host,
                    "inline": True
                },
                {
                    "name": "Alert Type",
                    "value": alert_type,
                    "inline": True
                },
                {
                    "name": "Threshold",
                    "value": str(threshold),
                    "inline": True
                },
                {
                    "name": "Current Value",
                    "value": str(value),
                    "inline": True
                }
            ],
            "footer": {
                "text": self.service_name
            }
        }
        
        payload = {"embeds": [embed]}
        
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=5)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending Discord alert: {e}", file=sys.stderr)
            return False
    
    def send_generic(self, alert: Dict):
        """Send alert to generic webhook"""
        try:
            resp = requests.post(self.webhook_url, json=alert, timeout=5)
            resp.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending webhook alert: {e}", file=sys.stderr)
            return False


def parse_netdiag_log(log_line: str) -> Optional[Dict]:
    """Parse netdiag alert log line"""
    # Example: "WARNING - ALERT: Host 8.8.8.8 is unreachable"
    # Example: "WARNING - ALERT: Host 1.1.1.1 packet loss 15%"
    # Example: "WARNING - ALERT: Host 1.0.0.1 latency 250ms"
    
    if "ALERT:" not in log_line:
        return None
    
    try:
        parts = log_line.split("ALERT:")[1].strip()
        
        if "is unreachable" in parts:
            host = parts.split()[1]
            return {
                "type": "host_down",
                "host": host,
                "alert_type": "down",
                "value": 100.0,
                "unit": "%"
            }
        
        elif "packet loss" in parts:
            host = parts.split()[1]
            loss = float(parts.split()[-2])
            return {
                "type": "high_loss",
                "host": host,
                "alert_type": "packet_loss",
                "value": loss,
                "unit": "%"
            }
        
        elif "latency" in parts:
            host = parts.split()[1]
            latency = float(parts.split()[-2])
            return {
                "type": "high_latency",
                "host": host,
                "alert_type": "latency",
                "value": latency,
                "unit": "ms"
            }
    
    except (IndexError, ValueError):
        pass
    
    return None


# Example usage
if __name__ == "__main__":
    # Set your webhook URL (Slack example)
    WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    handler = AlertHandler(WEBHOOK_URL)
    
    # Example: Host down
    handler.send_slack("8.8.8.8", "down", 100.0, 0.0)
    
    # Example: High packet loss
    handler.send_slack("1.1.1.1", "packet_loss", 15.0, 5.0)
    
    # Example: High latency
    handler.send_slack("1.0.0.1", "latency", 250.0, 100.0)
