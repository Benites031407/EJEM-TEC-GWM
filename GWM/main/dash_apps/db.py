import psycopg2
import pandas as pd

def conectar():
    return psycopg2.connect(
        dbname="GWM",
        user="postgres",
        password="banana",
        host="localhost",
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
    
   