import requests
from typing import List, Dict, Optional
from app.api.auth_api import request_com_auth, SessionExpiredError


class MovimentacaoAPI:
    """Classe para gerenciar requisições à API de movimentações de estoque"""

    BASE_URL = "http://localhost:8000"

    TIPO_ENTRADA = "ENTRADA"
    TIPO_SAIDA   = "SAIDA"

    MOTIVO_CADASTRO_INICIAL = "CADASTRO_INICIAL"
    MOTIVO_COMPRA           = "COMPRA"
    MOTIVO_VENDA            = "VENDA"
    MOTIVO_AJUSTE           = "AJUSTE"
    MOTIVO_PERDA            = "PERDA"
    MOTIVO_DEVOLUCAO        = "DEVOLUCAO"
    MOTIVO_INVENTARIO       = "INVENTARIO"

    MOTIVOS_ENTRADA = ["COMPRA", "DEVOLUCAO", "INVENTARIO", "CADASTRO_INICIAL"]
    MOTIVOS_SAIDA   = ["VENDA", "PERDA", "AJUSTE", "INVENTARIO"]

    @staticmethod
    def registrar_movimentacao(movimentacao_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth(
                "POST",
                f"{MovimentacaoAPI.BASE_URL}/movimentacoes/",
                json=movimentacao_data,
            )
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao registrar movimentação: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except Exception:
                    detail = e.response.text
                print(f"Detalhes: {detail}")
            return None

    @staticmethod
    def listar_por_produto(produto_id: int) -> List[Dict]:
        try:
            response = request_com_auth("GET", f"{MovimentacaoAPI.BASE_URL}/movimentacoes/produto/{produto_id}")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar movimentações do produto {produto_id}: {e}")
            return []

    @staticmethod
    def listar_por_venda(venda_id: int) -> List[Dict]:
        try:
            response = request_com_auth("GET", f"{MovimentacaoAPI.BASE_URL}/movimentacoes/venda/{venda_id}")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar movimentações da venda {venda_id}: {e}")
            return []

    @staticmethod
    def exportar(
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        tipo: Optional[str] = None,
        salvar_em: Optional[str] = None,
    ) -> Optional[bytes]:
        params = {}
        if data_inicio:
            params["data_inicio"] = data_inicio
        if data_fim:
            params["data_fim"] = data_fim
        if tipo and tipo in (MovimentacaoAPI.TIPO_ENTRADA, MovimentacaoAPI.TIPO_SAIDA):
            params["tipo"] = tipo

        try:
            response = request_com_auth(
                "GET",
                f"{MovimentacaoAPI.BASE_URL}/movimentacoes/exportar",
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            conteudo = response.content

            if salvar_em:
                with open(salvar_em, "wb") as f:
                    f.write(conteudo)
                print(f"Exportação salva em: {salvar_em}")

            return conteudo

        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao exportar movimentações: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except Exception:
                    detail = e.response.text
                print(f"Detalhes: {detail}")
            return None