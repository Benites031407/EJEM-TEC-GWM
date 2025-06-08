from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('main', '0040_alter_estatisticas_advisory_and_more'),  # Change this to your latest migration
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE main_estatisticas 
            SET qtd_rv = 0 
            WHERE qtd_rv IS NULL;
            
            UPDATE main_estatisticas 
            SET qtd_cambio = 0 
            WHERE qtd_cambio IS NULL;
            
            UPDATE main_estatisticas 
            SET qtd_seguros = 0 
            WHERE qtd_seguros IS NULL;
            
            UPDATE main_estatisticas 
            SET qtd_consorcio = 0 
            WHERE qtd_consorcio IS NULL;
            
            UPDATE main_estatisticas 
            SET qtd_corporate = 0 
            WHERE qtd_corporate IS NULL;
            
            UPDATE main_estatisticas 
            SET qtd_expansao = 0 
            WHERE qtd_expansao IS NULL;
            
            UPDATE main_estatisticas 
            SET qtd_banking = 0 
            WHERE qtd_banking IS NULL;
            
            UPDATE main_estatisticas 
            SET qtd_advisory = 0 
            WHERE qtd_advisory IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ] 