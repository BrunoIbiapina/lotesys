# relatorios/views.py
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.db.models.functions import TruncMonth, Coalesce
from django.shortcuts import render
from django.utils import timezone

from financeiro.models import Despesa


def _parse_date(s: str | None):
    if not s:
        return None
    try:
        y, m, d = map(int, s.split("-"))
        return date(y, m, d)
    except Exception:
        return None


def _is_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(_is_admin)
def comissoes_pagas(request):
    hoje = timezone.localdate()
    inicio = _parse_date(request.GET.get("inicio")) or hoje.replace(day=1)
    fim    = _parse_date(request.GET.get("fim"))    or hoje

    base_qs = (Despesa.objects
               .filter(status="PAGA",
                       data__range=(inicio, fim),
                       descricao__icontains="comiss"))

    total = base_qs.aggregate(s=Coalesce(Sum("valor"), Decimal("0.00")))["s"] or Decimal("0.00")

    mensal = (base_qs
              .annotate(mes=TruncMonth("data"))
              .values("mes")
              .annotate(v=Coalesce(Sum("valor"), Decimal("0.00")))
              .order_by("mes"))

    itens = base_qs.order_by("-data", "-id")[:100]

    ctx = dict(
        titulo="Comissões pagas",
        hoje=hoje, inicio=inicio, fim=fim,
        total=total,
        itens=itens,
        mensal_labels=[r["mes"].strftime("%Y-%m") for r in mensal if r["mes"]],
        mensal_values=[float(r["v"]) for r in mensal if r["mes"]],
    )
    return render(request, "relatorios/comissoes_pagas.html", ctx)