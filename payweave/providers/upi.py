"""
PayWeave UPI Payment Method Handler.
Provides simulated UPI Virtual Payment Address (VPA) validation, intent links, and QR codes.
"""

import re
from typing import Tuple, Dict, Any


class UPIHandler:
    """Helper utilities for simulating UPI transactions."""

    @staticmethod
    def validate_vpa(vpa: str) -> Tuple[bool, str]:
        """Validates UPI VPA format (e.g. user@okaxis, merchant@upi)."""
        pattern = r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$"
        if re.match(pattern, vpa):
            return True, "Valid VPA format."
        return False, "Invalid UPI ID format. Expected format: name@bank"

    @staticmethod
    def generate_simulated_qr_code(amount: float, merchant_vpa: str = "payweave@simulator") -> Dict[str, Any]:
        """Generates synthetic UPI intent payload for simulation."""
        intent_url = f"upi://pay?pa={merchant_vpa}&pn=PayWeaveMerchant&am={amount:.2f}&cu=INR"
        return {
            "merchant_vpa": merchant_vpa,
            "amount": amount,
            "currency": "INR",
            "intent_url": intent_url,
            "qr_payload_simulated": f"BASE64_SIMULATED_QR_{amount}"
        }
