# Exemplo de implementação WhatsApp Business Cloud API
# Similar ao que fizemos no Telegram

def whatsapp_callback(request):
    """
    Webhook do WhatsApp Business - retorna relatório financeiro completo
    Baseado no telegram_callback que já funciona
    """
    try:
        if request.method == 'GET':
            # Verificação do webhook do WhatsApp (obrigatório)
            verify_token = "SeuTokenVerificacao123"
            mode = request.GET.get('hub.mode')
            token = request.GET.get('hub.verify_token')
            challenge = request.GET.get('hub.challenge')
            
            if mode == 'subscribe' and token == verify_token:
                return HttpResponse(challenge)
            return HttpResponse('Forbidden', status=403)
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Método não permitido'}, status=405)
        
        data = json.loads(request.body)
        
        # Estrutura do WhatsApp é diferente do Telegram
        if 'entry' in data and len(data['entry']) > 0:
            entry = data['entry'][0]
            if 'changes' in entry and len(entry['changes']) > 0:
                change = entry['changes'][0]
                if 'value' in change and 'messages' in change['value']:
                    messages = change['value']['messages']
                    
                    for message in messages:
                        # Processar mensagem
                        from_number = message['from']
                        message_text = message.get('text', {}).get('body', '').lower()
                        
                        # Se mencionou palavras financeiras, envia relatório
                        if any(palavra in message_text for palavra in ['relatorio', 'relatório', 'financeiro', 'saldo']):
                            response_result = send_whatsapp_report(from_number)
                            return JsonResponse({'status': 'report_sent', 'result': response_result})
                        else:
                            # Resposta padrão
                            response_result = send_whatsapp_message(
                                from_number, 
                                "👋 Olá! Para ver o relatório financeiro, digite 'relatório' ou 'financeiro'."
                            )
                            return JsonResponse({'status': 'message_sent', 'result': response_result})
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def send_whatsapp_report(to_number):
    """
    Enviar relatório financeiro via WhatsApp
    Usa a mesma lógica do Telegram
    """
    import requests
    from datetime import date
    import calendar
    
    # Token do WhatsApp Business Cloud API
    access_token = "SEU_ACCESS_TOKEN_WHATSAPP"
    phone_number_id = "SEU_PHONE_NUMBER_ID"
    
    # Buscar dados financeiros (igual o Telegram)
    hoje = date.today()
    ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
    inicio = date(hoje.year, hoje.month, 1)
    fim = date(hoje.year, hoje.month, ultimo_dia)
    ctx = _monta_contexto_extrato(inicio, fim)
    
    # Buscar despesas
    despesas_mes = Despesa.objects.filter(
        data__year=hoje.year,
        data__month=hoje.month
    ).order_by('-valor')
    
    despesas_pagas = despesas_mes.filter(status='PAGA')
    despesas_previstas = despesas_mes.filter(status='PREVISTA')
    
    # Calcular valores corretos (igual Telegram)
    receitas_valor = ctx['total_receitas']
    despesas_fluxo_valor = ctx['total_despesas_pagas_fluxo']
    resultado_correto = receitas_valor - despesas_fluxo_valor
    
    # Criar texto do relatório (similar ao Telegram)
    meses_pt = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    
    text = f"""📊 *RELATÓRIO COMPLETO*
*{meses_pt[hoje.month]} {hoje.year}*
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 *RECEITAS*
🏦 TOTAL: *{_brl(receitas_valor)}*

💸 *DESPESAS*
✅ Pagas (contábil): {_brl(ctx['total_despesas_pagas'])}
⏳ Previstas: {_brl(ctx['total_despesas_previstas'])}"""

    # Adicionar despesas pagas
    if despesas_pagas.exists():
        text += f"\n\n✅ *PAGAS ({despesas_pagas.count()}):*"
        for i, desp in enumerate(despesas_pagas[:10], 1):  # Limitar a 10 no WhatsApp
            text += f"\n{i}. {desp.descricao[:30]} - {_brl(desp.valor)}"
        
        if despesas_pagas.count() > 10:
            text += f"\n... e mais {despesas_pagas.count() - 10} despesas"
    
    # Adicionar despesas previstas
    if despesas_previstas.exists():
        text += f"\n\n⏳ *PREVISTAS ({despesas_previstas.count()}):*"
        for i, desp in enumerate(despesas_previstas[:5], 1):
            text += f"\n{i}. {desp.descricao[:30]} - {_brl(desp.valor)}"
    
    # Saldo final
    text += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 *FLUXO DE CAIXA*
💰 Receitas: {_brl(receitas_valor)}
💸 Despesas (p/ fluxo): {_brl(despesas_fluxo_valor)}
*🏦 RESULTADO: {_brl(resultado_correto)}*

📝 _Despesas p/ fluxo = despesas pagas - comissões já abatidas nas vendas_
📅 {hoje.strftime('%d/%m/%Y às %H:%M')}"""
    
    # Enviar via WhatsApp API
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


def send_whatsapp_message(to_number, message_text):
    """
    Enviar mensagem simples via WhatsApp
    """
    import requests
    
    access_token = "SEU_ACCESS_TOKEN_WHATSAPP"
    phone_number_id = "SEU_PHONE_NUMBER_ID"
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()


# URLs para adicionar no urls.py
"""
from django.urls import path
from . import views

urlpatterns = [
    # ... outras URLs
    path('whatsapp-callback/', views.whatsapp_callback, name='whatsapp_callback'),
]
"""