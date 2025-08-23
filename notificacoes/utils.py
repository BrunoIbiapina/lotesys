# notificacoes/telegram.py
from __future__ import annotations
import os
import json
import time
from typing import Iterable, Optional
import requests

# Opcional: carrega .env em dev; em produção (Render) use env vars
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(override=True)
except Exception:
    pass

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
# Aceita 1 ou vários IDs separados por vírgula
DEFAULT_CHAT_IDS = [
    cid.strip() for cid in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if cid.strip()
]

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else ""


class TelegramNotConfigured(RuntimeError):
    pass


def _ensure_config() -> None:
    if not BOT_TOKEN:
        raise TelegramNotConfigured("TELEGRAM_BOT_TOKEN não configurado")
    if not API_BASE:
        raise TelegramNotConfigured("Token inválido ou não informado")


def tg_send(
    text: str,
    chat_ids: Optional[Iterable[str | int]] = None,
    *,
    parse_mode: Optional[str] = None,  # "MarkdownV2" | "HTML"
    disable_web_page_preview: bool = True,
    disable_notification: bool = False,
    timeout: int = 10,
    throttle_ms: int = 0,  # útil se enviar para vários IDs
) -> dict:
    """
    Envia uma mensagem de texto para 1 ou mais chat_ids.
    Se chat_ids não for informado, usa TELEGRAM_CHAT_IDS do ambiente.

    Retorna um dicionário com 'ok' geral e os resultados por chat.
    Nunca levanta exceção por erro de rede — apenas retorna 'ok': False nesse item.
    """
    _ensure_config()
    ids = list(chat_ids) if chat_ids else DEFAULT_CHAT_IDS
    if not ids:
        raise TelegramNotConfigured(
            "Nenhum chat_id informado e TELEGRAM_CHAT_IDS está vazio"
        )

    url = f"{API_BASE}/sendMessage"
    results = []
    for cid in ids:
        payload = {
            "chat_id": str(cid),
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
            "disable_notification": disable_notification,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            resp = requests.post(url, data=payload, timeout=timeout)
            data = resp.json() if resp.headers.get("content-type","").startswith("application/json") else {"ok": False, "description": resp.text}
            results.append({"chat_id": str(cid), "status": resp.status_code, "response": data})
        except Exception as e:
            # Não derruba a execução
            results.append({"chat_id": str(cid), "status": None, "response": {"ok": False, "error": str(e)}})

        if throttle_ms > 0:
            time.sleep(throttle_ms / 1000.0)

    return {"ok": all(r["response"].get("ok") for r in results), "results": results}


def tg_send_markdown(text_md: str, chat_ids: Optional[Iterable[str | int]] = None, **kwargs) -> dict:
    """Atalho para enviar com MarkdownV2 (escape se necessário)."""
    return tg_send(text_md, chat_ids, parse_mode="MarkdownV2", **kwargs)


def tg_send_html(text_html: str, chat_ids: Optional[Iterable[str | int]] = None, **kwargs) -> dict:
    """Atalho para enviar com HTML (tags suportadas pelo Telegram)."""
    return tg_send(text_html, chat_ids, parse_mode="HTML", **kwargs)