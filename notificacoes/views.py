# notificacoes/views.py
import os
import json
import logging
from threading import Thread

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.management import call_command
from django.db.models import Q, Sum

logger = logging.getLogger(__name__)

# (opcionais)
try:
    from .models import DestinatarioTelegram
except Exception:
    DestinatarioTelegram = None

# Preferimos usar o util, mas nunca bloquear a view
try:
    from .utils import tg_send as _tg_send_util  # pode ter timeout interno
except Exception:
    _tg_send_util = None

# === ENV ===
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "secret")
TASK_TOKEN = os.getenv("TASK_TRIGGER_TOKEN", "task-secret")

# === AJUDA / MENU ===
HELP = (
    "Olá! Eu sou o bot do LoteSys.\n"
    "/start – registrar este chat para receber avisos\n"
    "/stop – parar de receber avisos\n"
    "/status – ver sua inscrição\n"
    "/id – ver seu chat_id\n"
    "/help – este menu\n\n"
    "Menu rápido:\n"
    "1️⃣ Vencem hoje\n"
    "2️⃣ Atrasadas\n"
    "3️⃣ Resumo\n"
)

# ---------- Utilidades ----------
def _get_parcela_model():
    try:
        from vendas.models import Parcela
    except Exception:
        from financeiro.models import Parcela  # type: ignore
    return Parcela

def _brl(x) -> str:
    try:
        v = float(x or 0)
    except Exception:
        v = 0.0
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def _stats_text():
    """Mostra contagens básicas de parcelas (diagnóstico rápido)."""
    Parcela = _get_parcela_model()
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

def _flag_from_qs(request, name: str) -> bool:
    v = (request.GET.get(name) or "").strip()
    return v in ("1", "true", "True", "yes", "on")

def tg_send_safe(chat_id: str, text: str) -> None:
    """
    Envia mensagem sem nunca bloquear a resposta do webhook.
    Usa utilidade se existir; caso contrário, fallback via requests com timeout curto.
    """
    try:
        if _tg_send_util:
            _tg_send_util(chat_id, text)
        else:
            import requests
            token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            if not token:
                logger.warning("TELEGRAM_BOT_TOKEN ausente; não foi possível enviar para %s", chat_id)
                return
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            requests.post(
                url,
                json={"chat_id": str(chat_id), "text": text, "parse_mode": "HTML"},
                timeout=5,  # timeout curto
            )
    except Exception as e:
        # Nunca deixar exceção vazar
        logger.exception("Falha ao enviar Telegram: %s", e)

# ---------- Trigger HTTP para rodar o comando avisos_telegram ----------
@csrf_exempt
def task_notify(request):
    """
    GET /notificacoes/run/?token=...&dry_run=1&force=1&debug=1&date=YYYY-MM-DD
    GET /notificacoes/run/?token=...&stats=1      -> texto de diagnóstico
    GET /notificacoes/run/?token=...&echo=webhook -> ecoa o segredo do webhook (mascarado)
    GET /notificacoes/run/?token=...&send=Oi&chat_id=842553869 -> envia teste direto
    """
    if request.GET.get("token") != TASK_TOKEN:
        return HttpResponse(status=403)

    # eco do segredo do webhook
    if request.GET.get("echo") == "webhook":
        masked = WEBHOOK_SECRET[:2] + "…" if WEBHOOK_SECRET else "(vazio)"
        return HttpResponse(f"webhook_secret={masked}", content_type="text/plain; charset=utf-8")

    # envio de teste direto
    if request.GET.get("send"):
        chat_id = request.GET.get("chat_id")
        if not chat_id:
            return HttpResponse("faltou chat_id", status=400)
        msg = request.GET.get("send")
        Thread(target=tg_send_safe, args=(chat_id, msg), daemon=True).start()
        return HttpResponse("ok (send)", content_type="text/plain; charset=utf-8")

    # stats
    if request.GET.get("stats") == "1":
        return HttpResponse(_stats_text(), content_type="text/plain; charset=utf-8")

    # flags -> kwargs do management command
    dry_run = _flag_from_qs(request, "dry_run")
    force   = _flag_from_qs(request, "force")
    debug   = _flag_from_qs(request, "debug")
    date_str = request.GET.get("date")

    kwargs = {}
    if dry_run: kwargs["dry_run"] = True
    if force:   kwargs["force"] = True
    if debug:   kwargs["debug"] = True
    if date_str: kwargs["date"] = date_str

    call_command("avisos_telegram", **kwargs)

    parts = []
    if dry_run: parts.append("dry-run")
    if force:   parts.append("force")
    if debug:   parts.append("debug")
    if date_str: parts.append(f"date={date_str}")
    body = "ok" + (f" ({', '.join(parts)})" if parts else "")
    return HttpResponse(body, content_type="text/plain; charset=utf-8")

