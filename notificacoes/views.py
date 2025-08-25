# notificacoes/views.py
import os
import json
from datetime import timedelta
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.management import call_command
from django.db.models import Q, Sum

# (opcionais – se você não tem esses módulos, o código continua funcionando)
try:
    from .models import DestinatarioTelegram
except Exception:
    DestinatarioTelegram = None  # type: ignore

try:
    from .utils import tg_send
except Exception:
    def tg_send(chat_id, text):  # fallback silencioso
        pass

# ====== CONFIG VIA ENV ======
WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "secret")
TASK_TOKEN = os.getenv("TASK_TRIGGER_TOKEN", "task-secret")

HELP = (
    "Olá! Eu sou o bot do LoteSys.\n"
    "/start – registrar este chat para receber avisos\n"
    "/stop – parar de receber avisos\n"
    "/status – ver sua inscrição\n"
    "/menu – ver opções rápidas\n"
    "\nOu responda com um número do menu."
)

# ====== HELPERS ======
def _brl(v) -> str:
    v = Decimal(v or 0)
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

def _menu_text() -> str:
    return (
        "📋 <b>Menu LoteSys</b>\n"
        "1) 🗓️ Vencem HOJE\n"
        "2) ⚠️ Parcelas ATRASADAS\n"
        "3) ⏳ Vencem nos PRÓXIMOS 7 dias\n"
        "4) 📊 Totais do mês (entradas/despesas)\n"
        "5) ❔ Ajuda\n"
        "\nResponda com o número da opção."
    )

def _listar_parcelas(qs, titulo, limit=15):
    """
    qs deve vir com select_related('venda', 'venda__cliente') e ordenado.
    Limita a 'limit' itens e exibe '+X restante(s)'.
    """
    linhas = [f"<b>{titulo}</b>"]
    total = Decimal("0")
    count = 0
    items = []
    for p in qs[:limit]:
        cliente = getattr(getattr(p, "venda", None), "cliente", None)
        cliente_nome = getattr(cliente, "nome", "Cliente")
        total += Decimal(p.valor or 0)
        count += 1
        items.append(
            f"• Venda #{p.venda_id} — {cliente_nome} — Parc. {p.numero}/"
            f"{getattr(getattr(p, 'venda', None), 'parcelas_total', '?')} — "
            f"<b>{_brl(p.valor)}</b> — {p.vencimento.strftime('%d/%m/%Y')}"
        )
    resto = max(qs.count() - count, 0)

    if count == 0:
        linhas.append("Nenhum item.")
    else:
        linhas.append("")
        linhas.extend(items)
        linhas.append("")
        linhas.append(f"<b>Total listado:</b> {_brl(total)}")
        if resto > 0:
            linhas.append(f"(+{resto} restante(s) não exibidos)")

    return "\n".join(linhas)

def _totais_mes():
    try:
        from vendas.models import Parcela
    except Exception:
        from financeiro.models import Parcela  # type: ignore
    from vendas.models import Venda as _Venda  # se existir
    try:
        from financeiro.models import Despesa
    except Exception:
        # sem despesas, retorna zeros
        Despesa = None  # type: ignore

    hoje = timezone.localdate()
    inicio = hoje.replace(day=1)
    fim = hoje

    pagas = (
        Parcela.objects.filter(status__iexact="PAGO", data_pagamento__range=[inicio, fim])
        .aggregate(s=Sum("valor"))["s"] or 0
    )

    # entradas líquidas por venda no período
    entradas_liquidas = Decimal("0")
    try:
        entradas_liquidas = sum(
            (v.entrada_liquida for v in _Venda.objects.filter(data_venda__range=[inicio, fim])),
            Decimal("0"),
        )
    except Exception:
        pass

    despesas_pagas = Decimal("0")
    if Despesa:
        despesas_pagas = (
            Despesa.objects.filter(status__iexact="PAGA", data__range=[inicio, fim])
            .aggregate(s=Sum("valor"))["s"] or 0
        )

    fluxo = Decimal(pagas) + Decimal(entradas_liquidas) - Decimal(despesas_pagas)

    return (
        f"📊 <b>Totais do mês ({inicio.strftime('%d/%m')}–{fim.strftime('%d/%m')})</b>\n"
        f"✔️ Parcelas pagas: {_brl(pagas)}\n"
        f"➕ Entradas líquidas (vendas): {_brl(entradas_liquidas)}\n"
        f"❌ Despesas pagas: {_brl(despesas_pagas)}\n"
        f"📈 Fluxo líquido: <b>{_brl(fluxo)}</b>"
    )

