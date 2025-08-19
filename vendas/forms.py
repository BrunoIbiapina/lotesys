# vendas/forms.py
from django import forms
from .models import Venda

class VendaAdminForm(forms.ModelForm):
    """
    Formulário simples: os campos da Venda.
    As parcelas são geradas automaticamente no admin.save_model.
    """
    class Meta:
        model = Venda
        fields = (
            "cliente",
            "lote",                     # <-- ADICIONADO AQUI
            "data_venda",
            "valor_total",
            "entrada_bruta",
            "desconto",
            "forma_pagamento",
            "parcelas_total",
            "juros_mensal",
            "data_inicio_parcelamento",
            "comissao_percent",
        )