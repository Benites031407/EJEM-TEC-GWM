# main/utils.py

from datetime import datetime
from django.db.models import Q
from .models import CustomUser, Unidade, Area

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

def mes_em_portugues(month_number):
    return MONTHS_PT.get(month_number, 'Mês inválido')


def data_formatada_em_portugues(data: datetime) -> str:
    """
    Retorna data no formato '17 de Abril de 2025'
    """
    dia = data.day
    mes = mes_em_portugues(data.month)
    ano = data.year
    return f"{dia} de {mes} de {ano}"

def get_all_unit_heads():
    """
    Returns all users with the role of Unit Head
    """
    return CustomUser.objects.filter(cargo='headunidade')

def get_all_area_heads():
    """
    Returns all users with the role of Area Head
    """
    return CustomUser.objects.filter(cargo='head')

def get_all_advisors():
    """
    Returns all users with the role of Advisor
    """
    return CustomUser.objects.filter(cargo='assessor')

def get_unit_heads_without_unit():
    """
    Returns all Unit Heads that are not assigned to a unit
    """
    assigned_unit_heads = Unidade.objects.exclude(head=None).values_list('head', flat=True)
    return CustomUser.objects.filter(cargo='headunidade').exclude(id__in=assigned_unit_heads)

def get_area_heads_without_area():
    """
    Returns all Area Heads that are not assigned as head of any area
    """
    assigned_area_heads = Area.objects.exclude(head=None).values_list('head', flat=True).distinct()
    return CustomUser.objects.filter(cargo='head').exclude(id__in=assigned_area_heads)

def get_advisors_without_area():
    """
    Returns all Advisors that are not assigned to an area
    """
    return CustomUser.objects.filter(cargo='assessor', area_ref=None)

def get_team_hierarchy(supervisor):
    """
    Returns a dictionary representing the hierarchical team under a supervisor
    """
    if not supervisor:
        return {}
    
    # Get direct subordinates
    subordinates = CustomUser.objects.filter(supervisor=supervisor)
    
    # Build the hierarchy
    hierarchy = {
        'supervisor': {
            'id': supervisor.id,
            'name': supervisor.get_full_name() or supervisor.username,
            'cargo': supervisor.get_cargo_display(),
            'unidade': supervisor.unidade.nome if supervisor.unidade else None,
            'area': supervisor.area_ref.nome if supervisor.area_ref else None,
        },
        'subordinates': []
    }
    
    # Add each subordinate and their subordinates recursively
    for subordinate in subordinates:
        sub_hierarchy = get_team_hierarchy(subordinate)
        hierarchy['subordinates'].append(sub_hierarchy)
    
    return hierarchy

def get_unit_structure(unidade):
    """
    Returns a complete structure of a unit with its areas and members
    """
    if not unidade:
        return {}
    
    # Get the unit head
    unit_head = unidade.head
    
    # Get all users in the unit
    members = CustomUser.objects.filter(unidade=unidade)
    
    # Group members by area
    area_members = {}
    for member in members:
        if member.area_ref:
            if member.area_ref.id not in area_members:
                area_members[member.area_ref.id] = {
                    'area': member.area_ref,
                    'advisors': []
                }
            if member.cargo == 'assessor':
                area_members[member.area_ref.id]['advisors'].append(member)
    
    # Structure for the unit
    structure = {
        'unit': {
            'id': unidade.id,
            'name': unidade.nome,
            'roa': unidade.roa,
        },
        'unit_head': {
            'id': unit_head.id,
            'name': unit_head.get_full_name() or unit_head.username,
        } if unit_head else None,
        'areas': []
    }
    
    # Add each area with its head and advisors
    for area_id, data in area_members.items():
        area = data['area']
        advisors = data['advisors']
        
        area_structure = {
            'area': {
                'id': area.id,
                'name': area.nome,
            },
            'area_head': {
                'id': area.head.id,
                'name': area.head.get_full_name() or area.head.username,
            } if area.head else None,
            'advisors': [
                {
                    'id': advisor.id,
                    'name': advisor.get_full_name() or advisor.username,
                }
                for advisor in advisors
            ]
        }
        
        structure['areas'].append(area_structure)
    
    return structure
