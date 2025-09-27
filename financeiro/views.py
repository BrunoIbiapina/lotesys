# financeiro/views.py
from datetime import date, timedelta
from decimal import Decimal
import json
import urllib.request
import urllib.parse

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Despesa
from vendas.models import Parcela, Venda


# ---------------- utilidades ----------------
def _parse_date(s: str | None):
    if not s:
        return None
    try:
        y, m, d = map(int, s.split("-"))
        return date(y, m, d)
    except Exception:
        return None


def _brl(val) -> str:
    try:
        v = float(val or 0)
    except Exception:
        v = 0.0
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


# === NOVO: saldo acumulado até uma data (caixa) ===
def _saldo_caixa_ate(data_limite: date) -> dict:
    """
    Saldo de caixa acumulado até data_limite (assume saldo inicial 0).
    Regras:
      - Receitas = parcelas pagas até a data + entradas LÍQUIDAS de vendas até a data.
      - Despesas para FLUXO = despesas PAGAS até a data MENOS a comissão já abatida nas entradas.
        (evita descontar a comissão duas vezes)
    """
    # Despesas pagas até a data (contábil)
    despesas_pagas_ate = (
        Despesa.objects.filter(status="PAGA", data__lte=data_limite)
        .aggregate(v=Coalesce(Sum("valor"), Decimal("0.00")))["v"] or Decimal("0.00")
    )

    # Despesas de comissão pagas até a data
    despesas_comissao_pagas_ate = (
        Despesa.objects.filter(status="PAGA", categoria="COMISSAO", data__lte=data_limite)
        .aggregate(v=Coalesce(Sum("valor"), Decimal("0.00")))
        .get("v") or Decimal("0.00")
    )

    # Vendas até a data: somo entrada_liquida (não acumula comissão de entrada)
    entradas_liquidas_ate = Decimal("0.00")
    for v in Venda.objects.filter(data_venda__lte=data_limite).select_related("cliente"):
        entrada_bruta = getattr(v, "entrada_bruta", Decimal("0.00")) or Decimal("0.00")
        comissao_entr = getattr(v, "comissao_paga_na_entrada", None)
        if comissao_entr is None:
            # fallback: se não existir o campo, calcula mínimo entre comissão total e entrada
            com_total = getattr(v, "comissao_total", None)
            if com_total is None:
                valor_total = getattr(v, "valor_total", None) or getattr(v, "valor_venda", None)
                perc = getattr(v, "percentual_comissao", None)
                if valor_total is not None and perc is not None:
                    try:
                        com_total = Decimal(str(valor_total)) * (Decimal(str(perc)) / Decimal("100"))
                    except Exception:
                        com_total = None
            try:
                comissao_entr = min(Decimal(str(entrada_bruta)), Decimal(str(com_total))) if com_total is not None else Decimal("0.00")
            except Exception:
                comissao_entr = Decimal("0.00")
        else:
            try:
                comissao_entr = Decimal(str(comissao_entr))
            except Exception:
                comissao_entr = Decimal("0.00")
        entrada_liq = getattr(v, "entrada_liquida", None)
        if entrada_liq is None:
            entrada_liq = entrada_bruta - comissao_entr
        entradas_liquidas_ate += (entrada_liq or Decimal("0.00"))

    # Parcelas pagas até a data
    parcelas_pagas_ate = (
        Parcela.objects.filter(status__iexact="PAGO", data_pagamento__lte=data_limite)
        .aggregate(v=Coalesce(Sum("valor"), Decimal("0.00")))["v"] or Decimal("0.00")
    )

    receitas_ate = parcelas_pagas_ate + entradas_liquidas_ate

    # Despesas para fluxo (não desconta comissão duas vezes)
    despesas_fluxo_ate = despesas_pagas_ate - despesas_comissao_pagas_ate
    if despesas_fluxo_ate < 0:
        despesas_fluxo_ate = Decimal("0.00")

    caixa_ate = receitas_ate - despesas_fluxo_ate

    return dict(
        receitas_ate=receitas_ate,
        despesas_pagas_ate=despesas_pagas_ate,
        comissoes_entrada_ate=despesas_comissao_pagas_ate,
        despesas_fluxo_ate=despesas_fluxo_ate,
        caixa_ate=caixa_ate,
    )


