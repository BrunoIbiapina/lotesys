# vendas/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Venda, Parcela


def _is_staff(user):
    """Permite apenas usuários autenticados com is_staff=True."""
    return user.is_authenticated and user.is_staff


def _safe_next(request, default="/"):
    """
    Retorna uma URL de retorno segura (mesmo host) vinda de POST/GET `next`.
    Evita open-redirect.
    """
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return default


@login_required
def vendas_list(request):
    """
    Lista de vendas com filtros opcionais:
      - ?mes=1..12
      - ?ano=YYYY
      - ?q=texto (cliente/lote)
    """
    vendas = (
        Venda.objects.select_related("cliente", "lote")
        .all()
        .order_by("-data_venda", "-id")
    )

    mes = request.GET.get("mes")
    ano = request.GET.get("ano")
    q = request.GET.get("q")

    if ano and ano.isdigit():
        vendas = vendas.filter(data_venda__year=int(ano))
    if mes and mes.isdigit():
        vendas = vendas.filter(data_venda__month=int(mes))
    if q:
        vendas = vendas.filter(
            Q(cliente__nome__icontains=q)
            | Q(lote__numero__icontains=q)
            | Q(lote__quadra__icontains=q)
        )

    context = {
        "vendas": vendas,
        "mes": mes or "",
        "ano": ano or "",
        "q": q or "",
    }
    return render(request, "vendas/list.html", context)


@login_required
def venda_detail(request, pk: int):
    """Página de detalhes de uma venda + suas parcelas."""
    venda = get_object_or_404(
        Venda.objects.select_related("cliente", "lote"),
        pk=pk,
    )
    parcelas = venda.parcelas.all().order_by("numero", "id")
    return render(request, "vendas/detail.html", {"venda": venda, "parcelas": parcelas})


@user_passes_test(_is_staff)
@require_POST
def parcela_pagar(request, pk: int):
    """
    Marca uma parcela como PAGO.
    - Apenas staff
    - Apenas POST
    - Preenche data_pagamento se estiver vazia
    """
    parcela = get_object_or_404(Parcela, pk=pk)
    parcela.status = "PAGO"
    if not parcela.data_pagamento:
        parcela.data_pagamento = timezone.now().date()
    parcela.save(update_fields=["status", "data_pagamento"])

    messages.success(
        request, f"Parcela #{parcela.numero} da venda {parcela.venda_id} marcada como paga."
    )
    return redirect(_safe_next(request))


@user_passes_test(_is_staff)
@require_POST
def parcela_desfazer(request, pk: int):
    """
    Volta a parcela para PENDENTE.
    - Apenas staff
    - Apenas POST
    - Zera data_pagamento
    """
    parcela = get_object_or_404(Parcela, pk=pk)
    parcela.status = "PENDENTE"
    parcela.data_pagamento = None
    parcela.save(update_fields=["status", "data_pagamento"])

    messages.info(
        request, f"Pagamento da parcela #{parcela.numero} da venda {parcela.venda_id} foi desfeito."
    )
    return redirect(_safe_next(request))