# Estrutura recomendada para WhatsApp sem Meta

# 1. Criar um servidor Node.js separado (whatsapp-bot/)
mkdir whatsapp-bot
cd whatsapp-bot
npm init -y
npm install whatsapp-web.js qrcode-terminal axios

# 2. Arquivo: whatsapp-bot/bot.js
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', (qr) => {
    console.log('📱 Escaneie o QR Code:');
    qrcode.generate(qr, {small: true});
});

client.on('ready', () => {
    console.log('✅ WhatsApp Bot conectado!');
});

client.on('message', async msg => {
    console.log(`📨 Mensagem de ${msg.from}: ${msg.body}`);
    
    const messageText = msg.body.toLowerCase();
    
    // Se mencionou palavras financeiras
    if (messageText.includes('relatório') || 
        messageText.includes('relatorio') || 
        messageText.includes('financeiro') || 
        messageText.includes('saldo')) {
        
        try {
            console.log('💰 Buscando relatório financeiro...');
            
            // Chamar API do Django (igual ActivePieces)
            const response = await axios.get('https://lotesys.onrender.com/financeiro/relatorio-mensal/', {
                headers: {
                    'Authorization': 'Token SeuTokenSecreto123'
                },
                params: {
                    mes: new Date().toISOString().slice(0, 7) // 2024-09
                }
            });
            
            const data = response.data;
            
            // Montar relatório (usando mesma lógica do Telegram)
            let report = `📊 *RELATÓRIO COMPLETO*\n`;
            report += `*${data.mes_ano}*\n`;
            report += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
            
            report += `💰 *RECEITAS*\n`;
            report += `🏦 TOTAL: *${data.total_receitas}*\n\n`;
            
            report += `💸 *DESPESAS*\n`;
            report += `✅ Pagas: ${data.total_despesas_pagas}\n`;
            report += `⏳ Previstas: ${data.total_despesas_previstas}\n\n`;
            
            // Adicionar algumas despesas principais
            if (data.despesas && data.despesas.length > 0) {
                report += `✅ *PRINCIPAIS PAGAS:*\n`;
                const pagas = data.despesas.filter(d => d.status_class === 'paga').slice(0, 8);
                pagas.forEach((desp, i) => {
                    report += `${i+1}. ${desp.descricao.substring(0, 30)} - ${desp.valor}\n`;
                });
                
                if (data.despesas.filter(d => d.status_class === 'paga').length > 8) {
                    const restantes = data.despesas.filter(d => d.status_class === 'paga').length - 8;
                    report += `... e mais ${restantes} despesas\n`;
                }
            }
            
            report += `\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
            report += `💵 *FLUXO DE CAIXA*\n`;
            report += `💰 Receitas: ${data.total_receitas}\n`;
            
            // Usar dados corretos se disponíveis
            if (data.total_despesas_pagas_fluxo) {
                report += `💸 Despesas (p/ fluxo): ${data.total_despesas_pagas_fluxo}\n`;
                report += `*🏦 RESULTADO: ${data.resultado_correto || data.fluxo_liquido}*\n\n`;
                report += `📝 _Despesas p/ fluxo = despesas pagas - comissões já abatidas nas vendas_\n`;
            } else {
                report += `💸 Despesas: ${data.total_despesas_pagas}\n`;
                report += `*🏦 RESULTADO: ${data.fluxo_liquido}*\n\n`;
            }
            
            report += `📅 ${new Date().toLocaleDateString('pt-BR')} às ${new Date().toLocaleTimeString('pt-BR')}`;
            
            await msg.reply(report);
            console.log('✅ Relatório enviado!');
            
        } catch (error) {
            console.error('❌ Erro ao buscar relatório:', error.message);
            await msg.reply('❌ Erro ao gerar relatório. Tente novamente em alguns minutos.');
        }
    } else if (messageText.includes('oi') || 
               messageText.includes('olá') || 
               messageText.includes('menu')) {
        
        // Resposta de boas-vindas
        const welcomeMsg = `👋 Olá! Sou o assistente financeiro da *LoteSys*!\n\n` +
                          `📊 Para ver o relatório financeiro, digite:\n` +
                          `• "relatório"\n` +
                          `• "financeiro"\n` +
                          `• "saldo"\n\n` +
                          `💡 _Respondo automaticamente com os dados atualizados!_`;
        
        await msg.reply(welcomeMsg);
        console.log('👋 Mensagem de boas-vindas enviada');
    }
});

client.on('disconnected', (reason) => {
    console.log('❌ WhatsApp desconectado:', reason);
});

// Inicializar
console.log('🚀 Iniciando WhatsApp Bot...');
client.initialize();

# 3. Arquivo: whatsapp-bot/package.json
{
  "name": "lotesys-whatsapp-bot",
  "version": "1.0.0",
  "description": "Bot WhatsApp para relatórios financeiros LoteSys",
  "main": "bot.js",
  "scripts": {
    "start": "node bot.js",
    "dev": "nodemon bot.js"
  },
  "dependencies": {
    "whatsapp-web.js": "^1.23.0",
    "qrcode-terminal": "^0.12.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.0"
  }
}

# 4. Para executar:
# npm start
# Escanear QR Code com WhatsApp
# Pronto! Bot funcionando 24/7