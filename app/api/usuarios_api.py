import requests
from typing import List, Dict, Optional
from app.api.auth_api import request_com_auth, SessionExpiredError


class UsuariosAPI:
    """Classe para gerenciar requisições à API de usuários"""

    BASE_URL = "http://localhost:8000"

    @staticmethod
    def criar_usuario(usuario_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth("POST", f"{UsuariosAPI.BASE_URL}/usuarios/", json=usuario_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def listar_usuarios() -> List[Dict]:
        try:
            response = request_com_auth("GET", f"{UsuariosAPI.BASE_URL}/usuarios/")
            response.raise_for_status()
            usuarios = response.json()

            # Espelha no banco local para uso offline
            try:
                from app.utils.local_db import upsert_usuarios_local
                upsert_usuarios_local(usuarios)
            except Exception as e:
                print(f"[UsuariosAPI] Erro ao espelhar usuários: {e}")

            return usuarios
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar usuários: {e}")
            return []

    @staticmethod
    def listar_usuarios_offline() -> List[Dict]:
        """Lê usuários do espelho local — usado quando offline."""
        try:
            from app.utils.local_db import listar_usuarios_local
            return listar_usuarios_local()
        except Exception as e:
            print(f"[UsuariosAPI] Erro ao listar usuários offline: {e}")
            return []

    @staticmethod
    def obter_usuario(usuario_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("GET", f"{UsuariosAPI.BASE_URL}/usuarios/{usuario_id}")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao obter usuário: {e}")
            return None

    @staticmethod
    def atualizar_usuario(usuario_id: int, usuario_data: Dict) -> Optional[Dict]:
        try:
            response = request_com_auth("PATCH", f"{UsuariosAPI.BASE_URL}/usuarios/{usuario_id}", json=usuario_data)
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao atualizar usuário: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def desativar_usuario(usuario_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("PATCH", f"{UsuariosAPI.BASE_URL}/usuarios/{usuario_id}/desativar")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao desativar usuário: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def listar_inativos() -> List[Dict]:
        """Lista usuários inativos.
        O back filtra só ativos no GET /usuarios/ — retorna lista vazia por ora.
        Quando o back tiver rota /usuarios/inativos/, atualizar aqui.
        """
        return []

    @staticmethod
    def reativar_usuario(usuario_id: int) -> Optional[Dict]:
        try:
            response = request_com_auth("PATCH", f"{UsuariosAPI.BASE_URL}/usuarios/{usuario_id}/reativar")
            response.raise_for_status()
            return response.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao reativar usuário: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalhes: {e.response.text}")
            return None