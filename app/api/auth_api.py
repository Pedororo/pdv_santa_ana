import requests
from typing import Optional
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

# ============================================================================
# SESSÃO GLOBAL — tokens e dados do usuário logado
# ============================================================================
_sessao = {
    "access_token":  None,
    "refresh_token": None,
    "username":      None,
    "role":          None,
    "usuario_id":    None,
    "usuario_nome":  None,
}


def get_access_token() -> Optional[str]:
    return _sessao["access_token"]

def get_username() -> Optional[str]:
    return _sessao["username"]

def get_role() -> Optional[str]:
    return _sessao["role"]

def esta_logado() -> bool:
    return _sessao["access_token"] is not None

def _salvar_tokens(access_token: str, refresh_token: str):
    _sessao["access_token"]  = access_token
    _sessao["refresh_token"] = refresh_token

def logout():
    for k in _sessao:
        _sessao[k] = None
    # Limpa sessão persistida no SQLite
    try:
        from app.utils.local_db import limpar_sessao
        limpar_sessao()
    except Exception as e:
        print(f"[Auth] Erro ao limpar sessão local: {e}")


# ============================================================================
# HEADERS COM TOKEN
# ============================================================================
def headers_auth() -> dict:
    token = _sessao["access_token"]
    if not token:
        return {"Content-Type": "application/json"}
    return {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {token}",
    }


# ============================================================================
# REFRESH AUTOMÁTICO
# ============================================================================
def _tentar_refresh() -> bool:
    refresh = _sessao["refresh_token"]
    if not refresh:
        # Tenta pegar da sessão local (modo offline)
        try:
            from app.utils.local_db import carregar_sessao
            sessao_local = carregar_sessao()
            if sessao_local:
                refresh = sessao_local.get("refresh_token")
                _sessao["refresh_token"] = refresh
        except Exception:
            pass

    if not refresh:
        return False

    try:
        resp = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            novo_access  = data["access_token"]
            novo_refresh = data.get("refresh_token", refresh)
            _salvar_tokens(novo_access, novo_refresh)

            # Persiste novo access_token localmente
            try:
                from app.utils.local_db import atualizar_access_token
                nova_expira = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
                atualizar_access_token(novo_access, nova_expira)
            except Exception as e:
                print(f"[Auth] Erro ao persistir novo token: {e}")

            return True
        return False
    except (requests.ConnectionError, requests.Timeout):
        # Sem rede — NÃO derruba a sessão, usuário pode continuar offline
        print("[Auth] Sem conexão para renovar token — sessão local mantida")
        return False
    except Exception as e:
        print(f"[Auth] Erro no refresh: {e}")
        return False


def request_com_auth(method: str, url: str, **kwargs) -> requests.Response:
    """
    Wrapper para requests que:
    1. Injeta o token automaticamente
    2. Se receber 401, tenta refresh e retenta UMA vez
    3. Se refresh falhar ONLINE  → SessionExpiredError (força novo login)
       Se refresh falhar OFFLINE → OfflineSessionError (sessão mantida, operação bloqueada)
    """
    from app.utils.connectivity import esta_online

    kwargs.setdefault("headers", {}).update(headers_auth())
    kwargs.setdefault("timeout", 10)

    try:
        resp = requests.request(method, url, **kwargs)
    except (requests.ConnectionError, requests.Timeout):
        # Sem rede — propaga como ConnectionError para a OfflineLayer tratar
        raise

    if resp.status_code == 401:
        print("[Auth] Token expirado, tentando refresh...")
        if _tentar_refresh():
            kwargs["headers"].update(headers_auth())
            resp = requests.request(method, url, **kwargs)
        else:
            if not esta_online():
                # Offline com token expirado — mantém sessão local, bloqueia só esta operação
                print("[Auth] Offline com token expirado — sessão local preservada")
                raise OfflineSessionError(
                    "Token expirado e sem conexão. "
                    "Operações online indisponíveis até reconectar."
                )
            # Online mas refresh falhou → sessão inválida, força relogin
            print("[Auth] Refresh falhou — usuário precisa fazer login novamente")
            logout()
            raise SessionExpiredError("Sessão expirada. Faça login novamente.")

    return resp


