import os

import qrcode

from app.config import BACKEND_URL


def generate_qr(registration_no: str) -> str:
    """Generate a QR code containing the public AUM verification URL."""
    os.makedirs("uploads/qr", exist_ok=True)

    path = f"uploads/qr/{registration_no}.png"
    verification_url = f"{BACKEND_URL}/api/volunteers/verify/{registration_no}"

    qr = qrcode.make(verification_url)
    qr.save(path)

    return path
