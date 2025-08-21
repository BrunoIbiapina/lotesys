from django.db import models
from django.conf import settings  # <<< use settings, não get_user_model

class Mensagem(models.Model):
    TIPOS = [
        ("info", "Informação"),
        ("warning", "Aviso"),
        ("important", "Importante"),
        ("success", "Sucesso"),
    ]

    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default="info")
    fixada = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    # Use o AUTH_USER_MODEL em string – não chama get_user_model() aqui
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mensagens",
    )

    class Meta:
        ordering = ["-fixada", "-criada_em"]
        indexes = [models.Index(fields=["fixada", "criada_em"])]

    def __str__(self):
        return self.titulo