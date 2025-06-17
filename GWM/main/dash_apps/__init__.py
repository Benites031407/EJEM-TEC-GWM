from .components.evolucao_entrevistas import app as EvolucaoEntrevistasApp
from .components.evolucao_contratacoes import app as EvolucaoContratacoesApp
from .components.evolucao_reunioes import app as EvolucaoReunioesApp
from .components.evolucao_volume import app as EvolucaoVolumeApp

# Register all apps here
__all__ = [
    'EvolucaoEntrevistasApp',
    'EvolucaoContratacoesApp',
    'EvolucaoReunioesApp',
    'EvolucaoVolumeApp'
]
