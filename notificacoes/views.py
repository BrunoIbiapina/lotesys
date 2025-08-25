# notificacoes/views.py
import os
import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.management import call_command
from django.db.models import Q, Sum

# (opcionais)
try:
    from .models import DestinatarioTelegram
except Exception:
    DestinatarioTelegram = None

try:
    from .utils import tg_send
except Exception:
    def tg_send(chat_id, text):
        pass

WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "secret")
TASK_TOKEN = os.getenv("TASK_TRIGGER_TOKEN", "task-secret")

HELP = (
    "Olá! Eu sou o bot do LoteSys.\n"
    "/start – registrar este chat para receber avisos\n"
    "/stop – parar de receber avisos\n"
    "/status – ver sua inscrição\n"
)

def _stats_text():
    """Mostra contagens básicas de parcelas (diagnóstico rápido)."""
    try:
        from vendas.models import Parcela
    except Exception:
        from financeiro.models import Parcela  # type: ignore

    hoje = timezone.localdate()
    elegiveis = Parcela.objects.filter(
        Q(status__iexact="PENDENTE") | Q(status__iexact="VENCIDO"),
        vencimento__isnull=False,
    )
    vencem_hoje = elegiveis.filter(vencimento=hoje)
    atrasadas = elegiveis.filter(vencimento__lt=hoje)

    total_hoje = vencem_hoje.aggregate(s=Sum("valor"))["s"] or 0
    total_atraso = atrasadas.aggregate(s=Sum("valor"))["s"] or 0

    return (
        "[stats]\n"
        f"hoje={hoje}\n"
        f"elegiveis_qtd={elegiveis.count()}\n"
        f"vencem_hoje_qtd={vencem_hoje.count()} total_hoje={total_hoje}\n"
        f"atrasadas_qtd={atrasadas.count()} total_atraso={total_atraso}\n"
    )

@csrf_exempt
def task_notify(request):
    """
    GET /notificacoes/run/?token=...&dry_run=1&force=1&debug=1&date=YYYY-MM-DD
    ou GET /notificacoes/run/?token=...&stats=1 para texto de diagnóstico.
    """
    if request.GET.get("token") != TASK_TOKEN:
        return HttpResponse(status=403)

    if request.GET.get("stats") == "1":
        return HttpResponse(_stats_text(), content_type="text/plain; charset=utf-8")

    # flags -> kwargs do management command
    def _flag(name: str) -> bool:
        v = request.GET.get(name, "")
        return v in ("1", "true", "True", "yes", "on")

    dry_run = _flag("dry_run")
    force = _flag("force")
    debug = _flag("debug")
    date_str = request.GET.get("date")

    kwargs = {}
    if dry_run: kwargs["dry_run"] = True
    if force: kwargs["force"] = True
    if debug: kwargs["debug"] = True
    if date_str: kwargs["date"] = date_str

    call_command("avisos_telegram", **kwargs)

    parts = []
    if dry_run: parts.append("dry-run")
    if force: parts.append("force")
    if debug: parts.append("debug")
    if date_str: parts.append(f"date={date_str}")

    body = "ok" + (f" ({', '.join(parts)})" if parts else "")
    return HttpResponse(body, content_type="text/plain; charset=utf-8")

@csrf_exempt
def telegram_webhook(request, secret: str):
    """
    POST do Telegram chega aqui. Também aceita GET para teste manual.
    """
    if secret != WEBHOOK_SECRET:
        return HttpResponse(status=403)

    if request.method == "GET":
        # útil para testar no navegador/cURL
        return HttpResponse("ok (webhook up)", content_type="text/plain; charset=utf-8")

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
        if DestinatarioTelegram:
            dest, _ = DestinatarioTelegram.objects.get_or_create(
                chat_id=chat_id,
                defaults={"nome": chat.get("first_name") or "Usuário"},
            )
            dest.ativo = True
            dest.save()
        tg_send(chat_id, "✅ Inscrição registrada!\n" + HELP)

    elif text.startswith("/stop"):
        if DestinatarioTelegram:
            try:
                dest = DestinatarioTelegram.objects.get(chat_id=chat_id)
                dest.ativo = False
                dest.save()
                tg_send(chat_id, "🛑 Ok, avisos desativados. Use /start para reativar.")
            except DestinatarioTelegram.DoesNotExist:
                tg_send(chat_id, "Você não está inscrito. Use /start.")
        else:
            tg_send(chat_id, "🛑 Ok. (Cadastro simples indisponível)")

    elif text.startswith("/status"):
        if DestinatarioTelegram:
            try:
                d = DestinatarioTelegram.objects.get(chat_id=chat_id)
                tg_send(
                    chat_id,
                    f"Status: {'ativo' if d.ativo else 'inativo'}\n"
                    f"Vence hoje: {'on' if getattr(d, 'recebe_vencimentos_hoje', True) else 'off'}\n"
                    f"Atrasados: {'on' if getattr(d, 'recebe_atrasados', True) else 'off'}"
                )
            except DestinatarioTelegram.DoesNotExist:
                tg_send(chat_id, "Você não está inscrito. Use /start.")
        else:
            tg_send(chat_id, "Cadastro simples indisponível.")
    else:
        tg_send(chat_id, HELP)

    return JsonResponse({"ok": True})