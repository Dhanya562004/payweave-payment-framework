"""
PayWeave Card Payment Method Handler.
Provides card BIN lookup simulation, Luhn validation check, and tokenization.
(No real card data is ever collected or processed).
"""

from typing import Tuple, Dict, Any


class CardHandler:
    """Helper utilities for card simulation."""

    @staticmethod
    def validate_luhn(card_number_str: str) -> bool:
        """Standard Luhn algorithm check on digits."""
        digits = [int(c) for c in card_number_str if c.isdigit()]
        if not digits or len(digits) < 13:
            return False
        checksum = 0
        reverse_digits = digits[::-1]
        for i, d in enumerate(reverse_digits):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0

    @staticmethod
    def get_bin_info(card_number_str: str) -> Dict[str, Any]:
        """Simulates BIN network detection (Visa, Mastercard, RuPay, Amex)."""
        clean = "".join([c for c in card_number_str if c.isdigit()])
        if clean.startswith("4"):
            brand = "VISA"
        elif clean.startswith(("51", "52", "53", "54", "55")):
            brand = "MASTERCARD"
        elif clean.startswith("60") or clean.startswith("6521"):
            brand = "RUPAY"
        elif clean.startswith(("34", "37")):
            brand = "AMEX"
        else:
            brand = "GENERIC_CARD"

        return {
            "bin": clean[:6] if len(clean) >= 6 else "400000",
            "brand": brand,
            "type": "CREDIT",
            "issuer": "Simulated Partner Bank"
        }
