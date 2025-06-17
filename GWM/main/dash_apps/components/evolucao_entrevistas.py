from django_plotly_dash import DjangoDash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
from ..db import pegar_planejado
from ..db import pegar_realizado

# Instancia o app
app = DjangoDash("EvolucaoEntrevistasApp", suppress_callback_exceptions=True)

# Carrega os dados
df_planejado = pegar_planejado()
df_executado = pegar_realizado()

# Verifica se os dados foram carregados corretamente
if df_planejado is None or df_executado is None or df_planejado.empty or df_executado.empty:
    raise ValueError("Erro ao carregar dados. Verifique a conexão com o banco ou a consulta SQL.")

# Definindo os filtros disponíveis
anos = sorted([int(a) for a in df_planejado["year"].unique()])
meses = sorted([int(m) for m in df_planejado["month"].unique()])

# Estilo dos dropdowns
dropdown_style = {
    "width": "100%",
    "minHeight": "50px",
    "fontSize": "16px",
    "padding": "6px"
}

# Função para formatar os números nos gráficos
def formatar_numero(valor):
    if pd.isna(valor):
        return ""
    if abs(valor) >= 1_000_000:
        return f"{valor / 1_000_000:.1f}M"
    elif abs(valor) >= 1_000:
        return f"{valor / 1_000:.1f}k"
    else:
        return f"{valor:.0f}"

# Layout do app
app.layout = html.Div([
    html.H3("Evolução de Entrevistas", style={"textAlign": "center", "color": "black"}),

    html.Div([
        html.Div([
            dcc.Dropdown(
                id="entrevistas-ano",
                options=[{"label": str(ano), "value": int(ano)} for ano in anos],
                placeholder="Ano",
                clearable=False,
                style=dropdown_style
            )
        ], style={"flex": "1", "margin": "10px"}),

        html.Div([
            html.Label("Intervalo de Meses", style={"fontSize": "14px", "marginBottom": "6px"}),
            dcc.RangeSlider(
                id="entrevistas-meses",
                min=int(min(meses)),
                max=int(max(meses)),
                step=1,
                marks={int(m): str(int(m)) for m in meses},
                value=[int(min(meses)), int(max(meses))],
                allowCross=False
            )
        ], style={"flex": "1", "margin": "10px", "paddingTop": "10px"})
    ], style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap"}),

    html.Div([
        dcc.Graph(
            id="entrevistas-graph",
            config={"responsive": True},
            style={"width": "100%", "height": "100%"}
        )
    ], style={"width": "100%", "maxWidth": "1000px", "margin": "0 auto"})
])

# Callback para atualizar o gráfico
@app.callback(
    Output("entrevistas-graph", "figure"),
    [
        Input("entrevistas-ano", "value"),
        Input("entrevistas-meses", "value")
    ]
)
def atualizar_grafico(ano, intervalo_meses):
    if not ano or not intervalo_meses:
        return go.Figure().update_layout(
            title="Selecione todos os filtros para visualizar os dados."
        )

    mes_inicio, mes_fim = map(int, intervalo_meses)

    # Filtra os dados de planejado
    df_plan = df_planejado[
        (df_planejado["year"] == ano) &
        (df_planejado["month"] >= mes_inicio) &
        (df_planejado["month"] <= mes_fim)
    ][["year", "month", "entrevistas"]].rename(columns={"entrevistas": "planejado"})

    # Filtra os dados de realizado
    df_real = df_executado[
        (df_executado["year"] == ano) &
        (df_executado["month"] >= mes_inicio) &
        (df_executado["month"] <= mes_fim)
    ][["year", "month", "entrevistas"]].rename(columns={"entrevistas": "realizado"})

    # Merge dos dados
    df = pd.merge(df_plan, df_real, on=["year", "month"], how="outer").sort_values("month")

    if df.empty:
        return go.Figure().update_layout(
            title="Nenhum dado encontrado para os filtros selecionados."
        )

    # Calcula % atingido e pace
    df["planejado"] = pd.to_numeric(df["planejado"], errors="coerce")
    df["realizado"] = pd.to_numeric(df["realizado"], errors="coerce")
    df["porcentagem_atingido"] = (df["realizado"] / df["planejado"]) * 100
    df["pace"] = df["porcentagem_atingido"] / 12

    nomes_meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                  "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    x_labels = [nomes_meses[int(m) - 1] for m in df["month"]]

    max_valor = max(df["planejado"].max(), df["realizado"].max())
    y_max = max_valor * 1.4 if max_valor > 0 else 10

    fig = go.Figure()

    planejado_vals = df["planejado"].tolist()
    fig.add_trace(go.Bar(
        x=x_labels,
        y=planejado_vals,
        name="Planejado",
        marker_color="#00587A",
        text=[formatar_numero(v) for v in planejado_vals],
        textposition='outside',
        cliponaxis=False,
        yaxis='y',
        orientation='v',
        hovertemplate='<b>%{fullData.name}</b><br>Mês: %{x}<br>Valor: %{y}<extra></extra>'
    ))

    realizado_vals = df["realizado"].tolist()
    fig.add_trace(go.Bar(
        x=x_labels,
        y=realizado_vals,
        name="Realizado",
        marker_color="#506F4D",
        text=[formatar_numero(v) for v in realizado_vals],
        textposition='outside',
        cliponaxis=False,
        yaxis='y',
        orientation='v',
        hovertemplate='<b>%{fullData.name}</b><br>Mês: %{x}<br>Valor: %{y}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=x_labels,
        y=[v * 100 if v <= 1 else v for v in df["porcentagem_atingido"]],
        name="% Atingido",
        mode="lines+markers+text",
        text=[f"{(v * 100 if v <= 1 else v):.1f}%" if pd.notna(v) else "" for v in df["porcentagem_atingido"]],
        textposition="top center",
        cliponaxis=False,
        yaxis='y2',
        line=dict(color="#1E1E1E", width=2)
    ))

    fig.add_trace(go.Scatter(
        x=x_labels,
        y=[v * 100 if v <= 1 else v for v in df["pace"]],
        name="Pace",
        mode="lines+markers+text",
        text=[f"{(v * 100 if v <= 1 else v):.1f}%" if pd.notna(v) else "" for v in df["pace"]],
        textposition="top center",
        textfont=dict(size=16, color="#ffffff", family="Arial Bold"),
        cliponaxis=False,
        yaxis='y2',
        line=dict(color="#ffffff", width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=dict(
            text=f"Evolução de Entrevistas<br><sup>{x_labels[0]} a {x_labels[-1]}/{ano}</sup>",
            x=0.5,
            xanchor="center",
            font=dict(size=20, color="#222222")
        ),
        template='plotly',
        plot_bgcolor='rgba(240,240,240,0.6)',
        paper_bgcolor='rgba(240,240,240,0.9)',
        font=dict(color='#333', size=14),
        xaxis=dict(title="Meses", tickfont=dict(size=13), showgrid=False, zeroline=False),
        yaxis=dict(
            title="Quantidade de Entrevistas",
            tickfont=dict(size=13),
            gridcolor="rgba(200,200,200,0.5)",
            range=[0, y_max],
            tickformat=",~s"
        ),
        yaxis2=dict(title="Percentuais", overlaying='y', side='right', tickfont=dict(size=13), range=[0, 100], showgrid=False),
        margin=dict(l=40, r=40, t=140, b=60),
        autosize=True,
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=13, color='#222222')
        )
    )

    return fig 