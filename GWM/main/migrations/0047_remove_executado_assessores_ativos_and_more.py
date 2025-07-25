# Generated by Django 5.1.7 on 2025-05-17 14:41

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0046_executado_assessores_ativos_executado_captacao_mesa_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='executado',
            name='assessores_ativos',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='captacao_mesa',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='cartoes_emitidos',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='cpfs_operados',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='interacoes',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='leads_sociais',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='ofertas_publicas',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='percentual_pl_credito',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='percentual_pl_liquidez',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='pl_liquidez',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='principalidade',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='qtd_consorcios',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='qtd_reunioes',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='qtd_seguros',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='seguidores',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='volume_credito',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='volume_financeiro',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='volume_ofertas',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='volume_operado',
        ),
        migrations.RemoveField(
            model_name='executado',
            name='volume_pa',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='assessores_ativos',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='captacao_mesa',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='cartoes_emitidos',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='cpfs_operados',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='interacoes',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='leads_sociais',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='ofertas_publicas',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='percentual_pl_credito',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='percentual_pl_liquidez',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='pl_liquidez',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='principalidade',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='qtd_consorcios',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='qtd_reunioes',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='qtd_seguros',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='seguidores',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='volume_credito',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='volume_financeiro',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='volume_ofertas',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='volume_operado',
        ),
        migrations.RemoveField(
            model_name='planejado',
            name='volume_pa',
        ),
        migrations.CreateModel(
            name='ObjetivoAnual',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(verbose_name='Ano')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=15, verbose_name='Objetivo Anual (PL)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('definido_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='objetivos_definidos', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='objetivos_anuais', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Objetivo Anual',
                'verbose_name_plural': 'Objetivos Anuais',
                'unique_together': {('user', 'year')},
            },
        ),
    ]
