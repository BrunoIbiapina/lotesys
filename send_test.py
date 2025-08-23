# send_test.py
import os, requests
from dotenv import load_dotenv

# força sobrescrever variáveis já existentes no ambiente
load_dotenv(override=True)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_IDS")

print("BOT_TOKEN:", BOT_TOKEN)
print("CHAT_ID:", CHAT_ID)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": "✅ Teste do bot Concil: integração funcionando!"}
print(requests.post(url, data=payload).json())