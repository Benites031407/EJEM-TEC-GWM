import psycopg2
import pandas as pd

# def conectar():
#     return psycopg2.connect(
#     dbname="gwm1807",
#     user="gwm1807_user",
#     password="Sx9MIqQ160xrb8kaFN0Mh3Jezc9jc1NY",
#     host="dpg-d1sndaali9vc73c96o3g-a.virginia-postgres.render.com",
#     port="5432",
#     sslmode='require'
#     )

def conectar():
    return psycopg2.connect(
    dbname="gwm2508",
    user="adm",
    password="admingwm",
    host="localhost",
    port="5432",
    )

# def conectar():
#     return psycopg2.connect(
#     dbname="GWM180725",
#     user="postgres",
#     password="banana",
#     host="localhost",
#     port="5432",
#     )

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
    
   