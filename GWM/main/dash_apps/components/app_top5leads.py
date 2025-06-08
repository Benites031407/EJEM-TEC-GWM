from ..db import pegar_cliente

from django_plotly_dash import DjangoDash
import dash
import plotly.graph_objects as go
from dash import html, dcc


def top5_leads_component():
    df = pegar_cliente()
    df_top5 = df.sort_values(by='pl_total', ascending=False).head(5)

    fig = go.Figure(data=[
        go.Bar(
            x=df_top5['nome'],
            y=df_top5['pl_total'],
            marker_color='royalblue'
        )
    ])

    fig.update_layout(
        title="Top 5 Clientes por PL Total",
        xaxis_title="Cliente",
        yaxis_title="PL Total",
        template="plotly_white"
    )

    
    return html.Div(
        dcc.Graph(figure=fig, id="grafico-top5-clientes")
    )


# Nome único pro app
app = DjangoDash("Top5LeadsApp")

# componentes/grafico_top5_leads.py
# Define o layout usando o componente
app.layout = top5_leads_component()
# app.layout =  html.Div("è isso aqui")