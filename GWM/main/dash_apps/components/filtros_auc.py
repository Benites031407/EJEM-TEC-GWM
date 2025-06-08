from dash_apps.db import pegar_consolidado, pegar_cliente

def filtrar_auc_por_mes_ano(mes, ano):
    df = pegar_consolidado()

    df_filtrado = df[
        (df["mes"] == mes) &
        (df["ano"] == ano) &
        (df["nome_tipo"] == "auc")
    ]
    return df_filtrado

