import psycopg2
import psycopg2.extras
import random
import uuid
import os
import sys
from datetime import datetime, timedelta
from databricks import sql

def fetch_fx_rates_map() -> dict:
    print("Conectando ao Databricks para buscar taxas de referência...")
    connection = sql.connect(
        server_hostname=os.environ.get("DATABRICKS_HOST"),
        http_path=os.environ.get("DATABRICKS_HTTP_PATH"),
        access_token=os.environ.get("DATABRICKS_TOKEN"),
    )
    with connection.cursor() as cursor:
        cursor.execute("SELECT execution_date, close_rate FROM workspace.default.stg_fx_rates")
        linhas = cursor.fetchall()
    connection.close()
    mapa = {str(linha.execution_date): float(linha.close_rate) for linha in linhas}
    print(f"Sucesso! {len(mapa)} taxas de referência carregadas.")
    return mapa

def get_connection():
    dsn = os.environ.get("LAKEBASE_CONNECTION_STRING")
    return psycopg2.connect(dsn)

def reset_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM orders;")
    conn.commit()

def gerar_executed_rate(close_rate: float) -> float:
    if random.random() < 0.05:
        desvio_pct = random.uniform(0.01, 0.03) * random.choice([-1, 1])
    else:
        desvio_pct = random.uniform(-0.005, 0.005)
    return round(close_rate * (1 + desvio_pct), 2)

def gerar_registro_limpo(execution_date: str, close_rate: float) -> dict:
    return {
        "order_id": str(uuid.uuid4()),
        "execution_date": execution_date,
        "currency_pair": "USD/BRL",
        "executed_rate": gerar_executed_rate(close_rate),
        "trade_volume": round(random.uniform(1, 500), 2),     
        "client_id": f"CLIENT-{random.randint(1000, 9999)}",
    }

def aplicar_sujeira_execution_date(registro: dict) -> dict:
    if random.random() < 0.3:
        data = datetime.strptime(registro["execution_date"], "%Y-%m-%d")
        registro["execution_date"] = data.strftime("%d/%m/%Y")
    return registro

def aplicar_sujeira_currency_pair(registro: dict) -> dict:
    if random.random() < 0.3:
        registro["currency_pair"] = registro["currency_pair"].lower().replace("-", "")
    return registro

def gerar_lote(n: int, fx_rates_map: dict) -> list[dict]:
    datas_disponiveis = list(fx_rates_map.keys())
    lote = []
    for _ in range(n):
        execution_date = random.choice(datas_disponiveis)
        close_rate = fx_rates_map[execution_date]
        r = gerar_registro_limpo(execution_date, close_rate)
        r = aplicar_sujeira_execution_date(r)
        r = aplicar_sujeira_currency_pair(r)
        lote.append(r)
    return lote

def inserir_lote(conn, registros: list[dict]) -> None:
    with conn.cursor() as cur:
        valores = [
            (r["order_id"], r["execution_date"], r["currency_pair"], r["executed_rate"], r["trade_volume"], r["client_id"])
            for r in registros
        ]
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO orders (order_id, execution_date, currency_pair, executed_rate, trade_volume, client_id) VALUES %s",
            valores
        )
    conn.commit()

def main():
    fx_rates_map = fetch_fx_rates_map()
    if not fx_rates_map:
        print("Erro: stg_fx_rates retornou vazio. Rode os models de FX no dbt primeiro.")
        sys.exit(1)

    conn = get_connection()
    try:
        reset_table(conn)
        lote = gerar_lote(300, fx_rates_map)
        inserir_lote(conn, lote)
        print(f"{len(lote)} registros inseridos com sucesso.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()