import psycopg2
import pandas as pd

def conectar():
    return psycopg2.connect(
    dbname="gwmdeploy",
    user="gwmdeploy_user",
    password="Tz6WY8Qk68u5bctdVJdQPjsKUX0q3p2h",
    host="dpg-d13mllm3jp1c73d85d30-a.virginia-postgres.render.com",
    port="5432",
    sslmode='require'
    )


def pegar_planejado():
    conn = conectar()
    query = "SELECT * FROM main_planejado;"  # Altere para sua view ou tabela correta
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def pegar_realizado():
    conn = conectar()
    query = "SELECT * FROM main_executado;"  # Altere para sua view ou tabela correta
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def pegar_captacao():
    conn = conectar()
    query = "SELECT * FROM main_captacao;"  # Altere para sua view ou tabela correta
    df = pd.read_sql(query, conn)
    conn.close()
    return df
    
   