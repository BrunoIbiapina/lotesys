from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from .models import Mensagem

@login_required
def mural_index(request):
    # Fixadas
    fixadas = (
        Mensagem.objects
        .filter(fixada=True)
        .order_by('-criada_em')
    )

    # Recentes = não fixadas (inclui possíveis NULL antigos)
    recentes = (
        Mensagem.objects
        .filter(Q(fixada=False) | Q(fixada__isnull=True))
        .order_by('-criada_em')
    )

    return render(request, "mural/index.html", {
        "fixadas": fixadas,
        "recentes": recentes,
    })