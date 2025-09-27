#!/bin/bash

echo "🤖 LoteSys WhatsApp Bot - Instalação Automática"
echo "================================================"

# Verificar Node.js
echo "🔍 Verificando Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado!"
    echo "📥 Instale Node.js versão 16+ em: https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt "16" ]; then
    echo "⚠️  Node.js versão $NODE_VERSION encontrada. Recomendado: 16+"
    echo "📥 Atualize em: https://nodejs.org"
fi

echo "✅ Node.js $(node --version) encontrado"

# Verificar npm
echo "🔍 Verificando npm..."
if ! command -v npm &> /dev/null; then
    echo "❌ npm não encontrado!"
    exit 1
fi
echo "✅ npm $(npm --version) encontrado"

# Instalar dependências
echo "📦 Instalando dependências..."
if npm install; then
    echo "✅ Dependências instaladas com sucesso!"
else
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

# Configurar ambiente
echo "⚙️  Configurando ambiente..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 Arquivo .env criado a partir do exemplo"
    echo "⚠️  IMPORTANTE: Edite o arquivo .env com suas configurações!"
else
    echo "✅ Arquivo .env já existe"
fi

# Verificar Chrome/Chromium (para Puppeteer)
echo "🔍 Verificando Chrome/Chromium..."
if command -v google-chrome &> /dev/null || command -v chromium &> /dev/null || command -v chromium-browser &> /dev/null; then
    echo "✅ Chrome/Chromium encontrado"
else
    echo "⚠️  Chrome/Chromium não encontrado"
    echo "📥 O bot tentará baixar o Chromium automaticamente"
fi

echo ""
echo "🎉 INSTALAÇÃO CONCLUÍDA!"
echo "========================"
echo ""
echo "📋 Próximos passos:"
echo "1. 📝 Edite o arquivo .env com suas configurações"
echo "2. 🚀 Execute: npm start"
echo "3. 📱 Escaneie o QR Code com seu WhatsApp"
echo "4. ✅ Pronto! O bot estará funcionando"
echo ""
echo "💡 Comandos úteis:"
echo "   npm start     - Iniciar o bot"
echo "   npm run clean - Limpar sessão (para reconectar)"
echo "   npm run reset - Limpar e reiniciar"
echo ""
echo "📚 Leia o README.md para mais informações"