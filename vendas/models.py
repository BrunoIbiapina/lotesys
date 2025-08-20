# vendas/models.py
from __future__ import annotations

from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
import os

from cadastros.models import Cliente, Lote

DEC_0 = Decimal("0.00")


# ===== caminhos de upload dos comprovantes =====
def comprovante_venda_path(instance: "Venda", filename: str) -> str:
    # Ex.: comprovantes/vendas/2025/08/<arquivo.pdf>
    data = getattr(instance, "data_venda", None) or timezone.now().date()
    return f"comprovantes/vendas/{data:%Y/%m}/{filename}"


def comprovante_parcela_path(instance: "Parcela", filename: str) -> str:
    # Ex.: comprovantes/parcelas/2025/08/<arquivo.pdf>
    venc = getattr(instance, "vencimento", None) or timezone.now().date()
    return f"comprovantes/parcelas/{venc:%Y/%m}/{filename}"


class Venda(models.Model):
    FORMA = (("AVISTA", "À vista"), ("PARCELADO", "Parcelado"))

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    lote = models.OneToOneField(Lote, on_delete=models.PROTECT)

    data_venda = models.DateField(default=timezone.now)

    # valores
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    entrada_bruta = models.DecimalField(max_digits=12, decimal_places=2, default=DEC_0)
    desconto = models.DecimalField(max_digits=12, decimal_places=2, default=DEC_0)

    forma_pagamento = models.CharField(max_length=10, choices=FORMA, default="PARCELADO")
    parcelas_total = models.PositiveIntegerField(default=0)
    juros_mensal = models.DecimalField(max_digits=5, decimal_places=2, default=DEC_0)  # %
    data_inicio_parcelamento = models.DateField(null=True, blank=True)

    # comissão % aplicada SOBRE O VALOR TOTAL DA VENDA
    comissao_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("20.00"))

    # 🔹 COMPROVANTE (anexo da venda)
    comprovante = models.FileField(upload_to=comprovante_venda_path, blank=True, null=True)

    def __str__(self):
        return f"Venda #{self.pk} - {self.cliente}"

    # ---- Cálculos ----
    @property
    def comissao_valor(self) -> Decimal:
        """Comissão total sobre o valor total da venda."""
        base = self.valor_total or DEC_0
        pct = self.comissao_percent or DEC_0
        return (base * pct) / Decimal("100")

    @property
    def comissao_paga_na_entrada(self) -> Decimal:
        """
        Parte da comissão que é paga na ENTRADA.
        É limitada pela entrada: min(comissão_total, entrada_bruta).
        """
        entrada = self.entrada_bruta or DEC_0
        return min(self.comissao_valor, entrada)

    @property
    def entrada_liquida(self) -> Decimal:
        """
        Entrada líquida = entrada_bruta - comissão_paga_na_entrada (nunca negativa).
        """
        entrada = self.entrada_bruta or DEC_0
        liq = entrada - self.comissao_paga_na_entrada
        return liq if liq > 0 else DEC_0

    # ---- Utilidades de comprovante ----
    @property
    def tem_comprovante(self) -> bool:
        return bool(self.comprovante)

    @property
    def nome_arquivo_comprovante(self) -> str:
        return os.path.basename(self.comprovante.name) if self.comprovante else ""


class Parcela(models.Model):
    STATUS = (
        ("PENDENTE", "Pendente"),
        ("PAGO", "Pago"),
        ("VENCIDO", "Vencido"),
    )

    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name="parcelas")
    numero = models.PositiveIntegerField()
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    vencimento = models.DateField()
    status = models.CharField(max_length=8, choices=STATUS, default="PENDENTE")
    data_pagamento = models.DateField(null=True, blank=True)

    # 🔹 COMPROVANTE (anexo do pagamento da parcela)
    comprovante = models.FileField(upload_to=comprovante_parcela_path, blank=True, null=True)

    class Meta:
        unique_together = ("venda", "numero")
        ordering = ["vencimento"]

    def __str__(self):
        return f"Parcela {self.numero}/{self.venda.parcelas_total} da venda {self.venda_id}"

    def save(self, *args, **kwargs):
        """
        Mantém consistência entre status e data_pagamento:
        - Se marcar como PAGO e não houver data_pagamento, usa a data de hoje.
        - Se mudar para PENDENTE/VENCIDO, zera a data_pagamento.
        """
        if self.status == "PAGO" and not self.data_pagamento:
            self.data_pagamento = timezone.now().date()
        elif self.status != "PAGO" and self.data_pagamento:
            self.data_pagamento = None
        super().save(*args, **kwargs)

    # ---- Utilidades de comprovante ----
    @property
    def tem_comprovante(self) -> bool:
        return bool(self.comprovante)

    @property
    def nome_arquivo_comprovante(self) -> str:
        return os.path.basename(self.comprovante.name) if self.comprovante else ""


# ===== Limpeza de arquivos ao trocar/excluir =====

def _delete_file(fieldfile) -> None:
    """Remove o arquivo do storage se existir (não quebra a transação se falhar)."""
    try:
        storage = fieldfile.storage
        if fieldfile.name and storage.exists(fieldfile.name):
            storage.delete(fieldfile.name)
    except Exception:
        pass


@receiver(pre_delete, sender=Venda)
def venda_delete_file(sender, instance: Venda, **kwargs):
    if instance.comprovante:
        _delete_file(instance.comprovante)


@receiver(pre_delete, sender=Parcela)
def parcela_delete_file(sender, instance: Parcela, **kwargs):
    if instance.comprovante:
        _delete_file(instance.comprovante)


@receiver(pre_save, sender=Venda)
def venda_replace_file(sender, instance: Venda, **kwargs):
    # se for update e o arquivo foi trocado, apaga o antigo
    if not instance.pk:
        return
    try:
        old = Venda.objects.get(pk=instance.pk)
    except Venda.DoesNotExist:
        return
    if old.comprovante and old.comprovante != instance.comprovante:
        _delete_file(old.comprovante)


@receiver(pre_save, sender=Parcela)
def parcela_replace_file(sender, instance: Parcela, **kwargs):
    if not instance.pk:
        return
    try:
        old = Parcela.objects.get(pk=instance.pk)
    except Parcela.DoesNotExist:
        return
    if old.comprovante and old.comprovante != instance.comprovante:
        _delete_file(old.comprovante)