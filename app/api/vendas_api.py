import requests
from typing import List, Dict, Optional
from app.api.auth_api import request_com_auth, SessionExpiredError

class VendasAPI:
    """Classe para gerenciar requisições à API de vendas"""
    
    BASE_URL = "http://localhost:8000"

    _PAGAMENTO_MAP = {
        "Dinheiro":       "DINHEIRO",
        "Débito":         "CARTAO_DEBITO",
        "Crédito":        "CARTAO_CREDITO",
        "PIX":            "PIX",
    }

    @classmethod
    def normalizar_pagamento(cls, tipo: str) -> str:
        return cls._PAGAMENTO_MAP.get(tipo, tipo.upper())

    # ============= VENDAS =============

    @staticmethod
    def listar_vendas() -> List[Dict]:
        try:
            response = request_com_auth("GET", f"{VendasAPI.BASE_URL}/vendas/")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar vendas: {e}")
            return []

    @staticmethod
    def criar_venda(venda_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth("POST", f"{VendasAPI.BASE_URL}/vendas/", json=venda_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao criar venda: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def listar_ultimas_vendas() -> List[Dict]:
        try:
            response = request_com_auth("GET", f"{VendasAPI.BASE_URL}/vendas/ultimas")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar últimas vendas: {e}")
            return []

    @staticmethod
    def listar_vendas_periodo(data_inicio: str = None, data_fim: str = None) -> List[Dict]:
        try:
            params = {}
            if data_inicio:
                params['data_inicio'] = data_inicio
            if data_fim:
                params['data_fim'] = data_fim
            response = request_com_auth("GET", f"{VendasAPI.BASE_URL}/vendas/periodo", params=params)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar vendas por período: {e}")
            return []

    @staticmethod
    def obter_venda(venda_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("GET", f"{VendasAPI.BASE_URL}/vendas/{venda_id}")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao obter venda: {e}")
            return None

    @staticmethod
    def atualizar_venda(venda_id: int, venda_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth("PUT", f"{VendasAPI.BASE_URL}/vendas/{venda_id}", json=venda_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao atualizar venda: {e}")
            return None

    @staticmethod
    def finalizar_venda(venda_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("PATCH", f"{VendasAPI.BASE_URL}/vendas/{venda_id}/finalizar")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao finalizar venda: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def cancelar_venda(venda_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("PATCH", f"{VendasAPI.BASE_URL}/vendas/{venda_id}/cancelar")
            if response.status_code == 400:
                try:
                    detail = response.json().get("detail", "Venda não pode ser cancelada.")
                except Exception:
                    detail = response.text or "Venda não pode ser cancelada."
                print(f"Erro ao cancelar venda {venda_id}: {detail}")
                return {"erro": detail}
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao cancelar venda: {e}")
            return None

    @staticmethod
    def recalcular_total(venda_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("PUT", f"{VendasAPI.BASE_URL}/vendas/{venda_id}/recalcular-total")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao recalcular total: {e}")
            return None

    # ============= ITENS DE VENDA =============

    @staticmethod
    def adicionar_item(venda_id: int, item_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth("POST", f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens", json=item_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao adicionar item: {e}")
            detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except Exception:
                    detail = e.response.text
                print(f"Detalhes: {detail}")
            return {"erro": detail or str(e)}

    @staticmethod
    def listar_itens(venda_id: int) -> List[Dict]:
        try:
            response = request_com_auth("GET", f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar itens: {e}")
            return []

    @staticmethod
    def obter_item(venda_id: int, item_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("GET", f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens/{item_id}")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao obter item: {e}")
            return None

    @staticmethod
    def atualizar_item(venda_id: int, item_id: int, item_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth("PUT", f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens/{item_id}", json=item_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao atualizar item: {e}")
            return None

    @staticmethod
    def deletar_item(venda_id: int, item_id: int) -> bool:
        try:
            response = request_com_auth("DELETE", f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens/{item_id}")
            response.raise_for_status()
            return True
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao deletar item: {e}")
            return False

    # ============= PAGAMENTOS =============

    @staticmethod
    def registrar_pagamento(venda_id: int, pagamento_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth("POST", f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento", json=pagamento_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao registrar pagamento: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def atualizar_pagamento(venda_id: int, pagamento_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth("PUT", f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento", json=pagamento_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao atualizar pagamento: {e}")
            return None

    @staticmethod
    def obter_pagamento(venda_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("GET", f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao obter pagamento: {e}")
            return None