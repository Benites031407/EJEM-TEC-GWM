from dash import dcc, html, Input, Output
from ..db import pegar_cliente
from django_plotly_dash import DjangoDash
import plotly.graph_objects as go

app = DjangoDash("CallBackComparativoPL")

# Estilo unificado para os dropdowns
dropdown_style = {
    "width": "100%",
    "minHeight": "50px",
    "fontSize": "16px",
    "padding": "6px"
}

# Layout do app
def layout():
    df = pegar_cliente()

    nome_opcoes = [{"label": nome, "value": nome} for nome in sorted(df["nome"].unique())]
    mes_opcoes = [{"label": str(m), "value": m} for m in sorted(df["mes"].unique())]
    ano_opcoes = [{"label": str(a), "value": a} for a in sorted(df["ano"].unique())]

    return html.Div([
        html.H3("Comparativo PL x Migração", style={"textAlign": "center", "color": "black"}),

        # Grid com os filtros
        html.Div([
            dcc.Dropdown(
                id="dropdown-nome",
                options=nome_opcoes,
                placeholder="Nome",
                clearable=False,
                style=dropdown_style
            ),
            dcc.Dropdown(
                id="dropdown-mes",
                options=mes_opcoes,
                placeholder="Mês",
                clearable=False,
                style=dropdown_style
            ),
            dcc.Dropdown(
                id="dropdown-ano",
                options=ano_opcoes,
                placeholder="Ano",
                clearable=False,
                style=dropdown_style
            ),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "1fr 0.5fr 0.5fr",
            "gap": "16px",
            "width": "100%",
            "maxWidth": "1000px",
            "margin": "10px auto",
            "padding": "10px 0",
        }),

        # Gráfico
        html.Div([
            dcc.Graph(
                id="grafico-pl-migracao",
                config={"responsive": True},
                style={
                    "width": "100% !important",
                    "height": "100% !important",
                    "min-width": "0 !important",
                    "min-height": "0 !important",
                }
            )
        ], style={
            "width": "100%",
            "height": "300px",
            "maxHeight": "300px",
            "maxWidth": "1000px",
            "margin": "5px auto",
            "padding": "2px",
            "overflow": "hidden",
            "display": "flex",
            "flexDirection": "column",
            "flex-grow": 1,
        }),
    ], style={
        "display": "flex",
        "flexDirection": "column",
        "alignItems": "stretch",
        "width": "100%",
        "maxWidth": "1000px",
        "margin": "0 auto",
        "padding": "2px",
        "overflowX": "hidden",
        "flex-grow": 1,
    })

app.layout = layout()

@app.callback(
    Output("grafico-pl-migracao", "figure"),
    Input("dropdown-nome", "value"),
    Input("dropdown-mes", "value"),
    Input("dropdown-ano", "value")
)
def atualizar_grafico(nome, mes, ano):
    if not (nome and mes and ano):
        return gerar_figura_vazia("Selecione todos os filtros.")

    try:
        mes = int(mes)
        ano = int(ano)
    except ValueError:
        return gerar_figura_vazia("Mês ou ano inválidos.")

    df = pegar_cliente()
    df["nome"] = df["nome"].str.strip()
    nome = nome.strip()

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
        data=[go.Bar(
            x=["PL Total", "Migração Planejada"],
            y=[pl_valor, migracao_valor],
            marker=dict(
                color=["#808080", "#00A6CB"],
                line=dict(color="white", width=0.5)
            ),
            width=0.5,
        )]
    )

    fig.update_layout(
        title={
            'text': "",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=6, color="#333")
        },
        xaxis_title="",
        yaxis_title="",
        yaxis=dict(showgrid=True, gridcolor="lightgrey", tickfont=dict(size=6)),
        xaxis=dict(tickfont=dict(size=6)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=2, r=2, t=2, b=2),
        autosize=True,
        font=dict(family="Arial", size=6, color="#333"),
    )

    return fig

def gerar_figura_vazia(mensagem):
    fig = go.Figure()
    fig.update_layout(
        title={'text': mensagem, 'x': 0.5, 'font': {'size': 8}},
        xaxis={"visible": False},
        yaxis={"visible": False},
        plot_bgcolor="#f0f0f0",
        paper_bgcolor="#f0f0f0",
        annotations=[{
            'text': mensagem,
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 8, 'color': 'gray'},
            'x': 0.5,
            'y': 0.5
        }]
    )
    return fig
    