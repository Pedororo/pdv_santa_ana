from typing import Optional, Dict
from app.api.auth_api import request_com_auth, SessionExpiredError


class RelatorioAPI:
    BASE_URL = "http://localhost:8000"

    @staticmethod
    def _fmt_dt(dt_str: str, fim_do_dia: bool = False) -> str:
        """Converte DD/MM/AAAA para datetime ISO aceito pelo back.
        fim_do_dia=True → usa 23:59:59 para cobrir o dia inteiro na data_fim.
        """
        try:
            from datetime import datetime
            dt = datetime.strptime(dt_str.strip(), "%d/%m/%Y")
            hora = "23:59:59" if fim_do_dia else "00:00:00"
            return dt.strftime(f"%Y-%m-%dT{hora}")
        except Exception:
            return dt_str

    @staticmethod
    def vendas(data_inicio: str, data_fim: str) -> Optional[Dict]:
        try:
            resp = request_com_auth("GET", f"{RelatorioAPI.BASE_URL}/relatorios/vendas",
                params={"data_inicio": RelatorioAPI._fmt_dt(data_inicio),
                        "data_fim":   RelatorioAPI._fmt_dt(data_fim, fim_do_dia=True)})
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError: raise
        except Exception as e:
            print(f"Erro relatório vendas: {e}")
            return None

    @staticmethod
    def estoque() -> Optional[Dict]:
        try:
            resp = request_com_auth("GET", f"{RelatorioAPI.BASE_URL}/relatorios/estoque")
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError: raise
        except Exception as e:
            print(f"Erro relatório estoque: {e}")
            return None

    @staticmethod
    def margem(data_inicio: str, data_fim: str) -> Optional[Dict]:
        try:
            resp = request_com_auth("GET", f"{RelatorioAPI.BASE_URL}/relatorios/margem",
                params={"data_inicio": RelatorioAPI._fmt_dt(data_inicio),
                        "data_fim":   RelatorioAPI._fmt_dt(data_fim, fim_do_dia=True)})
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError: raise
        except Exception as e:
            print(f"Erro relatório margem: {e}")
            return None

    @staticmethod
    def caixa(data_inicio: str, data_fim: str) -> Optional[Dict]:
        try:
            resp = request_com_auth("GET", f"{RelatorioAPI.BASE_URL}/relatorios/caixa",
                params={"data_inicio": RelatorioAPI._fmt_dt(data_inicio),
                        "data_fim":   RelatorioAPI._fmt_dt(data_fim, fim_do_dia=True)})
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError: raise
        except Exception as e:
            print(f"Erro relatório caixa: {e}")
            return None

    @staticmethod
    def geral(data_inicio: str, data_fim: str) -> Optional[Dict]:
        try:
            resp = request_com_auth("GET", f"{RelatorioAPI.BASE_URL}/relatorios/geral",
                params={"data_inicio": RelatorioAPI._fmt_dt(data_inicio),
                        "data_fim":   RelatorioAPI._fmt_dt(data_fim, fim_do_dia=True)})
            resp.raise_for_status()
            return resp.json()
        except SessionExpiredError: raise
        except Exception as e:
            print(f"Erro relatório geral: {e}")
            return None