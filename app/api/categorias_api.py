import requests
from typing import List, Dict, Optional
from app.api.auth_api import request_com_auth, SessionExpiredError

class CategoriasAPI:
    """Classe para gerenciar requisições à API de categorias"""
    
    BASE_URL = "http://localhost:8000"
    
    @staticmethod
    def listar_categorias(nome: str = None) -> List[Dict]:
        try:
            params = {}
            if nome:
                params['nome'] = nome
            response = request_com_auth("GET", f"{CategoriasAPI.BASE_URL}/categorias/", params=params)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar categorias: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes do erro: {e.response.text}")
            return []
    
    @staticmethod
    def criar_categoria(categoria_data: Dict) -> Optional[Dict]:
        try:
            print(f"Enviando categoria para API: {categoria_data}")
            response = request_com_auth("POST", f"{CategoriasAPI.BASE_URL}/categorias/", json=categoria_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao criar categoria: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes do erro: {e.response.text}")
            return None
    
    @staticmethod
    def obter_categoria(categoria_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("GET", f"{CategoriasAPI.BASE_URL}/categorias/{categoria_id}")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao obter categoria: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Detalhes do erro: {e.response.text}")
            return None