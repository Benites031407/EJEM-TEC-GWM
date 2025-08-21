from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import (
    PlanejadoForm, ExecutadoForm, CaptacaoForm, EstatisticasForm,
    PlanejadoExpansaoForm, ExecutadoExpansaoForm,
    PlanejadoSegurosForm, ExecutadoSegurosForm,
    PlanejadoRendaVariavelForm, ExecutadoRendaVariavelForm,
    PlanejadoCambioForm, ExecutadoCambioForm,
    PlanejadoCorporateForm, ExecutadoCorporateForm,
    PlanejadoBankingForm, ExecutadoBankingForm,
    PlanejadoMarketingForm, ExecutadoMarketingForm,
    PlanejadoConsorcioForm, ExecutadoConsorcioForm,
    PlanejadoAdvisoryForm, ExecutadoAdvisoryForm,
    FinanceForm,
)
from django.contrib import messages
from .models import Planejado, Executado, Captacao, Estatisticas, Unidade, CustomUser, AlertaDuplicado, CodigoEdicao, Area, AgendamentoMensal, ObjetivoAnual, ObjetivoUnidade, FinanceHistory
from datetime import datetime, timedelta, date
from decimal import Decimal
# from main.dash_apps.components.app_top5leads import app
# from main.dash_apps.components.cliente_pizza import app
# from main.dash_apps.components.callback_pl_auc import app
# from main.dash_apps.components.app_seguro import app
# from main.dash_apps.components.app_expansao import app
# from main.dash_apps.components.app_renda_variavel import app
# from main.dash_apps.components.app_corporate import app
# from main.dash_apps.components.app_banking import app
# from main.dash_apps.components.app_consorcio import app
# from main.dash_apps.components.app_marketing import app
# from main.dash_apps.components.app_cambio import app
# from main.dash_apps.components.app_advisory import app
from django.views.decorators.http import require_POST
import re
from django.db.models import Sum, F, Func, Value, DecimalField, Q, Count, Avg, Max
from django.db.models.functions import TruncMonth, NullIf, Cast, Replace
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from .utils import get_unit_structure, get_team_hierarchy
from django.db import models
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
import plotly.graph_objects as go
import plotly.offline as opy
import unicodedata

@login_required
def login_redirect(request):
    user = request.user

    if user.is_master():
        return redirect('home_master')  # nome da URL para a home do master
    elif user.is_head():
        return redirect('home_head')    # nome da URL para a home do head
    elif user.is_assessor():
        return redirect('home')         # nome da URL para a home do assessor
    elif user.is_headunidade():
        return redirect('home_headunidade')  # nome da URL para a home do head unidade
    else:
        return redirect('admin:index')  # fallback


# Tradutor de meses
MONTHS_PT = {
    1: 'Janeiro',
    2: 'Fevereiro',
    3: 'Março',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro',
}

def get_current_period():
    now = datetime.now()
    return now.month, now.year

def get_previous_month():
    today = datetime.today()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    return last_day_last_month.month, last_day_last_month.year


def is_within_range(start_day, end_day):
    today = datetime.now().day
    return start_day <= today <= end_day


# Página Home
@user_passes_test(lambda u: u.is_assessor())
def home(request):
    month = datetime.now().month
    year = datetime.now().year
    user = request.user

    show_planejado = datetime.now().day <= 5
    show_executado = datetime.now().day >= 25

    has_planejado = Planejado.objects.filter(user=user, month=month, year=year).exists()
    has_executado = Executado.objects.filter(user=user, month=month, year=year).exists()
    has_estatisticas = Estatisticas.objects.filter(user=user, month=month, year=year).exists()
    captacao_qtd = Captacao.objects.filter(user=user, month=month, year=year).count()

    return render(request, 'main/home.html', {
        'show_planejado': show_planejado and not has_planejado,
        'show_executado': show_executado and not has_executado,
        'has_planejado': has_planejado,
        'has_executado': has_executado,
        'has_estatisticas': has_estatisticas,
        'captacao_qtd': captacao_qtd,
        'user': user,
    })

