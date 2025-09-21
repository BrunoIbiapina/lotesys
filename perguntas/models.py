from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Categoria(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    cor = models.CharField(
        max_length=7, 
        default="#007bff", 
        verbose_name="Cor (hex)",
        help_text="Cor em formato hexadecimal para o card (ex: #007bff)"
    )
    icone = models.CharField(
        max_length=50, 
        default="fas fa-question-circle",
        verbose_name="Ícone FontAwesome",
        help_text="Classe do ícone FontAwesome (ex: fas fa-question-circle)"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Pergunta(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('respondida', 'Respondida'),
        ('arquivada', 'Arquivada'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título da Pergunta")
    pergunta = models.TextField(verbose_name="Pergunta")
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.CASCADE,
        verbose_name="Categoria"
    )
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Usuário",
        related_name="perguntas"
    )
    
    # Campos da resposta
    resposta = models.TextField(blank=True, verbose_name="Resposta")
    respondido_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Respondido por",
        related_name="respostas_dadas"
    )
    respondido_em = models.DateTimeField(null=True, blank=True)
    
    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name="Status"
    )
    publica = models.BooleanField(
        default=True,
        verbose_name="Pública",
        help_text="Se marcado, a pergunta será visível para todos os usuários"
    )
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pergunta"
        verbose_name_plural = "Perguntas"
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.titulo} - {self.usuario.first_name or self.usuario.username}"

    def save(self, *args, **kwargs):
        if self.resposta and not self.respondido_em:
            self.respondido_em = timezone.now()
            self.status = 'respondida'
        super().save(*args, **kwargs)

    @property
    def nome_usuario(self):
        """Retorna o nome completo do usuário ou username"""
        if self.usuario.first_name and self.usuario.last_name:
            return f"{self.usuario.first_name} {self.usuario.last_name}"
        elif self.usuario.first_name:
            return self.usuario.first_name
        else:
            return self.usuario.username

    @property
    def nome_respondente(self):
        """Retorna o nome completo do respondente ou username"""
        if not self.respondido_por:
            return None
        if self.respondido_por.first_name and self.respondido_por.last_name:
            return f"{self.respondido_por.first_name} {self.respondido_por.last_name}"
        elif self.respondido_por.first_name:
            return self.respondido_por.first_name
        else:
            return self.respondido_por.username
