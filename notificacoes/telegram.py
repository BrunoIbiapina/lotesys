# notificacoes/telegram.py
import os
import requests

def tg_send(texto: str, chat_id: str | None = None) -> None:
    """
    Envia uma mensagem de texto simples via Telegram.
    - Usa TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_IDS (se não for passado chat_id).
    - Silenciosa em caso de erro de rede (não derruba execução).
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado")

    if not chat_id:
        chats = os.getenv("TELEGRAM_CHAT_IDS", "").strip()
        if not chats:
            raise RuntimeError("TELEGRAM_CHAT_IDS não configurado")
        chat_id = chats.split(",")[0].strip()

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(
            url,
            json={"chat_id": chat_id, "text": texto, "parse_mode": "HTML"},
            timeout=15,
        )
    except Exception:
        # não quebra a execução se houver falha de rede/timeout
        pass