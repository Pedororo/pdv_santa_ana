from typing import Optional, Dict, List
from app.api.auth_api import request_com_auth, SessionExpiredError
import traceback


class TurnoAPI:
    BASE_URL = "http://localhost:8000"

    # 🔥 NORMALIZADOR (evita crash por resposta incompleta)
    @staticmethod
    def _normalizar_turno(data: Dict) -> Dict:
        if not data or not isinstance(data, dict):
            return TurnoAPI._turno_offline()
            
        return {
            "id": data.get("id"),
            "status": data.get("status"),
            "data_abertura": data.get("data_abertura"),
            "valor_inicial": data.get("valor_inicial", 0),
            "total_vendas": data.get("total_vendas", 0),
            "quantidade_vendas": data.get("quantidade_vendas", 0),
            "usuario_nome": data.get("usuario_nome"),
            "offline": data.get("offline", False)  # 🔥 NOVO
        }

    # 🔥 TURNO OFFLINE PADRÃO
    @staticmethod
    def _turno_offline() -> Dict:
        return {
            "id": "offline",
            "status": "ABERTO",
            "data_abertura": None,
            "valor_inicial": 0,
            "total_vendas": 0,
            "quantidade_vendas": 0,
            "usuario_nome": None,
            "offline": True
        }

    @staticmethod
    def abrir_turno(valor_inicial: float) -> Optional[Dict]:
        try:
            resp = request_com_auth(
                "POST",
                f"{TurnoAPI.BASE_URL}/turnos/abrir",
                json={"valor_inicial": float(valor_inicial)},
            )

            if resp.status_code == 500:
                print("Erro interno ao abrir turno")
                print(resp.text)
                return None

            resp.raise_for_status()
            data = resp.json()

            return TurnoAPI._normalizar_turno(data)

        except SessionExpiredError:
            raise
        except Exception:
            traceback.print_exc()
            return None

    @staticmethod
    def fechar_turno(valor_informado: float, observacoes: str = None) -> Optional[Dict]:
        try:
            payload = {"valor_informado": float(valor_informado)}

            if observacoes:
                payload["observacoes"] = observacoes

            resp = request_com_auth(
                "POST",
                f"{TurnoAPI.BASE_URL}/turnos/fechar",
                json=payload,
            )

            # 🔥 SE ESTIVER OFFLINE → NÃO QUEBRA
            if resp.status_code in [500, 404]:
                print("Falha ao fechar turno no servidor (modo offline)")
                return {
                    "status": "FECHADO",
                    "offline": True
                }

            resp.raise_for_status()
            return resp.json()

        except SessionExpiredError:
            raise
        except Exception:
            traceback.print_exc()

            # 🔥 SEM INTERNET → FECHA LOCAL
            return {
                "status": "FECHADO",
                "offline": True
            }

    @staticmethod
    def get_turno_ativo() -> Optional[Dict]:
        try:
            resp = request_com_auth(
                "GET",
                f"{TurnoAPI.BASE_URL}/turnos/ativo"
            )

            # 404 = nenhum turno ativo, 500 = erro real no servidor
            if resp.status_code == 404:
                return None  # sem turno ativo — comportamento correto

            if resp.status_code == 500:
                print("[TurnoAPI] Erro interno no servidor ao buscar turno")
                return None

            resp.raise_for_status()
            data = resp.json()

            # Back pode retornar 200 com body null quando não há turno ativo
            if not data:
                return None

            return TurnoAPI._normalizar_turno(data)

        except SessionExpiredError:
            raise
        except Exception:
            traceback.print_exc()
            # Sem internet — não cria turno fictício, retorna None
            # A view decide o que fazer (badge offline já está visível)
            return None

    @staticmethod
    def historico() -> List[Dict]:
        try:
            resp = request_com_auth(
                "GET",
                f"{TurnoAPI.BASE_URL}/turnos/historico"
            )
            
            # 🔥 PROTEÇÃO CONTRA NONE TYPE: Se falhar, retorna lista vazia imediatamente
            if resp.status_code != 200:
                return []

            resp.raise_for_status()
            data = resp.json()

            # 🔥 PROTEÇÃO: Garante que data é uma lista antes de iterar
            if not isinstance(data, list):
                return []

            return [TurnoAPI._normalizar_turno(item) for item in data]

        except SessionExpiredError:
            raise
        except Exception:
            traceback.print_exc()
            return []  # 🔥 PROTEÇÃO: Nunca retorna None

    @staticmethod
    def historico_todos() -> List[Dict]:
        try:
            resp = request_com_auth(
                "GET",
                f"{TurnoAPI.BASE_URL}/turnos/historico/todos"
            )

            if resp.status_code == 404:
                return TurnoAPI.historico()
                
            # 🔥 PROTEÇÃO CONTRA NONE TYPE
            if resp.status_code != 200:
                return []

            resp.raise_for_status()
            data = resp.json()

            # 🔥 PROTEÇÃO: Garante que data é uma lista antes de iterar
            if not isinstance(data, list):
                return []

            return [TurnoAPI._normalizar_turno(item) for item in data]

        except SessionExpiredError:
            raise
        except Exception:
            traceback.print_exc()
            return TurnoAPI.historico()  # Fallback para o histórico comum que já retorna []