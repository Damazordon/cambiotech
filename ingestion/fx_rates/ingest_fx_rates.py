import requests
import sys
import json
import os
from datetime import datetime
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError

class CotaEstouradaError(Exception):
    pass

def fetch_from_api(api_key: str) -> dict:
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_DAILY",
        "from_symbol": "USD", 
        "to_symbol": "BRL",
        "apikey": api_key
    }
    response = requests.get(url, params=params)
    response.raise_for_status() 
    return response.json()

def validar_resposta_api(payload: dict) -> None:
    if "Note" in payload or "Information" in payload:
        raise CotaEstouradaError("Limite de cota atingido retornado no payload.")

def build_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"raw_{timestamp}.json"

def save_local(payload: dict, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)
    print(f"Artefato salvo com sucesso: {filename}")

def upload_para_storage(local_filename: str) -> None:
    w = WorkspaceClient()

    volume_path = f"/Volumes/workspace/default/raw/{local_filename}"
    w.files.upload_from(volume_path, local_filename, overwrite=True)

    print(f"Upload de {local_filename} concluído com sucesso.")

def main():
    
    api_alpha = os.environ.get("ALPHA_VANTAGE_API_KEY")
    
    if not api_alpha:
        print("Erro: Chave da API não encontrada nas variáveis de ambiente.")
        sys.exit(1)
    try:
        payload = fetch_from_api(api_key=api_alpha)
        validar_resposta_api(payload)     
         
    except CotaEstouradaError as e:
        print(f"Aviso: {e}")
        sys.exit(0)  
        
    except requests.exceptions.RequestException as e:
        print(f"Erro genérico de rede na API: {e}")
        sys.exit(1)
        
    filename = build_filename()
    save_local(payload, filename)

    try:
        upload_para_storage(filename)
    except DatabricksError as e:
        print(f"Erro na comunicação com o Databricks (SDK): {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado durante o upload: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()