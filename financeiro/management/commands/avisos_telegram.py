# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from decimal import Decimal
from typing import Iterable

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import QuerySet

# ====== MODELO Parcela ======
# No seu projeto, Parcela está em vendas.models. Mantive um fallback por segurança.
try:
    from vendas.models import Parcela
except Exception:  # pragma: no cover
    from financeiro.models import Parcela  # type: ignore


# ====== CONFIG TELEGRAM ======
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_TIMEOUT = 15  # segundos
TELEGRAM_CHUNK = 3500  # segurança (limite real ~4096 chars)


def _send_message(token: str, chat_id: str, text: str, parse_mode: str = "HTML") -> None:
    """Envia uma mensagem. Nunca levanta exceção (para não quebrar o comando)."""
    try:
        requests.post(
            TELEGRAM_API.format(token=token),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
            timeout=TELEGRAM_TIMEOUT,
        )
    except Exception as e:  # pragma: no cover
        print(f"[telegram] erro ao enviar para {chat_id}: {e}")


def _send_long(token: str, chat_id: str, text: str) -> None:
    """Quebra mensagens longas em partes menores para caber no limite do Telegram."""
    if len(text) <= TELEGRAM_CHUNK:
        _send_message(token, chat_id, text)
        return
    i = 0
    while i < len(text):
        _send_message(token, chat_id, text[i : i + TELEGRAM_CHUNK])
        i += TELEGRAM_CHUNK


def brl(valor: Decimal | float | int) -> str:
    """Formata em BRL (ex.: 1234.5 -> 'R$ 1.234,50')."""
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    s = f"{valor:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def linhas_vencem_hoje(qs: QuerySet[Parcela]) -> tuple[str, Decimal] | tuple[str, Decimal]:
    """Monta texto e total de 'vencem hoje'."""
    if not qs.exists():
        return "", Decimal("0")

    linhas: list[str] = ["<b>🔔 Vencimentos de HOJE</b>\n"]
    total = Decimal("0")
    for p in qs:
        cliente = getattr(getattr(p, "venda", None), "cliente", None)
        cliente_nome = getattr(cliente, "nome", "Cliente")
        try:
            total += Decimal(p.valor)
        except Exception:
            total += Decimal(str(p.valor))

        linhas.append(
            (
                f"• Venda #{p.venda_id} — {cliente_nome} — "
                f"Parc. {p.numero}/{p.venda.parcelas_total} — "
                f"<b>{brl(p.valor)}</b> — vence <b>{p.vencimento.strftime('%d/%m/%Y')}</b>"
            )
        )

    linhas.append(f"\n<b>Total hoje:</b> {brl(total)}")
    return "\n".join(linhas), total


def linhas_atrasadas(qs: QuerySet[Parcela], hoje) -> tuple[str, Decimal]:
    """
    Monta texto e total de 'atrasadas', apenas quando (hoje - vencimento) % 2 == 0
    para cada parcela (notificação a cada 2 dias).
    """
    linhas: list[str] = []
    total = Decimal("0")
    for p in qs:
        dias = (hoje - p.vencimento).days
        if dias % 2 != 0:
            continue
        cliente = getattr(getattr(p, "venda", None), "cliente", None)
        cliente_nome = getattr(cliente, "nome", "Cliente")
        try:
            total += Decimal(p.valor)
        except Exception:
            total += Decimal(str(p.valor))

        linhas.append(
            (
                f"• Venda #{p.venda_id} — {cliente_nome} — "
                f"Parc. {p.numero}/{p.venda.parcelas_total} — "
                f"<b>{brl(p.valor)}</b> — venceu em <b>{p.vencimento.strftime('%d/%m/%Y')}</b> — "
                f"{dias} dia(s) atraso"
            )
        )

    if not linhas:
        return "", Decimal("0")

    cabeca = "<b>⚠️ Parcelas ATRASADAS</b>\n\n"
    rodape = f"\n\n<b>Total em atraso (itens de hoje):</b> {brl(total)}"
    return cabeca + "\n".join(linhas) + rodape, total


class Command(BaseCommand):
    help = "Envia avisos de vencimentos/atrasos das parcelas via Telegram."

    def handle(self, *args, **options):
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_ids_raw = os.getenv("TELEGRAM_CHAT_IDS", "").strip()

        if not token or not chat_ids_raw:
            self.stderr.write(
                self.style.ERROR(
                    "Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_IDS (IDs separados por vírgula)."
                )
            )
            return

        chat_ids: list[str] = [c.strip() for c in chat_ids_raw.split(",") if c.strip()]
        hoje = timezone.localdate()

        # Apenas parcelas pendentes
        pendentes = (
            Parcela.objects.filter(status="PENDENTE")
            .select_related("venda", "venda__cliente")
        )

        # Que vencem hoje
        vencem_hoje_qs = pendentes.filter(vencimento=hoje)

        # Atrasadas (vencimento < hoje)
        atrasadas_qs = pendentes.filter(vencimento__lt=hoje).order_by("vencimento")

        # Monta mensagens
        msg_hoje, _ = linhas_vencem_hoje(vencem_hoje_qs)
        msg_atraso, _ = linhas_atrasadas(atrasadas_qs, hoje)

        # Envia para todos os chats configurados
        for cid in chat_ids:
            if msg_hoje:
                _send_long(token, cid, msg_hoje)
            if msg_atraso:
                _send_long(token, cid, msg_atraso)

        self.stdout.write(self.style.SUCCESS("Avisos de Telegram processados."))