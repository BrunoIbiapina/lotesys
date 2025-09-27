# 🤖 LoteSys WhatsApp Bot

Bot do WhatsApp para envio automático de relatórios financeiros do sistema LoteSys.

## 📋 Características

✅ **Sem dependência do Meta/Facebook** - Usa WhatsApp Web.js  
✅ **Autenticação por QR Code** - Como WhatsApp Web  
✅ **Relatórios automáticos 24/7** - Resposta instantânea  
✅ **Dados sempre atualizados** - Conecta com API do Django  
✅ **Interface amigável** - Mensagens formatadas e emojis  
✅ **Robusto** - Tratamento de erros e reconexão automática  

## 🛠 Pré-requisitos

- **Node.js** versão 16 ou superior
- **npm** ou **yarn**
- **Google Chrome** (para Puppeteer)
- **WhatsApp** instalado no celular

## 📦 Instalação

### 1. Clone e entre na pasta
```bash
cd lotesys
cd whatsapp-bot
```

### 2. Instale as dependências
```bash
npm install
```

### 3. Configure o ambiente
```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:
```env
API_URL=https://lotesys.onrender.com/financeiro/relatorio-mensal/
API_TOKEN=Token SeuTokenSecreto123
```

### 4. Execute o bot
```bash
npm start
```

## 📱 Configuração do WhatsApp

1. **Execute o bot**: `npm start`
2. **QR Code aparecerá** no terminal
3. **Abra WhatsApp no celular** → Configurações → Dispositivos conectados
4. **Escaneie o QR Code** mostrado no terminal
5. **Bot conectado!** ✅

## 💬 Como usar

O bot responde automaticamente a mensagens com palavras-chave:

### Comandos que ativam o relatório:
- `relatório` ou `relatorio`
- `financeiro`
- `saldo`
- `receitas` ou `despesas`
- `fluxo` ou `caixa`
- `balanço` ou `extrato`

### Outros comandos:
- `oi` ou `olá` → Mensagem de boas-vindas
- `ajuda` ou `help` → Lista de comandos

### Exemplo de conversa:
```
👤 Você: "Oi"
🤖 Bot: "Olá! Sou o assistente financeiro da LoteSys..."

👤 Você: "relatório"
🤖 Bot: "📊 Gerando relatório financeiro... ⏳"
🤖 Bot: "📊 RELATÓRIO FINANCEIRO COMPLETO..."
```

## 📊 Relatório gerado

O bot retorna dados completos:
- 💰 **Receitas totais**
- 💸 **Despesas pagas e previstas**
- 📋 **Lista das principais despesas**
- 💵 **Fluxo de caixa calculado**
- 📅 **Data/hora da consulta**

## 🔧 Scripts disponíveis

```bash
# Iniciar o bot
npm start

# Instalar dependências
npm install

# Desenvolvimento (com restart automático)
npm run dev
```

## 🏗 Estrutura do projeto

```
whatsapp-bot/
├── bot.js              # Código principal do bot
├── package.json        # Dependências Node.js
├── .env.example        # Modelo de configuração
├── .env                # Suas configurações (criar)
├── README.md           # Este arquivo
└── .wwebjs_auth/       # Sessão WhatsApp (criada automaticamente)
```

## ⚙️ Configurações avançadas

### Arquivo `bot.js` - principais configurações:

```javascript
const config = {
    apiUrl: 'https://lotesys.onrender.com/financeiro/relatorio-mensal/',
    apiToken: 'Token SeuTokenSecreto123',
    maxRetries: 3,
    retryDelay: 5000
};
```

### Personalizar mensagens:
- Edite as funções `formatFinancialReport()`, `sendWelcomeMessage()`, `sendHelpMessage()`

### Adicionar novos comandos:
- Modifique a função `handleMessage()` 

## 🚀 Produção

### Opção 1: PM2 (Recomendado)
```bash
# Instalar PM2
npm install -g pm2

# Iniciar com PM2
pm2 start bot.js --name "lotesys-whatsapp"

# Ver status
pm2 status

# Parar
pm2 stop lotesys-whatsapp
```

### Opção 2: Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["node", "bot.js"]
```

### Opção 3: Servidor VPS
1. Instale Node.js no servidor
2. Clone o código
3. Configure `.env` 
4. Execute com `nohup npm start &`

## 🔒 Segurança

- ✅ **Autenticação local** - Sessão salva localmente
- ✅ **Sem API do Meta** - Não precisa de aprovação Facebook
- ✅ **Token API protegido** - Configure no `.env`
- ✅ **HTTPS obrigatório** - API sempre segura

## 🐛 Troubleshooting

### Erro "Session not found"
```bash
rm -rf .wwebjs_auth
npm start  # Escanear QR novamente
```

### Erro "Puppeteer/Chrome"
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y chromium-browser

# CentOS/RHEL
sudo yum install -y chromium
```

### Bot não responde
1. Verifique se o WhatsApp Web está funcionando
2. Confirme se a API está respondendo
3. Veja os logs no terminal
4. Reinicie o bot

### Timeout da API
- Aumente `timeout` em `axios.get()`
- Verifique conectividade com o servidor Django

## 📞 Suporte

Para problemas:
1. Verifique os **logs no terminal**
2. Teste a **API manualmente**: `curl https://lotesys.onrender.com/financeiro/relatorio-mensal/`
3. Confirme se o **WhatsApp Web funciona** no navegador
4. Reinicie o bot: **Ctrl+C** → `npm start`

## 📈 Roadmap

- [ ] Suporte a múltiplos usuários autorizados
- [ ] Relatórios de períodos específicos
- [ ] Gráficos e imagens
- [ ] Notificações proativas (alertas)
- [ ] Comandos de administração

---

🔥 **Bot criado com WhatsApp Web.js - Alternativa livre ao Meta Business API**