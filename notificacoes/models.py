from django.db import models

class DestinatarioTelegram(models.Model):
    nome = models.CharField(max_length=100)
    chat_id = models.CharField(max_length=32, unique=True)
    recebe_vencimentos_hoje = models.BooleanField(default=True)
    recebe_atrasados = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.chat_id})"