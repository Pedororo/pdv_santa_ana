import requests
from typing import List, Dict, Optional


class UsuariosAPI:
    """Classe para gerenciar requisições à API de usuários"""

    BASE_URL = "http://localhost:8000"

    @staticmethod
    def criar_usuario(usuario_data: Dict) -> Optional[Dict]:
        """Cria um novo usuário.

        usuario_data deve conter:
        - nome: str
        - username: str
        - senha: str
        - role: "ADMIN" | "VENDEDOR"
        """
        try:
            response = requests.post(
                f"{UsuariosAPI.BASE_URL}/usuarios/",
                json=usuario_data,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao criar usuário: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def listar_usuarios() -> List[Dict]:
        """Lista todos os usuários."""
        try:
            response = requests.get(f"{UsuariosAPI.BASE_URL}/usuarios/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar usuários: {e}")
            return []

    @staticmethod
    def obter_usuario(usuario_id: int) -> Optional[Dict]:
        """Obtém um usuário específico pelo ID."""
        try:
            response = requests.get(f"{UsuariosAPI.BASE_URL}/usuarios/{usuario_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter usuário: {e}")
            return None

    @staticmethod
    def atualizar_usuario(usuario_id: int, usuario_data: Dict) -> Optional[Dict]:
        """Atualiza dados de um usuário.

        usuario_data pode conter:
        - nome: str
        - username: str
        - senha: str
        - ativo: bool
        """
        try:
            response = requests.patch(
                f"{UsuariosAPI.BASE_URL}/usuarios/{usuario_id}",
                json=usuario_data,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao atualizar usuário: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def desativar_usuario(usuario_id: int) -> Optional[Dict]:
        """Desativa um usuário."""
        try:
            response = requests.patch(
                f"{UsuariosAPI.BASE_URL}/usuarios/{usuario_id}/desativar"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao desativar usuário: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalhes: {e.response.text}")
            return None

    @staticmethod
    def reativar_usuario(usuario_id: int) -> Optional[Dict]:
        """Reativa um usuário desativado."""
        try:
            response = requests.patch(
                f"{UsuariosAPI.BASE_URL}/usuarios/{usuario_id}/reativar"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao reativar usuário: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Detalhes: {e.response.text}")
            return None