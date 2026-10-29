import logging
import os

import requests

logger = logging.getLogger(__name__)

SMS_LEOPARD_URL = "https://api.smsleopard.com/v1/sms/send"
SMS_TIMEOUT = 15


def normalize_phone(phone_number: str) -> str:
    """
    Normalise a phone number for SMS Leopard.

    Kenyan and Rwandan numbers should be stored in international format,
    for example 2547XXXXXXXX or 2507XXXXXXXX.
    """
    phone = phone_number.strip().replace(" ", "").replace("-", "")

    if phone.startswith("+"):
        phone = phone[1:]

    if not phone.isdigit():
        raise ValueError("Phone number must contain digits and an optional leading '+'.")

    if not phone:
        raise ValueError("Phone number is required.")

    return f"+{phone}"


def send_sms(phone_number: str, message: str) -> bool:
    """
    Send an SMS using SMS Leopard.

    Returns True when SMS Leopard accepts the message for sending.
    Returns False when configuration, transport or provider errors occur.
    """
    api_key = os.getenv("SMS_LEOPARD_API_KEY")
    api_secret = os.getenv("SMS_LEOPARD_API_SECRET")
    sender_id = os.getenv("SMS_LEOPARD_SENDER_ID", "SMS_Leopard")

    if not api_key or not api_secret:
        logger.error("SMS Leopard credentials are not configured.")
        return False

    if not message or not message.strip():
        logger.error("Cannot send an empty SMS message.")
        return False

    try:
        destination = normalize_phone(phone_number)

        response = requests.post(
            SMS_LEOPARD_URL,
            auth=(api_key, api_secret),
            json={
                "source": sender_id,
                "message": message.strip(),
                "destination": [{"number": destination}],
            },
            timeout=SMS_TIMEOUT,
        )

        if response.status_code != 201:
            logger.error(
                "SMS Leopard request failed with HTTP status %s.",
                response.status_code,
            )
            return False

        try:
            result = response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error("SMS Leopard returned an invalid JSON response.")
            return False

        if not result.get("success"):
            logger.error("SMS Leopard did not accept the SMS request.")
            return False

        recipients = result.get("recipients", [])

        if not recipients:
            logger.error("SMS Leopard returned no recipient status.")
            return False

        accepted_statuses = {"queued", "success", "sent"}

        accepted = any(recipient.get("status", "").lower() in accepted_statuses for recipient in recipients)

        if not accepted:
            logger.warning("SMS Leopard did not confirm that the SMS was queued.")
            return False

        logger.info("SMS Leopard accepted the SMS for %s.", destination)
        return True

    except ValueError as exc:
        logger.warning("Invalid SMS destination: %s", exc)
        return False

    except requests.RequestException:
        logger.exception("Could not connect to SMS Leopard.")
        return False
