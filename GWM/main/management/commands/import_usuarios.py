import csv
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import CustomUser

class Command(BaseCommand):
    help = 'Importa usuários do arquivo CSV utilizando email como username e cge como senha'

    def handle(self, *args, **options):
        filepath = os.path.join('main', 'usuarios.csv')
        
        # Contadores para estatísticas
        created_count = 0
        updated_count = 0
        error_count = 0
        
        self.stdout.write(self.style.SUCCESS(f"Iniciando importação de usuários de: {filepath}"))
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                cge = row['cge']
                nome = row['nome']
                email = row['email']
                
                if not email or email == 'sem_email':
                    self.stdout.write(self.style.WARNING(f"Usuário {nome} não possui email. Pulando..."))
                    error_count += 1
                    continue
                
                try:
                    # Verifica se o usuário já existe
                    user = CustomUser.objects.filter(email=email).first()
                    
                    if user:
                        # Atualiza usuário existente
                        user.cge = cge
                        
                        # Divide o nome em primeiro nome e sobrenome
                        name_parts = nome.split()
                        if len(name_parts) > 0:
                            user.first_name = name_parts[0]
                            user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                        
                        # Define senha (não redefine se já estiver definida)
                        if not user.has_usable_password():
                            user.set_password(cge)
                        
                        user.save()
                        self.stdout.write(self.style.SUCCESS(f"Atualizado: {email}"))
                        updated_count += 1
                    else:
                        # Cria novo usuário
                        user = CustomUser(
                            username=email,
                            email=email,
                            cge=cge,
                        )
                        
                        # Divide o nome em primeiro nome e sobrenome
                        name_parts = nome.split()
                        if len(name_parts) > 0:
                            user.first_name = name_parts[0]
                            user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                        
                        # Define senha
                        user.set_password(cge)
                        
                        # Define como ativo com permissões padrão
                        user.is_active = True
                        user.cargo = 'assessor'  # Definindo como assessor por padrão
                        
                        user.save()
                        self.stdout.write(self.style.SUCCESS(f"Criado: {email}"))
                        created_count += 1
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erro ao processar {nome}: {str(e)}"))
                    error_count += 1
        
        self.stdout.write("\nImportação concluída!")
        self.stdout.write(self.style.SUCCESS(f"Usuários criados: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"Usuários atualizados: {updated_count}"))
        self.stdout.write(self.style.ERROR(f"Erros: {error_count}")) 