def _monta_contexto_extrato(inicio: date, fim: date) -> dict:
    hoje = timezone.localdate()

    # --- Despesas no período (contábil)
    despesas_qs = (
        Despesa.objects
        .filter(data__range=[inicio, fim])
        .order_by("-data", "-id")
    )
    total_despesas_pagas = despesas_qs.filter(status="PAGA").aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"] or Decimal("0.00")

    total_despesas_previstas = despesas_qs.filter(status="PREVISTA").aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"] or Decimal("0.00")

    # Despesas de comissão pagas no período
    despesas_comissao_pagas_periodo = despesas_qs.filter(status="PAGA", categoria="COMISSAO").aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"] or Decimal("0.00")

    # --- Parcelas pagas (receitas) no período
    parcelas_pagas_qs = (
        Parcela.objects
        .select_related("venda", "venda__cliente")
        .filter(status__iexact="PAGO", data_pagamento__range=[inicio, fim])
        .order_by("-data_pagamento", "-id")
    )
    total_parcelas_pagas = parcelas_pagas_qs.aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"] or Decimal("0.00")

    # --- Entradas de vendas no período (abatendo comissão)
    vendas_periodo_qs = (
        Venda.objects
        .select_related("cliente")
        .filter(data_venda__range=[inicio, fim])
        .order_by("-data_venda", "-id")
    )

    entradas_detalhe: list[dict] = []
    total_entradas_brutas = Decimal("0.00")
    total_comissoes = Decimal("0.00")          # comissão usada na entrada
    total_entradas_liquidas = Decimal("0.00")

    for v in vendas_periodo_qs:
        entrada_bruta = getattr(v, "entrada_bruta", Decimal("0.00")) or Decimal("0.00")
        comissao_entr = getattr(v, "comissao_paga_na_entrada", Decimal("0.00")) or Decimal("0.00")
        entrada_liq   = getattr(v, "entrada_liquida", Decimal("0.00")) or (entrada_bruta - comissao_entr)

        if entrada_bruta > 0 or entrada_liq != 0:
            entradas_detalhe.append(
                dict(
                    venda=v,
                    entrada_bruta=entrada_bruta,
                    comissao=comissao_entr,
                    entrada_liquida=entrada_liq,
                )
            )
            total_entradas_brutas   += entrada_bruta
            total_comissoes         += comissao_entr
            total_entradas_liquidas += entrada_liq

    # Receita do período
    total_receitas = total_parcelas_pagas + total_entradas_liquidas

    # Despesa para FLUXO no período (sem comissão já abatida nas entradas)
    total_despesas_pagas_fluxo = total_despesas_pagas - despesas_comissao_pagas_periodo
    if total_despesas_pagas_fluxo < 0:
        total_despesas_pagas_fluxo = Decimal("0.00")

    # Caixa no PERÍODO (fluxo líquido)
    fluxo_liquido = total_receitas - total_despesas_pagas_fluxo  # == caixa_no_periodo

    # --- Vencidas/Pendentes
    vencidas_qs = (
        Parcela.objects
        .select_related("venda", "venda__cliente")
        .filter(status__iexact="PENDENTE", vencimento__lt=hoje)
        .order_by("vencimento", "id")
    )
    total_vencidas = vencidas_qs.aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"] or Decimal("0.00")

    pendentes_qs = (
        Parcela.objects
        .select_related("venda", "venda__cliente")
        .filter(status__iexact="PENDENTE", vencimento__gte=hoje)
        .order_by("vencimento", "id")
    )
    total_a_receber = pendentes_qs.aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"] or Decimal("0.00")

    por_mes_qs = (
        pendentes_qs
        .annotate(mes=TruncMonth("vencimento"))
        .values("mes")
        .order_by("mes")
        .annotate(total=Coalesce(Sum("valor"), Decimal("0.00")))
    )
    por_mes = [
        {"mes_label": r["mes"].strftime("%m/%Y"), "valor": r["total"]}
        for r in por_mes_qs if r["mes"]
    ]

    # === acumulados até as datas ===
    saldo_fim  = _saldo_caixa_ate(fim)
    saldo_hoje = _saldo_caixa_ate(hoje)

    return dict(
        hoje=hoje,
        inicio=inicio,
        fim=fim,

        # Despesas (contábil e para fluxo)
        despesas=despesas_qs,
        total_despesas_pagas=total_despesas_pagas,
        total_despesas_previstas=total_despesas_previstas,
        total_despesas_pagas_fluxo=total_despesas_pagas_fluxo,  # p/ fluxo
        total_despesas_comissao_pagas=despesas_comissao_pagas_periodo,
        comissao_paga_com_entradas_no_periodo=total_comissoes,

        # Receitas
        parcelas_pagas=parcelas_pagas_qs,
        total_parcelas_pagas=total_parcelas_pagas,
        entradas_detalhe=entradas_detalhe,
        total_entradas_brutas=total_entradas_brutas,
        total_comissoes=total_comissoes,
        total_entradas_liquidas=total_entradas_liquidas,
        total_receitas=total_receitas,

        # Fluxo / Caixa
        fluxo_liquido=fluxo_liquido,           # == caixa_no_periodo
        caixa_no_periodo=fluxo_liquido,        # alias
        caixa_ate_fim=saldo_fim["caixa_ate"],  # saldo acumulado até 'fim'
        caixa_ate_hoje=saldo_hoje["caixa_ate"],

        # Projeção
        vencidas=vencidas_qs,
        total_vencidas=total_vencidas,
        pendentes=pendentes_qs,
        total_a_receber=total_a_receber,
        por_mes=por_mes,
    )


