# 📁 Configuração de Upload de Arquivos

## 🔥 Problema Identificado
Os arquivos de upload (comprovantes) estão sendo perdidos a cada deploy no Render porque o sistema de arquivos é **efêmero**.

## ✅ Solução: Cloudinary

### 1. **Criar conta Cloudinary** (GRATUITO)
- Acesse: https://cloudinary.com/users/register/free
- Crie uma conta gratuita (25GB de armazenamento)
- Anote suas credenciais do Dashboard

### 2. **Configurar variáveis no Render**
No painel do Render, vá em **Environment** e adicione:

```bash
# Suas credenciais do Cloudinary Dashboard
CLOUDINARY_URL=cloudinary://sua_api_key:sua_api_secret@seu_cloud_name
CLOUDINARY_CLOUD_NAME=seu_cloud_name
CLOUDINARY_API_KEY=sua_api_key
CLOUDINARY_API_SECRET=sua_api_secret
```

### 3. **Deploy com nova configuração**
Após configurar as variáveis, faça um novo deploy. Os uploads agora serão:

✅ **Permanentes** - não são perdidos no deploy  
✅ **Rápidos** - CDN global  
✅ **Otimizados** - compressão automática  
✅ **Seguros** - backup na nuvem  

## 🏠 Desenvolvimento Local
Para desenvolvimento, os arquivos continuam sendo salvos na pasta `media/` local.

## 🔄 Migração de Arquivos Existentes
Se você já tem comprovantes salvos localmente, eles precisarão ser re-enviados após a configuração do Cloudinary.

## 📊 Monitoramento
- Dashboard Cloudinary: https://cloudinary.com/console
- Uso de storage, transformações, etc.

## 🆘 Troubleshooting
- Verifique se todas as variáveis estão configuradas no Render
- Teste localmente primeiro comentando as variáveis no .env
- Logs do Django mostrarão erros de upload se houver

---
*Configuração implementada em: 29/09/2025*