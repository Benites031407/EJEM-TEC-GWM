from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
from ..db import pegar_consolidado, pegar_meta_anual_mais_recente

app = DjangoDash("AUCApp", suppress_callback_exceptions=True)

# Carrega os dados
df_auc_completo = pegar_consolidado()

# Valores únicos
nomes_auc = sorted(df_auc_completo["nome"].unique())
anos_auc = sorted([int(a) for a in df_auc_completo["ano"].unique()])
meses_auc = sorted([int(m) for m in df_auc_completo["mes"].unique()])

dropdown_style = {
    "width": "100%",
    "minHeight": "50px",
    "fontSize": "16px",
    "padding": "6px"
}

# Layout atualizado
app.layout = html.Div([
    html.H3("Comparativo de AUC", style={"textAlign": "center", "color": "black"}),

    html.Div([
        html.Div([
            dcc.Dropdown(
                id="auc-nome",
                options=[{"label": n, "value": n} for n in nomes_auc],
                placeholder="Nome",
                clearable=False,
                style=dropdown_style
            )
        ], style={"flex": "1", "margin": "10px"}),

        html.Div([
            dcc.Dropdown(
                id="auc-ano",
                options=[{"label": str(a), "value": a} for a in anos_auc],
                placeholder="Ano",
                clearable=False,
                style=dropdown_style
            )
        ], style={"flex": "1", "margin": "10px"}),

        html.Div([
            html.Label("Intervalo de Meses", style={"fontSize": "14px", "marginBottom": "6px"}),
            dcc.RangeSlider(
                id="auc-meses",
                min=min(meses_auc),
                max=max(meses_auc),
                step=1,
                marks={m: str(m) for m in meses_auc},
                value=[min(meses_auc), max(meses_auc)],
                allowCross=False
            )
        ], style={"flex": "1", "margin": "10px", "paddingTop": "10px"})
    ], style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap"}),

    html.Div([
        dcc.Graph(
            id="auc-graph",
            config={"responsive": True},
            style={"width": "100%", "height": "100%"}
        )
    ], style={"width": "100%", "maxWidth": "1000px", "margin": "0 auto"})
])

@app.callback(
    Output("auc-graph", "figure"),
    [
        Input("auc-nome", "value"),
        Input("auc-ano", "value"),
        Input("auc-meses", "value")
    ]
)
def atualizar_grafico_auc(nome, ano, intervalo_meses):
    if not nome or not ano or not intervalo_meses:
        return go.Figure().update_layout(title="Selecione todos os filtros para visualizar os dados.")

    mes_inicio, mes_fim = intervalo_meses

    df_filtrado = df_auc_completo[
        (df_auc_completo["nome"] == nome) &
        (df_auc_completo["nome_tipo"] == "auc") &
        (df_auc_completo["ano"] == ano) &
        (df_auc_completo["mes"] >= mes_inicio) &
        (df_auc_completo["mes"] <= mes_fim)
    ].sort_values("mes")

    if df_filtrado.empty:
        return go.Figure().update_layout(title="Nenhum dado encontrado para os filtros selecionados.")

    # Conversões seguras
    df_filtrado["planejado"] = pd.to_numeric(df_filtrado["planejado"], errors="coerce")
    df_filtrado["realizado"] = pd.to_numeric(df_filtrado["realizado"], errors="coerce")

    nomes_meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    x_labels = [nomes_meses[m - 1] for m in df_filtrado["mes"]]

    planejado_vals = df_filtrado["planejado"].tolist()
    realizado_vals = df_filtrado["realizado"].tolist()

    meta_anual = pegar_meta_anual_mais_recente() or 0
    y_max = max(max(planejado_vals + realizado_vals + [meta_anual]), 10) * 1.2

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_labels,
        y=planejado_vals,
        mode='lines+markers+text',
        name='Planejado',
        line=dict(color='#2ca02c', width=2),
        text=[f"{v:.0f}" if pd.notna(v) else "" for v in planejado_vals],
        textposition='top center'
    ))

    fig.add_trace(go.Scatter(
        x=x_labels,
        y=realizado_vals,
        mode='lines+markers+text',
        name='Realizado',
        line=dict(color='#ff7f0e', width=2),
        text=[f"{v:.0f}" if pd.notna(v) else "" for v in realizado_vals],
        textposition='bottom center'
    ))

    fig.add_trace(go.Scatter(
        x=x_labels,
        y=[meta_anual] * len(x_labels),
        mode='lines',
        name='Meta Anual',
        line=dict(color='#1f77b4', width=2, dash='dash')
    ))

    fig.update_layout(
        title=dict(
            text=f"Comparativo de AUC - {nome}<br><sup>{x_labels[0]} a {x_labels[-1]}/{ano}</sup>",
            x=0.5,
            xanchor="center",
            font=dict(size=20)
        ),
        template='plotly_white',
        plot_bgcolor='rgba(240,240,240,0.6)',
        paper_bgcolor='rgba(240,240,240,0.9)',
        font=dict(color='#333', size=14),
        xaxis=dict(title="Meses", tickfont=dict(size=13), showgrid=False),
        yaxis=dict(title="Valores", tickfont=dict(size=13), range=[0, y_max], gridcolor="rgba(200,200,200,0.4)"),
        margin=dict(l=40, r=40, t=100, b=50),
        autosize=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=13)
        )
    )

    return fig