#HOMEPAGE HEAD
@user_passes_test(lambda u: u.is_head())
def home_head(request):
    user = request.user
    month = datetime.now().month
    year = datetime.now().year

    head_areas = user.areas_gerenciadas.all()
    if user.area_ref and not head_areas.filter(id=user.area_ref.id).exists():
        head_areas = list(head_areas)
        head_areas.append(user.area_ref)
    primary_area = None
    if head_areas:
        if isinstance(head_areas, list):
            primary_area = head_areas[0]
        else:
            primary_area = head_areas.first()
    if not head_areas:
        return render(request, 'main/home_head.html', {
            'no_area': True,
            'message': 'Você não possui áreas atribuídas. Entre em contato com o administrador.',
        })
    advisors = CustomUser.objects.none()
    for area in head_areas:
        advisors = advisors | CustomUser.objects.filter(area_ref=area, cargo='assessor')
    advisors = advisors.distinct()
    advisor_count = advisors.count()
    has_planejado = Planejado.objects.filter(user=user, month=month, year=year).exists()
    has_executado = Executado.objects.filter(user=user, month=month, year=year).exists()
    captacoes = Captacao.objects.filter(user__in=advisors, month=month, year=year)
    total_captacoes = captacoes.count()
    from django.db.models import Sum, F, Value, DecimalField
    from django.db.models.functions import Replace, Cast
    pl_stats = (
        captacoes
        .exclude(pl__isnull=True)
        .filter(pl__gt=0)
        .annotate(pl_text=Cast('pl', output_field=models.TextField()))
        .annotate(pl_temp=Replace(F('pl_text'), Value('R$'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value('.'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value(','), Value('.')))
        .annotate(
            pl_number=Cast('pl_temp', output_field=DecimalField(max_digits=20, decimal_places=2))
        )
        .aggregate(Sum('pl_number'))
    )
    total_pl = pl_stats['pl_number__sum'] or 0
    estatisticas = Estatisticas.objects.filter(user__in=advisors, month=month, year=year)
    estatisticas_count = estatisticas.count()
    indicators = {}
    for area in head_areas:
        area_name = area.nome.lower() if hasattr(area, 'nome') else ""
        if area_name == 'expansão':
            indicators['expansao'] = estatisticas.filter(expansao=True).count()
        elif area_name == 'seguro' or area_name == 'seguros':
            indicators['seguros'] = estatisticas.filter(seguros=True).count()
        elif area_name == 'renda variável':
            indicators['rv'] = estatisticas.filter(rv=True).count()
        elif area_name == 'cambio':
            indicators['cambio'] = estatisticas.filter(cambio=True).count()
        elif area_name == 'corporate':
            indicators['corporate'] = estatisticas.filter(corporate=True).count()
        elif area_name == 'banking':
            indicators['banking'] = estatisticas.filter(banking=True).count()
        
        elif area_name == 'consórcio':
            indicators['consorcio'] = estatisticas.filter(consorcio=True).count()
        elif area_name == 'advisory':
            indicators['advisory'] = estatisticas.filter(advisory=True).count()

    # Função para detectar área do registro Executado
    def detect_area(obj):
        if getattr(obj, 'qtd_consorcios', None) is not None or getattr(obj, 'volume_financeiro', None) is not None:
            return 'Consórcio'
        if getattr(obj, 'qtd_seguros', None) is not None or getattr(obj, 'volume_pa', None) is not None:
            return 'Seguros'
        if getattr(obj, 'entrevistas', None) is not None and getattr(obj, 'contratacoes', None) is not None:
            return 'Expansão'
        if getattr(obj, 'cpfs_operados', None) is not None or getattr(obj, 'volume_ofertas', None) is not None:
            return 'Renda Variável'
        if getattr(obj, 'volume_operado', None) is not None or getattr(obj, 'assessores_ativos', None) is not None:
            return 'Câmbio'
        if getattr(obj, 'volume_credito', None) is not None:
            return 'Corporate'
        if getattr(obj, 'principalidade', None) is not None or getattr(obj, 'cartoes_emitidos', None) is not None:
            return 'Banking'
        if getattr(obj, 'seguidores', None) is not None or getattr(obj, 'interacoes', None) is not None:
            return 'Marketing'
        if getattr(obj, 'pl_liquidez', None) is not None or getattr(obj, 'ofertas_publicas', None) is not None:
            return 'Advisory'
        return 'Outro'

    def normalize_area(nome):
        if not nome:
            return ""
        return unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII').lower()

    # Buscar todos os Executado e Planejado do mês/ano do usuário
    executados = Executado.objects.filter(user=user, month=month, year=year)
    planejados = Planejado.objects.filter(user=user, month=month, year=year)
    # Para cada área, buscar o registro Executado e Planejado correspondente
    for area in head_areas:
        if not hasattr(area, 'nome'):
            continue
        area_nome = normalize_area(area.nome)
        area_exec = None
        area_plan = None
        for exec_item in executados:
            if normalize_area(detect_area(exec_item)) == area_nome:
                area_exec = exec_item
                break
        for plan_item in planejados:
            if normalize_area(detect_area(plan_item)) == area_nome:
                area_plan = plan_item
                break
        # Inicializar métricas executadas
        setattr(area, 'entrevistas', 0)
        setattr(area, 'contratacoes', 0)
        setattr(area, 'nps', 0)
        setattr(area, 'volume_pa', 0)
        setattr(area, 'qtd_reunioes', 0)
        setattr(area, 'qtd_seguros', 0)
        setattr(area, 'receita', 0)
        setattr(area, 'cpfs_operados', 0)
        setattr(area, 'volume_ofertas', 0)
        setattr(area, 'volume_operado', 0)
        setattr(area, 'assessores_ativos', 0)
        setattr(area, 'volume_credito', 0)
        setattr(area, 'principalidade', 0)
        setattr(area, 'cartoes_emitidos', 0)
        setattr(area, 'seguidores', 0)
        setattr(area, 'interacoes', 0)
        setattr(area, 'leads_sociais', 0)
        setattr(area, 'captacao_mesa', 0)
        setattr(area, 'qtd_consorcios', 0)
        setattr(area, 'volume_financeiro', 0)
        setattr(area, 'pl_liquidez', 0)
        setattr(area, 'percentual_pl_liquidez', 0)
        setattr(area, 'volume_credito', 0)
        setattr(area, 'percentual_pl_credito', 0)
        setattr(area, 'ofertas_publicas', 0)
        # Inicializar métricas de meta (planejado)
        setattr(area, 'entrevistas_meta', 0)
        setattr(area, 'contratacoes_meta', 0)
        setattr(area, 'nps_meta', 0)
        setattr(area, 'volume_pa_meta', 0)
        setattr(area, 'qtd_reunioes_meta', 0)
        setattr(area, 'qtd_seguros_meta', 0)
        setattr(area, 'receita_meta', 0)
        setattr(area, 'cpfs_operados_meta', 0)
        setattr(area, 'volume_ofertas_meta', 0)
        setattr(area, 'volume_operado_meta', 0)
        setattr(area, 'assessores_ativos_meta', 0)
        setattr(area, 'volume_credito_meta', 0)
        setattr(area, 'principalidade_meta', 0)
        setattr(area, 'cartoes_emitidos_meta', 0)
        setattr(area, 'seguidores_meta', 0)
        setattr(area, 'interacoes_meta', 0)
        setattr(area, 'leads_sociais_meta', 0)
        setattr(area, 'captacao_mesa_meta', 0)
        setattr(area, 'qtd_consorcios_meta', 0)
        setattr(area, 'volume_financeiro_meta', 0)
        setattr(area, 'pl_liquidez_meta', 0)
        setattr(area, 'percentual_pl_liquidez_meta', 0)
        setattr(area, 'volume_credito_meta', 0)
        setattr(area, 'percentual_pl_credito_meta', 0)
        setattr(area, 'ofertas_publicas_meta', 0)
        # Preencher métricas executadas
        if area_exec:
            if area_nome == normalize_area('Expansão'):
                area.entrevistas = area_exec.entrevistas or 0
                area.contratacoes = area_exec.contratacoes or 0
                area.nps = area_exec.nps or 0
            elif area_nome == normalize_area('Seguros'):
                area.qtd_reunioes = area_exec.qtd_reunioes or 0
                area.qtd_seguros = area_exec.qtd_seguros or 0
                area.volume_pa = area_exec.volume_pa or 0
            elif area_nome == normalize_area('Consórcio'):
                area.qtd_reunioes = area_exec.qtd_reunioes or 0
                area.qtd_consorcios = area_exec.qtd_consorcios or 0
                area.volume_financeiro = area_exec.volume_financeiro or 0
                area.percentual_atingido = area_exec.percentual_atingido or 0
                area.pace = area_exec.pace or 0
            elif area_nome == normalize_area('Renda Variável'):
                area.receita = area_exec.receita or 0
                area.cpfs_operados = area_exec.cpfs_operados or 0
                area.volume_ofertas = area_exec.volume_ofertas or 0
            elif area_nome == normalize_area('Câmbio'):
                area.receita = area_exec.receita or 0
                area.volume_operado = area_exec.volume_operado or 0
                area.assessores_ativos = area_exec.assessores_ativos or 0
            elif area_nome == normalize_area('Corporate'):
                area.volume_credito = area_exec.volume_credito or 0
                area.qtd_reunioes = area_exec.qtd_reunioes or 0
            elif area_nome == normalize_area('Banking'):
                area.principalidade = area_exec.principalidade or 0
                area.cartoes_emitidos = area_exec.cartoes_emitidos or 0
            elif area_nome == normalize_area('Marketing'):
                area.seguidores = area_exec.seguidores or 0
                area.interacoes = area_exec.interacoes or 0
                area.leads_sociais = area_exec.leads_sociais or 0
                area.percentual_pl_credito = area_exec.percentual_pl_credito or 0
                area.captacao_mesa = area_exec.captacao_mesa or 0
            elif area_nome == normalize_area('Advisory'):
                area.pl_liquidez = area_exec.pl_liquidez or 0
                area.percentual_pl_liquidez = area_exec.percentual_pl_liquidez or 0
                area.volume_credito = area_exec.volume_credito or 0
                area.percentual_pl_credito = area_exec.percentual_pl_credito or 0
                area.ofertas_publicas = area_exec.ofertas_publicas or 0
        # Preencher métricas de meta (planejado)
        if area_plan:
            if area_nome == normalize_area('Expansão'):
                area.entrevistas_meta = area_plan.entrevistas or 0
                area.contratacoes_meta = area_plan.contratacoes or 0
                area.nps_meta = area_plan.nps or 0
            elif area_nome == normalize_area('Seguros'):
                area.qtd_reunioes_meta = area_plan.qtd_reunioes or 0
                area.qtd_seguros_meta = area_plan.qtd_seguros or 0
                area.volume_pa_meta = area_plan.volume_pa or 0
            elif area_nome == normalize_area('Consórcio'):
                area.qtd_reunioes_meta = area_plan.qtd_reunioes or 0
                area.qtd_consorcios_meta = area_plan.qtd_consorcios or 0
                area.volume_financeiro_meta = area_plan.volume_financeiro or 0
            elif area_nome == normalize_area('Renda Variável'):
                area.receita_meta = area_plan.receita or 0
                area.cpfs_operados_meta = area_plan.cpfs_operados or 0
                area.volume_ofertas_meta = area_plan.volume_ofertas or 0
            elif area_nome == normalize_area('Câmbio'):
                area.receita_meta = area_plan.receita or 0
                area.volume_operado_meta = area_plan.volume_operado or 0
                area.assessores_ativos_meta = area_plan.assessores_ativos or 0
            elif area_nome == normalize_area('Corporate'):
                area.volume_credito_meta = area_plan.volume_credito or 0
                area.qtd_reunioes_meta = area_plan.qtd_reunioes or 0
            elif area_nome == normalize_area('Banking'):
                area.principalidade_meta = area_plan.principalidade or 0
                area.cartoes_emitidos_meta = area_plan.cartoes_emitidos or 0
            elif area_nome == normalize_area('Marketing'):
                area.seguidores_meta = area_plan.seguidores or 0
                area.interacoes_meta = area_plan.interacoes or 0
                area.leads_sociais_meta = area_plan.leads_sociais or 0
                area.percentual_pl_credito_meta = area_plan.percentual_pl_credito or 0
                area.captacao_mesa_meta = area_plan.captacao_mesa or 0
            elif area_nome == normalize_area('Advisory'):
                area.pl_liquidez_meta = area_plan.pl_liquidez or 0
                area.percentual_pl_liquidez_meta = area_plan.percentual_pl_liquidez or 0
                area.volume_credito_meta = area_plan.volume_credito or 0
                area.percentual_pl_credito_meta = area_plan.percentual_pl_credito or 0
                area.ofertas_publicas_meta = area_plan.ofertas_publicas or 0

    context = {
        'has_planejado': has_planejado,
        'has_executado': has_executado,
        'advisor_count': advisor_count,
        'total_captacoes': total_captacoes,
        'total_pl': total_pl,
        'estatisticas_count': estatisticas_count,
        'indicators': indicators,
        'areas': head_areas,
        'advisors': advisors,
        'primary_area': primary_area,
    }
    return render(request, 'main/home_head.html', context)

# Dashboard Head
@user_passes_test(lambda u: u.is_head())
def dashboard(request):
    user = request.user
    
    # Get the areas the head is responsible for, using same logic as home_head
    # First check areas_gerenciadas (where user is set as head of area)
    head_areas = user.areas_gerenciadas.all()
    
    # Also check if the user has an area_ref assigned in admin
    if user.area_ref and not head_areas.filter(id=user.area_ref.id).exists():
        # If user's area_ref exists and is not already in head_areas, add it
        head_areas = list(head_areas)
        head_areas.append(user.area_ref)
    
    # If we still have no areas after both checks
    if not head_areas:
        # If no areas are assigned, redirect to home
        return redirect('home_head')
    
    # Current date
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Calculate monthly percentage (for pace)
    months_elapsed = current_month
    months_total = 12
    time_elapsed_percentage = (months_elapsed / months_total) * 100
    
    # Calculate evolution data for the last 6 months
    evolution_dates = []
    evolution_values = []
    
    # Get metrics for each area
    area_metrics = {}
    for area in head_areas:
        if not hasattr(area, 'nome'):
            continue
            
        # Initialize metrics for this area
        area_name = area.nome
        area_metrics[area_name] = {
            'entrevistas': 0,
            'contratacoes': 0,
            'nps': 0,
            'volume_pa': 0,
            'receita': 0,
            'cpfs_operados': 0,
            'volume_ofertas': 0,
            'volume_operado': 0,
            'assessores_ativos': 0,
            'volume_credito': 0,
            'qtd_reunioes': 0,
            'principalidade': 0,
            'cartoes_emitidos': 0,
            'seguidores': 0,
            'interacoes': 0,
            'leads_sociais': 0,
            'captacao_mesa': 0,
            'qtd_consorcios': 0,
            'volume_financeiro': 0,
            'pl_liquidez': 0,
            'percentual_pl_liquidez': 0,
            'percentual_pl_credito': 0,
            'ofertas_publicas': 0,
            'meta': 100,  # Default meta value
            'percentual_atingido': 0,
            'pace': 0
        }
        
        # Here you would fetch the actual metrics from your database
        # For example, from Planejado, Executado, or other models
        # This is a placeholder - replace with actual data fetching
        try:
            # Example: Get the most recent Executado data for this area
            executado = Executado.objects.filter(
                user=user, 
                year=current_year
            ).order_by('-month').first()
            
            if executado:
                if area_name == 'Expansão':
                    area_metrics[area_name]['entrevistas'] = executado.entrevistas or 0
                    area_metrics[area_name]['contratacoes'] = executado.contratacoes or 0
                    area_metrics[area_name]['nps'] = executado.nps or 0
                # Add similar mappings for other area types
        except Exception:
            # Just continue if there's an error fetching metrics
            pass
    
    for i in range(5, -1, -1):
        date = current_date - timedelta(days=30*i)
        evolution_dates.append(date.strftime('%b/%Y'))
        
        # Calculate total value for this month based on area types
        month_total = 0
        for area in head_areas:
            if not hasattr(area, 'nome'):
                continue
                
            area_name = area.nome
            area_metric = 0
            
            if area_name in area_metrics:
                if area_name == 'Expansão':
                    area_metric = area_metrics[area_name]['entrevistas']
                elif area_name == 'Seguro':
                    area_metric = area_metrics[area_name]['volume_pa']
                elif area_name == 'Renda Variável':
                    area_metric = area_metrics[area_name]['receita']
                elif area_name == 'Cambio':
                    area_metric = area_metrics[area_name]['volume_operado']
                elif area_name == 'Corporate':
                    area_metric = area_metrics[area_name]['volume_credito']
                elif area_name == 'Banking':
                    area_metric = area_metrics[area_name]['principalidade']
                elif area_name == 'Marketing':
                    area_metric = area_metrics[area_name]['seguidores']
                elif area_name == 'Consórcio':
                    area_metric = area_metrics[area_name]['volume_financeiro']
                elif area_name == 'Advisory':
                    area_metric = area_metrics[area_name]['pl_liquidez']
            
            month_total += area_metric
        
        evolution_values.append(month_total)
    
    # Calculate distribution data
    distribution_labels = []
    distribution_values = []
    
    for area in head_areas:
        if not hasattr(area, 'nome'):
            continue
            
        area_name = area.nome
        distribution_labels.append(area_name)
        
        area_metric = 0
        if area_name in area_metrics:
            if area_name == 'Expansão':
                area_metric = area_metrics[area_name]['entrevistas']
            elif area_name == 'Seguro':
                area_metric = area_metrics[area_name]['volume_pa']
            elif area_name == 'Renda Variável':
                area_metric = area_metrics[area_name]['receita']
            elif area_name == 'Cambio':
                area_metric = area_metrics[area_name]['volume_operado']
            elif area_name == 'Corporate':
                area_metric = area_metrics[area_name]['volume_credito']
            elif area_name == 'Banking':
                area_metric = area_metrics[area_name]['principalidade']
            elif area_name == 'Marketing':
                area_metric = area_metrics[area_name]['seguidores']
            elif area_name == 'Consórcio':
                area_metric = area_metrics[area_name]['volume_financeiro']
            elif area_name == 'Advisory':
                area_metric = area_metrics[area_name]['pl_liquidez']
        
        distribution_values.append(area_metric)
    
    # Calculate performance metrics for each area
    for area in head_areas:
        if not hasattr(area, 'nome'):
            continue
            
        area_name = area.nome
        if area_name not in area_metrics:
            continue
            
        metrics = area_metrics[area_name]
        
        # Calculate percentual atingido based on area type
        if area_name == 'Expansão':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['entrevistas'] or 0) / metrics['meta'] * 100), 100)
        elif area_name == 'Seguro':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['volume_pa'] or 0) / metrics['meta'] * 100), 100)
        elif area_name == 'Renda Variável':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['receita'] or 0) / metrics['meta'] * 100), 100)
        elif area_name == 'Cambio':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['volume_operado'] or 0) / metrics['meta'] * 100), 100)
        elif area_name == 'Corporate':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['volume_credito'] or 0) / metrics['meta'] * 100), 100)
        elif area_name == 'Banking':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['principalidade'] or 0) / metrics['meta'] * 100), 100)
        elif area_name == 'Marketing':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['seguidores'] or 0) / metrics['meta'] * 100), 100)
        elif area_name == 'Consórcio':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['volume_financeiro'] or 0) / metrics['meta'] * 100), 100)
        elif area_name == 'Advisory':
            if metrics['meta'] > 0:
                metrics['percentual_atingido'] = min(int((metrics['pl_liquidez'] or 0) / metrics['meta'] * 100), 100)
        
        # Calculate pace
        if time_elapsed_percentage > 0:
            metrics['pace'] = int((metrics['percentual_atingido'] / time_elapsed_percentage * 100))
        
        # Add the metrics to the area object for template access
        for key, value in metrics.items():
            setattr(area, key, value)
    
    context = {
        'areas': head_areas,
        'evolution_dates': json.dumps(evolution_dates),
        'evolution_values': json.dumps(evolution_values),
        'distribution_labels': json.dumps(distribution_labels),
        'distribution_values': json.dumps(distribution_values),
    }
    
    return render(request, 'main/dashboard.html', context)


def get_area_form_classes(area_nome):
    """Return the correct Planejado/Executado form classes for a given area name."""
    area_map = {
        'Expansão': (PlanejadoExpansaoForm, ExecutadoExpansaoForm),
        'Seguros': (PlanejadoSegurosForm, ExecutadoSegurosForm),
        'Renda Variável': (PlanejadoRendaVariavelForm, ExecutadoRendaVariavelForm),
        'Câmbio': (PlanejadoCambioForm, ExecutadoCambioForm),
        'Corporate': (PlanejadoCorporateForm, ExecutadoCorporateForm),
        'Banking': (PlanejadoBankingForm, ExecutadoBankingForm),
        'Marketing': (PlanejadoMarketingForm, ExecutadoMarketingForm),
        'Consórcio': (PlanejadoConsorcioForm, ExecutadoConsorcioForm),
        'Advisory': (PlanejadoAdvisoryForm, ExecutadoAdvisoryForm),
    }
    return area_map.get(area_nome, (PlanejadoForm, ExecutadoForm))

