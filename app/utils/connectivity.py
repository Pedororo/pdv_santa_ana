import os
import threading
import time
import requests
from typing import Callable

# Tenta importar settings; se app.core ainda não existir, usa variável de
# ambiente ou o padrão localhost.
try:
    from app.core.config import settings
    _BASE_URL = settings.BASE_URL
except Exception:
    _BASE_URL = os.environ.get("PDV_BASE_URL", "http://localhost:8000")

_HEALTH_URL    = f"{_BASE_URL}/health"
_INTERVALO_SEG = 10
_TIMEOUT_SEG   = 3

# Estado global compartilhado (thread-safe via Lock)
_lock         = threading.Lock()
_esta_online  = True   # Assume online até provar o contrário no boot
_callbacks_on : list[Callable] = []   # Chamados quando OFFLINE → ONLINE
_callbacks_off: list[Callable] = []   # Chamados quando ONLINE  → OFFLINE
_monitor_ativo = False


def _checar_api() -> bool:
    """Faz um ping rápido no endpoint de health do backend."""
    try:
        r = requests.get(_HEALTH_URL, timeout=_TIMEOUT_SEG)
        return r.status_code == 200
    except requests.RequestException:
        # Qualquer erro de rede (Timeout, ConnectionRefused, etc)
        return False
    except Exception:
        return False


def _loop_monitor():
    """Roda em background verificando a saúde da rede a cada X segundos."""
    global _esta_online
    
    while _monitor_ativo:
        novo_estado = _checar_api()
        
        with _lock:
            estado_anterior = _esta_online
            mudou = novo_estado != estado_anterior
            _esta_online = novo_estado

        # Dispara eventos apenas se o estado da rede mudou (Edge Trigger)
        if mudou:
            if novo_estado:
                # Transição: OFFLINE → ONLINE
                print("[Conectividade] ✓ Voltou online — disparando callbacks de sync")
                for cb in _callbacks_on:
                    try:
                        # Roda em thread separada para não travar o monitor
                        threading.Thread(target=cb, daemon=True).start()
                    except Exception as e:
                        print(f"[Conectividade] Erro no callback online: {e}")
            else:
                # Transição: ONLINE → OFFLINE
                print("[Conectividade] ✗ Ficou offline — modo local ativado")
                for cb in _callbacks_off:
                    try:
                        threading.Thread(target=cb, daemon=True).start()
                    except Exception as e:
                        print(f"[Conectividade] Erro no callback offline: {e}")

        time.sleep(_INTERVALO_SEG)


# =============================================================================
# API PÚBLICA
# =============================================================================

def iniciar_monitor():
    """Inicia o loop de verificação em thread daemon. Chamar uma vez no boot."""
    global _monitor_ativo
    with _lock:
        if _monitor_ativo:
            return  # Já está rodando, evita threads duplicadas
        _monitor_ativo = True

    t = threading.Thread(target=_loop_monitor, daemon=True, name="ConnectivityMonitor")
    t.start()
    print(f"[Conectividade] Monitor iniciado — verificando {_HEALTH_URL} a cada {_INTERVALO_SEG}s")


def parar_monitor():
    """Para o loop de verificação (útil para testes ou encerramento limpo)."""
    global _monitor_ativo
    with _lock:
        _monitor_ativo = False


def esta_online() -> bool:
    """Retorna o estado atual da rede de forma thread-safe."""
    with _lock:
        return _esta_online


def esta_offline() -> bool:
    """Retorna o inverso do estado atual."""
    return not esta_online()


def ao_voltar_online(callback: Callable):
    """Registra função a ser chamada quando a rede volta (OFFLINE → ONLINE)."""
    if callback not in _callbacks_on:
        _callbacks_on.append(callback)


def ao_ficar_offline(callback: Callable):
    """Registra função a ser chamada quando a rede cai (ONLINE → OFFLINE)."""
    if callback not in _callbacks_off:
        _callbacks_off.append(callback)


def checar_agora() -> bool:
    """Verificação imediata fora do ciclo — útil no boot (ex: run.py)."""
    global _esta_online
    resultado = _checar_api()
    with _lock:
        _esta_online = resultado
    return resultado