"""
PayWeave Multi-Data-Center Failover Simulator.
Simulates DC-1 primary, DC-2 failover, capacity shifting, outage injection, and failover recovery.
"""

from typing import Dict, Any, List
import time
from payweave.infrastructure.infrastructure_dsl import InfrastructureDSLConfig, DataCenterSpec


class MultiDCSimulator:
    """Simulates distributed multi-datacenter operational states and failover behavior."""

    def __init__(self, config: InfrastructureDSLConfig = None):
        self.config = config or InfrastructureDSLConfig(
            datacenters={
                "dc1": DataCenterSpec(name="Mumbai DC1 Primary", capacity=1000, providers=["psp-a", "psp-b"]),
                "dc2": DataCenterSpec(name="Bengaluru DC2 Failover", capacity=1000, providers=["psp-b", "psp-c"])
            }
        )
        self.dc1_outage = False
        self.dc2_outage = False
        self.active_dc = self.config.primary_dc
        self.failover_history: List[Dict[str, Any]] = []

    def simulate_dc_failure(self, dc_id: str) -> Dict[str, Any]:
        """Injects a simulated data center outage."""
        if dc_id in self.config.datacenters:
            self.config.datacenters[dc_id].status = "unhealthy"
            
            if dc_id == self.config.primary_dc:
                self.dc1_outage = True
                self.active_dc = self.config.failover_dc
                
                # Shift capacity to failover DC
                self.config.datacenters[self.config.failover_dc].capacity = 1800
                
                log_entry = {
                    "timestamp": time.time(),
                    "formatted_time": time.strftime("%H:%M:%S"),
                    "event": f"DC OUTAGE DETECTED on {dc_id.upper()}",
                    "action": f"Automatic failover triggered. Active traffic shifted to {self.config.failover_dc.upper()}.",
                    "new_active_dc": self.config.failover_dc
                }
                self.failover_history.append(log_entry)
                return log_entry
        return {"status": "NO_CHANGE"}

    def recover_dc(self, dc_id: str) -> Dict[str, Any]:
        """Restores a data center from outage status."""
        if dc_id in self.config.datacenters:
            self.config.datacenters[dc_id].status = "healthy"
            if dc_id == "dc1":
                self.dc1_outage = False
                self.active_dc = self.config.primary_dc
                self.config.datacenters["dc2"].capacity = 1000
                
                log_entry = {
                    "timestamp": time.time(),
                    "formatted_time": time.strftime("%H:%M:%S"),
                    "event": f"DC RECOVERY CONFIRMED on {dc_id.upper()}",
                    "action": f"Restored primary traffic flow to {self.config.primary_dc.upper()}.",
                    "new_active_dc": self.config.primary_dc
                }
                self.failover_history.append(log_entry)
                return log_entry
        return {"status": "NO_CHANGE"}

    def get_dc_status_summary(self) -> Dict[str, Any]:
        return {
            "primary_dc": self.config.primary_dc,
            "failover_dc": self.config.failover_dc,
            "active_dc": self.active_dc,
            "auto_failover_enabled": self.config.auto_failover,
            "datacenters": {
                k: {
                    "name": v.name,
                    "status": v.status,
                    "capacity": v.capacity,
                    "providers": v.providers,
                    "baseline_latency_ms": v.baseline_latency_ms
                }
                for k, v in self.config.datacenters.items()
            },
            "recent_events": self.failover_history[-5:]
        }
