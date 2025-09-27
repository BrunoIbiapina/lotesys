const { Client, LocalAuth, MessageTypes } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const moment = require('moment');

// Carregar variáveis de ambiente
require('dotenv').config();

// Configurações
const config = {
    apiUrl: process.env.API_URL || 'https://lotesys.onrender.com/financeiro/relatorio-mensal/',
    apiToken: process.env.API_TOKEN || 'Token SeuTokenSecreto123',
    maxRetries: parseInt(process.env.MAX_RETRIES) || 3,
    retryDelay: parseInt(process.env.RETRY_DELAY) || 5000,
    nodeEnv: process.env.NODE_ENV || 'development'
};

class LoteSysWhatsAppBot {
    constructor() {
        this.client = new Client({
            authStrategy: new LocalAuth({
                clientId: "lotesys-bot"
            }),
            puppeteer: {
                headless: true,
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            }
        });

        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.client.on('qr', (qr) => {
            console.log('📱 Escaneie o QR Code com seu WhatsApp:');
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            qrcode.generate(qr, { small: true });
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log('⏰ QR Code expira em 20 segundos. Se não conseguir, reinicie o bot.');
        });

        this.client.on('ready', () => {
            console.log('✅ LoteSys WhatsApp Bot conectado com sucesso!');
            console.log('🏦 Pronto para receber solicitações de relatórios financeiros');
            console.log(`📊 API configurada: ${config.apiUrl}`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        });

        this.client.on('authenticated', () => {
            console.log('🔐 WhatsApp autenticado com sucesso!');
        });

        this.client.on('disconnected', (reason) => {
            console.log('❌ WhatsApp desconectado:', reason);
            console.log('🔄 Tentando reconectar em 10 segundos...');
            setTimeout(() => {
                this.client.initialize();
            }, 10000);
        });

        this.client.on('message', async (msg) => {
            await this.handleMessage(msg);
        });
    }

    async handleMessage(msg) {
        try {
            // Ignorar mensagens próprias e de grupos grandes
            if (msg.fromMe) return;
            
            const chat = await msg.getChat();
            const contact = await msg.getContact();
            
            console.log(`📨 Mensagem recebida de ${contact.pushname || contact.number}: ${msg.body}`);
            
            const messageText = msg.body.toLowerCase().trim();
            
            // Verificar se é solicitação de relatório
            if (this.isFinancialRequest(messageText)) {
                await this.handleFinancialReport(msg, contact);
            } 
            // Mensagens de saudação
            else if (this.isGreeting(messageText)) {
                await this.sendWelcomeMessage(msg, contact);
            }
            // Ajuda
            else if (messageText.includes('ajuda') || messageText.includes('help') || messageText.includes('menu')) {
                await this.sendHelpMessage(msg, contact);
            }

        } catch (error) {
            console.error('❌ Erro ao processar mensagem:', error);
            await msg.reply('❌ Ocorreu um erro interno. Tente novamente em alguns minutos.');
        }
    }

    isFinancialRequest(text) {
        const keywords = [
            'relatório', 'relatorio', 'financeiro', 'saldo', 
            'receitas', 'despesas', 'fluxo', 'caixa',
            'balanço', 'balanco', 'extrato', 'resumo'
        ];
        return keywords.some(keyword => text.includes(keyword));
    }

    isGreeting(text) {
        const greetings = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'e aí', 'eai'];
        return greetings.some(greeting => text.includes(greeting));
    }

    async handleFinancialReport(msg, contact) {
        try {
            console.log('💰 Solicitação de relatório financeiro detectada');
            
            // Enviar mensagem de "digitando..." e processando
            await msg.reply('📊 Gerando relatório financeiro... ⏳');
            
            const reportData = await this.fetchFinancialData();
            
            if (!reportData) {
                await msg.reply('❌ Não foi possível gerar o relatório no momento. Verifique a conexão com o servidor.');
                return;
            }

            const report = this.formatFinancialReport(reportData);
            
            await msg.reply(report);
            
            console.log(`✅ Relatório enviado para ${contact.pushname || contact.number}`);
            
        } catch (error) {
            console.error('❌ Erro ao gerar relatório:', error);
            await msg.reply('❌ Erro ao gerar o relatório financeiro. Tente novamente em alguns minutos.');
        }
    }

    async fetchFinancialData(retryCount = 0) {
        try {
            console.log(`🔄 Buscando dados financeiros (tentativa ${retryCount + 1}/${config.maxRetries})...`);
            
            const currentMonth = moment().format('YYYY-MM');
            
            const response = await axios.get(config.apiUrl, {
                headers: {
                    'Authorization': config.apiToken,
                    'User-Agent': 'LoteSys-WhatsApp-Bot/1.0'
                },
                params: {
                    mes: currentMonth
                },
                timeout: 15000
            });

            console.log('✅ Dados financeiros obtidos com sucesso');
            return response.data;

        } catch (error) {
            console.error(`❌ Erro ao buscar dados (tentativa ${retryCount + 1}):`, error.message);
            
            if (retryCount < config.maxRetries - 1) {
                console.log(`🔄 Aguardando ${config.retryDelay/1000}s antes da próxima tentativa...`);
                await new Promise(resolve => setTimeout(resolve, config.retryDelay));
                return this.fetchFinancialData(retryCount + 1);
            }
            
            return null;
        }
    }

