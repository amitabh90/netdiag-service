"""
Network Diagnostics Service Python Client
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime


class NetDiagClient:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health(self) -> Dict:
        """Check service health"""
        resp = self.session.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()
    
    def scan(self, targets: Optional[List[str]] = None) -> Dict:
        """Trigger an on-demand scan"""
        data = {}
        if targets:
            data["targets"] = targets
        
        resp = self.session.post(
            f"{self.base_url}/api/scan",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        return resp.json()
    
    def get_results(self, host: Optional[str] = None) -> Dict:
        """Get latest scan results (all or specific host)"""
        if host:
            resp = self.session.get(f"{self.base_url}/api/results/{host}")
        else:
            resp = self.session.get(f"{self.base_url}/api/results")
        
        resp.raise_for_status()
        return resp.json()
    
    def get_history(self, host: str, hours: int = 1) -> List[Dict]:
        """Get historical results for a host"""
        resp = self.session.get(
            f"{self.base_url}/api/results/{host}",
            params={"hours": hours}
        )
        resp.raise_for_status()
        return resp.json().get("history", [])
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        resp = self.session.get(f"{self.base_url}/api/config")
        resp.raise_for_status()
        return resp.json()
    
    def update_config(self, config: Dict) -> Dict:
        """Update configuration"""
        resp = self.session.put(
            f"{self.base_url}/api/config",
            json=config,
            headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        return resp.json()
    
    def set_config_value(self, key: str, value) -> Dict:
        """Update a single config value"""
        config = self.get_config()
        config[key] = value
        return self.update_config(config)
    
    def print_results(self, results: Dict, verbose: bool = False):
        """Pretty print results"""
        if "results" in results:
            results = results["results"]
        
        print(f"\n{'Host':<15} {'Status':<10} {'Avg Latency':<12} {'Loss %':<8} {'Packets':<10}")
        print("-" * 60)
        
        for host, data in results.items():
            status = data.get("status", "unknown").upper()
            avg = f"{data['avg_ms']:.2f}ms" if data.get("avg_ms") else "N/A"
            loss = f"{data.get('packet_loss_pct', 0):.1f}%"
            packets = f"{data.get('packets_sent', 0)}/{data.get('packets_received', 0)}"
            
            print(f"{host:<15} {status:<10} {avg:<12} {loss:<8} {packets:<10}")
        
        if verbose:
            print(f"\n{json.dumps(results, indent=2)}")


if __name__ == "__main__":
    # Example usage
    client = NetDiagClient()
    
    # Check health
    print("Health:", client.health())
    
    # Get config
    print("\nConfig:", client.get_config())
    
    # Trigger scan
    print("\nScanning...")
    results = client.scan(["8.8.8.8", "1.1.1.1"])
    
    # Print results
    client.print_results(results)
