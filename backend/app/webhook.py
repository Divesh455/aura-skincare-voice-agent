import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
N8N_WEBHOOK_SECRET = os.getenv("N8N_WEBHOOK_SECRET", "aura_n8n_secret_dev")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@auraskincare.com")


def trigger_n8n_support_webhook(payload: dict[str, Any]) -> bool:
    """
    Trigger the n8n webhook asynchronously after call completion.
    Non-blocking: executed in a FastAPI background task so the client request
    returns immediately without waiting.
    """
    webhook_url = os.getenv("N8N_WEBHOOK_URL", N8N_WEBHOOK_URL).strip()
    if not webhook_url:
        logger.info("N8N_WEBHOOK_URL is not configured. Webhook dispatch skipped.")
        return False

    headers = {
        "Content-Type": "application/json",
        "X-Aura-Webhook-Secret": os.getenv("N8N_WEBHOOK_SECRET", N8N_WEBHOOK_SECRET),
        "User-Agent": "AuraSkincare-Backend/1.0",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook_url, json=payload, headers=headers)
            if response.status_code in (200, 201, 202):
                logger.info(
                    f"Successfully triggered n8n webhook for interaction {payload.get('interaction_id')}."
                )
                return True
            else:
                logger.warning(
                    f"n8n webhook returned status {response.status_code}: {response.text}"
                )
                return False

    except Exception as exc:
        logger.warning(f"Could not connect to n8n webhook at {webhook_url}: {exc}")
        return False
