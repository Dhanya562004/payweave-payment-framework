"""
PayWeave Synthetic Telemetry Generator.
Generates realistic streaming telemetry and allows on-demand anomaly injection.
"""

import time
import random
from typing import List, Dict, Any


class TelemetrySimulator:
    """Generates synthetic payment operational metrics for visualization & testing."""

    @staticmethod
    def generate_telemetry_stream(num_records: int = 50,
                                  inject_anomaly_provider: str = None) -> List[Dict[str, Any]]:
        providers = ["psp-a", "psp-b", "psp-c"]
        regions = ["asia_south_1", "asia_south_2", "us_east_1"]
        methods = ["upi", "card"]
        records = []

        now = time.time() - (num_records * 5)

        for i in range(num_records):
            timestamp = now + (i * 5)
            pid = providers[i % len(providers)]
            
            # Baseline normal metrics
            if pid == "psp-a":
                base_lat = 140.0
                base_succ = 0.985
                base_err = 0.015
            elif pid == "psp-b":
                base_lat = 110.0
                base_succ = 0.990
                base_err = 0.010
            else:
                base_lat = 220.0
                base_succ = 0.965
                base_err = 0.035

            lat = base_lat + random.uniform(-15.0, 20.0)
            succ = min(1.0, max(0.0, base_succ + random.uniform(-0.01, 0.005)))
            err = 1.0 - succ

            # Anomaly injection for testing
            if inject_anomaly_provider and pid == inject_anomaly_provider and i >= (num_records - 10):
                lat = base_lat * random.uniform(3.0, 4.5)  # 3x-4.5x latency spike
                succ = max(0.40, base_succ - random.uniform(0.35, 0.50))  # drop to ~50%
                err = 1.0 - succ

            records.append({
                "timestamp": timestamp,
                "formatted_time": time.strftime("%H:%M:%S", time.localtime(timestamp)),
                "provider": pid,
                "transaction_count": random.randint(150, 600),
                "success_rate": round(succ, 4),
                "latency": round(lat, 2),
                "error_rate": round(err, 4),
                "amount": round(random.uniform(250.0, 25000.0), 2),
                "region": random.choice(regions),
                "payment_method": random.choice(methods)
            })

        return records
