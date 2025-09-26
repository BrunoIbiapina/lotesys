# lotesys/activepieces.py
import os, logging, requests
from typing import Any, Dict

log = logging.getLogger(__name__)

AP_URL = os.environ.get("AP_WEBHOOK_URL")
AP_TOKEN = os.environ.get("AP_WEBHOOK_TOKEN", "")

def send_event(payload: Dict[str, Any]) -> None:
    if not AP_URL:
        log.error("AP_WEBHOOK_URL não configurada")
        return
    try:
        resp = requests.post(
            AP_URL,
            json=payload,
            headers={"Content-Type": "application/json", "X-AP-Token": AP_TOKEN},
            timeout=10,
        )
        resp.raise_for_status()
        log.info("Activepieces OK %s", resp.status_code)
    except Exception as e:
        log.exception("Falha ao notificar Activepieces: %s", e)