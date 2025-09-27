@csrf_exempt
def telegram_callback(request):
    """
    Endpoint simples - sempre retorna relatório completo (sem botões)
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
        chat_id = callback_query['message']['chat']['id']
        message_id = callback_query['message']['message_id']
        
        # Importar requests
        import requests
        
        bot_token = "8390754722:AAH_lZ6D0Xl9lZVJkmYyebRLKvX8Vpqp2_o"
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        
        # Buscar dados financeiros do mês atual
        hoje = date.today()
        dados = _relatorio_mensal(hoje.year, hoje.month)
        
        # Calcular saldo
        saldo = dados['total_receitas'] - dados['total_despesas_pagas']
        emoji_saldo = "💚" if saldo >= 0 else "❌"
        
        # Buscar principais despesas do mês
        despesas_mes = Despesa.objects.filter(
            data_vencimento__year=hoje.year,
            data_vencimento__month=hoje.month,
            pago=True
        ).order_by('-valor')[:3]  # Top 3 despesas
        
        # Criar relatório completo resumido
        text = f"""📊 <b>RELATÓRIO FINANCEIRO</b>
<b>{hoje.strftime('%B/%Y').upper()}</b>

💰 <b>RECEITAS</b>
• Parcelas: {_brl(dados['parcelas_pagas'])}
• Entradas: {_brl(dados['entradas_liquidas'])}
• <b>Total: {_brl(dados['total_receitas'])}</b>

💸 <b>DESPESAS</b>
• <b>Total Pago: {_brl(dados['total_despesas_pagas'])}</b>"""

        # Adicionar principais despesas
        if despesas_mes:
            text += "\n\n📋 <b>Principais:</b>"
            for i, desp in enumerate(despesas_mes, 1):
                text += f"\n{i}. {desp.descricao[:20]} - {_brl(desp.valor)}"
        
        # Adicionar saldo final
        text += f"""

{emoji_saldo} <b>SALDO FINAL</b>
<b>{_brl(saldo)}</b>"""

        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        return JsonResponse({
            'status': 'success', 
            'telegram_response': response.json() if response.status_code == 200 else f"Erro {response.status_code}"
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)