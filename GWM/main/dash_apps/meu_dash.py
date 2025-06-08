from django_plotly_dash import DjangoDash
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
from dash_apps.components import filtrar_auc_por_mes_ano, filtrar_PL
from main.db import pegar_consolidado, pegar_cliente, pegar_meta_anual_mais_recente, pegar_pl_migracao
from src.graficos import gerar_pizza_origem, gerar_comparativo_pl_migracao, gerar_grafico_top5_leads
from dash_apps.layouts import layout_auc  # Componente do gráfico AUC

# Substitui Dash pelo DjangoDash
app = DjangoDash('meu_dash_principal', suppress_callback_exceptions=True)

# Dados iniciais
df = pegar_consolidado()
nomes_disponiveis = sorted(df["nome"].unique())
meses_disponiveis = sorted(df["mes"].unique())
anos_disponiveis = sorted(df["ano"].unique())

mes1_default = meses_disponiveis[0] if meses_disponiveis else None
mes2_default = meses_disponiveis[1] if len(meses_disponiveis) > 1 else mes1_default
ano1_default = anos_disponiveis[0] if anos_disponiveis else None
ano2_default = anos_disponiveis[1] if len(anos_disponiveis) > 1 else ano1_default

df_cliente = pegar_cliente()
origem_disponivel = sorted(df_cliente["origem"].unique())
origem_default = origem_disponivel[0] if origem_disponiveis else None

# Layout
app.layout = html.Div(
    style={
        'backgroundColor': '#121212',
        'color': 'white',
        'fontFamily': 'Arial, sans-serif',
        'padding': '20px'
    },
    children=[ 
        html.Link(
            rel='stylesheet',
            href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css'
        ),
        dcc.Location(id='url', refresh=False),
        html.Div([ 
            dcc.Link([ 
                html.I(className='fas fa-chart-bar', style={'color': '#FF9F00', 'fontSize': '24px'}), 
                ' Comparativo AUC'
            ], href='/', style={'marginRight': '20px', 'fontSize': '20px', 'color': '#FF9F00'}),
            dcc.Link([ 
                html.I(className='fas fa-users', style={'color': '#FF9F00', 'fontSize': '24px'}), 
                ' Origem Clientes'
            ], href='/origem', style={'marginRight': '20px', 'fontSize': '20px', 'color': '#FF9F00'}),
            dcc.Link([ 
                html.I(className='fas fa-balance-scale', style={'color': '#FF9F00', 'fontSize': '24px'}), 
                ' Comparação PL'
            ], href='/comparacao-pl', style={'marginRight': '20px', 'fontSize': '20px', 'color': '#FF9F00'}),
            dcc.Link([ 
                html.I(className='fas fa-star', style={'color': '#FF9F00', 'fontSize': '24px'}), 
                ' Top 5 Leads'
            ], href='/top-leads', style={'fontSize': '20px', 'color': '#FF9F00'})
        ], style={'padding': '10px', 'textAlign': 'center'}),

        # Seção de dropdowns para filtros
        html.Div([
            html.Label("Selecione o head:", style={'fontSize': '18px', 'fontWeight': 'bold'}), 
            dcc.Dropdown(
                id='dropdown-nome',
                options=[{'label': nome, 'value': nome} for nome in nomes_disponiveis],
                value=nomes_disponiveis[0],
                style={'backgroundColor': '#2b2b2b', 'color': 'white'}
            ),
            html.Div([ 
                html.Div([ 
                    html.Label("Mês 1:"), dcc.Dropdown(id='dropdown-mes1',
                        options=[{'label': m, 'value': m} for m in meses_disponiveis],
                        value=mes1_default,
                        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
                    ),
                    html.Label("Ano 1:"), dcc.Dropdown(id='dropdown-ano1',
                        options=[{'label': a, 'value': a} for a in anos_disponiveis],
                        value=ano1_default,
                        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
                    )
                ], style={'width': '45%', 'display': 'inline-block'}),

                html.Div([ 
                    html.Label("Mês 2:"), dcc.Dropdown(id='dropdown-mes2',
                        options=[{'label': m, 'value': m} for m in meses_disponiveis],
                        value=mes2_default,
                        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
                    ),
                    html.Label("Ano 2:"), dcc.Dropdown(id='dropdown-ano2',
                        options=[{'label': a, 'value': a} for a in anos_disponiveis],
                        value=ano2_default,
                        style={'backgroundColor': '#2b2b2b', 'color': 'white'}
                    )
                ], style={'width': '45%', 'display': 'inline-block'})
            ]) 
        ], style={'marginBottom': '30px'}),

        html.Div([ 
            # Outros gráficos...
            html.Div([dcc.Graph(figure=gerar_pizza_origem())], className='card'),
            html.Div([dcc.Graph(id='grafico-pl-migracao', figure=gerar_comparativo_pl_migracao(pegar_pl_migracao()["pl_somado"].iloc[0], pegar_pl_migracao()["migracao_somado"].iloc[0]))], className='card'),
            html.Div([dcc.Graph(figure=gerar_grafico_top5_leads())], className='card'),
        ], style={ 
            'display': 'grid',
            'gridTemplateColumns': 'repeat(auto-fit, minmax(500px, 1fr))',
            'gap': '20px'
        }),

        # Adicionando o componente de AUC
        layout_auc  # Componente do gráfico AUC aqui
    ]
)

# Callback para o gráfico AUC
@app.callback(
    Output('grafico-comparativo', 'figure'),
    Input('dropdown-nome', 'value'),
    Input('dropdown-mes1', 'value'),
    Input('dropdown-ano1', 'value'),
    Input('dropdown-mes2', 'value'),
    Input('dropdown-ano2', 'value')
)
def atualizar_grafico_auc(nome, mes1, ano1, mes2, ano2):
    dados1 = filtrar_auc_por_mes_ano(mes1, ano1)
    dados2 = filtrar_auc_por_mes_ano(mes2, ano2)

    dados1 = dados1[dados1["nome"] == nome]
    dados2 = dados2[dados2["nome"] == nome]

    if dados1.empty or dados2.empty:
        return go.Figure().update_layout(title="Dados insuficientes para comparação.")

    pl1 = dados1.iloc[0]["planejado"]
    rl1 = dados1.iloc[0]["realizado"]
    pl2 = dados2.iloc[0]["planejado"]
    rl2 = dados2.iloc[0]["realizado"]

    meta_anual = pegar_meta_anual_mais_recente() or 0

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[f"{mes1}/{ano1}", f"{mes2}/{ano2}"], y=[pl1, pl2], mode='lines+markers', name='Planejado', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=[f"{mes1}/{ano1}", f"{mes2}/{ano2}"], y=[rl1, rl2], mode='lines+markers', name='Realizado', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=[f"{mes1}/{ano1}", f"{mes2}/{ano2}"], y=[meta_anual, meta_anual], mode='lines', name='Meta Anual', line=dict(dash='dash', color='white')))

    fig.update_layout(
        title=f"AUC Planejado x Realizado x Meta - {nome}",
        template='plotly_dark',
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font=dict(color='white'),
        xaxis_tickangle=-45
    )
    return fig
