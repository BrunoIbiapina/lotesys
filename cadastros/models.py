from django.db import models

class Empreendimento(models.Model):
    nome = models.CharField(max_length=120)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)

    def __str__(self):
        return self.nome

class Cliente(models.Model):
    nome = models.CharField(max_length=150)
    cpf_cnpj = models.CharField(max_length=20, unique=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    endereco = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.nome} ({self.cpf_cnpj})"

class Lote(models.Model):
    class Status(models.TextChoices):
        DISPONIVEL = 'DISP', 'Disponível'
        RESERVADO = 'RESV', 'Reservado'
        VENDIDO = 'VEND', 'Vendido'

    empreendimento = models.ForeignKey(Empreendimento, on_delete=models.CASCADE)
    quadra = models.CharField(max_length=10)
    numero = models.CharField(max_length=10)
    area_m2 = models.DecimalField(max_digits=10, decimal_places=2)
    preco_tabela = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=4, choices=Status.choices, default=Status.DISPONIVEL)

    class Meta:
        unique_together = ('empreendimento', 'quadra', 'numero')

    def __str__(self):
        return f"{self.empreendimento} Q{self.quadra} L{self.numero}"