# ---------- Processamento do webhook (em thread) ----------
def _process_update(payload: dict) -> None:
    """
    Faz todo o trabalho pesado do webhook fora da request HTTP,
    para responder rápido ao Telegram.
    """
    try:
        msg = payload.get("message") or payload.get("edited_message")
        if not msg:
            return

        chat = msg.get("chat", {})
        chat_id = str(chat.get("id"))
        text_raw = (msg.get("text") or "").strip()
        text = text_raw.lower()

        logger.info("Webhook msg chat_id=%s text=%r", chat_id, text_raw)

        Parcela = _get_parcela_model()
        hoje = timezone.localdate()

        # ----- Comandos -----
        if text.startswith("/start"):
            if DestinatarioTelegram:
                dest, _ = DestinatarioTelegram.objects.get_or_create(
                    chat_id=chat_id,
                    defaults={"nome": chat.get("first_name") or "Usuário"},
                )
                dest.ativo = True
                dest.save()
            tg_send_safe(chat_id, "✅ Inscrição registrada!\n" + HELP)
            return

        if text.startswith("/id"):
            tg_send_safe(chat_id, f"Seu chat_id é: <code>{chat_id}</code>")
            return

        if text.startswith("/help") or text == "menu":
            tg_send_safe(chat_id, HELP)
            return

        if text.startswith("/stop"):
            if DestinatarioTelegram:
                try:
                    dest = DestinatarioTelegram.objects.get(chat_id=chat_id)
                    dest.ativo = False
                    dest.save()
                    tg_send_safe(chat_id, "🛑 Ok, avisos desativados. Use /start para reativar.")
                except DestinatarioTelegram.DoesNotExist:
                    tg_send_safe(chat_id, "Você não está inscrito. Use /start.")
            else:
                tg_send_safe(chat_id, "🛑 Ok. (Cadastro simples indisponível)")
            return

        if text.startswith("/status"):
            if DestinatarioTelegram:
                try:
                    d = DestinatarioTelegram.objects.get(chat_id=chat_id)
                    tg_send_safe(
                        chat_id,
                        f"Status: {'ativo' if d.ativo else 'inativo'}\n"
                        f"Vence hoje: {'on' if getattr(d, 'recebe_vencimentos_hoje', True) else 'off'}\n"
                        f"Atrasados: {'on' if getattr(d, 'recebe_atrasados', True) else 'off'}"
                    )
                except DestinatarioTelegram.DoesNotExist:
                    tg_send_safe(chat_id, "Você não está inscrito. Use /start.")
            else:
                tg_send_safe(chat_id, "Cadastro simples indisponível.")
            return

        # ----- Menu rápido (1/2/3) -----
        def _fmt_lista(qs, titulo: str):
            linhas = []
            total = 0.0
            for p in qs[:10]:
                venda_id = getattr(p, "venda_id", None)
                cliente = getattr(getattr(p, "venda", None), "cliente", None)
                nome = getattr(cliente, "nome", "Cliente")
                numero = getattr(p, "numero", "?")
                total_parc = getattr(getattr(p, "venda", None), "parcelas_total", "?")
                v = float(getattr(p, "valor", 0) or 0)
                total += v
                ven = getattr(p, "vencimento", None)
                ven = ven.strftime("%d/%m/%Y") if ven else "s/ data"
                linhas.append(
                    f"• Venda #{venda_id} — {nome} — Parc. {numero}/{total_parc} — {_brl(v)} — {ven}"
                )
            cab = f"<b>{titulo}</b>\n\n" if linhas else f"<b>{titulo}</b>\n\n(sem itens)"
            rod = f"\n\n<b>Total:</b> {_brl(total)}" if linhas else ""
            return cab + "\n".join(linhas) + rod

        if text in ("1", "vencem hoje", "hoje"):
            qs = (
                Parcela.objects.filter(status__iexact="PENDENTE", vencimento=hoje)
                .select_related("venda", "venda__cliente")
                .order_by("vencimento", "venda_id", "numero")
            )
            tg_send_safe(chat_id, _fmt_lista(qs, "🔔 Vencimentos de HOJE"))
            return

        if text in ("2", "atrasadas", "atrasado", "atraso"):
            qs = (
                Parcela.objects.filter(status__iexact="PENDENTE", vencimento__lt=hoje)
                .select_related("venda", "venda__cliente")
                .order_by("vencimento", "venda_id", "numero")
            )
            tg_send_safe(chat_id, _fmt_lista(qs, "⚠️ Parcelas ATRASADAS"))
            return

        if text in ("3", "resumo"):
            pend = Parcela.objects.filter(status__iexact="PENDENTE")
            hoje_qs = pend.filter(vencimento=hoje)
            atr_qs = pend.filter(vencimento__lt=hoje)
            from datetime import timedelta as _td
            prox_qs = pend.filter(vencimento__range=[hoje, hoje + _td(days=7)])

            t_hoje = hoje_qs.aggregate(s=Sum("valor"))["s"] or 0
            t_atr  = atr_qs.aggregate(s=Sum("valor"))["s"] or 0
            t_prox = prox_qs.aggregate(s=Sum("valor"))["s"] or 0

            txt = (
                "<b>📊 Resumo</b>\n\n"
                f"Vencem HOJE: {hoje_qs.count()} — {_brl(t_hoje)}\n"
                f"Atrasadas: {atr_qs.count()} — {_brl(t_atr)}\n"
                f"Próx. 7 dias: {prox_qs.count()} — {_brl(t_prox)}\n\n"
                "Envie 1, 2 ou 3 para detalhes; /help para ajuda."
            )
            tg_send_safe(chat_id, txt)
            return

        # default: ajuda
        tg_send_safe(chat_id, HELP)

    except Exception as e:
        logger.exception("Erro ao processar update do Telegram: %s", e)

# ---------- Webhook Telegram (ACK rápido) ----------
@csrf_exempt
def telegram_webhook(request, secret: str):
    """
    POST do Telegram chega aqui. Respondemos imediatamente para evitar timeout
    e processamos em background.
    """
    if secret != WEBHOOK_SECRET:
        return HttpResponse(status=403)

    if request.method == "GET":
        # health-check simples
        return HttpResponse("ok (webhook up)", content_type="text/plain; charset=utf-8")

    if request.method != "POST":
        return HttpResponse("ok")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        # Acknowledge mesmo com payload inválido para limpar fila do Telegram
        return HttpResponse("ignored", content_type="text/plain; charset=utf-8")

    # Dispara processamento em thread e responde 200 imediatamente
    Thread(target=_process_update, args=(payload,), daemon=True).start()
    return HttpResponse("ok", content_type="text/plain; charset=utf-8")