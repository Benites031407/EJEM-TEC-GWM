from dash_apps.db import pegar_consolidado, pegar_meta_anual_mais_recente
import plotly.graph_objects as go

def filtrar_auc_por_mes_ano(mes, ano, nome):
    df = pegar_consolidado()
    return df[
        (df["mes"] == mes) &
        (df["ano"] == ano) &
        (df["nome_tipo"] == "auc") &
        (df["nome"] == nome)
    ]

def gerar_grafico_auc(nome, dados1, dados2, mes1, ano1, mes2, ano2):
    if dados1.empty or dados2.empty:
        return go.Figure().update_layout(title="Dados insuficientes para comparação.")

    pl1 = dados1.iloc[0]["planejado"]
    rl1 = dados1.iloc[0]["realizado"]
    pl2 = dados2.iloc[0]["planejado"]
    rl2 = dados2.iloc[0]["realizado"]

    meta_anual = pegar_meta_anual_mais_recente() or 0

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[f"{mes1}/{ano1}", f"{mes2}/{ano2}"], y=[pl1, pl2],
                             mode='lines+markers', name='Planejado', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=[f"{mes1}/{ano1}", f"{mes2}/{ano2}"], y=[rl1, rl2],
                             mode='lines+markers', name='Realizado', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=[f"{mes1}/{ano1}", f"{mes2}/{ano2}"], y=[meta_anual, meta_anual],
                             mode='lines', name='Meta Anual', line=dict(dash='dash', color='white')))

    fig.update_layout(
        title=f"AUC Planejado x Realizado x Meta - {nome}",
        template='plotly_dark',
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font=dict(color='white'),
        xaxis_tickangle=-45
    )
    return fig