# Formulário de ações planejadas
@user_passes_test(lambda u: u.is_head())
def planejado_view(request):
    month, year = get_current_period()
    month_name = MONTHS_PT[month]
    
    # Novo: pegar área da querystring se existir
    area_nome = request.GET.get('area')
    user = request.user
    head_areas = user.areas_gerenciadas.all()
    if user.area_ref and not head_areas.filter(id=user.area_ref.id).exists():
        head_areas = list(head_areas)
        head_areas.append(user.area_ref)
    if not area_nome:
        primary_area = head_areas[0] if head_areas else None
        area_nome = primary_area.nome if primary_area else None
    # Verifica se já existe um registro para este mês/ano e área
    instance = Planejado.objects.filter(user=request.user, month=month, year=year).first()
    is_edit = instance is not None
    can_edit = is_formulario_aberto('Planejado')
    PlanejadoAreaForm, _ = get_area_form_classes(area_nome)
    if request.method == 'POST':
        if not can_edit and not request.session.get('edit_code_valid'):
            messages.error(request, "O período de edição está fechado.")
            return redirect('home_head')
        form = PlanejadoAreaForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.month = month
            obj.year = year
            obj.save()
            request.session.pop('edit_code_valid', None)
            messages.success(request, "Formulário enviado com sucesso!")
            return redirect('historico_head')
    else:
        form = PlanejadoAreaForm(instance=instance)
    if not can_edit and not request.session.get('edit_code_valid'):
        for field in form.fields.values():
            field.widget.attrs['readonly'] = True
            field.widget.attrs['disabled'] = True
    return render(request, 'main/planejado.html', {
        'form': form,
        'can_edit': can_edit,
        'month': month_name,
        'year': year,
        'area': area_nome,
        'is_edit': is_edit,
    })


# Formulário de ações executadas
@user_passes_test(lambda u: u.is_head())
def executado_view(request):
    month, year = get_current_period()
    month_name = MONTHS_PT[month]
    # Novo: pegar área da querystring se existir
    area_nome = request.GET.get('area')
    user = request.user
    head_areas = user.areas_gerenciadas.all()
    if user.area_ref and not head_areas.filter(id=user.area_ref.id).exists():
        head_areas = list(head_areas)
        head_areas.append(user.area_ref)
    if not area_nome:
        primary_area = head_areas[0] if head_areas else None
        area_nome = primary_area.nome if primary_area else None
    instance = Executado.objects.filter(user=request.user, month=month, year=year).first()
    is_edit = instance is not None
    can_edit = is_formulario_aberto('Executado')
    _, ExecutadoAreaForm = get_area_form_classes(area_nome)
    if request.method == 'POST':
        if not can_edit and not request.session.get('edit_code_valid'):
            messages.error(request, "O período de edição está fechado.")
            return redirect('home_head')
        form = ExecutadoAreaForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.month = month
            obj.year = year
            obj.save()
            request.session.pop('edit_code_valid', None)
            messages.success(request, "Formulário enviado com sucesso!")
            return redirect('historico_head')
    else:
        form = ExecutadoAreaForm(instance=instance)
    if not can_edit and not request.session.get('edit_code_valid'):
        for field in form.fields.values():
            field.widget.attrs['readonly'] = True
            field.widget.attrs['disabled'] = True
    return render(request, 'main/executado.html', {
        'form': form,
        'can_edit': can_edit,
        'month': month_name,
        'year': year,
        'area': area_nome,
        'is_edit': is_edit,
    })


# Formulário de captação de clientes
@user_passes_test(lambda u: u.is_assessor())
def captacao_view(request):
    now = datetime.now()
    month, year = now.month, now.year
    month_name = MONTHS_PT[month]

    if request.method == 'POST':
        form = CaptacaoForm(request.POST)
        if form.is_valid():
            new = form.save(commit=False)
            new.user = request.user
            new.month = month
            new.year = year
            new.save()

            # Verificar duplicidade
            duplicados = Captacao.objects.filter(
                Q(nome=new.nome)
            ).exclude(id=new.id)

            if duplicados.exists():
                AlertaDuplicado.objects.create(
                    assessor=request.user,
                    nome=new.nome,
                )

            messages.success(request, "Cliente cadastrado com sucesso!")
            return redirect('historico')
        else:
            messages.error(request, "Erro ao cadastrar cliente. Verifique os campos obrigatórios.")
    else:
        # Always provide a fresh form when visiting the page
        form = CaptacaoForm()

    entries = Captacao.objects.filter(user=request.user, month=month, year=year).order_by('-created_at')
    
    # Format currency fields for display in the template
    for entry in entries:
        entry.pl_formatted = format_br_currency(entry.pl)
        entry.planejado_migracao_formatted = format_br_currency(entry.planejado_migracao)

    return render(request, 'main/captacao.html', {
        'form': form,
        'entries': entries,
        'month': month_name,
        'year': year,
    })
    
def is_formulario_aberto(nome_formulario):
    today = datetime.now()
    try:
        periodo = AgendamentoMensal.objects.get(
            nome=nome_formulario,
            mes=today.month,
            ano=today.year
        )
        # Verifica se tem dias específicos configurados
        if periodo.dias_especificos:
            try:
                dias = [int(dia.strip()) for dia in periodo.dias_especificos.split(',') if dia.strip().isdigit()]
                return today.day in dias
            except (ValueError, TypeError):
                pass
        # Se não tem dias específicos ou se houve erro, usa o range padrão
        return periodo.dia_inicio <= today.day <= periodo.dia_fim
    except AgendamentoMensal.DoesNotExist:
        return False
    

#Formulário de estatísticas individuais
@user_passes_test(lambda u: u.is_assessor())
def estatisticas_view(request):
    now = datetime.now()
    month = now.month
    year = now.year
    month_name = MONTHS_PT[month]

    # Try to get existing entry
    try:
        instance = Estatisticas.objects.get(user=request.user, month=month, year=year)
        is_edit = True
    except Estatisticas.DoesNotExist:
        instance = None
        is_edit = False

    if request.method == 'POST':
        form = EstatisticasForm(request.POST, instance=instance)
        
        # Process "motivo_nao" field if provided and not using efetivou_operacao
        if 'motivo_nao' in request.POST and request.POST.get('motivo_nao'):
            if request.POST.get('efetivou_operacao') == 'False':
                # Add the motivo_nao content to the form data for the motivo field
                form.data = form.data.copy()
                form.data['motivo'] = request.POST.get('motivo_nao')
        
        # Check if the form is valid
        if form.is_valid():
            estatistica = form.save(commit=False)
            estatistica.user = request.user
            estatistica.month = month
            estatistica.year = year
            
            # If the user said they didn't make operations, set all areas to False
            if estatistica.efetivou_operacao is False:
                estatistica.rv = False
                estatistica.cambio = False
                estatistica.seguros = False
                estatistica.consorcio = False
                estatistica.corporate = False
                estatistica.expansao = False
                estatistica.banking = False
                estatistica.advisory = False
                
            # Ensure all quantity fields have default values (not NULL)
            qty_fields = [
                'qtd_rv', 'qtd_cambio', 'qtd_seguros', 'qtd_consorcio', 
                'qtd_corporate', 'qtd_expansao', 'qtd_banking', 'qtd_advisory'
            ]
            
            for field in qty_fields:
                if getattr(estatistica, field) is None:
                    setattr(estatistica, field, 0)
                
            # Save the entry
            estatistica.save()
            
            # Add success message
            action_msg = "atualizada" if is_edit else "enviada"
            messages.success(request, f"Estatística {action_msg} com sucesso!")
            
            # Redirect to the historico page
            return redirect('historico')
        else:
            print("Form is invalid with errors:", form.errors)
    else:
        # Always give a fresh form when GET request
        form = EstatisticasForm(instance=instance)

    return render(request, 'main/estatisticas.html', {
        'form': form,
        'month': month_name,
        'year': year,
        'is_edit': is_edit
    })


