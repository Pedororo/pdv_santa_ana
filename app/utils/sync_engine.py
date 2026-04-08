import json
import threading
import requests
import os
from datetime import datetime, timezone, timedelta

from app.utils.local_db import (
    listar_sync_pendentes, marcar_sync_enviado, marcar_sync_conflito,
    incrementar_tentativa, marcar_venda_sincronizada, contar_pendentes,
    upsert_produtos, get_ultima_sync_produtos, set_ultima_sync_produtos,
)

# =============================================================================
# CONFIGURAÇÃO DE URL (Sem depender do app.core.config)
# =============================================================================
_BASE_URL = os.environ.get("PDV_BASE_URL", "http://localhost:8000")

_TIMEOUT_SEG = 15
_MAX_TENTATIVAS = 3
_sync_lock = threading.Lock()
_callbacks_pos_sync: list = []

def ao_sincronizar(callback):
    _callbacks_pos_sync.append(callback)

def _renovar_token_se_necessario() -> str | None:
    from app.utils.local_db import carregar_sessao, atualizar_access_token
    sessao = carregar_sessao()
    if not sessao or not sessao.get("access_token"):
        return None

    try:
        expira_str = sessao.get("access_token_expira_em")
        expira_em = datetime.fromisoformat(expira_str).replace(tzinfo=timezone.utc) if expira_str else datetime.min.replace(tzinfo=timezone.utc)
        agora = datetime.now(timezone.utc)

        if expira_em > (agora + timedelta(seconds=10)):
            return sessao["access_token"]

        resp = requests.post(f"{_BASE_URL}/auth/refresh", 
                             json={"refresh_token": sessao.get("refresh_token")}, timeout=10)
        if resp.status_code == 200:
            novo_token = resp.json().get("access_token")
            nova_expira = (agora + timedelta(minutes=30)).isoformat()
            atualizar_access_token(novo_token, nova_expira)
            return novo_token
        return None
    except Exception:
        return None

def _processar_item(item: dict, access_token: str) -> bool:
    item_id, operacao = item["id"], item["operacao"]
    try:
        payload = json.loads(item["payload"])
    except:
        marcar_sync_conflito(item_id, "JSON Corrompido")
        return True

    if item.get("tentativas", 0) >= _MAX_TENTATIVAS:
        marcar_sync_conflito(item_id, "Limite de tentativas")
        return True

    if operacao == "REGISTRAR_VENDA":
        if payload.get("valor_total", 0) <= 0 or not payload.get("itens"):
            marcar_sync_conflito(item_id, "Venda zerada ou sem itens")
            return True

        if payload.get("turno_id") == "offline":
            try:
                r = requests.get(f"{_BASE_URL}/turnos/ativo", 
                                 headers={"Authorization": f"Bearer {access_token}"}, timeout=5)
                if r.status_code == 200 and r.json() and r.json().get("id"):
                    payload["turno_id"] = r.json()["id"]
                else:
                    return False
            except:
                return False

    try:
        url = f"{_BASE_URL}/vendas/" if operacao == "REGISTRAR_VENDA" else f"{_BASE_URL}/vendas/cancelar"
        resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {access_token}"}, timeout=_TIMEOUT_SEG)

        if resp.status_code in (200, 201):
            marcar_sync_enviado(item_id)
            venda_id = payload.get("id_offline") or payload.get("id")
            if venda_id: marcar_venda_sincronizada(venda_id)
            return True
        elif resp.status_code == 409:
            marcar_sync_conflito(item_id, "Duplicado")
            return True
        return False if resp.status_code in (401, 403) else True
    except:
        return False

def pausar_sync():
    """Para o sync engine adquirindo o lock indefinidamente (usado pelo reset)."""
    # Apenas sinaliza via flag — o lock não é adequado para pausar permanentemente.
    # O bloqueio real é feito pela flag _banco_foi_resetado no local_db.
    print("[Sync] Sync pausado até próximo login")

def sincronizar(forcar=False):
    # Bloqueia sync se o banco foi resetado — evita repopular imediatamente
    from app.utils.local_db import banco_foi_resetado
    if banco_foi_resetado():
        print("[Sync] Banco resetado — sync bloqueado até próximo login")
        return

    if not _sync_lock.acquire(blocking=False): return
    try:
        pendentes = listar_sync_pendentes()
        if not pendentes and not forcar:
            _sincronizar_produtos()
            return

        token = _renovar_token_se_necessario()
        if not token: return

        for item in pendentes:
            if not _processar_item(item, token): break

        _sincronizar_produtos()
        for cb in _callbacks_pos_sync: threading.Thread(target=cb, daemon=True).start()
    finally:
        _sync_lock.release()

def _sincronizar_produtos():
    # Bloqueia também aqui por segurança
    from app.utils.local_db import banco_foi_resetado, carregar_sessao
    if banco_foi_resetado():
        return
    sessao = carregar_sessao()
    if not sessao or not sessao.get("access_token"): return
    try:
        u = get_ultima_sync_produtos()
        r = requests.get(f"{_BASE_URL}/produtos/", 
                         headers={"Authorization": f"Bearer {sessao['access_token']}"},
                         params={"atualizado_apos": u} if u else {}, timeout=_TIMEOUT_SEG)
        if r.status_code == 200 and isinstance(r.json(), list):
            upsert_produtos(r.json())
            set_ultima_sync_produtos(datetime.now(timezone.utc).isoformat())
    except: pass

def sincronizar_em_background():
    threading.Thread(target=sincronizar, daemon=True, name="SyncEngine").start()