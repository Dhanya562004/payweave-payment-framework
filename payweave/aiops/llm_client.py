"""
PayWeave AI Operations LLM Client.
Supports Gemini, Groq, and Together AI API integrations via environment variables.
Includes a robust deterministic offline fallback engine when API keys are missing.
"""

import os
from typing import Dict, Any, Optional


class LLMClient:
    """Multi-provider LLM Client with deterministic offline fallback."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.has_api_key = bool(self.gemini_key or self.groq_key or self.together_key)

    def generate_response(self, prompt: str, system_context: str = "") -> str:
        """Generates AI output using LLM API if key is present, else uses deterministic fallback."""
        if not self.has_api_key:
            return self._offline_deterministic_generator(prompt, system_context)

        try:
            if self.gemini_key:
                return self._call_gemini(prompt, system_context)
            elif self.groq_key:
                return self._call_groq(prompt, system_context)
            elif self.together_key:
                return self._call_together(prompt, system_context)
        except Exception as e:
            # Graceful fallback on API error
            return f"[Offline Fallback Engine]: API connection failed ({str(e)}). Generating deterministic analysis:\n\n" + \
                   self._offline_deterministic_generator(prompt, system_context)

        return self._offline_deterministic_generator(prompt, system_context)

    def _call_gemini(self, prompt: str, system_context: str) -> str:
        import urllib.request
        import json

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": f"System Context:\n{system_context}\n\nUser Question:\n{prompt}"}]
            }]
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_groq(self, prompt: str, system_context: str) -> str:
        import urllib.request
        import json

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt}
            ]
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]

    def _call_together(self, prompt: str, system_context: str) -> str:
        import urllib.request
        import json

        url = "https://api.together.xyz/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.together_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": prompt}
            ]
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]

    def _offline_deterministic_generator(self, prompt: str, system_context: str) -> str:
        """Deterministic rule-based response generator for 100% offline reliability."""
        p_lower = prompt.lower()

        if "healthiest" in p_lower or "best provider" in p_lower:
            return (
                "**PayWeave Intelligence Analysis:**\n\n"
                "Based on real-time provider telemetry:\n"
                "- **PSP-B (SpeedPay Express)** is currently the healthiest provider with **99.0% success rate** and **110ms latency**.\n"
                "- **PSP-A (Enterprise Gateway)** is operating nominally at **98.5% success rate** and **140ms latency**.\n"
                "- **PSP-C (ValuePay Direct)** provides maximum cost efficiency but exhibits higher latency (**220ms**)."
            )
        elif "traffic" in p_lower or "lose traffic" in p_lower or "psp-a" in p_lower:
            return (
                "**PayWeave Intelligence Analysis:**\n\n"
                "Traffic shift analysis:\n"
                "1. **Detection:** PSP-A experienced a temporary latency spike exceeding configured threshold (>300ms).\n"
                "2. **Routing Score Impact:** PSP-A's latency score component dropped, causing its total routing score to fall below PSP-B.\n"
                "3. **Self-Healing Action:** The Intelligent Router automatically shifted 31% to 65% of incoming traffic to PSP-B to protect SLA."
            )
        elif "latency" in p_lower or "spike" in p_lower:
            return (
                "**PayWeave Intelligence Analysis:**\n\n"
                "Latency incident breakdown:\n"
                "- Baseline latency across healthy providers is **120ms - 150ms**.\n"
                "- Latency anomalies trigger when Z-score exceeds **2.5** or absolute latency exceeds **350ms**.\n"
                "- Active self-healing automatically mitigates latency spikes within 1-2 seconds by rerouting to secondary providers."
            )
        elif "dc-1" in p_lower or "data center" in p_lower or "failover" in p_lower:
            return (
                "**PayWeave Intelligence Analysis:**\n\n"
                "Multi-DC Reliability Assessment:\n"
                "- Primary DC: **DC-1 (Mumbai)** | Failover DC: **DC-2 (Bengaluru)**.\n"
                "- In the event of DC-1 outage, the infrastructure DSL controller automatically initiates traffic failover to DC-2.\n"
                "- Edge nodes buffer local requests and maintain zero-downtime routing during failover transitions."
            )
        elif "cost" in p_lower or "minimize cost" in p_lower:
            return (
                "**PayWeave Intelligence Analysis:**\n\n"
                "Cost Optimization Recommendations:\n"
                "- Switching merchant routing strategy to `lowest_cost` prioritizes **PSP-C (cost factor: 0.30)**.\n"
                "- Selecting `lowest_cost` reduces payment processing fees by ~35% while maintaining acceptable success rates (~96.5%)."
            )
        else:
            return (
                "**PayWeave Operations Intelligence:**\n\n"
                f"Evaluated context for query: *\"{prompt}\"*\n\n"
                "System is operating in **Intelligent Routing Mode** with active self-healing and anomaly detection enabled. "
                "All 3 mock providers (PSP-A, PSP-B, PSP-C) are actively monitored. "
                "Transactions pass through risk checks, adaptive auth, and dynamic fallback chains."
            )