# ---------------------- views ----------------------
@login_required
def ping(request):
    return HttpResponse("financeiro ok")


@csrf_exempt
def relatorio_mensal_api(request):
    """
    API para gerar relatório mensal automatizado
    Parâmetros: ?mes=2024-09 (formato YYYY-MM)
    Retorna: PDF do extrato mensal
    """
    # Verificação de token no header Authorization
    auth_header = request.META.get('HTTP_AUTHORIZATION')
    if not auth_header or auth_header != 'Token SeuTokenSecreto123':
        return HttpResponse('Unauthorized', status=401)
    
    import calendar
    from datetime import datetime
    
    # Nomes dos meses em português
    meses_pt = [
        '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    # Pega o mês solicitado ou mês anterior se não especificado
    mes_param = request.GET.get('mes')
    if mes_param:
        try:
            ano, mes = map(int, mes_param.split('-'))
        except:
            return HttpResponse("Formato inválido. Use ?mes=2024-09", status=400)
    else:
        # Mês anterior por padrão
        hoje = timezone.localdate()
        if hoje.month == 1:
            mes, ano = 12, hoje.year - 1
        else:
            mes, ano = hoje.month - 1, hoje.year
    
    # Primeiro e último dia do mês
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    
    # Gera contexto do extrato
    ctx = _monta_contexto_extrato(inicio, fim)
    
    # Se for requisição GET normal, retorna JSON com dados + lista de despesas
    if request.GET.get('format') != 'pdf':
        # Buscar todas as despesas do mês
        despesas_mes = Despesa.objects.filter(
            data__range=[inicio, fim]
        ).order_by('-data', 'categoria')
        
        # Preparar lista de despesas para o email
        lista_despesas = []
        despesas_texto = ""  # String formatada para ActivePieces
        
        for i, despesa in enumerate(despesas_mes):
            categoria_display = despesa.get_categoria_display()
            status_display = despesa.get_status_display()
            
            # Array de despesas (formato original)
            lista_despesas.append({
                'data': despesa.data.strftime('%d/%m/%Y'),
                'categoria': categoria_display,
                'descricao': despesa.descricao,
                'valor': _brl(despesa.valor),
                'status': status_display,
                'status_class': 'paga' if despesa.status == 'PAGA' else 'prevista'
            })
            
            # String formatada para ActivePieces
            despesas_texto += f"• {despesa.descricao}\n"
            despesas_texto += f"  💰 {_brl(despesa.valor)} | 📅 {despesa.data.strftime('%d/%m/%Y')} | 🏷️ {categoria_display} | ✅ {status_display}\n\n"
        
        # Campos individuais para TODAS as despesas (para ActivePieces fazer cards bonitos)
        response_data = {
            'periodo': f"{inicio.strftime('%d/%m/%Y')} - {fim.strftime('%d/%m/%Y')}",
            'mes_ano': f"{meses_pt[mes]} {ano}",
            'total_receitas': _brl(ctx['total_receitas']),
            'total_despesas_pagas': _brl(ctx['total_despesas_pagas']),
            'total_despesas_previstas': _brl(ctx['total_despesas_previstas']),
            'fluxo_liquido': _brl(ctx['fluxo_liquido']),
            'caixa_ate_fim': _brl(ctx['caixa_ate_fim']),
            'despesas': lista_despesas,
            'despesas_texto': despesas_texto.strip(),  # Texto formatado completo
            'total_despesas': len(lista_despesas),
        }
        
        # Adicionar cada despesa como campo individual (despesa_1, despesa_2, etc.)
        for i, despesa in enumerate(lista_despesas):
            response_data[f'despesa_{i+1}'] = despesa
        
        # Campos legados para compatibilidade
        response_data['primeira_despesa'] = lista_despesas[0] if lista_despesas else {}
        response_data['segunda_despesa'] = lista_despesas[1] if len(lista_despesas) > 1 else {}
        response_data['terceira_despesa'] = lista_despesas[2] if len(lista_despesas) > 2 else {}
        
        return JsonResponse(response_data)
    
    # Gera PDF usando a mesma lógica do extrato_pdf
    # Simula uma nova requisição com os parâmetros corretos
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    factory = RequestFactory()
    pdf_request = factory.get(f'/financeiro/extrato/pdf/?inicio={inicio}&fim={fim}')
    
    # Criar um usuário temporário para a requisição (necessário para @login_required)
    if hasattr(request, 'user') and request.user:
        pdf_request.user = request.user
    else:
        # Para API externa, criar usuário temporário
        from django.contrib.auth.models import User
        try:
            api_user = User.objects.get(username='api_user')
        except User.DoesNotExist:
            api_user = User.objects.create_user('api_user', 'api@lotesys.com', 'temp123')
        pdf_request.user = api_user
    
    pdf_response = extrato_pdf(pdf_request)
    
    # Forçar headers para melhor compatibilidade com ActivePieces
    filename = f'relatorio_{mes:02d}_{ano}.pdf'
    pdf_response['Content-Disposition'] = f'attachment; filename="{filename}"'
    pdf_response['Content-Type'] = 'application/pdf'
    pdf_response['Cache-Control'] = 'no-cache'
    pdf_response['X-Filename'] = filename
    
    return pdf_response
@login_required
def extrato(request):
    hoje = timezone.localdate()
    inicio = _parse_date(request.GET.get("inicio")) or hoje.replace(day=1)
    fim    = _parse_date(request.GET.get("fim")) or hoje

    ctx = _monta_contexto_extrato(inicio, fim)
    return render(request, "financeiro/extrato.html", ctx)


@login_required
def extrato_pdf(request):
    """Gera o PDF do extrato com visual profissional, seções coloridas e gráfico comparativo (mês atual x mês anterior)."""
    # Import local (evita carregar libs quando não usado)
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        KeepTogether
    )
    from reportlab.platypus.flowables import HRFlowable
    # gráfico
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart

    # --------- período ----------
    hoje = timezone.localdate()
    inicio = _parse_date(request.GET.get("inicio")) or hoje.replace(day=1)
    fim    = _parse_date(request.GET.get("fim")) or hoje
    periodo_txt = f"{inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"

    # --------- dados ----------
    ctx = _monta_contexto_extrato(inicio, fim)

    # --------- tema/cores ----------
    brand         = HexColor("#1e40af")  # indigo-800 (principal)
    brand_text    = HexColor("#111827")  # gray-900
    brand_light   = HexColor("#e0e7ff")  # indigo-100 (header tabela)
    brand_lighter = HexColor("#eef2ff")  # indigo-50  (fundo card)
    text_muted    = colors.Color(0.30, 0.30, 0.34)

    # paletas por seção
    azul_bg     = HexColor("#dbeafe")  # Receitas (header)
    azul_tx     = HexColor("#2563eb")
    vermelho_bg = HexColor("#fee2e2")  # Despesas (header)
    vermelho_tx = HexColor("#dc2626")
    amber_bg    = HexColor("#fef9c3")  # Projeção/Vencidas (header)
    amber_tx    = HexColor("#d97706")

    # --------- estilos ----------
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="H1",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=brand,
        spaceAfter=6,
    ))
    # três H2 com cores diferentes
    styles.add(ParagraphStyle(
        name="H2Receitas",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        textColor=azul_tx,
        spaceBefore=6,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="H2Despesas",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        textColor=vermelho_tx,
        spaceBefore=6,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="H2Projecao",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        textColor=amber_tx,
        spaceBefore=6,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Muted",
        parent=styles["Normal"],
        fontSize=9,
        textColor=text_muted,
    ))
    styles.add(ParagraphStyle(
        name="Badge",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=brand_text,
        spaceAfter=2,
    ))

    # --------- doc ----------
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=28, rightMargin=28, topMargin=52, bottomMargin=36,
        title="Extrato Financeiro"
    )

    # header/footer
    def _on_page(canvas, _doc):
        canvas.saveState()
        w, h = A4
        # header
        canvas.setFillColor(brand)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(28, h - 26, "Extrato Financeiro")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(text_muted)
        canvas.drawRightString(w - 28, h - 26, f"Período: {periodo_txt}")
        canvas.setStrokeColor(brand)
        canvas.setLineWidth(0.8)
        canvas.line(28, h - 30, w - 28, h - 30)
        # footer
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(text_muted)
        canvas.drawString(28, 22, f"Emitido em {hoje.strftime('%d/%m/%Y')}")
        canvas.drawRightString(w - 28, 22, f"Página {_doc.page}")
        canvas.restoreState()

    story = []

    # título + tags
    story.append(Paragraph("Extrato Financeiro", styles["H1"]))
    story.append(Paragraph(f"Período: {periodo_txt}", styles["Muted"]))
    story.append(Spacer(1, 4))

    # "tags" estilo badge (Receitas / Despesas / Projeção)
    badge_tbl = Table(
        [[
            Paragraph("Receitas", styles["Badge"]),
            Paragraph("Despesas", styles["Badge"]),
            Paragraph("Projeção", styles["Badge"]),
        ]],
        colWidths=[70, 70, 70],
        hAlign="LEFT"
    )
    badge_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), azul_bg),
        ("BACKGROUND", (1,0), (1,0), vermelho_bg),
        ("BACKGROUND", (2,0), (2,0), amber_bg),
        ("BOX", (0,0), (-1,-1), 0.25, colors.white),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING",(0,0), (-1,-1), 6),
        ("TOPPADDING",  (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ]))
    story.append(badge_tbl)

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", color=brand, thickness=0.8, spaceBefore=4, spaceAfter=10))
    
    # ---------------- KPIs em "cards" (grade 3x) ----------------
    kpis = [
        ("Parcelas PAGAS",             _brl(ctx["total_parcelas_pagas"])),
        ("Entradas brutas (vendas)",   _brl(ctx["total_entradas_brutas"])),
        ("Comissões sobre entradas",   _brl(ctx["total_comissoes"])),
        ("Entradas líquidas",          _brl(ctx["total_entradas_liquidas"])),
        ("Total de Receitas",          _brl(ctx["total_receitas"])),
        ("Despesas PAGAS (contábil)",  _brl(ctx["total_despesas_pagas"])),
        ("Despesas p/ FLUXO",          _brl(ctx["total_despesas_pagas_fluxo"])),
        ("Caixa no período",           _brl(ctx["caixa_no_periodo"])),
        ("Saldo em caixa desde o início",   _brl(ctx["caixa_ate_fim"])),
    ]

    def _kpi_card(title: str, value: str):
        t = Table(
            [[Paragraph(title, ParagraphStyle(
                name="kpiTitle", fontName="Helvetica", fontSize=8.8, textColor=text_muted
            ))],
             [Paragraph(value, ParagraphStyle(
                 name="kpiValue", fontName="Helvetica-Bold", fontSize=13, textColor=brand_text
             ))]],
            colWidths=[170]
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), brand_lighter),
            ("BOX", (0,0), (-1,-1), 0.5, brand_light),
            ("INNERGRID", (0,0), (-1,-1), 0.0, colors.white),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING",(0,0), (-1,-1), 8),
            ("TOPPADDING",  (0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ]))
        return t

    # organiza em linhas de 3 cards
    rows_cards = []
    row = []
    for idx, (t, v) in enumerate(kpis, 1):
        row.append(_kpi_card(t, v))
        if idx % 3 == 0:
            rows_cards.append(row)
            row = []
    if row:
        while len(row) < 3:
            row.append(Table([[""]], colWidths=[170], rowHeights=[0]))
        rows_cards.append(row)

    cards_tbl = Table(rows_cards, colWidths=[170, 170, 170], hAlign="LEFT", spaceBefore=2, spaceAfter=12)
    cards_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(cards_tbl)

    # ---------------- Helper para seções (tabelas) ----------------
    def _section_table(title: str, header: list[str], rows: list[list], col_widths: list[int], scheme: str):
        """scheme: 'receitas' | 'despesas' | 'projecao' (muda cores da header e do título)."""
        if scheme == "receitas":
            section_style = styles["H2Receitas"]
            head_bg, head_tx = azul_bg, azul_tx
        elif scheme == "despesas":
            section_style = styles["H2Despesas"]
            head_bg, head_tx = vermelho_bg, vermelho_tx
        else:
            section_style = styles["H2Projecao"]
            head_bg, head_tx = amber_bg, amber_tx

        story.append(Paragraph(title, section_style))
        tbl = Table([header] + rows, colWidths=col_widths, hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
            ("BACKGROUND", (0,0), (-1,0), head_bg),
            ("TEXTCOLOR", (0,0), (-1,0), head_tx),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.Color(0.98,0.98,0.98)]),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ALIGN", (-1,1), (-1,-1), "RIGHT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING",(0,0), (-1,-1), 6),
            ("TOPPADDING",  (0,0), (-1,0), 6),
            ("BOTTOMPADDING",(0,0), (-1,0), 6),
        ]))
        story.append(KeepTogether(tbl))
        story.append(Spacer(1, 10))

    # ---------------- Seção: Parcelas PAGAS (Receitas) ----------------
    rows_pagas = []
    for p in ctx["parcelas_pagas"][:200]:
        rows_pagas.append([
            p.data_pagamento.strftime("%d/%m/%Y") if p.data_pagamento else "",
            (getattr(getattr(p, "venda", None), "cliente", None).nome
             if getattr(p, "venda", None) and getattr(p.venda, "cliente", None) else ""),
            f"#{p.venda_id}",
            f"{getattr(p, 'numero', '')}/{getattr(getattr(p, 'venda', None), 'parcelas_total', '')}",
            _brl(getattr(p, "valor", 0)),
        ])
    _section_table(
        "Parcelas PAGAS no período (amostra)",
        ["Pagamento", "Cliente", "Venda", "Parcela", "Valor"],
        rows_pagas,
        [70, 210, 55, 60, 65],
        scheme="receitas",
    )

    # ---------------- Seção: Despesas ----------------
    rows_desp = []
    for d in ctx["despesas"][:200]:
        rows_desp.append([
            d.data.strftime("%d/%m/%Y") if d.data else "",
            d.descricao or "",
            d.status or "",
            _brl(getattr(d, "valor", 0)),
        ])
    _section_table(
        "Despesas no período (amostra)",
        ["Data", "Descrição", "Status", "Valor"],
        rows_desp,
        [70, 245, 60, 85],
        scheme="despesas",
    )

    # ---------------- Seção: Vencidas (Projeção/Atraso) ----------------
    rows_venc = []
    for p in ctx["vencidas"][:200]:
        rows_venc.append([
            p.vencimento.strftime("%d/%m/%Y") if p.vencimento else "",
            (getattr(getattr(p, "venda", None), "cliente", None).nome
             if getattr(p, "venda", None) and getattr(p.venda, "cliente", None) else ""),
            f"#{p.venda_id}",
            f"{getattr(p, 'numero', '')}/{getattr(getattr(p, 'venda', None), 'parcelas_total', '')}",
            _brl(getattr(p, "valor", 0)),
        ])
    _section_table(
        "Parcelas Vencidas (amostra)",
        ["Vencimento", "Cliente", "Venda", "Parcela", "Valor"],
        rows_venc,
        [70, 210, 55, 60, 65],
        scheme="projecao",
    )

    # ---------------- Gráfico comparativo (mês atual x mês anterior) ----------------
    # Define mês anterior respeitando o 'inicio' atual
    fim_mes_anterior = inicio - timedelta(days=1)
    inicio_mes_anterior = fim_mes_anterior.replace(day=1)
    ctx_prev = _monta_contexto_extrato(inicio_mes_anterior, fim_mes_anterior)

    receitas_atual  = float(ctx["total_receitas"] or 0)
    despesas_atual  = float(ctx["total_despesas_pagas"] or 0)
    receitas_prev   = float(ctx_prev["total_receitas"] or 0)
    despesas_prev   = float(ctx_prev["total_despesas_pagas"] or 0)

    story.append(Paragraph("Comparativo mês atual × mês anterior", styles["H2Projecao"]))

    drawing = Drawing(470, 220)  # largura x altura
    chart = VerticalBarChart()
    chart.x = 40
    chart.y = 40
    chart.height = 140
    chart.width = 380
    chart.data = [
        [receitas_prev, receitas_atual],  # série 0: Receitas
        [despesas_prev, despesas_atual],  # série 1: Despesas (contábil)
    ]
    chart.categoryAxis.categoryNames = ["Mês Anterior", "Mês Atual"]
    chart.valueAxis.valueMin = 0
    chart.barWidth = 22
    chart.groupSpacing = 16
    chart.barSpacing = 6

    # cores das séries
    chart.bars[0].fillColor = azul_tx       # Receitas
    chart.bars[1].fillColor = vermelho_tx   # Despesas

    # rótulos dos eixos
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 8.5
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 8.5
    chart.valueAxis.labelTextFormat = '%.0f'

    drawing.add(chart)
    drawing.add(String(40, 190, "R$ (valores)", fontName="Helvetica", fontSize=8.5, fillColor=text_muted))
    # legendinha simples
    drawing.add(String(340, 190, "■ Receitas", fontName="Helvetica-Bold", fontSize=9, fillColor=azul_tx))
    drawing.add(String(420, 190, "■ Despesas", fontName="Helvetica-Bold", fontSize=9, fillColor=vermelho_tx))

    # Embala o drawing para evitar quebra ruim de página
    story.append(Spacer(1, 4))
    story.append(KeepTogether(drawing))

    # renderiza PDF
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    pdf_bytes = buf.getvalue()
    buf.close()

    filename = f"extrato_{inicio.strftime('%Y%m%d')}_{fim.strftime('%Y%m%d')}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


