# mural/context_processors.py
from datetime import timedelta
from django.utils import timezone

def mural_badge(request):
    """
    Adiciona MURAL_NOVAS_QTD ao contexto global com base nas mensagens criadas
    nos últimos 7 dias. Nunca deve quebrar o site (retorna 0 em caso de erro).
    """
    try:
        from .models import Mensagem  # import atrasado evita "Apps aren't loaded yet"
    except Exception:
        return {"MURAL_NOVAS_QTD": 0}

    # (opcional) economizar consulta na tela de admin/login
    # if request.path.startswith("/admin/"):
    #     return {"MURAL_NOVAS_QTD": 0}

    limite = timezone.now() - timedelta(days=7)
    try:
        # use o nome de campo correto: 'criada_em' (não 'created_at')
        qtd = Mensagem.objects.filter(criada_em__gte=limite).count()
    except Exception:
        qtd = 0

    return {"MURAL_NOVAS_QTD": qtd}