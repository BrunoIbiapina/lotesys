from django.db import models
from django.utils import timezone

class Despesa(models.Model):
    CATEGORIA = (
        ('COMISSAO','Comissão de Vendas'),
        ('CUSTO','Custo Operacional'),
        ('PESSOAL','Pessoal/Família'),
        ('FAZENDA','Fazenda Aprazível'),
        ('EMPRESA','Empresa (Concil)'),
        ('OUTRA','Outra'),
    )
    STATUS = (('PREVISTA','Prevista'), ('PAGA','Paga'))

    data = models.DateField(default=timezone.now)
    categoria = models.CharField(max_length=10, choices=CATEGORIA)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=8, choices=STATUS, default='PREVISTA')
    origem = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.get_categoria_display()} - {self.descricao}"

class ReceitaExtra(models.Model):
    data = models.DateField(default=timezone.now)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.descricao