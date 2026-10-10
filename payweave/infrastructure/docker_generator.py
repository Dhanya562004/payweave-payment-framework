"""
PayWeave Docker Compose Generator.
Generates reproducible, multi-service Docker Compose topology from Declarative Merchant DSL.
Includes API gateway, Streamlit UI, Redis distributed state coordination, and isolated mock PSP nodes.
"""

import yaml
from typing import Dict, Any, Optional
from payweave.dsl.schema import MerchantConfig


class DockerComposeGenerator:
    """Generates Docker Compose specifications dynamically from PayWeave DSL configurations."""

    @staticmethod
    def generate_dict(config: Optional[MerchantConfig] = None) -> Dict[str, Any]:
        cfg = config or MerchantConfig()
        merchant_id = cfg.merchant.id
        primary_dc = cfg.infrastructure.primary_dc
        failover_dc = cfg.infrastructure.failover_dc

        services: Dict[str, Any] = {
            "payweave-api": {
                "build": {
                    "context": ".",
                    "dockerfile": "Dockerfile.api"
                },
                "image": "payweave-api:latest",
                "container_name": f"payweave-api-{merchant_id}",
                "ports": ["8000:8000"],
                "environment": {
                    "PORT": 8000,
                    "MERCHANT_ID": merchant_id,
                    "REDIS_URL": "redis://redis:6379/0",
                    "PRIMARY_DC": primary_dc,
                    "FAILOVER_DC": failover_dc,
                    "ANOMALY_THRESHOLD": cfg.anomaly.threshold,
                    "MAX_LATENCY_MS": cfg.infrastructure.max_latency_ms
                },
                "depends_on": {
                    "redis": {
                        "condition": "service_healthy"
                    }
                },
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 3,
                    "start_period": "5s"
                },
                "networks": ["payweave-network"],
                "restart": "unless-stopped"
            },
            "payweave-ui": {
                "build": {
                    "context": ".",
                    "dockerfile": "Dockerfile.ui"
                },
                "image": "payweave-ui:latest",
                "container_name": f"payweave-ui-{merchant_id}",
                "ports": ["8501:8501"],
                "environment": {
                    "API_BASE_URL": "http://payweave-api:8000",
                    "MERCHANT_ID": merchant_id
                },
                "depends_on": ["payweave-api"],
                "networks": ["payweave-network"],
                "restart": "unless-stopped"
            },
            "redis": {
                "image": "redis:7-alpine",
                "container_name": "payweave-redis-shared-state",
                "ports": ["6379:6379"],
                "command": ["redis-server", "--appendonly", "yes"],
                "volumes": ["redis-data:/data"],
                "healthcheck": {
                    "test": ["CMD", "redis-cli", "ping"],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 5
                },
                "networks": ["payweave-network"],
                "restart": "always"
            }
        }

        # Add simulated provider container mocks if fallback providers configured
        providers = cfg.routing.fallback.fallback_providers
        for p in providers:
            svc_name = f"mock-{p}"
            services[svc_name] = {
                "image": "kennethreitz/httpbin",
                "container_name": f"payweave-{p}",
                "environment": {
                    "PROVIDER_ID": p
                },
                "networks": ["payweave-network"],
                "restart": "unless-stopped"
            }

        compose_dict = {
            "version": "3.8",
            "services": services,
            "volumes": {
                "redis-data": {
                    "driver": "local"
                }
            },
            "networks": {
                "payweave-network": {
                    "driver": "bridge"
                }
            }
        }

        return compose_dict

    @staticmethod
    def generate(config: Optional[MerchantConfig] = None) -> str:
        """Serializes compose dictionary into clean YAML string."""
        compose_dict = DockerComposeGenerator.generate_dict(config)
        return yaml.dump(compose_dict, sort_keys=False, default_flow_style=False)

    @staticmethod
    def write_compose_file(output_path: str = "docker-compose.yml", config: Optional[MerchantConfig] = None) -> str:
        """Writes docker-compose.yml file and returns content."""
        content = DockerComposeGenerator.generate(config)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return content