# ---------- Diagnóstico rápido: contagens no banco ----------
def _stats_text():
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
        f"vencem_hoje_qtd={vencem_hoje.count()} total_hoje={_brl(total_hoje)}\n"
        f"atrasadas_qtd={atrasadas.count()} total_atraso={_brl(total_atraso)}\n"
    )

# ---------- Trigger HTTP para rodar o comando avisos_telegram ----------
@csrf_exempt
def task_notify(request):
    # Autorização simples por token
    if request.GET.get("token") != TASK_TOKEN:
        return HttpResponse(status=403)

    # Stats-only (não chama o comando)
    if request.GET.get("stats") == "1":
        return HttpResponse(_stats_text(), content_type="text/plain; charset=utf-8")

    # Mapeia flags da querystring -> kwargs do management command
    dry_run = request.GET.get("dry_run") in ("1", "true", "True", "yes", "on")
    force = request.GET.get("force") in ("1", "true", "True", "yes", "on")
    debug = request.GET.get("debug") in ("1", "true", "True", "yes", "on")
    date_str = request.GET.get("date")  # "YYYY-MM-DD" (opcional)

    kwargs = {}
    if dry_run:
        kwargs["dry_run"] = True
    if force:
        kwargs["force"] = True
    if debug:
        kwargs["debug"] = True
    if date_str:
        kwargs["date"] = date_str

    # Executa o management command
    call_command("avisos_telegram", **kwargs)

    # Responde dizendo o que rodou
    body = "ok"
    flags = []
    if dry_run: flags.append("dry-run")
    if force: flags.append("force")
    if debug: flags.append("debug")
    if date_str: flags.append(f"date={date_str}")
    if flags:
        body += " (" + ", ".join(flags) + ")"

    return HttpResponse(body, content_type="text/plain; charset=utf-8")

# ---------- Webhook (menu stateless) ----------
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
    text_raw = (msg.get("text") or "").strip()
    text = text_raw.lower()

    # /start registra (se tiver model) e mostra menu
    if text.startswith("/start"):
        if DestinatarioTelegram:
            try:
                dest, _ = DestinatarioTelegram.objects.get_or_create(
                    chat_id=chat_id,
                    defaults={"nome": chat.get("first_name") or "Usuário"},
                )
                dest.ativo = True
                dest.save()
            except Exception:
                pass
        tg_send(chat_id, "✅ Inscrição registrada!\n" + _menu_text())
        return JsonResponse({"ok": True})

    # /stop desativa (se tiver model)
    if text.startswith("/stop"):
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
        return JsonResponse({"ok": True})

    # /status
    if text.startswith("/status"):
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
        return JsonResponse({"ok": True})

    # /menu e /help
    if text.startswith("/menu") or text.startswith("/help") or text.startswith("/ajuda"):
        tg_send(chat_id, _menu_text())
        return JsonResponse({"ok": True})

    # ====== Opções do menu (stateless) ======
    try:
        from vendas.models import Parcela
    except Exception:
        from financeiro.models import Parcela  # type: ignore

    hoje = timezone.localdate()
    proximos_7 = hoje + timedelta(days=7)

    if text in {"1", "2", "3", "4", "5"}:
        if text == "1":
            qs = (
                Parcela.objects.filter(
                    Q(status__iexact="PENDENTE") | Q(status__iexact="VENCIDO"),
                    vencimento=hoje,
                )
                .select_related("venda", "venda__cliente")
                .order_by("vencimento", "venda_id", "numero")
            )
            tg_send(chat_id, _listar_parcelas(qs, "🗓️ Vencem HOJE"))

        elif text == "2":
            qs = (
                Parcela.objects.filter(
                    Q(status__iexact="PENDENTE") | Q(status__iexact="VENCIDO"),
                    vencimento__lt=hoje,
                )
                .select_related("venda", "venda__cliente")
                .order_by("vencimento", "venda_id", "numero")
            )
            tg_send(chat_id, _listar_parcelas(qs, "⚠️ Parcelas ATRASADAS"))

        elif text == "3":
            qs = (
                Parcela.objects.filter(
                    Q(status__iexact="PENDENTE") | Q(status__iexact="VENCIDO"),
                    vencimento__gt=hoje,
                    vencimento__lte=proximos_7,
                )
                .select_related("venda", "venda__cliente")
                .order_by("vencimento", "venda_id", "numero")
            )
            tg_send(chat_id, _listar_parcelas(qs, "⏳ Vencem nos PRÓXIMOS 7 dias"))

        elif text == "4":
            tg_send(chat_id, _totais_mes())

        elif text == "5":
            tg_send(chat_id, _menu_text())

        return JsonResponse({"ok": True})

    # Fallback: qualquer outra coisa, reenvia o menu
    tg_send(chat_id, _menu_text())
    return JsonResponse({"ok": True})