@csrf_exempt
def telegram_callback(request):
    """
    Endpoint para receber callbacks dos botões do Telegram
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Método não permitido'}, status=405)
        
        data = json.loads(request.body)
        
        # Se não for callback, apenas retorna OK
        if 'callback_query' not in data:
            return JsonResponse({'status': 'ok'})
        
        # Extrair dados do callback
        callback_query = data['callback_query']
        callback_data = callback_query['data']
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']
        
                # Importar requests
        import requests
        
        bot_token = "8390754722:AAH_lZ6D0Xl9lZVJkmYyebRLKvX8Vpqp2_o"
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        
        # Buscar dados financeiros do mês atual
        hoje = date.today()
        dados = _relatorio_mensal(hoje.year, hoje.month)
        
        # Gerar resposta baseada no botão clicado
        if callback_data == 'receitas':
            text = f"""💰 <b>RECEITAS - {hoje.strftime('%B/%Y').upper()}</b>

� <b>Parcelas Pagas:</b> {_brl(dados['parcelas_pagas'])}
💵 <b>Entradas Líquidas:</b> {_brl(dados['entradas_liquidas'])}

<b>TOTAL RECEITAS:</b> {_brl(dados['total_receitas'])}"""

        elif callback_data == 'despesas':
            text = f"""💸 <b>DESPESAS - {hoje.strftime('%B/%Y').upper()}</b>

