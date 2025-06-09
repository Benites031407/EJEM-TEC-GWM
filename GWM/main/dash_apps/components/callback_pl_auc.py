from dash import dcc, html, Input, Output
from ..db import pegar_captacao
from django_plotly_dash import DjangoDash
import plotly.graph_objects as go

app = DjangoDash("CallBackComparativoPL")

dropdown_style = {
    "width": "100%",
    "minHeight": "50px",
    "fontSize": "16px",
    "padding": "6px"
}

def layout():
    df = pegar_captacao()

    nome_opcoes = [{"label": nome, "value": nome} for nome in sorted(df["nome"].unique())]
    ano_opcoes = [{"label": str(a), "value": a} for a in sorted(df["year"].unique())]

    return html.Div([
        html.H3("Comparativo PL x Migração", style={"textAlign": "center", "color": "black"}),

        html.Div([
            dcc.Dropdown(
                id="dropdown-nome",
                options=nome_opcoes,
                placeholder="Nome",
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
            "gridTemplateColumns": "1fr 1fr",
            "gap": "16px",
            "width": "100%",
            "maxWidth": "1000px",
            "margin": "10px auto",
            "padding": "10px 0",
        }),

        html.Div([
            html.Label("Intervalo de Meses", style={"fontSize": "14px", "marginBottom": "4px"}),
            dcc.RangeSlider(
                id="range-slider-mes",
                min=1,
                max=12,
                step=1,
                value=[1, 12],
                marks={i: str(i) for i in range(1, 13)},
                allowCross=False,
                tooltip={"always_visible": True}
            ),
        ], style={
            "width": "90%",
            "maxWidth": "800px",
            "margin": "0 auto 20px auto"
        }),

        html.Div([
            dcc.Graph(
                id="grafico-pl-migracao",
                config={"responsive": True},
                style={"width": "100%", "height": "100%"}
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
    Input("range-slider-mes", "value"),
    Input("dropdown-ano", "value")
)
def atualizar_grafico(nome, range_meses, ano):
    if not (nome and range_meses and ano):
        return gerar_figura_vazia("Selecione todos os filtros.")

    try:
        mes_inicial, mes_final = map(int, range_meses)
        ano = int(ano)
    except ValueError:
        return gerar_figura_vazia("Filtros inválidos.")

    df = pegar_captacao()
    df["nome"] = df["nome"].str.strip()
    nome = nome.strip()

    df_filtrado = df[
        (df["nome"] == nome) &
        (df["year"] == ano) &
        (df["month"] >= mes_inicial) &
        (df["month"] <= mes_final)
    ]

    if df_filtrado.empty:
        return gerar_figura_vazia("Sem dados para os filtros selecionados.")

    pl_valor = df_filtrado["pl"].sum()
    migracao_valor = df_filtrado["planejado_migracao"].sum()

    fig = go.Figure(data=[
        go.Bar(
            x=["PL Total", "Migração Planejada"],
            y=[pl_valor, migracao_valor],
            marker=dict(color=["#808080", "#00A6CB"]),
            width=0.5
        )
    ])

    fig.update_layout(
        yaxis=dict(
            title="Valores",
            showgrid=True,
            gridcolor="lightgrey",
            tickfont=dict(size=10)
        ),
        xaxis=dict(tickfont=dict(size=10)),
        title={"text": "", "x": 0.5, "xanchor": "center"},
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=2, r=2, t=2, b=2),
        autosize=True,
        font=dict(family="Arial", size=10, color="#333"),
    )

    return fig

def gerar_figura_vazia(mensagem):
    fig = go.Figure()
    fig.update_layout(
        title={'text': mensagem, 'x': 0.5, 'font': {'size': 10}},
        xaxis={"visible": False},
        yaxis={"visible": False},
        plot_bgcolor="#f0f0f0",
        paper_bgcolor="#f0f0f0",
        annotations=[{
            'text': mensagem,
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 10, 'color': 'gray'},
            'x': 0.5,
            'y': 0.5
        }]
    )
    return fig
