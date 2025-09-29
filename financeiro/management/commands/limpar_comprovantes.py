"""
Comando para limpar comprovantes perdidos em produção
"""
from django.core.management.base import BaseCommand
from vendas.models import Venda, Parcela
from financeiro.models import Despesa


class Command(BaseCommand):
    help = 'Limpar comprovantes com links quebrados do banco de dados'
    
    def handle(self, *args, **options):
        self.stdout.write('=== LIMPANDO COMPROVANTES PERDIDOS ===')
        
        # Limpar parcelas
        parcelas_perdidas = 0
        for parcela in Parcela.objects.exclude(comprovante=''):
            try:
                # Tentar acessar o arquivo
                exists = parcela.comprovante.storage.exists(parcela.comprovante.name)
                if not exists:
                    self.stdout.write(f'Limpando parcela #{parcela.id}: {parcela.comprovante.name}')
                    parcela.comprovante = ''
                    parcela.save()
                    parcelas_perdidas += 1
            except Exception:
                # Se der erro, limpar também
                self.stdout.write(f'Erro na parcela #{parcela.id}, limpando...')
                parcela.comprovante = ''
                parcela.save()
                parcelas_perdidas += 1
        
        # Limpar vendas
        vendas_perdidas = 0
        for venda in Venda.objects.exclude(comprovante=''):
            try:
                exists = venda.comprovante.storage.exists(venda.comprovante.name)
                if not exists:
                    self.stdout.write(f'Limpando venda #{venda.id}: {venda.comprovante.name}')
                    venda.comprovante = ''
                    venda.save()
                    vendas_perdidas += 1
            except Exception:
                self.stdout.write(f'Erro na venda #{venda.id}, limpando...')
                venda.comprovante = ''
                venda.save()
                vendas_perdidas += 1
        
        # Limpar despesas
        despesas_perdidas = 0
        try:
            for despesa in Despesa.objects.exclude(comprovante=''):
                try:
                    exists = despesa.comprovante.storage.exists(despesa.comprovante.name)
                    if not exists:
                        self.stdout.write(f'Limpando despesa #{despesa.id}: {despesa.comprovante.name}')
                        despesa.comprovante = ''
                        despesa.save()
                        despesas_perdidas += 1
                except Exception:
                    self.stdout.write(f'Erro na despesa #{despesa.id}, limpando...')
                    despesa.comprovante = ''
                    despesa.save()
                    despesas_perdidas += 1
        except Exception as e:
            self.stdout.write(f'Erro ao processar despesas: {e}')
        
        self.stdout.write('=== RESULTADO ===')
        self.stdout.write(f'✅ {parcelas_perdidas} parcelas limpas')
        self.stdout.write(f'✅ {vendas_perdidas} vendas limpas')
        self.stdout.write(f'✅ {despesas_perdidas} despesas limpas')
        self.stdout.write('🎯 Links quebrados removidos!')