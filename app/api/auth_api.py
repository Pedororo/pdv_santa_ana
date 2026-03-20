import requests
from typing import Optional

BASE_URL = "http://localhost:8000"

# ============================================================================
# SESSÃO GLOBAL — tokens e dados do usuário logado
# ============================================================================
_sessao = {
    "access_token":  None,
    "refresh_token": None,
    "username":      None,
    "role":          None,
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


# ============================================================================
# HEADERS COM TOKEN
# ============================================================================
def headers_auth() -> dict:
    """Retorna headers com Authorization Bearer para usar em todas as APIs"""
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
    """Tenta renovar o access_token usando o refresh_token. Retorna True se ok."""
    refresh = _sessao["refresh_token"]
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
            _salvar_tokens(data["access_token"], data["refresh_token"])
            return True
        return False
    except Exception as e:
        print(f"[Auth] Erro no refresh: {e}")
        return False


def request_com_auth(method: str, url: str, **kwargs) -> requests.Response:
    """
    Wrapper para requests que:
    1. Injeta o token automaticamente
    2. Se receber 401, tenta refresh e retentar UMA vez
    3. Se refresh falhar, levanta exceção para o front tratar (redirecionar pro login)
    """
    kwargs.setdefault("headers", {}).update(headers_auth())
    kwargs.setdefault("timeout", 10)

    resp = requests.request(method, url, **kwargs)

    if resp.status_code == 401:
        print("[Auth] Token expirado, tentando refresh...")
        if _tentar_refresh():
            # Atualiza header com novo token e retentar
            kwargs["headers"].update(headers_auth())
            resp = requests.request(method, url, **kwargs)
        else:
            print("[Auth] Refresh falhou — usuário precisa fazer login novamente")
            logout()
            # Levanta exceção específica para o front capturar e redirecionar
            raise SessionExpiredError("Sessão expirada. Faça login novamente.")

    return resp


class SessionExpiredError(Exception):
    """Levantada quando o token e o refresh estão ambos expirados"""
    pass


# ============================================================================
# LOGIN
# ============================================================================
class AuthAPI:
    @staticmethod
    def login(username: str, password: str) -> dict | None:
        """
        Autentica o usuário. Retorna dict com dados do usuário ou None se falhar.
        Usa OAuth2PasswordRequestForm → envia como form-data (não JSON)
        """
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/login",
                data={"username": username, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                _salvar_tokens(data["access_token"], data["refresh_token"])

                # Decodifica payload do token para pegar username e role
                # (sem verificar assinatura — só pra pegar os dados)
                import base64, json
                try:
                    payload_b64 = data["access_token"].split(".")[1]
                    # Adiciona padding se necessário
                    payload_b64 += "=" * (4 - len(payload_b64) % 4)
                    payload = json.loads(base64.b64decode(payload_b64))
                    _sessao["username"] = payload.get("sub")
                    _sessao["role"]     = payload.get("role")
                except Exception:
                    pass

                return data
            elif resp.status_code == 401:
                return None
            else:
                print(f"[Auth] Login erro {resp.status_code}: {resp.text}")
                return None
        except Exception as e:
            print(f"[Auth] Erro de conexão no login: {e}")
            return None