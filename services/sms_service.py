import logging
import os
import re

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)


def _to_international(phone: str) -> str:
    """Convert a Rwanda phone number to international format."""
    return "+250" + re.sub(r"\D", "", phone or "")[-9:]


class SmsService:
    def __init__(self, db: Session):
        self.db = db

    def send_custom_sms(self, phone_number: str, message: str) -> bool:
        """Send an SMS through Africa's Talking when credentials are configured."""
        username = os.getenv("AT_USERNAME")
        api_key = os.getenv("AT_API_KEY")

        if not (username and api_key):
            logger.warning(
                "SMS (not sent, no AT credentials) to %s",
                phone_number,
            )
            return False

        import africastalking

        africastalking.initialize(username, api_key)
        response = africastalking.SMS.send(
            message,
            [_to_international(phone_number)],
        )
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        ok = bool(recipients) and all(
            recipient.get("status") == "Success" for recipient in recipients
        )

        if ok:
            logger.info("SMS sent to %s: %s", phone_number, message)
        else:
            logger.error(
                "Africa's Talking rejected SMS to %s: %s",
                phone_number,
                response,
            )

        return ok
