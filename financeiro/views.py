# financeiro/views.py
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

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


def _monta_contexto_extrato(inicio: date, fim: date) -> dict:
    hoje = timezone.localdate()

    # --- Despesas no período
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

    # --- Parcelas pagas (recebidas) no período
    parcelas_pagas_qs = (
        Parcela.objects
        .select_related("venda", "venda__cliente")
        .filter(status__iexact="PAGO", data_pagamento__range=[inicio, fim])
        .order_by("-data_pagamento", "-id")
    )
    total_parcelas_pagas = parcelas_pagas_qs.aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"] or Decimal("0.00")

    # --- Entradas de vendas no período (com liquidação de comissão)
    vendas_periodo_qs = (
        Venda.objects
        .select_related("cliente")
        .filter(data_venda__range=[inicio, fim])
        .order_by("-data_venda", "-id")
    )

    entradas_detalhe: list[dict] = []
    total_entradas_brutas = Decimal("0.00")
    total_comissoes = Decimal("0.00")
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
            total_entradas_brutas += entrada_bruta
            total_comissoes += comissao_entr
            total_entradas_liquidas += entrada_liq

    total_receitas = total_parcelas_pagas + total_entradas_liquidas

    # --- Vencidas (pendentes em atraso)
    vencidas_qs = (
        Parcela.objects
        .select_related("venda", "venda__cliente")
        .filter(status__iexact="PENDENTE", vencimento__lt=hoje)
        .order_by("vencimento", "id")
    )
    total_vencidas = vencidas_qs.aggregate(
        v=Coalesce(Sum("valor"), Decimal("0.00"))
    )["v"] or Decimal("0.00")

    # --- A receber (pendentes futuras)
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

    return dict(
        hoje=hoje,
        inicio=inicio,
        fim=fim,
        despesas=despesas_qs,
        total_despesas_pagas=total_despesas_pagas,
        total_despesas_previstas=total_despesas_previstas,
        parcelas_pagas=parcelas_pagas_qs,
        total_parcelas_pagas=total_parcelas_pagas,
        entradas_detalhe=entradas_detalhe,
        total_entradas_brutas=total_entradas_brutas,
        total_comissoes=total_comissoes,
        total_entradas_liquidas=total_entradas_liquidas,
        total_receitas=total_receitas,
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


@login_required
def extrato(request):
    hoje = timezone.localdate()
    inicio = _parse_date(request.GET.get("inicio")) or hoje.replace(day=1)
    fim    = _parse_date(request.GET.get("fim")) or hoje

    ctx = _monta_contexto_extrato(inicio, fim)
    return render(request, "financeiro/extrato.html", ctx)


@login_required
def extrato_pdf(request):
    """Gera o PDF do extrato com visual profissional (tema azul/indigo)."""
    # Import local (evita carregar libs quando não usado)
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )

    # --------- período ----------
    hoje = timezone.localdate()
    inicio = _parse_date(request.GET.get("inicio")) or hoje.replace(day=1)
    fim    = _parse_date(request.GET.get("fim")) or hoje
    periodo_txt = f"{inicio.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}"

    # --------- dados ----------
    ctx = _monta_contexto_extrato(inicio, fim)

    # --------- tema/cores ----------
    brand        = HexColor("#1e40af")  # indigo-800
    brand_text   = HexColor("#111827")  # gray-900
    brand_light  = HexColor("#e0e7ff")  # indigo-100
    brand_lighter= HexColor("#eef2ff")  # indigo-50
    accent       = HexColor("#3b82f6")  # blue-500
    text_muted   = colors.Color(0.30, 0.30, 0.34)

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
    styles.add(ParagraphStyle(
        name="H2",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        textColor=brand,
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
        ("BACKGROUND", (0,0), (0,0), HexColor("#dbeafe")),  # blue-100
        ("BACKGROUND", (1,0), (1,0), HexColor("#fee2e2")),  # red-100
        ("BACKGROUND", (2,0), (2,0), HexColor("#fef9c3")),  # yellow-100
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
        ("Parcelas PAGAS",            _brl(ctx["total_parcelas_pagas"])),
        ("Entradas brutas (vendas)",  _brl(ctx["total_entradas_brutas"])),
        ("Comissões sobre entradas",  _brl(ctx["total_comissoes"])),
        ("Entradas líquidas",         _brl(ctx["total_entradas_liquidas"])),
        ("Total de Receitas",         _brl(ctx["total_receitas"])),
        ("Despesas PAGAS",            _brl(ctx["total_despesas_pagas"])),
        ("Despesas PREVISTAS",        _brl(ctx["total_despesas_previstas"])),
        ("Vencidas (atraso)",         _brl(ctx["total_vencidas"])),
        ("A receber (pendentes)",     _brl(ctx["total_a_receber"])),
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
        # completa linha final com células vazias para alinhamento
        while len(row) < 3:
            row.append(Table([[""]], colWidths=[170], rowHeights=[0]))
        rows_cards.append(row)

    cards_tbl = Table(rows_cards, colWidths=[170, 170, 170], hAlign="LEFT", spaceBefore=2, spaceAfter=12)
    cards_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(cards_tbl)

    # ---------------- Helper para seções (tabelas) ----------------
    def _section_table(title: str, header: list[str], rows: list[list], col_widths: list[int]):
        story.append(Paragraph(title, styles["H2"]))
        tbl = Table([header] + rows, colWidths=col_widths, hAlign="LEFT")
        tbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
            ("BACKGROUND", (0,0), (-1,0), brand_light),
            ("TEXTCOLOR", (0,0), (-1,0), brand),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.Color(0.98,0.98,0.98)]),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ALIGN", (-1,1), (-1,-1), "RIGHT"),  # última coluna (valor) à direita
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING",(0,0), (-1,-1), 6),
            ("TOPPADDING",  (0,0), (-1,0), 6),
            ("BOTTOMPADDING",(0,0), (-1,0), 6),
        ]))
        story.append(KeepTogether(tbl))
        story.append(Spacer(1, 10))

    # ---------------- Seção: Parcelas PAGAS ----------------
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
    )

    # ---------------- Seção: Vencidas ----------------
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
    )

    # renderiza PDF
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    pdf_bytes = buf.getvalue()
    buf.close()

    filename = f"extrato_{inicio.strftime('%Y%m%d')}_{fim.strftime('%Y%m%d')}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp