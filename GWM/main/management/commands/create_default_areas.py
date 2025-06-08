from django.core.management.base import BaseCommand
from django.utils.text import slugify
from main.models import Area, CustomUser

class Command(BaseCommand):
    help = 'Cria áreas padrão para o sistema'

    def handle(self, *args, **options):
        # Define as áreas padrão baseadas nos AREA_CHOICES do modelo CustomUser
        area_choices = CustomUser.AREA_CHOICES
        
        for area_code, area_name in area_choices:
            if not area_code:  # Skip 'Nenhuma' option
                continue
                
            # Create the area if it doesn't exist
            area, created = Area.objects.get_or_create(
                slug=slugify(area_code),
                defaults={'nome': area_name}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Área criada: {area_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Área já existe: {area_name}'))
        
        # Count total areas
        total_areas = Area.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total de áreas no sistema: {total_areas}')) 