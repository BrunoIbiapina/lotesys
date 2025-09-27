def telegram_callback(request):
    """
    Endpoint simples - sempre retorna relatório completo (sem botões)
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Método não permitido'}, status=405)
        
        data = json.loads(request.body)
        
        # Verificar se é uma mensagem de texto normal
        if 'message' in data and 'text' in data['message']:
            # Responder a mensagens de texto
            chat_id = data['message']['chat']['id']
            message_text = data['message']['text'].lower()
            
            # Importar requests
            import requests
            
            bot_token = "8390754722:AAH_lZ6D0Xl9lZVJkmYyebRLKvX8Vpqp2_o"
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            # Resposta baseada no texto digitado
            if any(palavra in message_text for palavra in ['relatorio', 'relatório', 'financeiro', 'saldo', 'receita', 'despesa']):
                # Se mencionou palavras-chave, envia relatório completo
                response_text = "📊 <b>Gerando relatório...</b>\n\nClique no botão para ver os dados:"
                keyboard = [[{"text": "📊 Ver Relatório Completo", "callback_data": "relatorio"}]]
            else:
                # Resposta genérica para outras mensagens
                response_text = f"👋 Olá! Recebi sua mensagem: <i>'{data['message']['text'][:50]}...'</i>\n\nPara ver o relatório financeiro, use o botão abaixo:"
                keyboard = [[{"text": "📊 Ver Relatório", "callback_data": "relatorio"}]]
            
            payload = {
                'chat_id': chat_id,
                'text': response_text,
                'parse_mode': 'HTML',
                'reply_markup': {'inline_keyboard': keyboard}
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            return JsonResponse({
                'status': 'message_processed',
                'telegram_response': response.json() if response.status_code == 200 else f"Erro {response.status_code}"
            })
        
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
        
        # Buscar dados financeiros do mês atual usando a API existente
        hoje = date.today()
        
        # Simular uma requisição para pegar os dados via API
        from django.test import RequestFactory
        factory = RequestFactory()
        api_request = factory.get(f'/?mes={hoje.year}-{hoje.month:02d}')
        api_request.META['HTTP_AUTHORIZATION'] = 'Token SeuTokenSecreto123'
        
        # Chamar a API interna
        api_response = relatorio_mensal_api(api_request)
        dados = json.loads(api_response.content)
        
        # Buscar TODAS as despesas do mês
        despesas_mes = Despesa.objects.filter(
            data__year=hoje.year,
            data__month=hoje.month
        ).order_by('-valor')  # TODAS as despesas
        
        # Separar por status
        despesas_pagas = despesas_mes.filter(status='PAGA')
        despesas_previstas = despesas_mes.filter(status='PREVISTA')
        
        # Criar relatório COMPLETO (como email)
        text = f"""📊 <b>RELATÓRIO COMPLETO</b>
<b>{dados['mes_ano']}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 <b>RECEITAS</b>
🏦 TOTAL: <b>{dados['total_receitas']}</b>

💸 <b>DESPESAS</b>
✅ Pagas: {dados['total_despesas_pagas']}
⏳ Previstas: {dados['total_despesas_previstas']}"""

        # Adicionar TODAS as despesas pagas
        if despesas_pagas.exists():
            text += f"\n\n✅ <b>PAGAS ({despesas_pagas.count()}):</b>"
            for i, desp in enumerate(despesas_pagas[:8], 1):
                text += f"\n{i}. {desp.descricao[:35]} - {_brl(desp.valor)}"
        
        # Adicionar despesas previstas
        if despesas_previstas.exists():
            text += f"\n\n⏳ <b>PREVISTAS ({despesas_previstas.count()}):</b>"
            for i, desp in enumerate(despesas_previstas[:6], 1):
                text += f"\n{i}. {desp.descricao[:35]} - {_brl(desp.valor)}"
        
        # Saldo final detalhado
        text += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 <b>SALDO DO PERÍODO</b>
💰 Receitas: {dados['total_receitas']}
💸 Despesas Pagas: {dados['total_despesas_pagas']}
<b>🏦 RESULTADO: {dados.get('fluxo_liquido', 'R$ 0,00')}</b>

📅 {hoje.strftime('%d/%m/%Y às %H:%M')}"""

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