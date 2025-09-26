# 📧 Automação de Email - Relatório Mensal LoteSys

## 🎯 Objetivo
Enviar automaticamente o relatório financeiro mensal no último dia de cada mês.

## 🔗 Endpoint Criado
```
GET /financeiro/relatorio-mensal/
```

### Parâmetros:
- `mes` (opcional): formato YYYY-MM (ex: 2024-09)
- `format=pdf`: para baixar o PDF diretamente

### Exemplos:
```
# Dados JSON do mês anterior
https://seu-site.com/financeiro/relatorio-mensal/

# Mês específico (JSON)
https://seu-site.com/financeiro/relatorio-mensal/?mes=2025-09
https://seu-site.com/financeiro/relatorio-mensal/?mes=2024-09

# PDF do mês específico
https://seu-site.com/financeiro/relatorio-mensal/?mes=2024-09&format=pdf
```

## 🤖 Configuração no Activepieces

### 1️⃣ **TRIGGER - Schedule**
```json
{
  "name": "Monthly Report",
  "cron": "0 23 28-31 * *",
  "description": "Último dia do mês às 23h"
}
```

### 2️⃣ **STEP 1 - HTTP Request (Dados JSON)**

⚠️ **IMPORTANTE**: Para funcionar corretamente, adicione o parâmetro `&mes=2025-09` na URL para buscar setembro de 2025 (ou o mês desejado).

```json
{
  "method": "GET",
  "url": "https://lotesys-xxxxx.onrender.com/financeiro/relatorio-mensal/?token=SeuTokenSecreto123&mes=2025-09",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### 3️⃣ **STEP 2 - HTTP Request (Download PDF)**
```json
{
  "method": "GET", 
  "url": "{{steps.step1.body.url_pdf}}",
  "responseType": "arrayBuffer"
}
```

### 4️⃣ **STEP 3 - Send Email**
```json
{
  "to": ["seu-email@gmail.com"],
  "subject": "📊 Relatório Financeiro - {{steps.step1.body.mes_ano}}",
  "body": "
    Olá!
    
    Segue o relatório financeiro de {{steps.step1.body.mes_ano}}:
    
    💰 Total Receitas: {{steps.step1.body.total_receitas}}
    💸 Total Despesas: {{steps.step1.body.total_despesas}}
    📊 Saldo Líquido: {{steps.step1.body.saldo_liquido}}
    
    Período: {{steps.step1.body.periodo}}
    
    PDF em anexo.
  ",
  "attachments": [
    {
      "filename": "relatorio-{{steps.step1.body.mes_ano}}.pdf",
      "content": "{{steps.step2.body}}"
    }
  ]
}
```

## 🔧 Configuração Alternativa (Mais Simples)

Se preferir uma configuração mais simples:

### Trigger: 
- **Schedule**: "0 9 1 * *" (Todo dia 1 às 9h)

### Step único - Email com link:
```json
{
  "to": ["seu-email@gmail.com"],
  "subject": "📊 Relatório Mensal Disponível",
  "body": "
    Relatório do mês anterior disponível em:
    https://lotesys-xxxxx.onrender.com/financeiro/relatorio-mensal/?format=pdf
  "
}
```

## 🚀 Próximos Passos

1. ✅ Deploy do endpoint (já criado)
2. 🔧 Configurar no Activepieces
3. 🧪 Testar manualmente
4. 📅 Ativar automação

## ⚠️ Correção de Dados

**PROBLEMA IDENTIFICADO**: O endpoint estava buscando agosto de 2025 (mês anterior padrão), mas só há dados financeiros a partir de setembro de 2025.

**SOLUÇÃO**: Adicionar o parâmetro `&mes=2025-09` na URL do Step 1 do Activepieces para buscar os dados corretos.

### Dados Corretos (Setembro 2025):
- 💰 **Total Receitas**: R$ 6.000,00
- 💸 **Total Despesas Pagas**: R$ 4.200,00  
- 📊 **Fluxo Líquido**: R$ 5.000,00
- 🏦 **Caixa até Fim**: R$ 5.000,00

### Como Ajustar no Activepieces:
1. Vá no **Step 1** (HTTP Request)
2. Altere a URL para incluir `&mes=2025-09`
3. URL final: `https://lotesys-xxxxx.onrender.com/financeiro/relatorio-mensal/?token=SeuTokenSecreto123&mes=2025-09`
4. Teste novamente

### Para Meses Futuros:
- Para outubro: `&mes=2025-10`
- Para novembro: `&mes=2025-11`
- Ou deixe sem parâmetro `mes` para buscar sempre o mês anterior automaticamente

## 📞 URLs de Teste
- Dados: https://lotesys-xxxxx.onrender.com/financeiro/relatorio-mensal/
- PDF: https://lotesys-xxxxx.onrender.com/financeiro/relatorio-mensal/?format=pdf