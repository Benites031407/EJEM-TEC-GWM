from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from main.models import AgendamentoMensal
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Cria agendamentos para o próximo mês com base nos agendamentos recorrentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mes',
            type=int,
            help='Mês específico para criar agendamentos (1-12)',
        )
        parser.add_argument(
            '--ano',
            type=int,
            help='Ano específico para criar agendamentos (ex: 2025)',
        )

    def handle(self, *args, **options):
        # Determina mês e ano alvo para criação
        agora = timezone.now()
        
        if options['mes'] and options['ano']:
            mes_alvo = options['mes']
            ano_alvo = options['ano']
            if not 1 <= mes_alvo <= 12:
                raise CommandError("Mês inválido. Deve ser um valor entre 1 e 12.")
        else:
            # Por padrão, trabalhamos com o próximo mês
            if agora.month == 12:
                mes_alvo = 1
                ano_alvo = agora.year + 1
            else:
                mes_alvo = agora.month + 1
                ano_alvo = agora.year
        
        # Busca agendamentos recorrentes para replicar
        agendamentos_recorrentes = AgendamentoMensal.objects.filter(recorrente=True)
        
        contador_criados = 0
        contador_existentes = 0
        
        for agendamento in agendamentos_recorrentes:
            # Verifica se já existe um agendamento para este formulário no mês alvo
            ja_existe = AgendamentoMensal.objects.filter(
                nome=agendamento.nome,
                mes=mes_alvo,
                ano=ano_alvo
            ).exists()
            
            if not ja_existe:
                # Cria um novo agendamento para o mês alvo com as mesmas configurações
                novo = AgendamentoMensal.objects.create(
                    nome=agendamento.nome,
                    mes=mes_alvo,
                    ano=ano_alvo,
                    dia_inicio=agendamento.dia_inicio,
                    dia_fim=agendamento.dia_fim,
                    dias_especificos=agendamento.dias_especificos,
                    recorrente=agendamento.recorrente
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Criado agendamento para {novo.nome} - {mes_alvo}/{ano_alvo}'
                ))
                contador_criados += 1
            else:
                contador_existentes += 1
        
        if contador_criados == 0 and contador_existentes == 0:
            self.stdout.write(self.style.WARNING('Nenhum agendamento recorrente encontrado.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Processo concluído. Criados: {contador_criados}, Já existentes: {contador_existentes}'
            )) 