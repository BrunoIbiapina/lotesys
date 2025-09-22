"""
Comando para preparar estrutura de media e verificar configurações
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage


class Command(BaseCommand):
    help = "Prepara estrutura de media e verifica configurações"

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando configuração de media...")
        
        # Exibe configurações atuais
        self.stdout.write(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"MEDIA_URL: {settings.MEDIA_URL}")
        
        # Verifica se o diretório existe
        if os.path.exists(settings.MEDIA_ROOT):
            self.stdout.write(self.style.SUCCESS(f"✅ MEDIA_ROOT existe: {settings.MEDIA_ROOT}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ MEDIA_ROOT não existe: {settings.MEDIA_ROOT}"))
            
        # Cria estrutura de pastas necessárias
        folders_to_create = [
            "comprovantes",
            "comprovantes/despesas",
            "comprovantes/receitas", 
            "comprovantes/parcelas",
        ]
        
        for folder in folders_to_create:
            folder_path = os.path.join(settings.MEDIA_ROOT, folder)
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.stdout.write(f"📁 Pasta criada/verificada: {folder}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erro ao criar {folder}: {e}"))
        
        # Testa gravação
        try:
            test_file = os.path.join(settings.MEDIA_ROOT, "test_write.txt")
            with open(test_file, "w") as f:
                f.write("teste")
            os.remove(test_file)
            self.stdout.write(self.style.SUCCESS("✅ Permissão de escrita OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro de permissão de escrita: {e}"))
            
        self.stdout.write(self.style.SUCCESS("🎉 Verificação concluída!"))