class SessionExpiredError(Exception):
    pass


class OfflineSessionError(Exception):
    """Token expirado durante uso offline. Sessão local intacta."""
    pass


# ============================================================================
# RESTAURAR SESSÃO DO SQLite (chamado no boot, antes do login)
# ============================================================================
def restaurar_sessao_local() -> bool:
    """
    Tenta restaurar a sessão do SQLite ao abrir o app.
    Retorna True se conseguiu restaurar uma sessão válida.
    Usado para manter o usuário logado entre sessões e no modo offline.
    """
    try:
        from app.utils.local_db import carregar_sessao
        from datetime import timezone

        sessao = carregar_sessao()
        if not sessao:
            return False

        refresh_expira = datetime.fromisoformat(sessao["refresh_token_expira_em"])
        agora          = datetime.utcnow()

        if refresh_expira < agora:
            print("[Auth] Refresh token da sessão local expirado — requer novo login")
            return False

        # Restaura sessão em memória
        _sessao["access_token"]  = sessao["access_token"]
        _sessao["refresh_token"] = sessao["refresh_token"]
        _sessao["username"]      = sessao["username"]
        _sessao["role"]          = sessao["role"]
        _sessao["usuario_id"]    = sessao["usuario_id"]
        _sessao["usuario_nome"]  = sessao["usuario_nome"]

        print(f"[Auth] Sessão restaurada para '{sessao['username']}' (modo offline possível)")
        return True

    except Exception as e:
        print(f"[Auth] Erro ao restaurar sessão local: {e}")
        return False


# ============================================================================
# LOGIN
# ============================================================================
class AuthAPI:
    @staticmethod
    def login(username: str, password: str) -> dict | None:
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/login",
                data={"username": username, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                _salvar_tokens(data["access_token"], data["refresh_token"])

                # Decodifica payload do JWT para pegar username, role e id
                import base64, json as _json
                usuario_id   = ""
                usuario_nome = ""
                role         = ""
                try:
                    payload_b64 = data["access_token"].split(".")[1]
                    payload_b64 += "=" * (4 - len(payload_b64) % 4)
                    payload = _json.loads(base64.b64decode(payload_b64))
                    _sessao["username"]     = payload.get("sub")
                    _sessao["role"]         = payload.get("role")
                    _sessao["usuario_id"]   = str(payload.get("id", ""))
                    _sessao["usuario_nome"] = payload.get("nome", payload.get("sub", ""))
                    usuario_id   = _sessao["usuario_id"]
                    usuario_nome = _sessao["usuario_nome"]
                    role         = _sessao["role"] or ""
                except Exception:
                    pass

                # Persiste sessão no SQLite para uso offline futuro
                try:
                    from app.utils.local_db import salvar_sessao
                    access_expira  = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
                    refresh_expira = (datetime.utcnow() + timedelta(days=7)).isoformat()
                    salvar_sessao(
                        usuario_id              = usuario_id,
                        usuario_nome            = usuario_nome,
                        username                = _sessao["username"] or username,
                        role                    = role,
                        access_token            = data["access_token"],
                        refresh_token           = data["refresh_token"],
                        access_token_expira_em  = access_expira,
                        refresh_token_expira_em = refresh_expira,
                    )
                except Exception as e:
                    print(f"[Auth] Erro ao persistir sessão: {e}")

                # Libera o sync engine caso banco tenha sido resetado
                try:
                    from app.utils.local_db import confirmar_novo_login
                    confirmar_novo_login()
                except Exception:
                    pass

                return data

            elif resp.status_code == 401:
                return None
            else:
                print(f"[Auth] Login erro {resp.status_code}: {resp.text}")
                return None

        except requests.ConnectionError:
            # Sem conexão — tenta usar sessão local
            print("[Auth] Sem conexão — tentando sessão local...")
            if restaurar_sessao_local():
                # Retorna estrutura mínima para o front saber que logou
                return {
                    "access_token":  _sessao["access_token"],
                    "refresh_token": _sessao["refresh_token"],
                    "origem":        "local",
                }
            return None

        except Exception as e:
            print(f"[Auth] Erro de conexão no login: {e}")
            return None