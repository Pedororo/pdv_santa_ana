import requests
from typing import List, Dict, Optional
from app.api.auth_api import request_com_auth, SessionExpiredError
from app.api.offline_layer import OfflineLayer


class ProdutosAPI:
    BASE_URL = "http://localhost:8000"

    @staticmethod
    def listar_produtos() -> List[Dict]:
        """Online: busca da API e atualiza espelho. Offline: retorna espelho local."""
        def _online():
            response = request_com_auth("GET", f"{ProdutosAPI.BASE_URL}/produtos/")
            response.raise_for_status()
            return response.json()

        try:
            return OfflineLayer.listar_produtos(_online)
        except SessionExpiredError:
            raise

    @staticmethod
    def obter_produto(produto_id: int) -> Optional[Dict]:
        """Online: busca da API. Offline: busca no espelho local."""
        def _online():
            response = request_com_auth("GET", f"{ProdutosAPI.BASE_URL}/produtos/{produto_id}")
            response.raise_for_status()
            return response.json()

        try:
            return OfflineLayer.obter_produto(produto_id, _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def criar_produto(produto_data: Dict) -> Optional[Dict]:
        """Somente online — cadastro de produto exige conexão."""
        def _online():
            response = request_com_auth("POST", f"{ProdutosAPI.BASE_URL}/produtos/", json=produto_data)
            response.raise_for_status()
            return response.json()

        try:
            return OfflineLayer.somente_online("criar_produto", _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def atualizar_produto(produto_id: int, produto_data: Dict) -> Optional[Dict]:
        """Somente online."""
        def _online():
            response = request_com_auth("PATCH", f"{ProdutosAPI.BASE_URL}/produtos/{produto_id}", json=produto_data)
            response.raise_for_status()
            return response.json()

        try:
            return OfflineLayer.somente_online("atualizar_produto", _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def listar_inativos() -> List[Dict]:
        """Somente online."""
        def _online():
            response = request_com_auth("GET", f"{ProdutosAPI.BASE_URL}/produtos/inativos/")
            response.raise_for_status()
            return response.json()

        try:
            return OfflineLayer.somente_online("listar_inativos", _online, fallback=[])
        except SessionExpiredError:
            raise

    @staticmethod
    def reativar_produto(produto_id: int) -> Optional[Dict]:
        """Somente online."""
        def _online():
            response = request_com_auth("PATCH", f"{ProdutosAPI.BASE_URL}/produtos/{produto_id}/reativar")
            response.raise_for_status()
            return response.json()

        try:
            return OfflineLayer.somente_online("reativar_produto", _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def deletar_produto(produto_id: int) -> bool:
        """Somente online."""
        def _online():
            response = request_com_auth("DELETE", f"{ProdutosAPI.BASE_URL}/produtos/{produto_id}")
            response.raise_for_status()
            return True

        try:
            resultado = OfflineLayer.somente_online("deletar_produto", _online, fallback=False)
            return bool(resultado)
        except SessionExpiredError:
            raise