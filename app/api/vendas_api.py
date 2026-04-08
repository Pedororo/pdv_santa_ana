import requests
import json
from typing import List, Dict, Optional
from app.api.auth_api import request_com_auth, SessionExpiredError
from app.api.offline_layer import OfflineLayer
from app.utils.local_db import listar_vendas_pendentes_local


class VendasAPI:
    BASE_URL = "http://localhost:8000"

    _PAGAMENTO_MAP = {
        "Dinheiro": "DINHEIRO",
        "Débito":   "CARTAO_DEBITO",
        "Crédito":  "CARTAO_CREDITO",
        "PIX":      "PIX",
    }

    @classmethod
    def normalizar_pagamento(cls, tipo: str) -> str:
        return cls._PAGAMENTO_MAP.get(tipo, tipo.upper())

    # ── Vendas ────────────────────────────────────────────────────────────────

    @staticmethod
    def listar_vendas() -> List[Dict]:
        """
        Busca o histórico de vendas.
        Lê as vendas offline pendentes locais e mescla com as vendas do servidor.
        Garante que o vendedor veja o que acabou de fazer sem internet.
        """
        vendas_locais_pendentes = []
        
        # 1. Carrega as vendas locais que estão aguardando sincronização
        try:
            locais = listar_vendas_pendentes_local()
            for v in locais:
                payload = json.loads(v["payload_json"])
                payload["status"] = "PENDENTE"  # Força o status para aparecer laranja na View
                payload["offline"] = True
                vendas_locais_pendentes.append(payload)
        except Exception as e:
            print(f"[VendasAPI] Erro ao carregar vendas locais para o histórico: {e}")

        # 2. Tenta buscar as vendas do servidor
        def _online():
            r = request_com_auth("GET", f"{VendasAPI.BASE_URL}/vendas/")
            r.raise_for_status()
            return r.json()

        try:
            vendas_online = OfflineLayer.somente_online("listar_vendas", _online, fallback=[])
            if not vendas_online:
                vendas_online = []
                
            # 3. Mescla as pendentes locais com as online
            todas_vendas = vendas_locais_pendentes + vendas_online
            return todas_vendas
        except SessionExpiredError:
            raise

    @staticmethod
    def criar_venda(venda_data: Dict) -> Optional[Dict]:
        def _online():
            r = request_com_auth("POST", f"{VendasAPI.BASE_URL}/vendas/", json=venda_data)
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.criar_venda(venda_data, _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def cancelar_venda(venda_id, motivo: str = "") -> Optional[Dict]:
        def _online():
            r = request_com_auth(
                "PATCH",
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}/cancelar",
                json={"motivo": motivo} if motivo else {},
            )
            if r.status_code == 400:
                try:
                    detail = r.json().get("detail", "Venda não pode ser cancelada.")
                except Exception:
                    detail = r.text or "Venda não pode ser cancelada."
                return {"erro": detail}
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.cancelar_venda(venda_id, motivo, _online)
        except SessionExpiredError:
            raise

    # ── Métodos de fluxo online (chamados pela view no caminho online) ────────

    @staticmethod
    def adicionar_item(venda_id, item_data: Dict) -> Optional[Dict]:
        if str(venda_id).startswith("offline_"):
            return {"ok": True, "origem": "local"}

        def _online():
            r = request_com_auth(
                "POST",
                f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens",
                json=item_data,
            )
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.somente_online("adicionar_item", _online)
        except SessionExpiredError:
            raise
        except Exception as e:
            detail = ""
            if hasattr(e, "response") and e.response is not None:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except Exception:
                    detail = e.response.text
            return {"erro": detail or str(e)}

    @staticmethod
    def recalcular_total(venda_id) -> Optional[Dict]:
        if str(venda_id).startswith("offline_"):
            return None

        def _online():
            r = request_com_auth(
                "PUT",
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}/recalcular-total",
            )
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.somente_online("recalcular_total", _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def atualizar_venda(venda_id, venda_data: Dict) -> Optional[Dict]:
        if str(venda_id).startswith("offline_"):
            return None

        def _online():
            r = request_com_auth(
                "PUT",
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}",
                json=venda_data,
            )
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.somente_online("atualizar_venda", _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def finalizar_venda(venda_id) -> Optional[Dict]:
        if str(venda_id).startswith("offline_"):
            return {"id": venda_id, "status": "PENDENTE_SYNC", "origem": "local"}

        def _online():
            r = request_com_auth(
                "PATCH",
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}/finalizar",
            )
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.somente_online("finalizar_venda", _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def listar_itens(venda_id) -> List[Dict]:
        if str(venda_id).startswith("offline_"):
            import json as _json
            for v in listar_vendas_pendentes_local():
                if v["id"] == str(venda_id):
                    payload = _json.loads(v["payload_json"])
                    return payload.get("itens", [])
            return []

        def _online():
            r = request_com_auth(
                "GET",
                f"{VendasAPI.BASE_URL}/itens-venda/{venda_id}/itens",
            )
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.somente_online("listar_itens", _online, fallback=[])
        except SessionExpiredError:
            raise

    # ── Pagamentos ────────────────────────────────────────────────────────────

    @staticmethod
    def registrar_pagamento(venda_id, pagamento_data: Dict) -> Optional[Dict]:
        if str(venda_id).startswith("offline_"):
            return {"ok": True, "origem": "local"}

        def _online():
            r = request_com_auth(
                "POST", 
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento", 
                json=pagamento_data
            )
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.somente_online("registrar_pagamento", _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def atualizar_pagamento(venda_id: int, pagamento_data: Dict) -> Optional[Dict]:
        def _online():
            r = request_com_auth(
                "PUT", 
                f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento", 
                json=pagamento_data
            )
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.somente_online("atualizar_pagamento", _online)
        except SessionExpiredError:
            raise

    @staticmethod
    def obter_pagamento(venda_id: int) -> Optional[Dict]:
        def _online():
            r = request_com_auth("GET", f"{VendasAPI.BASE_URL}/vendas/{venda_id}/pagamento")
            r.raise_for_status()
            return r.json()

        try:
            return OfflineLayer.somente_online("obter_pagamento", _online)
        except SessionExpiredError:
            raise