from django.core.management.base import BaseCommand
from notificacoes.telegram import tg_send

class Command(BaseCommand):
    help = "Envia uma mensagem de teste via Telegram (para verificar deploy)"

    def handle(self, *args, **options):
        tg_send("🚀 Teste direto do Render (management command).")
        self.stdout.write(self.style.SUCCESS("Mensagem de teste enviada."))