from typing import Optional, Dict, List
from app.api.auth_api import request_com_auth, SessionExpiredError


class TurnoAPI:
    BASE_URL = "http://localhost:8000"

    @staticmethod
    def abrir_turno(valor_inicial: float) -> Optional[Dict]:
        """POST /turnos/abrir"""
        try:
            resp = request_com_auth(
                "POST",
                f"{TurnoAPI.BASE_URL}/turnos/abrir",
                json={"valor_inicial": valor_inicial},
            )
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao abrir turno: {e}")
            return None

    @staticmethod
    def fechar_turno(valor_informado: float, observacoes: str = None) -> Optional[Dict]:
        """POST /turnos/fechar"""
        try:
            payload = {"valor_informado": valor_informado}
            if observacoes:
                payload["observacoes"] = observacoes
            resp = request_com_auth(
                "POST",
                f"{TurnoAPI.BASE_URL}/turnos/fechar",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao fechar turno: {e}")
            return None

    @staticmethod
    def get_turno_ativo() -> Optional[Dict]:
        """GET /turnos/ativo — retorna turno aberto ou None"""
        try:
            resp = request_com_auth("GET", f"{TurnoAPI.BASE_URL}/turnos/ativo")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao buscar turno ativo: {e}")
            return None

    @staticmethod
    def historico() -> List[Dict]:
        """GET /turnos/historico"""
        try:
            resp = request_com_auth("GET", f"{TurnoAPI.BASE_URL}/turnos/historico")
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError:
            raise
        except Exception as e:
            print(f"Erro ao listar histórico de turnos: {e}")
            return []