#Dashboard Assessor
@user_passes_test(lambda u: u.is_assessor())
def dashboard_assessor(request):
    user = request.user
    current_date = datetime.now()
    current_year = current_date.year

    captacoes = Captacao.objects.filter(user=user)
    estatisticas = Estatisticas.objects.filter(user=user)
    planejado = Planejado.objects.filter(user=user)

     # For PL calculations - convert string to decimal before summing
    captacoes_pl = (
        captacoes
        .exclude(pl__isnull=True)
        .filter(pl__gt=0)  # Only include records with pl > 0 instead of excluding empty strings
        .annotate(pl_text=Cast('pl', output_field=models.TextField()))  # First cast to text
        .annotate(pl_temp=Replace(F('pl_text'), Value('R$'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value('.'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value(','), Value('.')))
        .annotate(
            pl_number=Cast('pl_temp', output_field=DecimalField(max_digits=20, decimal_places=2))
        )
    )
    
    # Calculate total PL properly - this is the sum of all client PL values
    # Divide by 100 to correct the decimal place issue
    pl_atual = float(captacoes_pl.aggregate(Sum('pl_number'))['pl_number__sum'] or 0) / 100
    
    # Calculate PL trend (month over month)
    current_month = current_date.month
    
    # Get last month's PL
    last_month = current_date.replace(day=1) - timedelta(days=1)
    last_month_pl = float(captacoes_pl.filter(
        created_at__year=last_month.year,
        created_at__month=last_month.month
    ).aggregate(Sum('pl_number'))['pl_number__sum'] or 0) / 100  # Also divide by 100
    
    # Calculate trend percentage
    pl_trend = ((pl_atual - last_month_pl) / last_month_pl * 100) if last_month_pl > 0 else 0
    
    roa = user.cge or 0  # Campo que define o ROA
    clientes_ativos = captacoes.count()
    
    # Get the annual objective from ObjetivoAnual model
    try:
        objetivo_anual = ObjetivoAnual.objects.get(user=user, year=current_year)
        objetivo_ano = float(objetivo_anual.valor)
    except ObjetivoAnual.DoesNotExist:
        # If no specific objective is set, use the sum from planejado as fallback
        objetivo_ano = float(planejado.aggregate(total=Sum('auc'))['total'] or 0)
    
    # Calculate performance metrics
    months_elapsed = current_month
    time_elapsed_percentage = (months_elapsed / 12) * 100
    
    # Calculate percentage of goal achieved
    percentual_atingido = (pl_atual / objetivo_ano * 100) if objetivo_ano > 0 else 0
    
    # Calculate pace (percentage achieved relative to time elapsed)
    pace = (percentual_atingido / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
    
    ticket_medio = (pl_atual / clientes_ativos) if clientes_ativos else 0

    # Calculate client counts by status
    clientes_frios = captacoes.filter(status='Frio').count()
    clientes_mornos = captacoes.filter(status='Morno').count()
    clientes_quentes = captacoes.filter(status='Quente').count()

    # Calculate horizon months (default to 12)
    horizonte_meses = 12
    
    # Calculate projected PL (current PL + planned migration)
    pl_projetado = pl_atual + float(planejado.aggregate(total=Sum('auc'))['total'] or 0)

    # ===== Gráficos =====

    # Evolução do PL
    pl_evolucao = (
        captacoes_pl
        .annotate(mes=TruncMonth('created_at'))
        .values('mes')
        .annotate(total_pl=Sum('pl_number'))
        .order_by('mes')
    )

    pl_mes = [d['mes'].strftime('%b/%Y') for d in pl_evolucao if d['mes']]
    pl_total = [float(d['total_pl'] or 0) / 100 for d in pl_evolucao]  # Divide by 100

    pl_evolucao_chart = go.Figure()
    pl_evolucao_chart.add_trace(go.Scatter(x=pl_mes, y=pl_total, mode='lines+markers', name='PL'))
    pl_evolucao_chart.update_layout(title='Evolução do PL', xaxis_title='Mês', yaxis_title='PL (Mi)')
    pl_evolucao_chart_html = opy.plot(pl_evolucao_chart, auto_open=False, output_type='div')

    # Comparativo Planejado vs Migrado - also needs conversion
    # Convert planejado_migracao field similar to how pl is converted
    captacoes_planejado = (
        captacoes
        .exclude(planejado_migracao__isnull=True)
        .filter(planejado_migracao__gt=0)
        .annotate(planejado_text=Cast('planejado_migracao', output_field=models.TextField()))
        .annotate(planejado_temp=Replace(F('planejado_text'), Value('R$'), Value('')))
        .annotate(planejado_temp=Replace(F('planejado_temp'), Value('.'), Value('')))
        .annotate(planejado_temp=Replace(F('planejado_temp'), Value(','), Value('.')))
        .annotate(
            planejado_number=Cast('planejado_temp', output_field=DecimalField(max_digits=20, decimal_places=2))
        )
    )
    
    # Get monthly data for both planejado and migrado
    planejado_por_mes = (
        captacoes_planejado
        .annotate(mes=TruncMonth('created_at'))
        .values('mes')
        .annotate(planejado=Sum('planejado_number'))
        .order_by('mes')
    )
    
    migrado_por_mes = (
        captacoes_pl
        .annotate(mes=TruncMonth('created_at'))
        .values('mes')
        .annotate(migrado=Sum('pl_number'))
        .order_by('mes')
    )

    # Create dictionaries for easy lookup
    planejado_dict = {d['mes']: float(d['planejado'] or 0) / 100 for d in planejado_por_mes}  # Divide by 100
    migrado_dict = {d['mes']: float(d['migrado'] or 0) / 100 for d in migrado_por_mes}  # Divide by 100
    
    # Get all unique months
    all_months = sorted(set(list(planejado_dict.keys()) + list(migrado_dict.keys())))
    
    # Create data for chart
    meses_comparativo = [d.strftime('%b/%Y') for d in all_months]
    planejado_valores = [planejado_dict.get(mes, 0) for mes in all_months]
    migrado_valores = [migrado_dict.get(mes, 0) for mes in all_months]

    comparativo_chart = go.Figure()
    comparativo_chart.add_trace(go.Bar(x=meses_comparativo, y=planejado_valores, name='Planejado'))
    comparativo_chart.add_trace(go.Bar(x=meses_comparativo, y=migrado_valores, name='Migrado'))
    comparativo_chart.update_layout(barmode='group', title='Comparativo Planejado x Migrado', xaxis_title='Mês', yaxis_title='Valor (Mi)')
    comparativo_chart_html = opy.plot(comparativo_chart, auto_open=False, output_type='div')

    # Evolução dos Clientes
    clientes_evolucao = (
        captacoes
        .annotate(mes=TruncMonth('created_at'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    clientes_mes = [d['mes'].strftime('%b/%Y') for d in clientes_evolucao if d['mes']]
    clientes_total = [d['total'] for d in clientes_evolucao]

    clientes_evolucao_chart = go.Figure()
    clientes_evolucao_chart.add_trace(go.Scatter(x=clientes_mes, y=clientes_total, mode='lines+markers', name='Clientes'))
    clientes_evolucao_chart.update_layout(title='Evolução dos Clientes', xaxis_title='Mês', yaxis_title='Número de Clientes')
    clientes_evolucao_chart_html = opy.plot(clientes_evolucao_chart, auto_open=False, output_type='div')
 
    # Calculate total planejado and migrado for display in footer
    total_planejado = float(captacoes_planejado.aggregate(Sum('planejado_number'))['planejado_number__sum'] or 0) / 100  # Divide by 100
    total_migrado = pl_atual

    # Contexto
    context = {
        'pl_atual': pl_atual,
        'roa': roa,
        'clientes_ativos': clientes_ativos,
        'clientes_frios': clientes_frios,
        'clientes_mornos': clientes_mornos,
        'clientes_quentes': clientes_quentes,
        'objetivo_ano': objetivo_ano,
        'ticket_medio': ticket_medio,
        'pl_evolucao_chart': pl_evolucao_chart_html,
        'comparativo_chart': comparativo_chart_html,
        'clientes_evolucao_chart': clientes_evolucao_chart_html,
        'pl_trend': pl_trend,
        'horizonte_meses': horizonte_meses,
        'pl_projetado': pl_projetado,
        'year': current_year,
        'data_atualizacao': datetime.now(),
        'percentual_atingido': percentual_atingido,
        'pace': pace,
        'total_planejado': total_planejado,
        'total_migrado': total_migrado
    }

    return render(request, 'main/dashboard_assessor.html', context)


#Histórico de envios
@user_passes_test(lambda u: u.is_assessor())
def historico_view(request):
    captacoes = Captacao.objects.filter(user=request.user).order_by('-created_at')
    estatisticas = Estatisticas.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'main/historico.html', {
        'captacoes': captacoes,
        'estatisticas': estatisticas
    })

#Histórico Head
@user_passes_test(lambda u: u.is_head())
def historico_head(request):
    user = request.user
    planejado = Planejado.objects.filter(user=user).order_by('-created_at')
    executado = Executado.objects.filter(user=user).order_by('-created_at')

    # Detectar área de cada registro pelo tipo de formulário preenchido
    def detect_area(obj):
        # Consórcio
        if getattr(obj, 'qtd_consorcios', None) is not None or getattr(obj, 'volume_financeiro', None) is not None:
            return 'Consórcio'
        # Seguros
        if getattr(obj, 'qtd_seguros', None) is not None or getattr(obj, 'volume_pa', None) is not None:
            return 'Seguros'
        # Expansão
        if getattr(obj, 'entrevistas', None) is not None and getattr(obj, 'contratacoes', None) is not None:
            return 'Expansão'
        # Renda Variável
        if getattr(obj, 'cpfs_operados', None) is not None or getattr(obj, 'volume_ofertas', None) is not None:
            return 'Renda Variável'
        # Câmbio
        if getattr(obj, 'volume_operado', None) is not None or getattr(obj, 'assessores_ativos', None) is not None:
            return 'Câmbio'
        # Corporate
        if getattr(obj, 'volume_credito', None) is not None:
            return 'Corporate'
        # Banking
        if getattr(obj, 'principalidade', None) is not None or getattr(obj, 'cartoes_emitidos', None) is not None:
            return 'Banking'
        # Marketing
        if getattr(obj, 'seguidores', None) is not None or getattr(obj, 'interacoes', None) is not None:
            return 'Marketing'
        # Advisory
        if getattr(obj, 'pl_liquidez', None) is not None or getattr(obj, 'ofertas_publicas', None) is not None:
            return 'Advisory'
        return 'Outro'

    for obj in planejado:
        obj.area_nome = detect_area(obj)
    for obj in executado:
        obj.area_nome = detect_area(obj)

    return render(request, 'main/historico_head.html', {
        'planejado': planejado,
        'executado': executado,
    })


@user_passes_test(lambda u: u.is_master())
def dashboard_master(request):
    # Get all areas
    areas = Area.objects.all()
    
    # Get current month and year
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Get all captacoes for PL calculations
    captacoes = (
        Captacao.objects
        .exclude(pl__isnull=True)
        .filter(pl__gt=0)  # Only include records with pl > 0 instead of excluding empty strings
        .annotate(pl_text=Cast('pl', output_field=models.TextField()))  # First cast to text
        .annotate(pl_temp=Replace(F('pl_text'), Value('R$'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value('.'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value(','), Value('.')))
        .annotate(
            pl_number=Cast('pl_temp', output_field=DecimalField(max_digits=20, decimal_places=2))
        )
    )

    # Calculate total PL - divide by 100 to fix decimal place issue
    pl_total_value = float(captacoes.aggregate(Sum('pl_number'))['pl_number__sum'] or 0) / 100
    pl_total = format_br_currency(pl_total_value)
    
    # Get ROA medio
    roa_medio = float(Unidade.objects.aggregate(avg_roa=models.Avg('roa'))['avg_roa'] or 0)
    
    # Get total active clients
    total_clientes = captacoes.count()
    
    # Calculate ticket médio
    ticket_medio_value = (pl_total_value / total_clientes) if total_clientes > 0 else 0
    ticket_medio = format_br_currency(ticket_medio_value)
    
    # Get total active leads (sum of all qtd_* fields from Estatisticas)
    total_leads = Estatisticas.objects.aggregate(
        total=Sum('qtd_rv') + Sum('qtd_cambio') + Sum('qtd_seguros') + 
              Sum('qtd_consorcio') + Sum('qtd_corporate') + Sum('qtd_expansao') + 
              Sum('qtd_banking') + Sum('qtd_advisory')
    )['total'] or 0
    
    # NEW KPIs with detailed breakdown
    # Calculate time-based metrics for pace calculations
    months_elapsed = current_month
    months_total = 12
    time_elapsed_percentage = (months_elapsed / months_total) * 100
    
    # 1. AUC (on+offshore) - Detailed breakdown
    auc_planejado = float(Planejado.objects.filter(year=current_year).aggregate(Sum('auc'))['auc__sum'] or 0)
    auc_executado = float(Executado.objects.filter(year=current_year).aggregate(Sum('auc'))['auc__sum'] or 0)
    auc_percentual_atingido = (auc_executado / auc_planejado * 100) if auc_planejado > 0 else 0
    auc_pace = (auc_percentual_atingido / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
    
    # 2. Receita PJ1 - Detailed breakdown (placeholder functions for now)
    receita_pj1_planejado = 5000000  # Placeholder - should come from actual data source
    receita_pj1_executado = get_receita_pj1_from_api()
    receita_pj1_percentual_atingido = (receita_pj1_executado / receita_pj1_planejado * 100) if receita_pj1_planejado > 0 else 0
    receita_pj1_pace = (receita_pj1_percentual_atingido / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
    
    # 3. Receita PJ2 - Detailed breakdown (placeholder functions for now)
    receita_pj2_planejado = 3000000  # Placeholder - should come from actual data source
    receita_pj2_executado = get_receita_pj2_from_master()
    receita_pj2_percentual_atingido = (receita_pj2_executado / receita_pj2_planejado * 100) if receita_pj2_planejado > 0 else 0
    receita_pj2_pace = (receita_pj2_percentual_atingido / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
    
    # 4. Receita total - Detailed breakdown
    receita_total_planejado = receita_pj1_planejado + receita_pj2_planejado
    receita_total_executado = receita_pj1_executado + float(receita_pj2_executado)
    receita_total_percentual_atingido = (receita_total_executado / receita_total_planejado * 100) if receita_total_planejado > 0 else 0
    receita_total_pace = (receita_total_percentual_atingido / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
    
    # Format values for display
    auc_planejado_formatted = format_br_currency(auc_planejado)
    auc_executado_formatted = format_br_currency(auc_executado)
    receita_pj1_planejado_formatted = format_br_currency(receita_pj1_planejado)
    receita_pj1_executado_formatted = format_br_currency(receita_pj1_executado)
    receita_pj2_planejado_formatted = format_br_currency(receita_pj2_planejado)
    receita_pj2_executado_formatted = format_br_currency(receita_pj2_executado)
    receita_total_planejado_formatted = format_br_currency(receita_total_planejado)
    receita_total_executado_formatted = format_br_currency(receita_total_executado)
    
    # Get total planned PL for the company (for overall performance)
    total_planejado = float(Planejado.objects.filter(
        year=current_year
    ).aggregate(total_planejado=Sum('auc'))['total_planejado'] or 0)
    
    # Calculate overall company performance
    percentual_atingido_geral = (pl_total_value / total_planejado * 100) if total_planejado > 0 else 0
    pace_geral = (percentual_atingido_geral / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
    
    # Area-specific data and charts
    areas_data = []
    for area in areas:
        # Get users in this area
        area_users = CustomUser.objects.filter(area_ref=area)
        
        # Get captacoes for this area
        area_captacoes = captacoes.filter(user__in=area_users)
        
        # Calculate area PL - divide by 100 to fix decimal place issue
        area_pl_value = float(area_captacoes.aggregate(Sum('pl_number'))['pl_number__sum'] or 0) / 100
        area_pl = format_br_currency(area_pl_value)
        
        # Get planned PL for this area (from Planejado model)
        area_planejado = float(Planejado.objects.filter(
            user__in=area_users,
            year=current_year
        ).aggregate(total_planejado=Sum('auc'))['total_planejado'] or 0)
        
        # Calculate percentage achieved
        percentual_atingido = (area_pl_value / area_planejado * 100) if area_planejado > 0 else 0
        
        # Calculate pace
        pace = (percentual_atingido / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
        
        # Calculate area ticket médio
        area_clientes = area_captacoes.count()
        area_ticket_medio = (area_pl_value / area_clientes) if area_clientes > 0 else 0
        
        # Get area statistics
        area_stats = Estatisticas.objects.filter(user__in=area_users)
        
        # Calculate total leads for this area
        area_leads = area_stats.aggregate(
            total=Sum('qtd_rv') + Sum('qtd_cambio') + Sum('qtd_seguros') + 
                  Sum('qtd_consorcio') + Sum('qtd_corporate') + Sum('qtd_expansao') + 
                  Sum('qtd_banking') + Sum('qtd_advisory')
        )['total'] or 0
        
        # Area-specific metrics (from dashboard_area)
        area_metrics = {
            'entrevistas': 0,
            'contratacoes': 0,
            'nps': 0,
            'volume_pa': 0,
            'qtd_reunioes': 0,
            'qtd_seguros': 0,
            'receita': 0,
            'cpfs_operados': 0,
            'volume_ofertas': 0,
            'volume_operado': 0,
            'assessores_ativos': 0,
            'volume_credito': 0,
            'principalidade': 0,
            'cartoes_emitidos': 0,
            'seguidores': 0,
            'interacoes': 0,
            'leads_redes': 0,
            'captacao_mesa': 0,
            'qtd_consorcios': 0,
            'volume_financeiro': 0,
            'pl_liquidez': 0,
            'percentual_pl_liquidez': 0,
            'vol_credito_corp': 0,
            'perc_pl_credito': 0,
            'ofertas_publicas': 0,
        }
        executado_data = Executado.objects.filter(
            user__in=area_users,
            year=current_year
        )
        for exec_item in executado_data:
            for field in ['headcount', 'auc', 'receita']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            if area.nome == 'Expansão':
                for field in ['entrevistas', 'contratacoes', 'nps']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            elif area.nome == 'Seguro' or area.nome == 'Seguros':
                for field in ['volume_pa', 'qtd_reunioes', 'qtd_seguros']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            elif area.nome == 'Renda Variável':
                for field in ['receita', 'cpfs_operados', 'volume_ofertas']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            elif area.nome == 'Câmbio' or area.nome == 'Cambio':
                for field in ['receita', 'volume_operado', 'assessores_ativos']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            elif area.nome == 'Corporate':
                for field in ['volume_credito', 'qtd_reunioes']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            elif area.nome == 'Banking':
                for field in ['principalidade', 'cartoes_emitidos']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            elif area.nome == 'Marketing':
                for field in ['seguidores', 'interacoes', 'leads_redes', 'percentual_pl_credito']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            elif area.nome == 'Consórcio' or area.nome == 'Consorcio':
                for field in ['volume_financeiro', 'qtd_consorcios']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
            elif area.nome == 'Advisory':
                for field in ['pl_liquidez', 'percentual_pl_liquidez', 'vol_credito_corp', 'perc_pl_credito', 'ofertas_publicas']:
                    if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                        area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        area_metrics['percentual_atingido'] = percentual_atingido
        area_metrics['pace'] = pace
        # Add area data to list - now with area_metrics
        areas_data.append({
            'nome': area.nome,
            'slug': area.slug,
            'users_count': area_users.count(),
            'pl_total': area_pl,
            'pl_planejado': format_br_currency(area_planejado),
            'percentual_atingido': percentual_atingido,
            'pace': pace,
            'leads_ativos': area_leads,
            'clientes_ativos': area_clientes,
            'ticket_medio': format_br_currency(area_ticket_medio),
            'metrics': area_metrics,
        })
    
    # Create overall PL evolution chart
    pl_evolucao_geral = (
        captacoes
        .annotate(mes=TruncMonth('created_at'))
        .values('mes')
        .annotate(total_pl=Sum('pl_number'))
        .order_by('mes')
    )
    
    pl_mes_geral = [d['mes'].strftime('%b/%Y') for d in pl_evolucao_geral if d['mes']]
    pl_total_geral = [float(d['total_pl'] or 0) / 100 for d in pl_evolucao_geral]  # Divide by 100
    
    pl_chart_geral = go.Figure()
    pl_chart_geral.add_trace(go.Scatter(x=pl_mes_geral, y=pl_total_geral, mode='lines+markers', name='PL Total'))
    pl_chart_geral.update_layout(
        title='PL Total da Empresa',
        xaxis_title='Mês',
        yaxis_title='PL (R$)',
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    pl_chart_geral_html = opy.plot(pl_chart_geral, auto_open=False, output_type='div')
    
    context = {
        'pl_total': pl_total,
        'roa_medio': roa_medio,
        'total_clientes': total_clientes,
        'total_leads': total_leads,
        'ticket_medio': ticket_medio,
        'areas_data': areas_data,
        'pl_chart_geral': pl_chart_geral_html,
        'percentual_atingido_geral': percentual_atingido_geral,
        'pace_geral': pace_geral,
        # AUC KPI variables
        'auc_planejado': auc_planejado_formatted,
        'auc_executado': auc_executado_formatted,
        'auc_percentual_atingido': auc_percentual_atingido,
        'auc_pace': auc_pace,
        # Receita PJ1 KPI variables
        'receita_pj1_planejado': receita_pj1_planejado_formatted,
        'receita_pj1_executado': receita_pj1_executado_formatted,
        'receita_pj1_percentual_atingido': receita_pj1_percentual_atingido,
        'receita_pj1_pace': receita_pj1_pace,
        # Receita PJ2 KPI variables
        'receita_pj2_planejado': receita_pj2_planejado_formatted,
        'receita_pj2_executado': receita_pj2_executado_formatted,
        'receita_pj2_percentual_atingido': receita_pj2_percentual_atingido,
        'receita_pj2_pace': receita_pj2_pace,
        # Receita Total KPI variables
        'receita_total_planejado': receita_total_planejado_formatted,
        'receita_total_executado': receita_total_executado_formatted,
        'receita_total_percentual_atingido': receita_total_percentual_atingido,
        'receita_total_pace': receita_total_pace,
    }
    
    return render(request, 'main/dashboard_master.html', context)

@user_passes_test(lambda u: u.is_master())
def dashboard_area(request, area_slug):
    """
    Detailed dashboard for a specific area
    """
    # Get area by slug
    area = get_object_or_404(Area, slug=area_slug)
    
    # Get current month and year
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Get users in this area
    area_users = CustomUser.objects.filter(area_ref=area)
    
    # Get captacoes for this area with PL calculations
    captacoes = (
        Captacao.objects
        .filter(user__in=area_users)
        .exclude(pl__isnull=True)
        .filter(pl__gt=0)  # Only include records with pl > 0 instead of excluding empty strings
        .annotate(pl_text=Cast('pl', output_field=models.TextField()))  # First cast to text
        .annotate(pl_temp=Replace(F('pl_text'), Value('R$'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value('.'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value(','), Value('.')))
        .annotate(
            pl_number=Cast('pl_temp', output_field=DecimalField(max_digits=20, decimal_places=2))
        )
    )
    
    # Calculate area PL total
    area_pl = float(captacoes.aggregate(Sum('pl_number'))['pl_number__sum'] or 0) / 100  # Divide by 100
    
    # Get planned PL for this area (from Planejado model)
    area_planejado = float(Planejado.objects.filter(
        user__in=area_users,
        year=current_year
    ).aggregate(total_planejado=Sum('auc'))['total_planejado'] or 0)
    
    # Calculate monthly percentage (for pace)
    months_elapsed = current_month
    months_total = 12
    time_elapsed_percentage = (months_elapsed / months_total) * 100
    
    # Calculate percentage achieved
    percentual_atingido = (area_pl / area_planejado * 100) if area_planejado > 0 else 0
    
    # Calculate pace
    pace = (percentual_atingido / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
    
    # Calculate area ticket médio
    area_clientes = captacoes.count()
    area_ticket_medio = (area_pl / area_clientes) if area_clientes > 0 else 0
    
    # Get area statistics
    area_stats = Estatisticas.objects.filter(user__in=area_users)
    
    # Calculate total leads for this area
    area_leads = area_stats.aggregate(
        total=Sum('qtd_rv') + Sum('qtd_cambio') + Sum('qtd_seguros') + 
              Sum('qtd_consorcio') + Sum('qtd_corporate') + Sum('qtd_expansao') + 
              Sum('qtd_banking') + Sum('qtd_advisory')
    )['total'] or 0
    
    # Create monthly PL evolution chart for this area
    pl_evolucao = (
        captacoes
            .annotate(mes=TruncMonth('created_at'))
            .values('mes')
            .annotate(total_pl=Sum('pl_number'))
            .order_by('mes')
        )
        
    pl_mes = [d['mes'].strftime('%b/%Y') for d in pl_evolucao if d['mes']]
    pl_total = [float(d['total_pl'] or 0) / 100 for d in pl_evolucao]  # Divide by 100
        
    pl_chart = go.Figure()
    pl_chart.add_trace(go.Scatter(x=pl_mes, y=pl_total, mode='lines+markers', name='PL'))
    pl_chart.update_layout(
        title=f'Evolução do PL - {area.nome}',
            xaxis_title='Mês',
            yaxis_title='PL (Mi)',
        height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
    pl_chart_html = opy.plot(pl_chart, auto_open=False, output_type='div')
        
        # Create client evolution chart
    clientes_evolucao = (
        captacoes
            .annotate(mes=TruncMonth('created_at'))
            .values('mes')
            .annotate(total=Count('id'))
            .order_by('mes')
        )
        
    clientes_mes = [d['mes'].strftime('%b/%Y') for d in clientes_evolucao if d['mes']]
    clientes_total = [d['total'] for d in clientes_evolucao]
        
    clientes_chart = go.Figure()
    clientes_chart.add_trace(go.Scatter(x=clientes_mes, y=clientes_total, mode='lines+markers', name='Clientes'))
    clientes_chart.update_layout(
        title=f'Evolução de Clientes - {area.nome}',
            xaxis_title='Mês',
            yaxis_title='Número de Clientes',
        height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
    clientes_chart_html = opy.plot(clientes_chart, auto_open=False, output_type='div')
        
    # Get area-specific metrics
    area_metrics = {
        'entrevistas': 0,
        'contratacoes': 0,
        'nps': 0,
        'volume_pa': 0,
        'qtd_reunioes': 0,
        'qtd_seguros': 0,
        'receita': 0,
        'cpfs_operados': 0,
        'volume_ofertas': 0,
        'volume_operado': 0,
        'assessores_ativos': 0,
        'volume_credito': 0,
        'principalidade': 0,
        'cartoes_emitidos': 0,
        'seguidores': 0,
        'interacoes': 0,
        'leads_redes': 0,
        'captacao_mesa': 0,
        'qtd_consorcios': 0,
        'volume_financeiro': 0,
        'pl_liquidez': 0,
        'percentual_pl_liquidez': 0,
        'vol_credito_corp': 0,
        'perc_pl_credito': 0,
        'ofertas_publicas': 0,
    }
    
    # Get KPI metrics based on executado data
    executado_data = Executado.objects.filter(
        user__in=area_users,
        year=current_year
    )
    
    # Accumulate metrics from all users in the area
    for exec_item in executado_data:
        # Common metrics that might be present regardless of area
        for field in ['headcount', 'auc', 'receita']:
            if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
                
        # Area-specific metrics
        if area.nome == 'Expansão':
            for field in ['entrevistas', 'contratacoes', 'nps']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        
        elif area.nome == 'Seguro' or area.nome == 'Seguros':
            for field in ['volume_pa', 'qtd_reunioes', 'qtd_seguros']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        
        elif area.nome == 'Renda Variável':
            for field in ['receita', 'cpfs_operados', 'volume_ofertas']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        
        elif area.nome == 'Câmbio' or area.nome == 'Cambio':
            for field in ['receita', 'volume_operado', 'assessores_ativos']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        
        elif area.nome == 'Corporate':
            for field in ['volume_credito', 'qtd_reunioes']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        
        elif area.nome == 'Banking':
            for field in ['principalidade', 'cartoes_emitidos']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        
        elif area.nome == 'Marketing':
            for field in ['seguidores', 'interacoes', 'leads_redes', 'perc_pl_credito']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        
        elif area.nome == 'Consórcio' or area.nome == 'Consorcio':
            for field in ['volume_financeiro', 'qtd_consorcios']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
        
        elif area.nome == 'Advisory':
            for field in ['pl_liquidez', 'percentual_pl_liquidez', 'vol_credito_corp', 'perc_pl_credito', 'ofertas_publicas']:
                if hasattr(exec_item, field) and getattr(exec_item, field) is not None:
                    area_metrics[field] = area_metrics.get(field, 0) + float(getattr(exec_item, field))
    
    # Add meta information to area metrics
    area_metrics['percentual_atingido'] = percentual_atingido
    area_metrics['pace'] = pace
    
    context = {
        'area': area,
        'area_metrics': area_metrics,
        'area_users_count': area_users.count(),
        'area_pl': area_pl,
        'area_planejado': area_planejado,
            'percentual_atingido': percentual_atingido,
            'pace': pace,
            'pl_chart': pl_chart_html,
            'clientes_chart': clientes_chart_html,
            'leads_ativos': area_leads,
            'clientes_ativos': area_clientes,
            'ticket_medio': area_ticket_medio,
    }
    
    return render(request, 'main/dashboard_area.html', context)

@user_passes_test(lambda u: u.is_master())
def lista_unidades(request):
    unidades = Unidade.objects.all()
    
    # Enhanced units with real-time data
    enhanced_units = []
    
    for unit in unidades:
        # Get assessores in this unit
        assessores = CustomUser.objects.filter(unidade=unit, cargo='assessor')
        
        # Get captacoes for assessores in this unit
        captacoes = Captacao.objects.filter(user__in=assessores)
        
        # Calculate PL total and other metrics
        pl_total = sum(parse_br_number(c.pl) for c in captacoes)
        planejado_migracao_total = sum(parse_br_number(c.planejado_migracao) for c in captacoes)
        
        # Calculate client counts by status
        clientes_count = captacoes.count()
        clientes_ativos = captacoes.filter(status='Ativo').count()
        clientes_frios = captacoes.filter(status='Frio').count()
        clientes_mornos = captacoes.filter(status='Morno').count()
        clientes_quentes = captacoes.filter(status='Quente').count()
        
        # Calculate ticket médio
        ticket_medio = (pl_total / clientes_count) if clientes_count > 0 else 0
        
        # Calculate performance percentage
        # Example: Based on goals achieved vs expected at this point in time
        current_month = datetime.now().month
        time_elapsed_percent = (current_month / 12) * 100
        
        # Get planned PL for this unit (from all assessors' Planejado records)
        unit_planejado = float(Planejado.objects.filter(
            user__in=assessores,
            year=datetime.now().year
        ).aggregate(total_planejado=Sum('auc'))['total_planejado'] or 0)
        
        # Calculate percentage of goal achieved
        if unit_planejado > 0:
            pct_achieved = min(100, (pl_total / unit_planejado) * 100)
        else:
            pct_achieved = 0
            
        # Calculate pace (percentage achieved relative to time elapsed)
        pace = (pct_achieved / time_elapsed_percent * 100) if time_elapsed_percent > 0 else 0
        
        # Add enhanced data to the unit
        unit.enhanced_data = {
        'pl_total': format_br_currency(pl_total),
            'assessores_count': assessores.count(),
            'clientes_count': clientes_count,
            'clientes_ativos': clientes_ativos,
            'clientes_frios': clientes_frios,
            'clientes_mornos': clientes_mornos,
            'clientes_quentes': clientes_quentes,
        'ticket_medio': format_br_currency(ticket_medio),
            'performance_percent': int(pct_achieved),
            'planejado': format_br_currency(unit_planejado),
            'pace': int(pace)
        }
        
        enhanced_units.append(unit)
    
    return render(request, 'main/unidades.html', {'unidades': enhanced_units})

@user_passes_test(lambda u: u.is_headunidade())
def home_headunidade(request):
    user = request.user
    month = datetime.now().month
    year = datetime.now().year

    # Try multiple methods to find the user's unit
    unidade = None
    
    # Method 1: Check if the user is directly set as the head of any unit
    try:
        unidade = Unidade.objects.get(head=user)
    except Unidade.DoesNotExist:
        # Method 2: Check if the user's unidade attribute is set
        if user.unidade:
            unidade = user.unidade
            # Check if this user is marked as a head but the unit's head field isn't set to them
            if unidade.head is None:
                # Update the unit to set this user as its head
                unidade.head = user
                unidade.save(update_fields=['head'])
        else:
            # Method 3: If user has headunidade role but no unit relationship yet,
            # look for units without a head
            headless_units = Unidade.objects.filter(head__isnull=True)
            if headless_units.exists():
                # Assign the first available unit to this head
                unidade = headless_units.first()
                unidade.head = user
                unidade.save(update_fields=['head'])
                # Also set the user's unidade attribute for consistency
                user.unidade = unidade
                user.save(update_fields=['unidade'])
    
    # Initialize units_info in all cases
    units_info = []
            
    # If no unit was found through any method, show the no-unit message
    if not unidade:
        # Method 4: For debugging, let's also list all available units
        all_units = Unidade.objects.all()
        units_info = [{'id': u.id, 'nome': u.nome, 'has_head': u.head is not None} for u in all_units]
        
        context = {
            'no_unit': True,
            'units_info': units_info
        }
    else:
        # Get all assessores in this unit
        assessores = CustomUser.objects.filter(unidade=unidade, cargo='assessor')
        
        # Get captações for this unit
        captacoes = Captacao.objects.filter(user__in=assessores)
        
        # Calculate PL total 
        pl_total = sum(parse_br_number(c.pl) for c in captacoes)
        formatted_pl_total = format_currency(pl_total)
        
        # Get assessors with pending estatisticas
        assessores_sem_estatisticas = assessores.exclude(
            id__in=Estatisticas.objects.filter(month=month, year=year).values_list('user', flat=True)
        )
        
        # Calculate indicators by area from estatisticas
        estatisticas = Estatisticas.objects.filter(user__in=assessores, month=month, year=year)
        indicators = {
            'rv': estatisticas.filter(rv=True).count(),
            'cambio': estatisticas.filter(cambio=True).count(),
            'seguros': estatisticas.filter(seguros=True).count(),
            'consorcio': estatisticas.filter(consorcio=True).count(),
            'corporate': estatisticas.filter(corporate=True).count(),
            'expansao': estatisticas.filter(expansao=True).count(),
            'banking': estatisticas.filter(banking=True).count(),
            'advisory': estatisticas.filter(advisory=True).count(),
        }
        
        context = {
            'unidade': unidade,
            'assessores': assessores,
            'assessor_count': assessores.count(),
            'total_captacoes': captacoes.count(),
            'total_pl': formatted_pl_total,
            'assessores_sem_estatisticas': assessores_sem_estatisticas,
            'indicators': indicators
        }
    
    return render(request, 'main/home_headunidade.html', context)

def format_currency(value):
    """Format currency values to be more readable by adding commas as thousand separators"""
    if isinstance(value, Decimal):
        return '{:,.2f}'.format(value).replace(',', 'X').replace('.', ',').replace('X', '.')
    return '{:,.2f}'.format(float(value)).replace(',', 'X').replace('.', ',').replace('X', '.')

@user_passes_test(lambda u: u.is_headunidade())
def dashboard_headunidade(request):
    """Dashboard for Unit Heads to see their unit performance metrics"""
    user = request.user
    
    # Find the unit associated with this head
    try:
        unidade = Unidade.objects.get(head=user)
    except Unidade.DoesNotExist:
        if user.unidade:
            unidade = user.unidade
        else:
            # No unit found, redirect to home
            return redirect('home_headunidade')
    
    # Find all assessors in this unit
    assessores = CustomUser.objects.filter(unidade=unidade, cargo='assessor')
    
    # Calculate aggregated metrics for the unit
    # Get all client acquisition entries (captacoes) from assessors in this unit
    captacoes = Captacao.objects.filter(user__in=assessores)
    
    # Calculate PL total by safely converting string representations to decimal
    pl_total = sum(parse_br_number(c.pl) for c in captacoes)
    planejado_migracao_total = sum(parse_br_number(c.planejado_migracao) for c in captacoes)
    
    # Get ROA for the unit
    roa_unidade = unidade.roa if hasattr(unidade, 'roa') else 0.0
    
    # Calculate migration expectation percentage
    expectativa_migracao = (planejado_migracao_total / pl_total * 100) if pl_total > 0 else 0
    
    # Count active clients
    clientes_ativos = captacoes.count()
    
    # Calculate average ticket
    ticket_medio = (pl_total / clientes_ativos) if clientes_ativos > 0 else 0
    
    # Count clients by status
    clientes_frios = captacoes.filter(status='Frio').count()
    clientes_mornos = captacoes.filter(status='Morno').count()
    clientes_quentes = captacoes.filter(status='Quente').count()
    
    # Collect data for each assessor
    assessores_data = []
    for assessor in assessores:
        # Get captacoes for this assessor
        assessor_captacoes = Captacao.objects.filter(user=assessor)
        
        # Calculate PL managed by this assessor
        pl_gerenciado = sum(parse_br_number(c.pl) for c in assessor_captacoes)
        
        # Count clients by status
        clients_count = assessor_captacoes.count()
        
        # Determine status based on activity
        status = "Ativo"
        status_color = "success"
        
        # Check if assessor has submitted estatisticas for current month
        month = datetime.now().month
        year = datetime.now().year
        has_estatisticas = Estatisticas.objects.filter(user=assessor, month=month, year=year).exists()
        
        if not has_estatisticas:
            status = "Pendente"
            status_color = "warning"
        
        assessores_data.append({
            'id': assessor.id,
            'username': assessor.username,
            'get_full_name': assessor.get_full_name() if callable(getattr(assessor, 'get_full_name', None)) else assessor.username,
            'pl_gerenciado': format_currency(pl_gerenciado),
            'clientes_count': clients_count,
            'status': status,
            'status_color': status_color
        })
    
    # Sort metrics for top performers (by PL)
    top_performers = sorted(assessores_data, key=lambda x: x['pl_gerenciado'], reverse=True)[:5]
    
    # Get recent operations (you may need to adjust this based on your model structure)
    # This is a placeholder - modify according to your data model
    recent_operations = []
    for assessor in assessores:
        try:
            latest_stats = Estatisticas.objects.filter(user=assessor).latest('created_at')
            if latest_stats:
                recent_operations.append({
                    'tipo': 'Estatísticas',
                    'assessor': assessor.get_full_name() or assessor.username,
                    'data': latest_stats.created_at.strftime('%d/%m/%Y')
                })
        except Estatisticas.DoesNotExist:
            pass
            
    # Sort by date (most recent first) and limit to 5
    recent_operations = sorted(recent_operations, key=lambda x: x['data'], reverse=True)[:5]
    
    context = {
        'unidade': unidade,
        'assessores_count': assessores.count(),
        'horizonte_meses': 12,
        'pl_total': format_currency(pl_total),
        'migracao_planejada': format_currency(planejado_migracao_total),
        'expectativa_migracao': round(expectativa_migracao, 2),
        'pl_atual': format_currency(pl_total),
        'roa': roa_unidade,
        'clientes_ativos': clientes_ativos,
        'clientes_frios': clientes_frios,
        'clientes_mornos': clientes_mornos, 
        'clientes_quentes': clientes_quentes,
        'ticket_medio': format_currency(ticket_medio),
        'data_atualizacao': datetime.now(),
        'assessores': assessores_data,
        'top_performers': top_performers,
        'recent_operations': recent_operations,
    }
    
    return render(request, 'main/dashboard_headunidade.html', context)

@user_passes_test(lambda u: u.is_headunidade())
def assessor_monitoring(request, assessor_id=None):
    """View for Unit Heads to monitor individual assessors' performance"""
    user = request.user
    
    # Find the unit associated with this head
    try:
        unidade = Unidade.objects.get(head=user)
    except Unidade.DoesNotExist:
        if user.unidade:
            unidade = user.unidade
        else:
            # No unit found, redirect to home
            return redirect('home_headunidade')
    
    # Get all assessors in this unit
    assessores = CustomUser.objects.filter(unidade=unidade, cargo='assessor')
    
    # If no assessor_id provided, show the list of all assessors
    if not assessor_id:
        # For each assessor, collect summary metrics
        assessor_metrics = []
        total_clientes = 0
        total_pl = 0
        total_operacoes = 0
        clientes_frios = 0
        clientes_mornos = 0
        clientes_quentes = 0
        
        for assessor in assessores:
            # Count captacoes (client acquisitions)
            captacoes = Captacao.objects.filter(user=assessor)
            captacoes_count = captacoes.count()
            
            # Count clients by status
            clientes_frios += captacoes.filter(status='Frio').count()
            clientes_mornos += captacoes.filter(status='Morno').count()
            clientes_quentes += captacoes.filter(status='Quente').count()
            
            # Get latest statistics
            try:
                latest_stats = Estatisticas.objects.filter(user=assessor).latest('created_at')
                assessor_operations = (
                    latest_stats.qtd_rv +
                    latest_stats.qtd_cambio +
                    latest_stats.qtd_seguros +
                    latest_stats.qtd_consorcio +
                    latest_stats.qtd_corporate +
                    latest_stats.qtd_expansao +
                    latest_stats.qtd_banking +
                    latest_stats.qtd_advisory
                )
            except Estatisticas.DoesNotExist:
                assessor_operations = 0
            
            # Calculate PL managed by this assessor
            captacoes = Captacao.objects.filter(user=assessor)
            assessor_pl_total = sum(parse_br_number(c.pl) for c in captacoes)
            
            # Sum totals
            total_clientes += captacoes_count
            total_pl += assessor_pl_total
            total_operacoes += assessor_operations
            
            assessor_metrics.append({
                'assessor': assessor,
                'captacoes_count': captacoes_count,
                'total_operations': assessor_operations,
                'pl_total': assessor_pl_total,
            })
        
        # Sort metrics for top performers (by PL)
        top_performers = sorted(assessor_metrics, key=lambda x: x['pl_total'], reverse=True)[:5]
        
        # Get recent operations (you may need to adjust this based on your model structure)
        # This is a placeholder - modify according to your data model
        recent_operations = []
        for assessor in assessores:
            try:
                latest_stats = Estatisticas.objects.filter(user=assessor).latest('created_at')
                if latest_stats:
                    recent_operations.append({
                        'tipo': 'Estatísticas',
                        'assessor': assessor.get_full_name() or assessor.username,
                        'data': latest_stats.created_at.strftime('%d/%m/%Y')
                    })
            except Estatisticas.DoesNotExist:
                pass
                
        # Sort by date (most recent first) and limit to 5
        recent_operations = sorted(recent_operations, key=lambda x: x['data'], reverse=True)[:5]
        
        context = {
            'unidade': unidade,
            'assessor_metrics': assessor_metrics,
            'total_clientes': total_clientes,
            'total_pl': format_currency(total_pl),
            'total_operacoes': total_operacoes,
            'clientes_frios': clientes_frios,
            'clientes_mornos': clientes_mornos,
            'clientes_quentes': clientes_quentes,
            'top_performers': top_performers,
            'recent_operations': recent_operations,
            'data_atualizacao': datetime.now()
        }
        return render(request, 'main/assessor_monitoring_list.html', context)
    
    # If assessor_id is provided, show detailed view for that assessor
    assessor = get_object_or_404(CustomUser, id=assessor_id, unidade=unidade, cargo='assessor')
    
    # Get the data similar to dashboard_assessor view but for this specific assessor
    captacoes = Captacao.objects.filter(user=assessor)
    estatisticas = Estatisticas.objects.filter(user=assessor)
    
    # For PL calculations - convert string to decimal before summing
    pl_total = sum(parse_br_number(c.pl) for c in captacoes)
    
    # Get current month and year
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Get last month's data for comparison
    last_month = current_date.replace(day=1) - timedelta(days=1)
    last_month_captacoes = Captacao.objects.filter(
        user=assessor,
        created_at__year=last_month.year,
        created_at__month=last_month.month
    )
    last_month_pl = sum(parse_br_number(c.pl) for c in last_month_captacoes)
    
    # Calculate trend percentage
    pl_trend = ((pl_total - last_month_pl) / last_month_pl * 100) if last_month_pl > 0 else 0
    
    # Get client counts
    clientes_ativos = captacoes.count()
    clientes_frios = captacoes.filter(status='Frio').count()
    clientes_mornos = captacoes.filter(status='Morno').count()
    clientes_quentes = captacoes.filter(status='Quente').count()
    
    # Calculate ticket médio
    ticket_medio = (pl_total / clientes_ativos) if clientes_ativos > 0 else 0
    
    # Get latest statistics
    try:
        latest_stats = estatisticas.latest('created_at')
        
        # Calculate operations by category
        operations = {
            'RV': latest_stats.qtd_rv,
            'Câmbio': latest_stats.qtd_cambio,
            'Seguros': latest_stats.qtd_seguros,
            'Consórcio': latest_stats.qtd_consorcio,
            'Corporate': latest_stats.qtd_corporate,
            'Expansão': latest_stats.qtd_expansao,
            'Banking': latest_stats.qtd_banking,
            'Advisory': latest_stats.qtd_advisory
        }
        
        total_operations = sum(operations.values())
    except Estatisticas.DoesNotExist:
        operations = {
            'RV': 0, 'Câmbio': 0, 'Seguros': 0, 'Consórcio': 0,
            'Corporate': 0, 'Expansão': 0, 'Banking': 0, 'Advisory': 0
        }
        total_operations = 0
        latest_stats = None
    
    context = {
        'unidade': unidade,
        'assessor': assessor,
        'pl_atual': format_currency(pl_total),
        'pl_trend': pl_trend,
        'clientes_ativos': clientes_ativos,
        'clientes_frios': clientes_frios,
        'clientes_mornos': clientes_mornos,
        'clientes_quentes': clientes_quentes,
        'ticket_medio': format_currency(ticket_medio),
        'operations': operations,
        'total_operations': total_operations,
        'latest_stats': latest_stats,
        'captacoes': captacoes.order_by('-created_at')[:10],  # Latest 10 client acquisitions
        'data_atualizacao': datetime.now(),
    }
    
    return render(request, 'main/assessor_monitoring_detail.html', context)

@login_required
def unit_hierarchy_view(request, unit_id=None):
    """
    View to display the structure of a unit or all units if no unit_id is provided
    """
    if unit_id:
        # Display a specific unit
        unit = get_object_or_404(Unidade, id=unit_id)
        context = {
            'unit': unit,
            'structure': get_unit_structure(unit)
        }
        return render(request, 'main/unit_hierarchy.html', context)
    else:
        # Display all units
        units = Unidade.objects.all()
        context = {
            'units': units
        }
        return render(request, 'main/units_list.html', context)

@login_required
def area_detail_view(request, area_id):
    """
    View to display details of a specific area including its head and advisors
    """
    area = get_object_or_404(Area, id=area_id)
    head = area.head
    
    # Find all units that have members in this area
    units = Unidade.objects.filter(membros__area_ref=area).distinct()
    
    # Get all advisors in this area
    advisors = CustomUser.objects.filter(area_ref=area, cargo='assessor')
    
    context = {
        'area': area,
        'head': head,
        'units': units,
        'advisors': advisors
    }
    
    return render(request, 'main/area_detail.html', context)

@login_required
def team_structure_view(request, user_id=None):
    """
    View to display the team structure under a supervisor
    """
    if not user_id and request.user.is_authenticated:
        user_id = request.user.id
        
    user = get_object_or_404(CustomUser, id=user_id)
    hierarchy = get_team_hierarchy(user)
    
    context = {
        'user': user,
        'hierarchy': hierarchy
    }
    
    return render(request, 'main/team_structure.html', context)

@login_required
def my_supervisor_view(request):
    """
    View to display information about the current user's supervisor
    """
    user = request.user
    supervisor = user.supervisor
    
    if not supervisor:
        return redirect('dashboard')
    
    context = {
        'supervisor': supervisor
    }
    
    return render(request, 'main/my_supervisor.html', context)

@login_required
def api_unit_structure(request, unit_id):
    """
    API endpoint to return JSON structure of a unit
    """
    unit = get_object_or_404(Unidade, id=unit_id)
    structure = get_unit_structure(unit)
    return JsonResponse(structure)

@login_required
def api_team_hierarchy(request, user_id):
    """
    API endpoint to return JSON structure of a team hierarchy
    """
    user = get_object_or_404(CustomUser, id=user_id)
    hierarchy = get_team_hierarchy(user)
    return JsonResponse(hierarchy)

@login_required
@require_POST
def save_contas_novas(request):
    """Save the new accounts count for the current user."""
    try:
        quantidade = int(request.POST.get('quantidade', 0))
        user = request.user
        user.contas_novas = quantidade
        user.save(update_fields=['contas_novas'])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_POST
def validar_codigo(request):
    try:
        data = json.loads(request.body)
        code_input = data.get("code")

        # Verifica se existe um código ativo com o valor fornecido
        is_valid = CodigoEdicao.objects.filter(codigo=code_input).exists()

        if is_valid:
            request.session['edit_code_valid'] = True

        return JsonResponse({"valid": is_valid})
    except Exception as e:
        return JsonResponse({"valid": False, "error": str(e)}, status=400)

def parse_decimal(value):
    """Converte strings como 'R$ 1.234.567,89' em Decimal."""
    if not value:
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    value = re.sub(r'[^\d,]', '', value)  # remove 'R$' e pontos
    value = value.replace('.', '').replace(',', '.')  # pt-BR → en-US
    try:
        return Decimal(value)
    except:
        return Decimal(0)

@user_passes_test(lambda u: u.is_master())
def home_master(request):
    total_unidades = Unidade.objects.count()
    total_assessores = CustomUser.objects.filter(cargo='assessor').count()
    total_clientes = Captacao.objects.count()

    # FILTRAGEM SEGURA sem conversão direta
    captacoes = (
        Captacao.objects
        .exclude(pl__isnull=True)
        .filter(pl__gt=0)  # Only include records with pl > 0 instead of excluding empty strings
        .annotate(pl_text=Cast('pl', output_field=models.TextField()))  # First cast to text
        .annotate(pl_temp=Replace(F('pl_text'), Value('R$'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value('.'), Value('')))
        .annotate(pl_temp=Replace(F('pl_temp'), Value(','), Value('.')))
        .annotate(
            pl_number=Cast('pl_temp', output_field=DecimalField(max_digits=20, decimal_places=2))
        )
    )

    pl_total = captacoes.aggregate(Sum('pl_number'))['pl_number__sum'] or 0
    
    # Dados de performance da empresa
    roa_medio = float(Unidade.objects.aggregate(avg_roa=models.Avg('roa'))['avg_roa'] or 0)
    
    # Dados de áreas
    areas = Area.objects.all()
    areas_data = []
    
    # Para cada área, podemos buscar estatísticas relevantes
    for area in areas:
        # Número de usuários na área
        users_count = CustomUser.objects.filter(area_ref=area).count()
        areas_data.append({
            'nome': area.nome,
            'users_count': users_count,
        })

    return render(request, 'main/home_master.html', {
        'total_unidades': total_unidades,
        'total_assessores': total_assessores,
        'total_clientes': total_clientes,
        'pl_total': pl_total,
        'roa_medio': roa_medio,
        'areas_data': areas_data,
    })

@user_passes_test(lambda u: u.is_master())
def painel_alertas_master(request):
    month = datetime.now().month
    year = datetime.now().year

    # Filtrar usuários por tipo
    # Abordagem alternativa: usar values_list para obter os IDs em vez de combinar querysets
    heads = CustomUser.objects.filter(cargo__in=['head', 'headunidade'])
    area_heads = CustomUser.objects.filter(areas_gerenciadas__isnull=False)
    
    # Combinar os IDs de todos os usuários e depois buscar novamente
    head_ids = list(heads.values_list('id', flat=True))
    area_head_ids = list(area_heads.values_list('id', flat=True))
    
    # Combinando IDs e removendo duplicatas com set()
    all_head_ids = list(set(head_ids + area_head_ids))
    
    # Obter todos os usuários com os IDs combinados
    all_heads = CustomUser.objects.filter(id__in=all_head_ids)
    
    # Apenas assessores para Estatísticas
    assessores = CustomUser.objects.filter(cargo='assessor')

    # Coleta pendências - todos os tipos de heads para Planejado e Executado
    planejado_pendentes = all_heads.exclude(
        id__in=Planejado.objects.filter(month=month, year=year).values_list('user', flat=True)
    )
    executado_pendentes = all_heads.exclude(
        id__in=Executado.objects.filter(month=month, year=year).values_list('user', flat=True)
    )
    
    # Apenas assessores para Estatísticas
    estatisticas_pendentes = assessores.exclude(
        id__in=Estatisticas.objects.filter(month=month, year=year).values_list('user', flat=True)
    )

    context = {
        'planejados_pendentes': planejado_pendentes,
        'executados_pendentes': executado_pendentes,
        'estatisticas_pendentes': estatisticas_pendentes,
        'alertas_duplicados': AlertaDuplicado.objects.all().order_by('-criado_em'),
        'prazo_planejado': get_prazo('Planejado'),
        'prazo_executado': get_prazo('Executado'),
        'prazo_estatisticas': get_prazo('Estatísticas'),
    }

    return render(request, 'main/painel_alertas_master.html', context)

@user_passes_test(lambda u: u.is_master())
def painel_alertas(request):
    alertas = AlertaDuplicado.objects.select_related('assessor').order_by('-criado_em')
    return render(request, 'main/painel_alertas.html', {'alertas': alertas})

def get_prazo(nome_formulario):
    """Retorna o agendamento do mês atual para um determinado formulário."""
    now = datetime.now()
    try:
        return AgendamentoMensal.objects.get(
            nome=nome_formulario,
            mes=now.month,
            ano=now.year
        )
    except AgendamentoMensal.DoesNotExist:
        return None

@user_passes_test(lambda u: u.is_headunidade())
def minhas_unidades(request):
    user = request.user
    
    # Get units managed by this head
    try:
        unidade = Unidade.objects.get(head=user)
        managed_units = [unidade]
    except Unidade.DoesNotExist:
        # As fallback, check user.unidade if direct management relation not found
        if user.unidade:
            managed_units = [user.unidade]
        else:
            managed_units = []
    
    # Enhanced units with real-time data
    enhanced_units = []
    
    for unit in managed_units:
        # Get assessores in this unit
        assessores = CustomUser.objects.filter(unidade=unit, cargo='assessor')
        
        # Get captacoes for assessores in this unit
        captacoes = Captacao.objects.filter(user__in=assessores)
        
        # Calculate PL total and other metrics
        pl_total = sum(parse_br_number(c.pl) for c in captacoes)
        planejado_migracao_total = sum(parse_br_number(c.planejado_migracao) for c in captacoes)
        
        # Get ROA for the unit
        roa = unit.roa
        
        # Calculate client counts by status
        clientes_count = captacoes.count()
        clientes_ativos = captacoes.filter(status='Ativo').count()
        clientes_frios = captacoes.filter(status='Frio').count()
        clientes_mornos = captacoes.filter(status='Morno').count()
        clientes_quentes = captacoes.filter(status='Quente').count()
        
        # Calculate ticket médio
        ticket_medio = (pl_total / clientes_count) if clientes_count > 0 else 0
        
        # Calculate performance percentage
        # Example: Based on goals achieved vs expected at this point in time
        current_month = datetime.now().month
        time_elapsed_percent = (current_month / 12) * 100
        
        # Get planned PL for this unit (from all assessors' Planejado records)
        unit_planejado = float(Planejado.objects.filter(
            user__in=assessores,
            year=datetime.now().year
        ).aggregate(total_planejado=Sum('auc'))['total_planejado'] or 0)
        
        # Calculate percentage of goal achieved
        if unit_planejado > 0:
            pct_achieved = min(100, (pl_total / unit_planejado) * 100)
        else:
            pct_achieved = 0
            
        # Calculate pace (percentage achieved relative to time elapsed)
        pace = (pct_achieved / time_elapsed_percent * 100) if time_elapsed_percent > 0 else 0
        
        # Add enhanced data to the unit
        unit.enhanced_data = {
            'pl_total': format_br_currency(pl_total),
            'assessores_count': assessores.count(),
            'clientes_count': clientes_count,
            'clientes_ativos': clientes_ativos,
            'clientes_frios': clientes_frios,
            'clientes_mornos': clientes_mornos,
            'clientes_quentes': clientes_quentes,
            'ticket_medio': format_br_currency(ticket_medio),
            'performance_percent': int(pct_achieved),
            'planejado': format_br_currency(unit_planejado),
            'pace': int(pace)
        }
        
        enhanced_units.append(unit)
    
    return render(request, 'main/minhas_unidades.html', {'unidades': enhanced_units})

@user_passes_test(lambda u: u.is_master())
def dashboard_unidade(request, slug):
    unidade = get_object_or_404(Unidade, slug=slug)

    # Busca todos os assessores dessa unidade
    assessores = CustomUser.objects.filter(unidade=unidade)
    
    # Busca todas as captações feitas por esses assessores
    captacoes = Captacao.objects.filter(user__in=assessores)

    # Calcular PL total e planejado de migração convertendo os textos
    pl_total = sum(parse_br_number(c.pl) for c in captacoes)
    planejado_migracao_total = sum(parse_br_number(c.planejado_migracao) for c in captacoes)

    # ROA da unidade (definido pelo Master manualmente - para simulação, está fixo)
    roa_unidade = unidade.roa if hasattr(unidade, 'roa') else 2.0  # você pode mover esse valor para o modelo `Unidade`

    # Expectativa de migração em %
    expectativa_migracao = (planejado_migracao_total / pl_total * 100) if pl_total > 0 else 0

    # PL atual e clientes ativos podem ser os mesmos de cima ou você pode usar outro modelo `Cliente` se quiser detalhar mais
    pl_atual = pl_total
    clientes_ativos = captacoes.count()
    ticket_medio = (pl_total / clientes_ativos) if clientes_ativos > 0 else 0

    # Calcular PL projetado baseado no modelo Planejado (AUC)
    current_year = datetime.now().year
    planejado_total = float(Planejado.objects.filter(
        user__in=assessores,
        year=current_year
    ).aggregate(total_planejado=Sum('auc'))['total_planejado'] or 0)
    
    # PL projetado = PL atual + planejado total
    pl_projetado = pl_atual + planejado_total

    # Contar clientes por status
    clientes_frios = captacoes.filter(status='Frio').count()
    clientes_mornos = captacoes.filter(status='Morno').count()
    clientes_quentes = captacoes.filter(status='Quente').count()

    # Buscar objetivo AUC da unidade
    try:
        objetivo_unidade = ObjetivoUnidade.objects.get(unidade=unidade, year=current_year)
        objetivo_auc = objetivo_unidade.objetivo_auc
    except ObjetivoUnidade.DoesNotExist:
        # Se não houver objetivo definido, usar valor padrão
        objetivo_auc = 3200000

    context = {
        'unidade': unidade,
        'horizonte_meses': 12,
        'pl_projetado': format_br_currency(pl_projetado),
        'roa': roa_unidade,
        'objetivo_auc': format_br_currency(objetivo_auc),
        'pl_total': format_br_currency(pl_total),
        'migracao_planejada': format_br_currency(planejado_migracao_total),
        'expectativa_migracao': round(expectativa_migracao, 2),
        'pl_atual': format_br_currency(pl_atual),
        'clientes_ativos': clientes_ativos,
        'clientes_frios': clientes_frios,
        'clientes_mornos': clientes_mornos,
        'clientes_quentes': clientes_quentes,
        'ticket_medio': format_br_currency(ticket_medio),
    }

    return render(request, 'main/dashboard_unidade.html', context)

# Helper functions for number formatting
def format_br_currency(value):
    """Format a number as Brazilian currency (R$ with thousand dots and decimal comma)"""
    if value is None:
        return "R$ 0,00"
        
    # Convert to float if needed
    if not isinstance(value, (int, float, Decimal)):
        try:
            value = float(value)
        except (ValueError, TypeError):
            return "R$ 0,00"
    
    # Format with Brazilian conventions
    integer_part = int(value)
    decimal_part = int(round((value - integer_part) * 100))
    
    # Add thousand separators
    integer_str = ""
    str_value = str(integer_part)
    for i, digit in enumerate(str_value[::-1]):
        if i > 0 and i % 3 == 0:
            integer_str = '.' + integer_str
        integer_str = digit + integer_str
    
    # Format with decimal comma
    return f"R$ {integer_str},{decimal_part:02d}"

def parse_br_number(value):
    """Convert a string with Brazilian number format to a float"""
    if not value:
        return 0.0
    
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    
    # Remove currency symbol and spaces
    value = str(value).replace('R$', '').strip()
    
    # Replace dots (thousand separators) and change comma to decimal point
    value = value.replace('.', '').replace(',', '.')
    
    try:
        # Convert to float and divide by 100 if the number is in the wrong scale
        result = float(value)
        # If the number is very large (likely due to decimal place error), divide by 100
        if result > 1000000:  # If greater than 1 million, it's likely in the wrong scale
            result = result / 100
        return result
    except ValueError:
        return 0.0

# Helper functions for the new KPIs
def get_receita_pj1_from_api():
    """
    Placeholder function to get Receita PJ1 from external API
    Replace this with actual API call implementation
    """
    # TODO: Implement actual API call
    # For now, return a placeholder value
    return 1500000.00  # R$ 1.500.000,00

def get_receita_pj2_from_master():
    """
    Placeholder function to get Receita PJ2 from master user
    You can add a field to CustomUser model to store this value
    """
    # TODO: Add a field to CustomUser model for receita_pj2
    # For now, return a placeholder value
    return 800000.00  # R$ 800.000,00


@login_required
def trocar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # mantém login após mudar a senha
            request.user.primeiro_login = False
            request.user.save()

           
            messages.success(request, 'Senha atualizada com sucesso!')

            return redirect('home')  # ou 'home_head', etc.
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'main/trocar_senha.html', {'form': form})
@csrf_exempt
def remover_popup_sessao(request):
    if request.method == 'POST':
        request.session.pop('exibir_popup_primeiro_login', None)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'erro'}, status=400)

def create_revenue_chart(revenue_data):
    """
    Creates a Plotly chart showing the evolution of revenues over time.
    
    Args:
        revenue_data: List of FinanceHistory objects ordered by date
        
    Returns:
        str: HTML representation of the Plotly chart
    """
    # Sort data by date
    revenue_data = sorted(revenue_data, key=lambda x: (x.year, x.month))
    
    # Prepare data for the chart
    months = [f"{d.month}/{d.year}" for d in revenue_data]
    receita_pj1 = [float(d.receita_pj1) for d in revenue_data]
    receita_pj2 = [float(d.receita_pj2) for d in revenue_data]
    receita_total = [float(d.receita_total) for d in revenue_data]
    receita_pj1_planejado = [float(d.receita_pj1_planejado) for d in revenue_data]
    receita_pj2_planejado = [float(d.receita_pj2_planejado) for d in revenue_data]
    receita_total_planejado = [float(d.receita_total_planejado) for d in revenue_data]
    
    # Create the figure
    fig = go.Figure()
    
    # Add traces for each revenue type
    fig.add_trace(go.Scatter(
        x=months,
        y=receita_pj1,
        mode='lines+markers',
        name='Receita PJ1',
        line=dict(color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=receita_pj1_planejado,
        mode='lines',
        name='PJ1 Planejado',
        line=dict(dash='dash', color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=receita_pj2,
        mode='lines+markers',
        name='Receita PJ2',
        line=dict(color='#ff7f0e')
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=receita_pj2_planejado,
        mode='lines',
        name='PJ2 Planejado',
        line=dict(dash='dash', color='#ff7f0e')
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=receita_total,
        mode='lines+markers',
        name='Receita Total',
        line=dict(color='#2ca02c')
    ))
    
    fig.add_trace(go.Scatter(
        x=months,
        y=receita_total_planejado,
        mode='lines',
        name='Total Planejado',
        line=dict(dash='dash', color='#2ca02c')
    ))
    
    # Update layout
    fig.update_layout(
        title='Evolução da Receita',
        xaxis_title='Mês/Ano',
        yaxis_title='Receita (R$)',
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Convert to HTML
    return opy.plot(fig, auto_open=False, output_type='div')


@user_passes_test(lambda u: u.is_master())
def finance_dashboard(request):
    # Get current month and year
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year

    # Calculate monthly percentage (for pace)
    months_elapsed = current_month
    months_total = 12
    time_elapsed_percentage = (months_elapsed / months_total) * 100

    # Try to get current month's finance history
    try:
        finance_history = FinanceHistory.objects.get(
            month=current_month,
            year=current_year
        )
    except FinanceHistory.DoesNotExist:
        # Create new record with default values
        finance_history = FinanceHistory(
            month=current_month,
            year=current_year
        )
        finance_history.save()

    # Handle form submission
    if request.method == 'POST':
        form = FinanceForm(request.POST, instance=finance_history)
        if form.is_valid():
            finance_history = form.save()
            messages.success(request, 'Valores atualizados com sucesso!')
            return redirect('finance_dashboard')
    else:
        form = FinanceForm(instance=finance_history)

    # Get historical data
    historical_data = FinanceHistory.objects.exclude(
        month=current_month,
        year=current_year
    ).order_by('year', 'month')

    # Calculate KPI metrics
    auc_planejado = float(Planejado.objects.filter(year=current_year).aggregate(Sum('auc'))['auc__sum'] or 0)
    auc_executado = float(Executado.objects.filter(year=current_year).aggregate(Sum('auc'))['auc__sum'] or 0)
    auc_percentual_atingido = (auc_executado / auc_planejado * 100) if auc_planejado > 0 else 0
    auc_pace = (auc_percentual_atingido / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0

    # Get PJ1 revenue from API
    receita_pj1_executado = get_receita_pj1_from_api()
    finance_history.receita_pj1 = Decimal(str(receita_pj1_executado))
    finance_history.save()

    # Calculate percentages and paces
    def calculate_metrics(executado, planejado):
        percentual = (float(executado) / float(planejado) * 100) if planejado > 0 else 0
        pace = (percentual / time_elapsed_percentage * 100) if time_elapsed_percentage > 0 else 0
        return percentual, pace

    # Calculate metrics for each revenue type
    receita_pj1_percentual, receita_pj1_pace = calculate_metrics(
        finance_history.receita_pj1, 
        finance_history.receita_pj1_planejado
    )
    
    receita_pj2_percentual, receita_pj2_pace = calculate_metrics(
        finance_history.receita_pj2, 
        finance_history.receita_pj2_planejado
    )
    
    receita_total_percentual, receita_total_pace = calculate_metrics(
        finance_history.receita_total, 
        finance_history.receita_total_planejado
    )

    # Create revenue evolution chart
    revenue_data = list(historical_data)
    revenue_data.append(finance_history)
    # Sort by date to ensure correct order
    revenue_data.sort(key=lambda x: (x.year, x.month))
    
    # Prepare data for the template
    context = {
        'form': form,
        'historical_data': historical_data,
        'current_data': {
            'auc_planejado': format_br_currency(auc_planejado),
            'auc_executado': format_br_currency(auc_executado),
            'auc_percentual': auc_percentual_atingido,
            'auc_pace': auc_pace,
            
            'receita_pj1_planejado': format_br_currency(finance_history.receita_pj1_planejado),
            'receita_pj1_executado': format_br_currency(finance_history.receita_pj1),
            'receita_pj1_percentual': receita_pj1_percentual,
            'receita_pj1_pace': receita_pj1_pace,
            
            'receita_pj2_planejado': format_br_currency(finance_history.receita_pj2_planejado),
            'receita_pj2_executado': format_br_currency(finance_history.receita_pj2),
            'receita_pj2_percentual': receita_pj2_percentual,
            'receita_pj2_pace': receita_pj2_pace,
            
            'receita_total_planejado': format_br_currency(finance_history.receita_total_planejado),
            'receita_total_executado': format_br_currency(finance_history.receita_total),
            'receita_total_percentual': receita_total_percentual,
            'receita_total_pace': receita_total_pace,
        },
        'revenue_chart': create_revenue_chart(revenue_data)
    }

    return render(request, 'main/finance_dashboard.html', context)


