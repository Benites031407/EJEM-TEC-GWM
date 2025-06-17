from .evolucao_base import create_evolution_app

app = create_evolution_app(
    app_name="EvolucaoReunioesApp",
    metric_name="reunioes",
    title="Evolução de Reuniões",
    y_axis_title="Quantidade de Reuniões"
) 