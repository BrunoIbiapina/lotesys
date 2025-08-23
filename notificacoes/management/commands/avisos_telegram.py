# -*- coding: utf-8 -*-
import os
from decimal import Decimal
from datetime import date, datetime

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

# ---- importa o modelo Parcela da app correta ----
try:
    from vendas.models import Parcela  # normalmente está aqui
except Exception:
    from financeiro.models import Parcela  # fallback se estiver em financeiro


TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def brl(valor) -> str:
    """Formata Decimal/float como R$ 1.234,56."""
    if valor is None:
        valor = Decimal("0")
    valor = Decimal(valor)
    s = f"{valor:,.2f}"
    # troca para pt-BR
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def send_message(token: str, chat_id: str, text: str) -> None:
    """Dispara mensagem, silenciosamente em caso de erro de rede."""
    try:
        requests.post(
            TELEGRAM_API.format(token=token),
            json={"chat_id": str(chat_id), "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
    except Exception as e:
        print(f"[telegram] erro ao enviar para {chat_id}: {e}")


class Command(BaseCommand):
    help = "Envia avisos de vencimentos/atrasos das parcelas via Telegram."

    # ---------- NOVO: flags ----------
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra as mensagens mas não envia nada.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ignora a regra de enviar atrasadas apenas a cada 2 dias.",
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Simula execução em uma data (YYYY-MM-DD).",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Exibe contagens detalhadas mesmo quando estiver vazio.",
        )

    def handle(self, *args, **options):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_ids_raw = os.getenv("TELEGRAM_CHAT_IDS", "").strip()

        if not token or not chat_ids_raw:
            self.stderr.write(
                "Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_IDS (IDs separados por vírgula)."
            )
            return

        chat_ids = [c.strip() for c in chat_ids_raw.split(",") if c.strip()]

        # ---------- data de referência ----------
        if options.get("date"):
            try:
                hoje = datetime.strptime(options["date"], "%Y-%m-%d").date()
            except ValueError:
                self.stderr.write("Formato inválido para --date (use YYYY-MM-DD).")
                return
        else:
            # usa a data local do servidor
            hoje: date = timezone.localdate()

        dry_run: bool = options.get("dry_run", False)
        force: bool = options.get("force", False)
        debug: bool = options.get("debug", False)

        # ---------- consultas ----------
        pendentes = Parcela.objects.filter(status="PENDENTE")
        vencem_hoje = pendentes.filter(vencimento=hoje).select_related(
            "venda", "venda__cliente"
        )
        atrasadas_qs = pendentes.filter(vencimento__lt=hoje).select_related(
            "venda", "venda__cliente"
        )

        if debug:
            print(
                f"[debug] hoje={hoje} | pendentes={pendentes.count()} | "
                f"vencem_hoje={vencem_hoje.count()} | atrasadas={atrasadas_qs.count()}"
            )

        # ---------- monta mensagem: vencem hoje ----------
        linhas_hoje = []
        total_hoje = Decimal("0")

        for p in vencem_hoje.order_by("vencimento", "venda_id", "numero"):
            venda_id = getattr(p, "venda_id", None)
            cliente = getattr(getattr(p, "venda", None), "cliente", None)
            cliente_nome = getattr(cliente, "nome", "Cliente")
            linhas_hoje.append(
                f"• Venda #{venda_id} — {cliente_nome} — Parc. {p.numero}/"
                f"{getattr(getattr(p, 'venda', None), 'parcelas_total', '?')} — "
                f"<b>{brl(p.valor)}</b> — vence <b>{p.vencimento.strftime('%d/%m/%Y')}</b>"
            )
            total_hoje += Decimal(p.valor)

        msg_hoje = ""
        if linhas_hoje:
            msg_hoje = "<b>🔔 Vencimentos de HOJE</b>\n\n" + "\n".join(linhas_hoje)
            msg_hoje += f"\n\n<b>Total hoje:</b> {brl(total_hoje)}"
        elif debug:
            print("[debug] Nenhuma parcela vencendo hoje.")

        # ---------- monta mensagem: atrasadas ----------
        linhas_atraso = []
        total_atraso = Decimal("0")

        for p in atrasadas_qs.order_by("vencimento", "venda_id", "numero"):
            dias = (hoje - p.vencimento).days
            if force or dias % 2 == 0:
                venda_id = getattr(p, "venda_id", None)
                cliente = getattr(getattr(p, "venda", None), "cliente", None)
                cliente_nome = getattr(cliente, "nome", "Cliente")
                linhas_atraso.append(
                    f"• Venda #{venda_id} — {cliente_nome} — Parc. {p.numero}/"
                    f"{getattr(getattr(p, 'venda', None), 'parcelas_total', '?')} — "
                    f"<b>{brl(p.valor)}</b> — venceu em <b>{p.vencimento.strftime('%d/%m/%Y')}</b> "
                    f"— {dias} dia(s) em atraso"
                )
                total_atraso += Decimal(p.valor)

        msg_atraso = ""
        if linhas_atraso:
            msg_atraso = "<b>⚠️ Parcelas ATRASADAS</b>\n\n" + "\n".join(linhas_atraso)
            msg_atraso += f"\n\n<b>Total em atraso (itens deste envio):</b> {brl(total_atraso)}"
        elif debug:
            print(
                "[debug] Nenhuma parcela atrasada elegível para aviso "
                "(use --force para ignorar a regra de 2 em 2 dias)."
            )

        # ---------- envia (ou só mostra) ----------
        mensagens = [m for m in (msg_hoje, msg_atraso) if m]

        if not mensagens:
            if debug:
                print("[debug] Nada para enviar.")
            self.stdout.write(self.style.SUCCESS("Avisos de Telegram processados."))
            return

        if dry_run:
            print("\n===== DRY-RUN (não será enviado) =====")
            for i, msg in enumerate(mensagens, 1):
                print(f"\n--- Mensagem {i} ---\n{msg}\n")
            print("===== FIM DRY-RUN =====\n")
        else:
            for cid in chat_ids:
                for msg in mensagens:
                    send_message(token, cid, msg)

        self.stdout.write(self.style.SUCCESS("Avisos de Telegram processados."))