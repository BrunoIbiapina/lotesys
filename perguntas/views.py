from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Categoria, Pergunta
from .forms import PerguntaForm


def lista_perguntas(request):
    """Lista todas as perguntas públicas e respondidas"""
    # Filtros
    categoria_id = request.GET.get('categoria')
    busca = request.GET.get('busca')
    
    # Query base - apenas perguntas públicas e respondidas
    perguntas = Pergunta.objects.filter(
        publica=True,
        status='respondida'
    ).select_related('categoria', 'usuario', 'respondido_por')
    
    # Aplicar filtros
    if categoria_id:
        perguntas = perguntas.filter(categoria_id=categoria_id)
    
    if busca:
        perguntas = perguntas.filter(
            Q(titulo__icontains=busca) |
            Q(pergunta__icontains=busca) |
            Q(resposta__icontains=busca)
        )
    
    # Paginação
    paginator = Paginator(perguntas, 12)  # 12 perguntas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Categorias para o filtro
    categorias = Categoria.objects.filter(ativo=True).annotate(
        total_perguntas=Count('pergunta', filter=Q(
            pergunta__publica=True,
            pergunta__status='respondida'
        ))
    )
    
    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'categoria_selecionada': categoria_id,
        'busca': busca,
        'total_perguntas': perguntas.count(),
    }
    
    return render(request, 'perguntas/lista.html', context)


def detalhes_pergunta(request, pk):
    """Exibe os detalhes de uma pergunta específica"""
    pergunta = get_object_or_404(
        Pergunta,
        pk=pk,
        publica=True,
        status='respondida'
    )
    
    # Perguntas relacionadas da mesma categoria
    perguntas_relacionadas = Pergunta.objects.filter(
        categoria=pergunta.categoria,
        publica=True,
        status='respondida'
    ).exclude(pk=pergunta.pk)[:3]
    
    context = {
        'pergunta': pergunta,
        'perguntas_relacionadas': perguntas_relacionadas,
    }
    
    return render(request, 'perguntas/detalhes.html', context)


@login_required
def nova_pergunta(request):
    """Formulário para criar uma nova pergunta"""
    if request.method == 'POST':
        form = PerguntaForm(request.POST)
        if form.is_valid():
            pergunta = form.save(commit=False)
            pergunta.usuario = request.user
            pergunta.save()
            
            messages.success(
                request,
                'Sua pergunta foi enviada com sucesso! '
                'Ela será analisada pela equipe e, quando respondida, '
                'aparecerá na lista de perguntas frequentes.'
            )
            return redirect('perguntas:lista')
    else:
        form = PerguntaForm()
    
    context = {
        'form': form,
        'categorias': Categoria.objects.filter(ativo=True),
    }
    
    return render(request, 'perguntas/nova.html', context)


@login_required
def minhas_perguntas(request):
    """Lista as perguntas do usuário logado"""
    perguntas = Pergunta.objects.filter(
        usuario=request.user
    ).select_related('categoria', 'respondido_por').order_by('-criado_em')
    
    # Paginação
    paginator = Paginator(perguntas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'perguntas/minhas.html', context)


def categoria_perguntas(request, categoria_id):
    """Lista perguntas de uma categoria específica"""
    categoria = get_object_or_404(Categoria, id=categoria_id, ativo=True)
    
    perguntas = Pergunta.objects.filter(
        categoria=categoria,
        publica=True,
        status='respondida'
    ).select_related('usuario', 'respondido_por')
    
    # Paginação
    paginator = Paginator(perguntas, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'categoria': categoria,
        'page_obj': page_obj,
    }
    
    return render(request, 'perguntas/categoria.html', context)
