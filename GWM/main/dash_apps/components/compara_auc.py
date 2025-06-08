from dash import html, dcc, Input, Output, callback
from dash_apps.components.auc_logic import filtrar_auc_por_mes_ano, gerar_grafico_auc
from dash_apps.db import pegar_consolidado

#LAYOUT + CALLBACKS AUC
# Carregando dados iniciais
df = pegar_consolidado()
nomes = sorted(df["nome"].unique())
meses = sorted(df["mes"].unique())
anos = sorted(df["ano"].unique())

# Layout para o AUC com os filtros e o gráfico
def auc_component(nomes, meses, anos):
    return html.Div([
        html.H2("Gráfico Comparativo de AUC", style={"textAlign": "center", "color": "#FF9F00"}),

        # Dropdown para seleção de nome
        dcc.Dropdown(
            id="auc-nome",
            options=[{"label": n, "value": n} for n in nomes],
            value=nomes[0],  # Valor padrão
            style={"backgroundColor": "#1e1e1e", "color": "white"}
        ),

        # Filtros para Mês e Ano 1
        html.Div([
            html.Div([  # Mês 1 e Ano 1
                html.Label("Mês 1"),
                dcc.Dropdown(
                    id="auc-mes1",
                    options=[{"label": m, "value": m} for m in meses],
                    value=meses[0],
                    style={'backgroundColor': '#2b2b2b', 'color': 'white'}
                ),
                html.Label("Ano 1"),
                dcc.Dropdown(
                    id="auc-ano1",
                    options=[{"label": a, "value": a} for a in anos],
                    value=anos[0],
                    style={'backgroundColor': '#2b2b2b', 'color': 'white'}
                ),
            ], style={'width': '45%', 'display': 'inline-block'}),

            html.Div([  # Mês 2 e Ano 2
                html.Label("Mês 2"),
                dcc.Dropdown(
                    id="auc-mes2",
                    options=[{"label": m, "value": m} for m in meses],
                    value=meses[1] if len(meses) > 1 else meses[0],
                    style={'backgroundColor': '#2b2b2b', 'color': 'white'}
                ),
                html.Label("Ano 2"),
                dcc.Dropdown(
                    id="auc-ano2",
                    options=[{"label": a, "value": a} for a in anos],
                    value=anos[1] if len(anos) > 1 else anos[0],
                    style={'backgroundColor': '#2b2b2b', 'color': 'white'}
                ),
            ], style={'width': '45%', 'display': 'inline-block', 'marginLeft': '5%'}),
        ], style={'marginBottom': '40px'}),

        # Gráfico onde o AUC será exibido
        dcc.Graph(id="auc-graph")
    ])

# Callback para atualizar o gráfico AUC
@callback(
    Output("auc-graph", "figure"),
    Input("auc-nome", "value"),
    Input("auc-mes1", "value"),
    Input("auc-ano1", "value"),
    Input("auc-mes2", "value"),
    Input("auc-ano2", "value"),
)
def atualizar_auc(nome, mes1, ano1, mes2, ano2):
    # Filtra os dados de AUC com base nos filtros selecionados
    df1 = filtrar_auc_por_mes_ano(mes1, ano1, nome)
    df2 = filtrar_auc_por_mes_ano(mes2, ano2, nome)
    
    # Gera o gráfico AUC
    return gerar_grafico_auc(nome, df1, df2, mes1, ano1, mes2, ano2)

