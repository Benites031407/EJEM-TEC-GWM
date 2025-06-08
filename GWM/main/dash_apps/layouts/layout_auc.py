from dash import html, dcc
from dash_apps.components.filtros_auc import filtrar_auc_por_mes_ano
from dash_apps.components.compara_auc import gerar_grafico_auc
from dash import Input, Output, callback

# Pré-carregar dados
from main.db import pegar_consolidado
df = pegar_consolidado()
nomes = sorted(df["nome"].unique())
meses = sorted(df["mes"].unique())
anos = sorted(df["ano"].unique())

layout_auc = html.Div([
    html.H3("Comparativo AUC", style={'color': '#FF9F00'}),

    dcc.Dropdown(
        id='dropdown-nome',
        options=[{'label': n, 'value': n} for n in nomes],
        value=nomes[0],
        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
    ),
    dcc.Dropdown(
        id='dropdown-mes1',
        options=[{'label': m, 'value': m} for m in meses],
        value=meses[0],
        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
    ),
    dcc.Dropdown(
        id='dropdown-ano1',
        options=[{'label': a, 'value': a} for a in anos],
        value=anos[0],
        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
    ),
    dcc.Dropdown(
        id='dropdown-mes2',
        options=[{'label': m, 'value': m} for m in meses],
        value=meses[-1],
        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
    ),
    dcc.Dropdown(
        id='dropdown-ano2',
        options=[{'label': a, 'value': a} for a in anos],
        value=anos[-1],
        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
    ),

    dcc.Graph(id='grafico-comparativo')
])

@callback(
    Output('grafico-comparativo', 'figure'),
    Input('dropdown-nome', 'value'),
    Input('dropdown-mes1', 'value'),
    Input('dropdown-ano1', 'value'),
    Input('dropdown-mes2', 'value'),
    Input('dropdown-ano2', 'value')
)
def atualizar_grafico_auc(nome, mes1, ano1, mes2, ano2):
    dados1 = filtrar_auc_por_mes_ano(mes1, ano1)
    dados2 = filtrar_auc_por_mes_ano(mes2, ano2)

    dados1 = dados1[dados1["nome"] == nome]
    dados2 = dados2[dados2["nome"] == nome]

    return gerar_grafico_auc(nome, dados1, dados2, mes1, ano1, mes2, ano2)
