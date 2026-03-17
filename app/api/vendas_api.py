import requests
from typing import List, Dict, Optional

class VendasAPI:
    """Classe para gerenciar requisições à API de vendas"""
    
    BASE_URL = "http://localhost:8000"

    # Mapeamento de labels amigáveis → valores esperados pela API
    _PAGAMENTO_MAP = {
        "Dinheiro":       "DINHEIRO",
        "Débito":         "CARTAO_DEBITO",
        "Crédito":        "CARTAO_CREDITO",
        "PIX":            "PIX",
    }

    @classmethod
    def normalizar_pagamento(cls, tipo: str) -> str:
        """Converte label da UI para o valor aceito pela API"""
        return cls._PAGAMENTO_MAP.get(tipo, tipo.upper())

    # ============= VENDAS =============
    
    @staticmethod
    def listar_vendas() -> List[Dict]:
        """Lista todas as vendas"""
        try:
            response = requests.get(f"{VendasAPI.BASE_URL}/vendas/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar vendas: {e}")
            return []
    
    @staticmethod
    def criar_venda(venda_data: Dict) -> Optional[Dict]:
        """Cria uma nova venda.

        venda_data deve conter:
        - forma_pagamento: {tipo, valor_recebido, troco}
        - acrescimo: float
        - desconto: float
        - itens: [] (lista de itens)
        """
        try:
            response = requests.post(
                f"{VendasAPI.BASE_URL}/vendas/",
                json=venda_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao criar venda: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes: {e.response.text}")
            return None
    
    @staticmethod
    def listar_ultimas_vendas() -> List[Dict]:
        """Lista as últimas vendas"""
        try:
            response = requests.get(f"{VendasAPI.BASE_URL}/vendas/ultimas")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar últimas vendas: {e}")
            return []
    
    @staticmethod
    def listar_vendas_periodo(data_inicio: str = None, data_fim: str = None) -> List[Dict]:
        """Lista vendas por período"""
        try:
            params = {}
            if data_inicio:
                params['data_inicio'] = data_inicio
            if data_fim:
                params['data_fim'] = data_fim
            
            response = requests.get(
                f"{VendasAPI.BASE_URL}/vendas/periodo",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar vendas por período: {e}")
            return []
    
    @staticmethod
    def obter_venda(venda_id: int) -> Optional[Dict]:
        """Obtém uma venda específica"""
        try:
            response = requests.get(f"{VendasAPI.BASE_URL}/vendas/{venda_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter venda: {e}")
            return None
    
    @staticmethod
    def atualizar_venda(venda_id: int, venda_data: Dict) -> Optional[Dict]:
        """Atualiza uma venda.

        venda_data pode conter:
        - forma_pagamento: string
        - acrescimo: float
        - desconto: float
        """
        try:
            response = requests.put(
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}",
                json=venda_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao atualizar venda: {e}")
            return None
    
    @staticmethod
    def finalizar_venda(venda_id: int) -> Optional[Dict]:
        """Finaliza uma venda"""
        try:
            response = requests.patch(f"{VendasAPI.BASE_URL}/vendas/{venda_id}/finalizar")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao finalizar venda: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes: {e.response.text}")
            return None
    
    @staticmethod
    def cancelar_venda(venda_id: int) -> Optional[Dict]:
        """Cancela uma venda. Retorna dict com 'erro' se o backend rejeitar (400)."""""
        try:
            response = requests.patch(f"{VendasAPI.BASE_URL}/vendas/{venda_id}/cancelar")
            if response.status_code == 400:
                try:
                    detail = response.json().get("detail", "Venda não pode ser cancelada.")
                except Exception:
                    detail = response.text or "Venda não pode ser cancelada."
                print(f"Erro ao cancelar venda {venda_id}: {detail}")
                return {"erro": detail}
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao cancelar venda: {e}")
            return None
    
    @staticmethod
    def recalcular_total(venda_id: int) -> Optional[Dict]:
        """Recalcula o total da venda"""
        try:
            response = requests.put(f"{VendasAPI.BASE_URL}/vendas/{venda_id}/recalcular-total")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao recalcular total: {e}")
            return None
    
    # ============= ITENS DE VENDA =============
    
    @staticmethod
    def adicionar_item(venda_id: int, item_data: Dict) -> Optional[Dict]:
        """Adiciona um item à venda. Retorna dict com 'erro' se o backend rejeitar."""
        try:
            response = requests.post(
                f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens",
                json=item_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
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
        """Lista itens de uma venda"""
        try:
            response = requests.get(f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar itens: {e}")
            return []
    
    @staticmethod
    def obter_item(venda_id: int, item_id: int) -> Optional[Dict]:
        """Obtém um item específico da venda"""
        try:
            response = requests.get(f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens/{item_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter item: {e}")
            return None
    
    @staticmethod
    def atualizar_item(venda_id: int, item_id: int, item_data: Dict) -> Optional[Dict]:
        """Atualiza um item da venda"""
        try:
            response = requests.put(
                f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens/{item_id}",
                json=item_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao atualizar item: {e}")
            return None
    
    @staticmethod
    def deletar_item(venda_id: int, item_id: int) -> bool:
        """Deleta um item da venda"""
        try:
            response = requests.delete(f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens/{item_id}")
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro ao deletar item: {e}")
            return False
    
    # ============= PAGAMENTOS =============
    
    @staticmethod
    def registrar_pagamento(venda_id: int, pagamento_data: Dict) -> Optional[Dict]:
        """Registra o pagamento de uma venda.

        pagamento_data deve conter:
        - tipo: "DINHEIRO", "DEBITO", "CREDITO", "PIX", "BOLETO"
        - valor_recebido: float
        """
        try:
            response = requests.post(
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento",
                json=pagamento_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao registrar pagamento: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes: {e.response.text}")
            return None
    
    @staticmethod
    def atualizar_pagamento(venda_id: int, pagamento_data: Dict) -> Optional[Dict]:
        """Atualiza o pagamento de uma venda.

        pagamento_data deve conter:
        - tipo: "DINHEIRO", "DEBITO", "CREDITO", "PIX", "BOLETO"
        - valor_recebido: float
        """
        try:
            response = requests.put(
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento",
                json=pagamento_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao atualizar pagamento: {e}")
            return None
    
    @staticmethod
    def obter_pagamento(venda_id: int) -> Optional[Dict]:
        """Obtém o pagamento de uma venda"""
        try:
            response = requests.get(f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter pagamento: {e}")
            return None