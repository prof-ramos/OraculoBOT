"""Explora estrutura do Supabase para entender legislações com embeddings."""

import os
import traceback

import requests
from postgrest import APIError
from supabase import create_client


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")
    return value

def main():
    supabase_url = _require_env("SUPABASE_URL")
    supabase_key = _require_env("SUPABASE_KEY")

    print("🔍 Conectando ao Supabase...")
    client = create_client(supabase_url, supabase_key)
    if client is None:
        raise RuntimeError("Falha ao criar cliente Supabase")

    print("\n📊 Listando todas as tabelas...")

    # Tentar descobrir tabelas comuns
    possible_tables = [
        "legislacoes",
        "legislacao",
        "laws",
        "documents",
        "embeddings",
        "legislacao_embeddings",
        "document_chunks",
        "chunks"
    ]

    for table in possible_tables:
        try:
            print(f"\n🔎 Tabela: {table}")
            result = client.table(table).select("*").limit(1).execute()

            if result.data:
                print(f"  ✅ Tabela existe! {len(result.data)} registro(s) de exemplo")
                print(f"  Colunas: {list(result.data[0].keys()) if result.data else 'N/A'}")

                # Se encontrar legislações, buscar estatísticas
                if "legisla" in table.lower() or "law" in table.lower():
                    count_result = client.table(table).select("*", count="exact").execute()
                    if hasattr(count_result, 'count'):
                        print(f"  📦 Total de registros: {count_result.count}")

                    # Mostrar estrutura de um exemplo completo
                    if result.data:
                        print(f"\n  📄 Exemplo de registro:")
                        for key, value in list(result.data[0].items())[:5]:
                            print(f"     {key}: {type(value).__name__} = {str(value)[:100]}")
            else:
                print(f"  ❌ Tabela não existe ou vazia")

        except requests.exceptions.RequestException as exc:
            print(f"  ⚠️  Erro de rede ({type(exc).__name__}): {exc}")
        except APIError as exc:
            print(f"  ⚠️  Erro da API Supabase: {exc.message}")
        except Exception as exc:
            print(f"  ⚠️  Erro inesperado ({type(exc).__name__}): {exc}")
            print(traceback.format_exc())

    print("\n🔍 Buscando tabelas via PostgreSQL query...")

    # Tentar usar RPC para listar tabelas
    try:
        result = client.rpc("get_tables").execute()
        print(f"  Tabelas encontradas: {result.data}")
    except requests.exceptions.RequestException as exc:
        print(f"  RPC indisponível por erro de rede: {exc}")
    except APIError as exc:
        print(f"  RPC não disponível: {exc.message}")
    except Exception as exc:
        print(f"  RPC falhou ({type(exc).__name__}): {exc}")
        print(traceback.format_exc())

    print("\n✅ Exploração concluída!")

if __name__ == "__main__":
    main()
