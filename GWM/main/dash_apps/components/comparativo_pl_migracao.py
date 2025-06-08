from dash import dcc, html, Input, Output
from urllib.parse import parse_qs, urlparse
from ..db import pegar_cliente
from django_plotly_dash import DjangoDash
import plotly.graph_objects as go




###APAGAR DEPOIS




# Mantendo o nome original do app
app = DjangoDash("ComparativoPL")

# Layout
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div([
        html.H3("Gráfico Comparativo PL x Migração", style={
            "textAlign": "center",
            "color": "#FFA500",
            "marginBottom": "20px"
        }),
        dcc.Graph(
            id="grafico-pl-migracao",
            config={"responsive": True},
            style={
                "width": "100%",
                "height": "100%",
                "maxWidth": "100%",    # Sem limite de largura
                "margin": "0 auto",
                "overflow": "visible", # Deixa crescer
            }
        )
    ], style={
        "padding": "10px",
        "height": "auto",        # Permite a altura variar
        "overflow": "visible",   # Sem cortar o gráfico
    })
])

# Callback para atualizar o gráfico
@app.callback(
    Output("grafico-pl-migracao", "figure"),
    Input("url", "href")
)
def atualizar_grafico(href):
    if not href:
        return gerar_figura_vazia("Nenhum parâmetro recebido.")

    query_params = parse_qs(urlparse(href).query)
    nome = query_params.get("nome", [None])[0]
    mes = query_params.get("mes", [None])[0]
    ano = query_params.get("ano", [None])[0]

    if not (nome and mes and ano):
        return gerar_figura_vazia("Parâmetros inválidos ou incompletos.")

    df = pegar_cliente()

    df["nome"] = df["nome"].str.strip()
    nome = nome.strip()

    try:
        mes = int(mes)
        ano = int(ano)
    except ValueError:
        return gerar_figura_vazia("Mês ou ano inválidos.")

    df_filtrado = df[
        (df["nome"] == nome) &
        (df["mes"] == mes) &
        (df["ano"] == ano)
    ]

    if df_filtrado.empty:
        return gerar_figura_vazia("Sem dados para os filtros selecionados.")

    pl_valor = df_filtrado["pl_total"].sum()
    migracao_valor = df_filtrado["planejado_migracao"].sum()

    fig = go.Figure(
        data=[
            go.Bar(
                x=["PL Total", "Migração Planejada"],
                y=[pl_valor, migracao_valor],
                text=[f"R${pl_valor:,.0f}", f"R${migracao_valor:,.0f}"],
                textposition="auto",
                marker=dict(
                    color=["#00BFFF", "#FFA500"],
                    line=dict(color="white", width=2),
                ),
                width=0.5,
            )
        ]
    )

    fig.update_layout(
        title={
            'text': f"{nome} - {mes}/{ano}",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=22, color="#333")
        },
        xaxis_title="Categoria",
        yaxis_title="Valor (R$)",
        yaxis=dict(showgrid=True, gridcolor="lightgrey"),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#f9f9f9",
        margin=dict(l=30, r=30, t=60, b=40),
        autosize=True,
        font=dict(family="Arial", size=14, color="#333"),
    )

    return fig

# Função para gráfico vazio
def gerar_figura_vazia(mensagem):
    fig = go.Figure()
    fig.update_layout(
        title={'text': mensagem, 'x': 0.5},
        xaxis={"visible": False},
        yaxis={"visible": False},
        plot_bgcolor="#f0f0f0",
        paper_bgcolor="#f0f0f0",
        annotations=[{
            'text': mensagem,
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 20, 'color': 'gray'},
            'x': 0.5,
            'y': 0.5
        }]
    )
    return fig
