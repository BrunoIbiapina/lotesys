# notificacoes/views.py
import os, json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from .models import DestinatarioTelegram
from .utils import tg_send

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "secret")
TASK_TOKEN = os.getenv("TASK_TRIGGER_TOKEN", "task-secret")

HELP = (
    "Olá! Eu sou o bot do LoteSys.\n"
    "/start – registrar este chat para receber avisos\n"
    "/stop – parar de receber avisos\n"
    "/status – ver sua inscrição\n"
)

@csrf_exempt
def task_notify(request):
    if request.GET.get("token") != TASK_TOKEN:
        return HttpResponse(status=403)

    debug = request.GET.get("debug")
    if debug:
        call_command("avisos_telegram", dry_run=True, debug=True, verbosity=2)
        return HttpResponse("ok (dry-run + debug)")

    call_command("avisos_telegram")
    return HttpResponse("ok")

@csrf_exempt
def telegram_webhook(request, secret: str):
    if secret != WEBHOOK_SECRET:
        return HttpResponse(status=403)
    if request.method != "POST":
        return HttpResponse("ok")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponse("ignored")

    msg = payload.get("message") or payload.get("edited_message")
    if not msg:
        return HttpResponse("ignored")

    chat = msg.get("chat", {})
    chat_id = str(chat.get("id"))
    text = (msg.get("text") or "").strip().lower()

    if text.startswith("/start"):
        dest, _ = DestinatarioTelegram.objects.get_or_create(
            chat_id=chat_id,
            defaults={"nome": chat.get("first_name") or "Usuário"},
        )
        dest.ativo = True
        dest.save()
        tg_send(chat_id, "✅ Inscrição registrada!\n" + HELP)

    elif text.startswith("/stop"):
        try:
            dest = DestinatarioTelegram.objects.get(chat_id=chat_id)
            dest.ativo = False
            dest.save()
            tg_send(chat_id, "🛑 Ok, avisos desativados. Use /start para reativar.")
        except DestinatarioTelegram.DoesNotExist:
            tg_send(chat_id, "Você não está inscrito. Use /start.")

    elif text.startswith("/status"):
        try:
            d = DestinatarioTelegram.objects.get(chat_id=chat_id)
            tg_send(chat_id,
                f"Status: {'ativo' if d.ativo else 'inativo'}\n"
                f"Vence hoje: {'on' if d.recebe_vencimentos_hoje else 'off'}\n"
                f"Atrasados: {'on' if d.recebe_atrasados else 'off'}"
            )
        except DestinatarioTelegram.DoesNotExist:
            tg_send(chat_id, "Você não está inscrito. Use /start.")
    else:
        tg_send(chat_id, HELP)

    return JsonResponse({"ok": True})