"""
PayWeave Kubernetes (K8s) Manifest Generator.
Generates production-grade Kubernetes YAML manifests from the merchant's Declarative DSL:
  - Namespace & ConfigMap
  - API Deployment & Service with Liveness/Readiness Probes
  - UI Deployment & Service
  - Redis Shared State Deployment & Service
  - Horizontal Pod Autoscaler (HPA) targeting CPU utilization
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from payweave.dsl.schema import MerchantConfig


class KubernetesManifestGenerator:
    """Generates declarative Kubernetes deployment manifests from PayWeave configurations."""

    @staticmethod
    def generate(config: Optional[MerchantConfig] = None) -> str:
        cfg = config or MerchantConfig()
        merchant_id = cfg.merchant.id
        primary_dc = cfg.infrastructure.primary_dc
        failover_dc = cfg.infrastructure.failover_dc

        manifest = f"""# ==============================================================================
# PayWeave Kubernetes Deployment Specification
# Merchant: {cfg.merchant.name} ({merchant_id})
# Generated from PayWeave Declarative Payment DSL
# ==============================================================================

apiVersion: v1
kind: Namespace
metadata:
  name: payweave-system
  labels:
    app.kubernetes.io/name: payweave
    app.kubernetes.io/part-of: payment-infrastructure
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: payweave-config
  namespace: payweave-system
data:
  MERCHANT_ID: "{merchant_id}"
  PRIMARY_DC: "{primary_dc}"
  FAILOVER_DC: "{failover_dc}"
  REDIS_URL: "redis://redis.payweave-system.svc.cluster.local:6379/0"
  PORT: "8000"
---
# ------------------------------------------------------------------------------
# Redis Shared State Coordination Layer
# ------------------------------------------------------------------------------
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-shared-state
  namespace: payweave-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command: ["redis-server", "--appendonly", "yes"]
          ports:
            - containerPort: 6379
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: payweave-system
spec:
  type: ClusterIP
  ports:
    - port: 6379
      targetPort: 6379
  selector:
    app: redis
---
# ------------------------------------------------------------------------------
# PayWeave FastAPI Routing Engine & ACID Ledger
# ------------------------------------------------------------------------------
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payweave-api
  namespace: payweave-system
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: payweave-api
  template:
    metadata:
      labels:
        app: payweave-api
    spec:
      containers:
        - name: api
          image: payweave-api:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: payweave-config
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: payweave-api
  namespace: payweave-system
spec:
  type: ClusterIP
  ports:
    - port: 8000
      targetPort: 8000
      name: http
  selector:
    app: payweave-api
---
# ------------------------------------------------------------------------------
# Horizontal Pod Autoscaler (HPA) for High-Throughput Burst Scaling
# ------------------------------------------------------------------------------
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payweave-api-hpa
  namespace: payweave-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payweave-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
---
# ------------------------------------------------------------------------------
# PayWeave Streamlit UI Dashboard
# ------------------------------------------------------------------------------
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payweave-ui
  namespace: payweave-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: payweave-ui
  template:
    metadata:
      labels:
        app: payweave-ui
    spec:
      containers:
        - name: ui
          image: payweave-ui:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8501
          env:
            - name: API_BASE_URL
              value: "http://payweave-api.payweave-system.svc.cluster.local:8000"
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: payweave-ui
  namespace: payweave-system
spec:
  type: LoadBalancer
  ports:
    - port: 8501
      targetPort: 8501
      name: http
  selector:
    app: payweave-ui
"""
        return manifest

    @staticmethod
    def write_manifests(output_path: str = "infrastructure/k8s/payweave-k8s.yaml", config: Optional[MerchantConfig] = None) -> str:
        content = KubernetesManifestGenerator.generate(config)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return content
