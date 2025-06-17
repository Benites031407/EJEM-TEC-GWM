from .evolucao_base import create_evolution_app

app = create_evolution_app(
    app_name="EvolucaoContratacoesApp",
    metric_name="contratacoes",
    title="Evolução de Contratações",
    y_axis_title="Quantidade de Contratações"
) 