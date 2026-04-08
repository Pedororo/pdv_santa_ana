"""
Camada de abstração online/offline — PDV Santa Ana.
Responsável por interceptar falhas de rede e salvar dados localmente.
A sincronização em background é gerenciada exclusivamente pelo sync_engine.py.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.utils import connectivity, local_db


# =============================================================================
# HELPERS
# =============================================================================

def _gerar_id_offline() -> str:
    return f"offline_{uuid.uuid4().hex}"


def _sessao_vendedor() -> tuple[str, str]:
    sessao = local_db.carregar_sessao()
    if sessao:
        return sessao.get("usuario_id", ""), sessao.get("usuario_nome", "")
    return "", ""


# =============================================================================
# VENDAS (LÓGICA DE PERSISTÊNCIA OFFLINE)
# =============================================================================

def registrar_venda_offline(venda: dict) -> dict:
    """
    Captura e persiste os dados completos da venda no SQLite local.
    
    venda esperada: {
        'total': float,
        'forma_pagamento': str,
        'itens': list,
        ...
    }
    """
    venda_id = f"offline_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:4]}"
    vendedor_id, vendedor_nome = _sessao_vendedor()

    # MONTAGEM DO PAYLOAD COMPLETO (Garante que nada chegue zerado ao servidor)
    payload = {
        "id":              venda_id,
        "id_offline":      venda_id,
        "turno_id":        "offline",  # Será resolvido pelo sync_engine.py ao voltar online
        "valor_total":     float(venda.get("total", 0)),
        "forma_pagamento": venda.get("forma_pagamento", "DINHEIRO"),
        "itens":           venda.get("itens", []),  
        "data_hora":       datetime.now().isoformat(),
        "vendedor_id":     vendedor_id,
        "vendedor_nome":   vendedor_nome,
        "origem":          "offline"
    }

    # PERSISTÊNCIA 1: Salva no histórico de vendas local (vendas_local)
    local_db.salvar_venda_local(
        venda_id=venda_id,
        payload_json=json.dumps(payload, ensure_ascii=False),
        vendedor_id=vendedor_id,
        vendedor_nome=vendedor_nome,
    )

    # PERSISTÊNCIA 2: Adiciona à fila de sincronização (sync_queue) para o sync_engine processar
    local_db.enfileirar_sync(
        operacao="REGISTRAR_VENDA",
        payload=json.dumps(payload, ensure_ascii=False),
    )

    print(f"[OFFLINE] ✓ Venda salva localmente: {venda_id} — R$ {payload['valor_total']:.2f}")
    return payload


def cancelar_venda_offline(venda_id: str, motivo: str = "") -> dict:
    """Enfileira uma intenção de cancelamento para sincronização posterior."""
    payload_json = json.dumps({
        "venda_id": venda_id,
        "motivo":   motivo,
        "data_cancelamento": datetime.now().isoformat()
    }, ensure_ascii=False)

    local_db.enfileirar_sync("CANCELAR_VENDA", payload_json)
    return {"ok": True, "origem": "local", "status": "cancelamento_pendente"}


# =============================================================================
# CAMADA PRINCIPAL (INTERCEPTAÇÃO API)
# =============================================================================

class OfflineLayer:
    """
    Gerencia a alternância entre chamadas de API online e persistência local offline.
    """

    @staticmethod
    def listar_produtos(fn_api_online) -> list:
        if connectivity.esta_online():
            try:
                produtos = fn_api_online()
                if produtos:
                    local_db.upsert_produtos(produtos)
                return produtos
            except Exception:
                pass
        return local_db.listar_produtos_local()

    @staticmethod
    def obter_produto(produto_id, fn_api_online) -> Optional[dict]:
        if connectivity.esta_online():
            try:
                return fn_api_online()
            except Exception:
                pass
        return local_db.buscar_produto_local(str(produto_id))

    @staticmethod
    def criar_venda(venda_data: dict, fn_api_online) -> Optional[dict]:
        """Tenta enviar online; em caso de falha ou offline, salva localmente."""
        if connectivity.esta_online():
            try:
                return fn_api_online()
            except Exception as e:
                print(f"[OFFLINE_LAYER] Falha na API ao criar venda, migrando para local: {e}")
        
        return registrar_venda_offline(venda_data)

    @staticmethod
    def cancelar_venda(venda_id, motivo: str, fn_api_online) -> Optional[dict]:
        if connectivity.esta_online():
            try:
                return fn_api_online()
            except Exception:
                pass
        return cancelar_venda_offline(str(venda_id), motivo)

    @staticmethod
    def somente_online(nome_operacao: str, fn_api_online, fallback=None):
        """Executa a operação apenas se houver conexão, sem fallback local."""
        if connectivity.esta_online():
            try:
                return fn_api_online()
            except Exception:
                return fallback
        return fallback

    @staticmethod
    def pendentes_sync() -> int:
        """Retorna a quantidade de itens aguardando sincronização."""
        return local_db.contar_pendentes()

    @staticmethod
    def conflitos_sync() -> list:
        """Retorna lista de itens que falharam na sincronização por regras de negócio."""
        return local_db.listar_conflitos()