💰 <b>Total Pago:</b> {_brl(dados['total_despesas_pagas'])}

<b>📋 PRINCIPAIS DESPESAS:</b>"""
            
            # Listar as 5 maiores despesas do período
            despesas_mes = Despesa.objects.filter(
                data_vencimento__year=hoje.year,
                data_vencimento__month=hoje.month,
                pago=True
            ).order_by('-valor')[:5]
            
            for i, desp in enumerate(despesas_mes, 1):
                text += f"\n{i}. {desp.descricao[:25]} - {_brl(desp.valor)}"
            
            if not despesas_mes:
                text += "\n<i>Nenhuma despesa paga neste período</i>"

        elif callback_data == 'saldo':
            saldo = dados['total_receitas'] - dados['total_despesas_pagas']
            emoji_saldo = "💚" if saldo >= 0 else "❌"
            
            text = f"""💵 <b>SALDO - {hoje.strftime('%B/%Y').upper()}</b>

� <b>Receitas:</b> {_brl(dados['total_receitas'])}
💸 <b>Despesas:</b> {_brl(dados['total_despesas_pagas'])}

{emoji_saldo} <b>SALDO FINAL:</b> {_brl(saldo)}"""

        else:
            text = "❓ Opção não reconhecida. Tente novamente."
        
        # Adicionar botões de navegação
        keyboard = [
            [
                {"text": "💰 Receitas", "callback_data": "receitas"},
                {"text": "💸 Despesas", "callback_data": "despesas"}
            ],
            [
                {"text": "💵 Saldo", "callback_data": "saldo"}
            ]
        ]
        
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'HTML',
            'reply_markup': {'inline_keyboard': keyboard}
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        return JsonResponse({
            'status': 'success', 
            'telegram_response': response.json() if response.status_code == 200 else f"Erro {response.status_code}"
        })
            
        callback_query = data['callback_query']
        callback_data = callback_query['data']
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']
        
        # Resposta simples para teste
        bot_token = "8390754722:AAH_lZ6D0Xl9lZVJkmYyebRLKvX8Vpqp2_o"
        telegram_url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        
        # Texto baseado no botão clicado
        if callback_data == 'receitas':
            novo_texto = "✅ <b>FUNCIONOU!</b>\n\n� Botão Receitas clicado com sucesso!"
        elif callback_data == 'despesas':
            novo_texto = "✅ <b>FUNCIONOU!</b>\n\n� Botão Despesas clicado com sucesso!"
        elif callback_data == 'saldo':
            novo_texto = "✅ <b>FUNCIONOU!</b>\n\n� Botão Saldo clicado com sucesso!"
        else:
            novo_texto = "✅ <b>FUNCIONOU!</b>\n\nBotão clicado com sucesso!"
        
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': novo_texto,
            'parse_mode': 'HTML',
            'reply_markup': {
                'inline_keyboard': [
                    [{'text': '⬅️ Teste Voltar', 'callback_data': 'voltar'}]
                ]
            }
        }
        
        # Apenas retornar sucesso sem conectar com Telegram por enquanto
        return JsonResponse({
            'status': 'received', 
            'callback_data': callback_data,
            'message': 'Webhook funcionando - callback recebido com sucesso!',
            'payload_que_seria_enviado': payload
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)