    formatFinancialReport(data) {
        let report = `📊 *RELATÓRIO FINANCEIRO COMPLETO*\n`;
        report += `*${data.mes_ano}*\n`;

        // Receitas
        report += `💰 *RECEITAS*\n`;
        report += `🏦 TOTAL: *${data.total_receitas}*\n\n`;
        report += `💰 *Qualquer dúvida acesse sua conta no LoteSys*\n`;

        // Despesas resumo
        report += `💸 *DESPESAS*\n`;
        report += `✅ Pagas: ${data.total_despesas_pagas}\n`;
        report += `⏳ Previstas: ${data.total_despesas_previstas}\n\n`;
        report += `💸 *Obs: As comissoes estao dentro das despesas, mas ja hora descontadas das receitas*\n`;

        // Despesas pagas (TODAS)
        if (data.despesas && data.despesas.length > 0) {
            const despesasPagas = data.despesas.filter(d => d.status_class === 'paga');
            
            if (despesasPagas.length > 0) {
                report += `✅ *TODAS AS DESPESAS PAGAS (${despesasPagas.length}):*\n`;
                
                // Mostrar TODAS as despesas pagas
                despesasPagas.forEach((desp, i) => {
                    const descricao = desp.descricao.length > 30 ? 
                                    desp.descricao.substring(0, 30) + '...' : 
                                    desp.descricao;
                    report += `${i + 1}. ${descricao} - ${desp.valor}\n`;
                });
                report += `\n`;
            }

            // Despesas previstas (TODAS)
            const despesasPrevistas = data.despesas.filter(d => d.status_class === 'prevista');
            if (despesasPrevistas.length > 0) {
                report += `⏳ *TODAS AS DESPESAS PREVISTAS (${despesasPrevistas.length}):*\n`;
                
                // Mostrar TODAS as despesas previstas
                despesasPrevistas.forEach((desp, i) => {
                    const descricao = desp.descricao.length > 30 ? 
                                    desp.descricao.substring(0, 30) + '...' : 
                                    desp.descricao;
                    report += `${i + 1}. ${descricao} - ${desp.valor}\n`;
                });
                report += `\n`;
            }
        }

        // Fluxo de caix
        report += `💵 *FLUXO DE CAIXA*\n`;
        report += `💰 Receitas: ${data.total_receitas}\n`;

        // Usar dados corretos se disponíveis
        if (data.total_despesas_pagas_fluxo && data.resultado_correto) {
            report += `💸 Despesas (p/ fluxo): ${data.total_despesas_pagas_fluxo}\n`;
            report += `*🏦 VALOR EM CAIXA: ${data.resultado_correto}*\n\n`;
            report += `📝 _Despesas p/ fluxo = despesas - comissões já abatidas_\n`;
        } else {
            report += `💸 Despesas: ${data.total_despesas_pagas}\n`;
            report += `*🏦 VALOR EM CAIXA: ${data.fluxo_liquido}*\n\n`;
        }

        report += `📅 ${moment().format('DD/MM/YYYY [às] HH:mm')}`;

        return report;
    }

    async sendWelcomeMessage(msg, contact) {
        const name = contact.pushname || 'usuário';
        const welcomeMsg = `👋 Olá ${name}! Sou o assistente financeiro da *Concil*!\n\n` +
                          `📊 Para ver o relatório financeiro do mês ${moment().format('MMMM YYYY')}, digite qualquer uma dessas palavras:\n` +
                          `• "Relatório financeiro geral"\n` +
                          `💡 _Respondo automaticamente com os dados atualizados!_\n\n` +
                          `ℹ️ Digite "ajuda" para ver mais opções.`;
        
        await msg.reply(welcomeMsg);
        console.log(`👋 Boas-vindas enviadas para ${name}`);
    }

    async sendHelpMessage(msg, contact) {
        const helpMsg = `🆘 *AJUDA - LoteSys Bot*\n\n` +
                       `📋 *Comandos disponíveis:*\n` +
                       `• Digite qualquer palavra relacionada a finanças\n` +
                       `• "relatório", "saldo", "receitas", etc.\n\n` +
                       `📊 *O que o bot faz:*\n` +
                       `• Gera relatório financeiro completo\n` +
                       `• Mostra receitas, despesas e saldo\n` +
                       `• Lista principais despesas do mês\n` +
                       `• Calcula fluxo de caixa atual\n\n` +
                       `⚡ *Resposta automática 24/7*\n` +
                       `🔄 Dados sempre atualizados\n\n` +
                       `❓ Dúvidas? Digite "oi" para começar!`;
        
        await msg.reply(helpMsg);
        console.log(`❓ Ajuda enviada para ${contact.pushname || contact.number}`);
    }

    async start() {
        try {
            console.log('🚀 Iniciando LoteSys WhatsApp Bot...');
            console.log('📡 Conectando ao WhatsApp Web...');
            await this.client.initialize();
        } catch (error) {
            console.error('❌ Erro ao inicializar bot:', error);
            process.exit(1);
        }
    }
}

// Inicializar bot
const bot = new LoteSysWhatsAppBot();

// Tratamento de sinais do sistema
process.on('SIGINT', async () => {
    console.log('\n🛑 Recebido sinal de interrupção. Desconectando bot...');
    await bot.client.destroy();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    console.log('\n🛑 Recebido sinal de término. Desconectando bot...');
    await bot.client.destroy();
    process.exit(0);
});

// Tratar erros não capturados
process.on('unhandledRejection', (reason, promise) => {
    console.error('❌ Erro não tratado:', reason);
});

process.on('uncaughtException', (error) => {
    console.error('❌ Exceção não capturada:', error);
    process.exit(1);
});

// Iniciar o bot
bot.start();