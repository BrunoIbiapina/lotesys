#!/usr/bin/env node

const axios = require('axios');
require('dotenv').config();

console.log('🧪 Teste de Conectividade - LoteSys WhatsApp Bot');
console.log('==================================================');

async function testAPI() {
    try {
        console.log('🔗 Testando conexão com a API...');
        console.log(`📡 URL: ${process.env.API_URL || 'https://lotesys.onrender.com/financeiro/relatorio-mensal/'}`);
        
        const startTime = Date.now();
        
        const response = await axios.get(
            process.env.API_URL || 'https://lotesys.onrender.com/financeiro/relatorio-mensal/',
            {
                headers: {
                    'Authorization': process.env.API_TOKEN || 'Token SeuTokenSecreto123',
                    'User-Agent': 'LoteSys-WhatsApp-Bot-Test/1.0'
                },
                timeout: 15000
            }
        );
        
        const responseTime = Date.now() - startTime;
        
        console.log(`✅ API respondeu com sucesso! (${responseTime}ms)`);
        console.log(`📊 Status: ${response.status}`);
        console.log(`📏 Tamanho: ${JSON.stringify(response.data).length} caracteres`);
        
        if (response.data && response.data.mes_ano) {
            console.log(`📅 Dados do mês: ${response.data.mes_ano}`);
            console.log(`💰 Receitas: ${response.data.total_receitas || 'N/A'}`);
            console.log(`💸 Despesas: ${response.data.total_despesas_pagas || 'N/A'}`);
        }
        
        console.log('\n🎉 Teste concluído com SUCESSO!');
        console.log('🚀 O bot está pronto para funcionar. Execute: npm start');
        
    } catch (error) {
        console.log('\n❌ Erro no teste:');
        
        if (error.code === 'ECONNREFUSED') {
            console.log('🔌 Erro de conexão - Servidor não está respondendo');
        } else if (error.code === 'ETIMEDOUT') {
            console.log('⏰ Timeout - Servidor demorou para responder');
        } else if (error.response) {
            console.log(`📊 Status HTTP: ${error.response.status}`);
            console.log(`📝 Resposta: ${error.response.data}`);
        } else {
            console.log(`🐛 Erro: ${error.message}`);
        }
        
        console.log('\n🔧 Possíveis soluções:');
        console.log('1. Verifique se a URL da API está correta no .env');
        console.log('2. Confirme se o token de autenticação está válido');
        console.log('3. Teste a URL manualmente no navegador');
        console.log('4. Verifique sua conexão com a internet');
        
        process.exit(1);
    }
}

async function testDependencies() {
    console.log('\n🔍 Verificando dependências...');
    
    try {
        require('whatsapp-web.js');
        console.log('✅ whatsapp-web.js: OK');
        
        require('qrcode-terminal');
        console.log('✅ qrcode-terminal: OK');
        
        require('moment');
        console.log('✅ moment: OK');
        
        console.log('✅ Todas as dependências estão instaladas!');
        
    } catch (error) {
        console.log(`❌ Dependência faltando: ${error.message}`);
        console.log('🔧 Execute: npm install');
        process.exit(1);
    }
}

async function runTests() {
    console.log('🚀 Iniciando testes...\n');
    
    // Testar dependências
    await testDependencies();
    
    // Testar API
    await testAPI();
}

// Executar testes
runTests().catch(error => {
    console.error('\n💥 Erro inesperado:', error);
    process.exit(1);
});