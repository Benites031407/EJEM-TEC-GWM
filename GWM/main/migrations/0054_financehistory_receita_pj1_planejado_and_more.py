# Generated by Django 5.1.7 on 2025-07-25 03:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0053_remove_financehistory_auc'),
    ]

    operations = [
        migrations.AddField(
            model_name='financehistory',
            name='receita_pj1_planejado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name='financehistory',
            name='receita_pj2_planejado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
        migrations.AddField(
            model_name='financehistory',
            name='receita_total_planejado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=20),
        ),
    ]
