from django.core.management.base import BaseCommand
from main.models import FinanceHistory
from decimal import Decimal
from datetime import datetime

class Command(BaseCommand):
    help = 'Adds mock finance data for the entire year'

    def handle(self, *args, **kwargs):
        current_year = datetime.now().year

        # Mock data for the entire year
        mock_data = [
            # Janeiro - Começo do ano
            {
                'month': 1,
                'receita_pj1': 1310000,
                'receita_pj2': 1120000,
                'receita_pj1_planejado': 	1250000,
                'receita_pj2_planejado': 1100000,
            },
            # Fevereiro
            {
                'month': 2,
                'receita_pj1': 1430000,
                'receita_pj2': 1250000,
                'receita_pj1_planejado': 1500000,
                'receita_pj2_planejado': 1300000,
            },
            # Março
            {
                'month': 3,
                'receita_pj1': 1750000,
                'receita_pj2': 1560000,
                'receita_pj1_planejado': 1700000,
                'receita_pj2_planejado': 1500000,
            },
            # Abril
            {
                'month': 4,
                'receita_pj1': 1380000,
                'receita_pj2': 1180000,
                'receita_pj1_planejado': 1400000,
                'receita_pj2_planejado': 1200000,
            },
            # Maio
            {
                'month': 5,
                'receita_pj1': 1620000,
                'receita_pj2': 1420000,
                'receita_pj1_planejado': 1600000,
                'receita_pj2_planejado': 1400000,
            },
            # Junho
            {
                'month': 6,
                'receita_pj1': 1790000,
                'receita_pj2': 1640000,
                'receita_pj1_planejado': 1800000,
                'receita_pj2_planejado': 1600000,
            },
            # Julho
            {
                'month': 7,
                'receita_pj1': 1390000,
                'receita_pj2': 1170000,
                'receita_pj1_planejado': 1300000,
                'receita_pj2_planejado': 1200000,
            },
            # Agosto
            {
                'month': 8,
                'receita_pj1': 1820000,
                'receita_pj2': 1500000,
                'receita_pj1_planejado': 1750000,
                'receita_pj2_planejado': 1450000,
            },
            # Setembro
            {
                'month': 9,
                'receita_pj1': 1510000,
                'receita_pj2': 1320000,
                'receita_pj1_planejado': 1600000,
                'receita_pj2_planejado': 1350000,
            },
            # Outubro
            {
                'month': 10,
                'receita_pj1': 1610000,
                'receita_pj2': 1530000,
                'receita_pj1_planejado': 1550000,
                'receita_pj2_planejado': 1500000,
            },
            # Novembro
            {
                'month': 11,
                'receita_pj1': 1740000,
                'receita_pj2': 1740000,
                'receita_pj1_planejado': 1700000,
                'receita_pj2_planejado': 1700000,
            },
            # Dezembro
            {
                'month': 12,
                'receita_pj1': 1880000,
                'receita_pj2': 1870000,
                'receita_pj1_planejado': 1900000,
                'receita_pj2_planejado': 1850000,
            },
        ]

        for data in mock_data:
            # Calculate total values
            data['receita_total'] = data['receita_pj1'] + data['receita_pj2']
            data['receita_total_planejado'] = data['receita_pj1_planejado'] + data['receita_pj2_planejado']
            
            # Convert to Decimal
            for key in ['receita_pj1', 'receita_pj2', 'receita_total', 
                       'receita_pj1_planejado', 'receita_pj2_planejado', 'receita_total_planejado']:
                data[key] = Decimal(str(data[key]))

            # Create or update the record
            FinanceHistory.objects.update_or_create(
                month=data['month'],
                year=current_year,
                defaults=data
            )

        self.stdout.write(self.style.SUCCESS('Successfully added mock finance data for all months'))