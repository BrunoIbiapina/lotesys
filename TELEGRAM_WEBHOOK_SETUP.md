# 🤖 CONFIGURAÇÃO DO WEBHOOK TELEGRAM - GUIA COMPLETO

## 📋 O QUE PRECISA SER FEITO

Para os botões do Telegram funcionarem, você precisa:

1. **Configurar o Webhook do Bot** 
2. **Criar um Flow no ActivePieces para processar os cliques**
3. **Testar as funcionalidades**

---

## ⚙️ PASSO 1: CONFIGURAR O WEBHOOK DO SEU BOT

### 1.1 - Abrir o navegador e acessar:
```
https://api.telegram.org/bot[SEU_TOKEN]/setWebhook?url=https://lotesys.onrender.com/financeiro/telegram-callback/
```

**🔥 IMPORTANTE:** Substitua `[SEU_TOKEN]` pelo token do seu bot!

### 1.2 - Você deve ver uma resposta assim:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

---

## 🔄 PASSO 2: CRIAR FLOW NO ACTIVEPIECES

### 2.1 - Criar um Novo Flow
- Acesse o ActivePieces
- Clique em "Create Flow"
- Nome: "Telegram Webhook Processor"

### 2.2 - Configurar o Trigger
- **Trigger Type:** Webhook
- **Webhook URL:** Será gerado automaticamente
- **Method:** POST

### 2.3 - Adicionar Ação: HTTP Request
- **Method:** POST
- **URL:** `https://api.telegram.org/bot[SEU_TOKEN]/editMessageText`
- **Headers:**
  ```json
  {
    "Content-Type": "application/json"
  }
  ```
- **Body:** (usar o resultado do webhook anterior)
  ```json
  {{steps.webhook.body}}
  ```

### 2.4 - Salvar e Ativar o Flow

---

## 🚀 PASSO 3: COMO TESTAR

### 3.1 - Enviar mensagem normal pelo ActivePieces
Use o template que criamos anteriormente:

**Message (HTML):**
```html
📊 <b>RELATÓRIO FINANCEIRO</b>
🗓️ <b>Período:</b> {{mes_inicio}} a {{mes_fim}}

💰 <b>Receitas:</b> {{total_receitas_formatted}}
💸 <b>Despesas:</b> {{total_despesas_formatted}}
━━━━━━━━━━━━━━━
💵 <b>Saldo:</b> {{saldo_formatted}}

<i>Escolha uma opção abaixo:</i>
```

**Reply Markup:**
```json
{
  "inline_keyboard": [
    [
      {"text": "💰 Ver Receitas", "callback_data": "receitas"},
      {"text": "💸 Ver Despesas", "callback_data": "despesas"}
    ],
    [
      {"text": "💵 Saldo Detalhado", "callback_data": "saldo"}
    ]
  ]
}
```

### 3.2 - Clicar nos botões e verificar se funcionam

---

## ⚡ VERSÃO SIMPLES (SE O ACTIVEPIECES NÃO FUNCIONAR)

Se tiver dificuldades com o ActivePieces, você pode configurar diretamente no Telegram:

### Opção 1: Webhook Direto
```bash
curl -X POST "https://api.telegram.org/bot[SEU_TOKEN]/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://lotesys.onrender.com/financeiro/telegram-callback/"}'
```

### Opção 2: Usar Postman ou Similar
- **Method:** POST
- **URL:** `https://api.telegram.org/bot[SEU_TOKEN]/setWebhook`
- **Body (JSON):**
  ```json
  {
    "url": "https://lotesys.onrender.com/financeiro/telegram-callback/"
  }
```

---

## 🔧 TROUBLESHOOTING

### Se os botões não aparecem:
- ✅ Verificar se o `Reply Markup` está no formato JSON correto
- ✅ Verificar se o `parse_mode` está como "HTML"

### Se os botões não respondem:
- ✅ Verificar se o webhook foi configurado corretamente
- ✅ Testar a URL: `https://lotesys.onrender.com/financeiro/telegram-callback/`

### Para verificar o webhook atual:
```
https://api.telegram.org/bot[SEU_TOKEN]/getWebhookInfo
```

### Para remover o webhook (se necessário):
```
https://api.telegram.org/bot[SEU_TOKEN]/deleteWebhook
```

---

## 📱 RESULTADO ESPERADO

Quando funcionando corretamente:

1. **Mensagem inicial:** Mostra resumo financeiro com botões
2. **Clique em "Ver Receitas":** Mostra detalhes das receitas + botão "Voltar"
3. **Clique em "Ver Despesas":** Mostra detalhes das despesas + botão "Voltar"  
4. **Clique em "Saldo Detalhado":** Mostra análise completa + botão "Voltar"
5. **Clique em "Voltar":** Retorna ao menu principal

---

## 🆘 PRECISA DE AJUDA?

Se algo não funcionar:
1. Verifique os logs do ActivePieces
2. Teste o endpoint diretamente: `https://lotesys.onrender.com/financeiro/telegram-callback/`
3. Confirme que o token do bot está correto
4. Verifique se o webhook está ativo: `/getWebhookInfo`

**O sistema agora está completo e os botões devem funcionar perfeitamente!** 🎉