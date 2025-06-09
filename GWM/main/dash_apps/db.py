import psycopg2
import pandas as pd

def conectar():
    return psycopg2.connect(
        dbname="gwm",
        user="gwm_user",
        password="0ULmVOmGX1NVi5dA287m0x7wWjoYqh55",
        host="dpg-d13ihr0dl3ps738tek30-a",
        port="5432"
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
    
   