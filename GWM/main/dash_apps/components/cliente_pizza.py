from ..db import pegar_captacao
from django_plotly_dash import DjangoDash
import plotly.express as px
from dash import html, dcc


def grafico_origem_clientes_component():
    df = pegar_captacao()

    if df.empty:
        return html.Div("Sem dados para exibir.")

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

    return html.Div([
        dcc.Graph(figure=fig, id="grafico-origem-clientes")
    ])


app = DjangoDash("grafico-origem-clientes-pizza")

# componentes/grafico_top5_leads.py
# Define o layout usando o componente
app.layout = grafico_origem_clientes_component()
# app.layout =  html.Div("è isso aqui")