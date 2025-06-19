import psycopg2
import pandas as pd

def conectar():
    return psycopg2.connect(
    dbname="deploy2",
    user="deploy2_user",
    password="s0N4Y56ytTN84reSeeoIGZPyr10mvsHl",
    host="dpg-d19lpvbipnbc7396bu1g-a.virginia-postgres.render.com",
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
    
   