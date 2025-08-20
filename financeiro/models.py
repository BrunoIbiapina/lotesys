# financeiro/models.py
from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
import os


def comprovante_despesa_path(instance: "Despesa", filename: str) -> str:
    # Ex.: comprovantes/despesas/2025/08/<arquivo.pdf>
    return f"comprovantes/despesas/{instance.data:%Y/%m}/{filename}"


def comprovante_receita_path(instance: "ReceitaExtra", filename: str) -> str:
    # Ex.: comprovantes/receitas/2025/08/<arquivo.pdf>
    return f"comprovantes/receitas/{instance.data:%Y/%m}/{filename}"


class Despesa(models.Model):
    CATEGORIA = (
        ("COMISSAO", "Comissão de Vendas"),
        ("CUSTO", "Custo Operacional"),
        ("PESSOAL", "Pessoal/Família"),
        ("FAZENDA", "Fazenda Aprazível"),
        ("EMPRESA", "Empresa (Concil)"),
        ("OUTRA", "Outra"),
    )

    STATUS = (("PREVISTA", "Prevista"), ("PAGA", "Paga"))

    data = models.DateField(default=timezone.now)
    categoria = models.CharField(max_length=10, choices=CATEGORIA)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=8, choices=STATUS, default="PREVISTA")
    origem = models.CharField(max_length=50, blank=True)

    # 🔹 Comprovante (anexo)
    comprovante = models.FileField(
        upload_to=comprovante_despesa_path, blank=True, null=True
    )

    # Auditoria simples
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data", "-id"]
        indexes = [
            models.Index(fields=["data"]),
            models.Index(fields=["categoria"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.get_categoria_display()} - {self.descricao}"

    @property
    def tem_comprovante(self) -> bool:
        return bool(self.comprovante)

    @property
    def nome_arquivo(self) -> str:
        return os.path.basename(self.comprovante.name) if self.comprovante else ""


class ReceitaExtra(models.Model):
    data = models.DateField(default=timezone.now)
    descricao = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=12, decimal_places=2)

    # 🔹 Comprovante (anexo)
    comprovante = models.FileField(
        upload_to=comprovante_receita_path, blank=True, null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data", "-id"]
        indexes = [
            models.Index(fields=["data"]),
        ]

    def __str__(self):
        return self.descricao

    @property
    def tem_comprovante(self) -> bool:
        return bool(self.comprovante)

    @property
    def nome_arquivo(self) -> str:
        return os.path.basename(self.comprovante.name) if self.comprovante else ""


# ---------- limpeza de arquivos antigos/órfãos ----------

def _delete_file(fieldfile) -> None:
    """Remove o arquivo do storage se existir."""
    try:
        storage = fieldfile.storage
        if fieldfile.name and storage.exists(fieldfile.name):
            storage.delete(fieldfile.name)
    except Exception:
        # Não interrompe a operação do banco caso falhe a remoção no disco/storage
        pass


@receiver(pre_delete, sender=Despesa)
def despesa_delete_file(sender, instance: Despesa, **kwargs):
    if instance.comprovante:
        _delete_file(instance.comprovante)


@receiver(pre_delete, sender=ReceitaExtra)
def receita_delete_file(sender, instance: ReceitaExtra, **kwargs):
    if instance.comprovante:
        _delete_file(instance.comprovante)


@receiver(pre_save, sender=Despesa)
def despesa_replace_file(sender, instance: Despesa, **kwargs):
    if not instance.pk:
        return
    try:
        old = Despesa.objects.get(pk=instance.pk)
    except Despesa.DoesNotExist:
        return
    # Se trocar o arquivo, apaga o antigo
    if old.comprovante and old.comprovante != instance.comprovante:
        _delete_file(old.comprovante)


@receiver(pre_save, sender=ReceitaExtra)
def receita_replace_file(sender, instance: ReceitaExtra, **kwargs):
    if not instance.pk:
        return
    try:
        old = ReceitaExtra.objects.get(pk=instance.pk)
    except ReceitaExtra.DoesNotExist:
        return
    if old.comprovante and old.comprovante != instance.comprovante:
        _delete_file(old.comprovante)