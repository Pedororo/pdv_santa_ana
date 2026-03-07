import requests
from typing import List, Dict, Optional

class ProdutosAPI:
    """Classe para gerenciar requisições à API de produtos"""
    
    BASE_URL = "http://localhost:8000"
    
    @staticmethod
    def listar_produtos() -> List[Dict]:
        """Lista todos os produtos ativos"""
        try:
            response = requests.get(f"{ProdutosAPI.BASE_URL}/produtos/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar produtos: {e}")
            return []
    
    @staticmethod
    def obter_produto(produto_id: int) -> Optional[Dict]:
        """Obtém um produto específico por ID"""
        try:
            response = requests.get(f"{ProdutosAPI.BASE_URL}/produtos/{produto_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter produto: {e}")
            return None
    
    @staticmethod
    def criar_produto(produto_data: Dict) -> Optional[Dict]:
        """Cria um novo produto"""
        try:
            response = requests.post(
                f"{ProdutosAPI.BASE_URL}/produtos/",
                json=produto_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao criar produto: {e}")
            return None
    
    @staticmethod
    def atualizar_produto(produto_id: int, produto_data: Dict) -> Optional[Dict]:
        """Atualiza um produto existente"""
        try:
            response = requests.patch(
                f"{ProdutosAPI.BASE_URL}/produtos/{produto_id}",
                json=produto_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao atualizar produto: {e}")
            return None
    
    @staticmethod
    def deletar_produto(produto_id: int) -> bool:
        """Deleta um produto"""
        try:
            response = requests.delete(f"{ProdutosAPI.BASE_URL}/produtos/{produto_id}")
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Erro ao deletar produto: {e}")
            return False