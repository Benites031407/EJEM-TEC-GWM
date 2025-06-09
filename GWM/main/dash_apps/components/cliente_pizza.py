from ..db import pegar_captacao
from django_plotly_dash import DjangoDash
import plotly.express as px
from dash import html, dcc, Input, Output


def gerar_grafico(df):
    if df.empty:
        return {
            "data": [],
            "layout": {"title": "Sem dados para exibir."}
        }

    agrupado = df.groupby("origem").size().reset_index(name='quantidade')

    fig = px.pie(
        agrupado,
        names="origem",
        values="quantidade",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu
    )

    fig.update_traces(
        textinfo="percent",
        textfont_size=16,
        hoverinfo="label+value+percent",
        hovertemplate="%{label}<br>Qtd: %{value}<br>Porcentagem: %{percent}",
    )

    fig.update_layout(
        title="Distribuição de Origem dos Clientes",
        title_font_size=24,
        title_x=0.5,
        paper_bgcolor="white",
        font=dict(color="black"),
        margin=dict(t=60, b=30, l=30, r=30)
    )

    return fig


# Criando o app Dash
app = DjangoDash("grafico-origem-clientes-pizza")

app.layout = html.Div([
    dcc.Interval(id="interval-update", interval=10*1000, n_intervals=0),  # 10 segundos
    dcc.Graph(id="grafico-origem-clientes")
])


@app.callback(
    Output("grafico-origem-clientes", "figure"),
    Input("interval-update", "n_intervals")
)
def atualizar_grafico(n):
    df = pegar_captacao()
    return gerar_grafico(df)