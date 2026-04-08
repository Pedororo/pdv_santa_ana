import sqlite3
import os
from datetime import datetime

# Caminho relativo ao próprio arquivo (app/utils/local_db.py → app/utils/local.db)
# Funciona em qualquer PC independente de onde o projeto estiver instalado.
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "local.db")

# Flag em memória: True enquanto o banco acabou de ser resetado.
# ATENÇÃO: esta flag é TAMBÉM persistida no banco (sync_meta) para
# sobreviver entre processos — a versão só-memória não funcionava
# porque o reset CLI e o boot do app são processos diferentes.
_banco_foi_resetado = False

def banco_foi_resetado() -> bool:
    """
    Retorna True se o banco foi resetado e ainda não houve novo login.
    Verifica memória primeiro (rápido), depois o banco (cross-processo).
    """
    global _banco_foi_resetado
    if _banco_foi_resetado:
        return True
    # Verifica flag persistida — sobrevive entre processos
    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT valor FROM sync_meta WHERE chave = 'banco_resetado'"
        ).fetchone()
        conn.close()
        if row and row["valor"] == "1":
            _banco_foi_resetado = True  # sincroniza memória
            return True
    except Exception:
        pass
    return False

def confirmar_novo_login():
    """Chamado após login bem-sucedido — libera o sync novamente."""
    global _banco_foi_resetado
    _banco_foi_resetado = False
    # Remove flag persistida do banco também
    try:
        conn = _get_conn()
        with conn:
            conn.execute(
                "DELETE FROM sync_meta WHERE chave = 'banco_resetado'"
            )
        conn.close()
    except Exception:
        pass


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def inicializar_banco():
    conn = _get_conn()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id          TEXT PRIMARY KEY,
                nome        TEXT NOT NULL,
                codigo_barra TEXT,
                preco_venda REAL NOT NULL,
                preco_compra REAL,
                estoque_ref INTEGER,
                estoque_minimo INTEGER DEFAULT 5,
                categoria_id TEXT,
                categoria_nome TEXT,
                ativo       INTEGER DEFAULT 1,
                updated_at  TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vendas_local (
                id              TEXT PRIMARY KEY,
                payload_json    TEXT NOT NULL,
                vendedor_id     TEXT NOT NULL,
                vendedor_nome   TEXT,
                criado_em       TEXT NOT NULL,
                sincronizado    INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                operacao    TEXT NOT NULL,
                payload     TEXT NOT NULL,
                status      TEXT DEFAULT 'PENDENTE',
                tentativas  INTEGER DEFAULT 0,
                erro_detalhe TEXT,
                criado_em   TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessao_local (
                id                      INTEGER PRIMARY KEY CHECK (id = 1),
                usuario_id              TEXT NOT NULL,
                usuario_nome            TEXT NOT NULL,
                username                TEXT NOT NULL,
                role                    TEXT NOT NULL,
                access_token            TEXT NOT NULL,
                refresh_token           TEXT NOT NULL,
                access_token_expira_em  TEXT NOT NULL,
                refresh_token_expira_em TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_meta (
                chave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_local (
                id          TEXT PRIMARY KEY,
                nome        TEXT NOT NULL,
                username    TEXT NOT NULL,
                role        TEXT NOT NULL,
                ativo       INTEGER DEFAULT 1
            )
        """)
    conn.close()


# =============================================================================
# GESTÃO DE SESSÃO
# =============================================================================

def salvar_sessao(usuario_id, usuario_nome, username, role,
                  access_token, refresh_token,
                  access_token_expira_em, refresh_token_expira_em):
    conn = _get_conn()
    with conn:
        conn.execute("""
            INSERT INTO sessao_local
                (id, usuario_id, usuario_nome, username, role,
                 access_token, refresh_token,
                 access_token_expira_em, refresh_token_expira_em)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                usuario_id              = excluded.usuario_id,
                usuario_nome            = excluded.usuario_nome,
                username                = excluded.username,
                role                    = excluded.role,
                access_token            = excluded.access_token,
                refresh_token           = excluded.refresh_token,
                access_token_expira_em  = excluded.access_token_expira_em,
                refresh_token_expira_em = excluded.refresh_token_expira_em
        """, (usuario_id, usuario_nome, username, role,
              access_token, refresh_token,
              access_token_expira_em, refresh_token_expira_em))
    conn.close()


def carregar_sessao() -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM sessao_local WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def atualizar_access_token(access_token: str, expira_em: str):
    conn = _get_conn()
    with conn:
        conn.execute("""
            UPDATE sessao_local
            SET access_token = ?, access_token_expira_em = ?
            WHERE id = 1
        """, (access_token, expira_em))
    conn.close()


def limpar_sessao():
    conn = _get_conn()
    with conn:
        conn.execute("DELETE FROM sessao_local WHERE id = 1")
    conn.close()


# =============================================================================
# GESTÃO DE PRODUTOS
# =============================================================================

def upsert_produtos(produtos: list[dict]):
    conn = _get_conn()
    with conn:
        for p in produtos:
            conn.execute("""
                INSERT INTO produtos
                    (id, nome, codigo_barra, preco_venda, preco_compra,
                     estoque_ref, estoque_minimo, categoria_id, categoria_nome,
                     ativo, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    nome           = excluded.nome,
                    codigo_barra   = excluded.codigo_barra,
                    preco_venda    = excluded.preco_venda,
                    preco_compra   = excluded.preco_compra,
                    estoque_ref    = excluded.estoque_ref,
                    estoque_minimo = excluded.estoque_minimo,
                    categoria_id   = excluded.categoria_id,
                    categoria_nome = excluded.categoria_nome,
                    ativo          = excluded.ativo,
                    updated_at     = excluded.updated_at
            """, (
                str(p.get("id", "")),
                p.get("nome", ""),
                p.get("codigo_barra", ""),
                float(p.get("preco_venda", 0)),
                float(p.get("preco_compra", 0)),
                int(p.get("estoque", 0)),
                int(p.get("estoque_minimo", 5)),
                str(p.get("categoria_id", "")),
                p.get("categoria_nome", ""),
                1 if p.get("ativo", True) else 0,
                p.get("updated_at", datetime.now().isoformat()),
            ))
    conn.close()


def listar_produtos_local() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buscar_produto_local(produto_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# =============================================================================
# GESTÃO DE VENDAS E SINCRONIZAÇÃO
# =============================================================================

def salvar_venda_local(venda_id: str, payload_json: str,
                       vendedor_id: str, vendedor_nome: str):
    conn = _get_conn()
    with conn:
        conn.execute("""
            INSERT OR IGNORE INTO vendas_local
                (id, payload_json, vendedor_id, vendedor_nome, criado_em)
            VALUES (?, ?, ?, ?, ?)
        """, (venda_id, payload_json, vendedor_id, vendedor_nome,
              datetime.now().isoformat()))
    conn.close()


def marcar_venda_sincronizada(venda_id: str):
    conn = _get_conn()
    with conn:
        conn.execute("UPDATE vendas_local SET sincronizado = 1 WHERE id = ?", (venda_id,))
    conn.close()


def listar_vendas_pendentes_local() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM vendas_local WHERE sincronizado = 0 ORDER BY criado_em"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def enfileirar_sync(operacao: str, payload: str):
    conn = _get_conn()
    with conn:
        conn.execute("""
            INSERT INTO sync_queue (operacao, payload, criado_em)
            VALUES (?, ?, ?)
        """, (operacao, payload, datetime.now().isoformat()))
    conn.close()


def listar_sync_pendentes() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT * FROM sync_queue
        WHERE status = 'PENDENTE'
        ORDER BY criado_em ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def marcar_sync_enviado(item_id: int):
    conn = _get_conn()
    with conn:
        conn.execute("UPDATE sync_queue SET status = 'ENVIADO' WHERE id = ?", (item_id,))
    conn.close()


def marcar_sync_conflito(item_id: int, detalhe: str):
    conn = _get_conn()
    with conn:
        conn.execute("""
            UPDATE sync_queue
            SET status = 'CONFLITO', erro_detalhe = ?
            WHERE id = ?
        """, (detalhe, item_id))
    conn.close()


def incrementar_tentativa(item_id: int):
    conn = _get_conn()
    with conn:
        conn.execute(
            "UPDATE sync_queue SET tentativas = tentativas + 1 WHERE id = ?",
            (item_id,)
        )
    conn.close()


def contar_pendentes() -> int:
    conn = _get_conn()
    row = conn.execute(
        "SELECT COUNT(*) as total FROM sync_queue WHERE status = 'PENDENTE'"
    ).fetchone()
    conn.close()
    return row["total"] if row else 0


def listar_conflitos() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM sync_queue WHERE status = 'CONFLITO' ORDER BY criado_em"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ultima_sync_produtos() -> str | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT valor FROM sync_meta WHERE chave = 'ultima_sync_produtos'"
    ).fetchone()
    conn.close()
    return row["valor"] if row else None


def set_ultima_sync_produtos(timestamp: str):
    conn = _get_conn()
    with conn:
        conn.execute("""
            INSERT INTO sync_meta (chave, valor) VALUES ('ultima_sync_produtos', ?)
            ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
        """, (timestamp,))
    conn.close()


# =============================================================================
# RESET DO BANCO LOCAL
# =============================================================================

# =============================================================================
# GESTÃO DE USUÁRIOS LOCAL (espelho offline)
# =============================================================================

def upsert_usuarios_local(usuarios: list[dict]):
    """Salva ou atualiza lista de usuários no espelho local."""
    conn = _get_conn()
    with conn:
        for u in usuarios:
            conn.execute("""
                INSERT INTO usuarios_local (id, nome, username, role, ativo)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    nome     = excluded.nome,
                    username = excluded.username,
                    role     = excluded.role,
                    ativo    = excluded.ativo
            """, (
                str(u.get("id", "")),
                u.get("nome", ""),
                u.get("username", ""),
                u.get("role", ""),
                1 if u.get("ativo", True) else 0,
            ))
    conn.close()


def listar_usuarios_local() -> list[dict]:
    """Retorna todos os usuários do espelho local."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM usuarios_local ORDER BY nome").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resetar_banco(remover_pasta: bool = False, parar_sync: bool = True):
    """
    Reseta completamente o banco SQLite local.

    POR QUE OS DADOS "VOLTAM" APÓS O RESET:
    ─────────────────────────────────────────
    O reset apaga o arquivo .db corretamente, MAS o sistema possui threads
    em background (sync_engine, monitor de conectividade) que continuam
    rodando e reinserem dados automaticamente:

    1. sincronizar_em_background() — ao detectar conexão, chama a API e
       faz upsert_produtos(), repopulando a tabela de produtos.
    2. restaurar_sessao_local() — no próximo boot, relê a sessão do SQLite.
       Se o login acontecer antes do reset ser percebido, salvar_sessao()
       regrava tudo.
    3. WAL mode — o SQLite com WAL pode ter dados em arquivos -wal e -shm
       que persistem mesmo após deletar o .db principal se as conexões não
       forem fechadas corretamente.

    SOLUÇÃO: este método para o sync antes de deletar, remove os arquivos
    WAL auxiliares e limpa a sessão em memória também.

    Parâmetros:
    - remover_pasta: se True, remove toda a pasta .pdv_santa_ana
    - parar_sync:    se True (padrão), tenta pausar o sync engine antes do reset

    Uso:
        from app.utils.local_db import resetar_banco
        resetar_banco()           # reset completo seguro
        resetar_banco(True)       # remove pasta inteira
        resetar_banco(parar_sync=False)  # força sem parar sync (uso CLI)
    """
    import shutil

    print("[Reset] Iniciando reset do banco local...")

    # ── 1. Para o sync engine para evitar que dados sejam reinseridos ────────
    if parar_sync:
        try:
            from app.utils.sync_engine import pausar_sync
            pausar_sync()
            print("[Reset] ✓ Sync engine pausado")
        except Exception as ex:
            print(f"[Reset] ⚠ Não foi possível pausar o sync: {ex}")

    # ── 2. Limpa a sessão em memória (evita que restaurar_sessao_local
    #        reescreva no banco logo após o reset) ────────────────────────────
    try:
        from app.api.auth_api import limpar_sessao_memoria
        limpar_sessao_memoria()
        print("[Reset] ✓ Sessão em memória limpa")
    except Exception as ex:
        print(f"[Reset] ⚠ Não foi possível limpar sessão em memória: {ex}")

    # ── 3. Fecha todas as conexões SQLite abertas ────────────────────────────
    try:
        conn = sqlite3.connect(_DB_PATH)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # força flush do WAL
        conn.close()
        print("[Reset] ✓ Conexões fechadas e WAL truncado")
    except Exception as ex:
        print(f"[Reset] ⚠ Erro ao fechar conexões: {ex}")

    # ── 4. Remove o banco e arquivos WAL auxiliares ──────────────────────────
    if remover_pasta:
        pasta = os.path.dirname(_DB_PATH)
        if os.path.exists(pasta):
            shutil.rmtree(pasta)
            print(f"[Reset] ✓ Pasta removida: {pasta}")
        else:
            print("[Reset] Pasta não encontrada — nada a remover")
    else:
        # Remove .db principal + arquivos WAL auxiliares (-wal e -shm)
        for caminho in [_DB_PATH, _DB_PATH + "-wal", _DB_PATH + "-shm"]:
            if os.path.exists(caminho):
                os.remove(caminho)
                print(f"[Reset] ✓ Removido: {caminho}")

    # ── 5. Ativa flag em memória — bloqueia sync no processo atual ───────────
    global _banco_foi_resetado
    _banco_foi_resetado = True

    # ── 6. Recria do zero com todas as tabelas ───────────────────────────────
    inicializar_banco()

    # ── 7. Persiste flag no banco recriado — bloqueia sync em processos futuros
    #   ESTA É A CORREÇÃO DO BUG: a flag só em memória morria ao fechar o CLI.
    #   Agora o próximo boot lê 'banco_resetado=1' da sync_meta e bloqueia o
    #   sync_engine até que confirmar_novo_login() seja chamado após login.
    try:
        conn = _get_conn()
        with conn:
            conn.execute("""
                INSERT INTO sync_meta (chave, valor) VALUES ('banco_resetado', '1')
                ON CONFLICT(chave) DO UPDATE SET valor = '1'
            """)
        conn.close()
        print("[Reset] ✓ Flag de reset persistida no banco (cross-processo)")
    except Exception as ex:
        print(f"[Reset] ⚠ Não foi possível persistir flag: {ex}")

    print("[Reset] ✓ Banco recriado vazio com sucesso")
    print(f"[Reset] ✓ Localização: {_DB_PATH}")
    print("[Reset] ⚠ ATENÇÃO: sync bloqueado até próximo login.")


def diagnosticar_banco() -> dict:
    """
    Retorna um diagnóstico do estado atual do banco local.
    Útil para rastrear de onde os dados estão vindo após um reset.

    Uso:
        from app.utils.local_db import diagnosticar_banco
        import pprint
        pprint.pprint(diagnosticar_banco())
    """
    resultado = {
        "db_path": _DB_PATH,
        "db_existe": os.path.exists(_DB_PATH),
        "wal_existe": os.path.exists(_DB_PATH + "-wal"),
        "shm_existe": os.path.exists(_DB_PATH + "-shm"),
        "db_tamanho_bytes": os.path.getsize(_DB_PATH) if os.path.exists(_DB_PATH) else 0,
        "sessao": None,
        "total_produtos": 0,
        "total_vendas_pendentes": 0,
        "total_sync_pendentes": 0,
        "total_sync_conflitos": 0,
        "ultima_sync_produtos": None,
        "origem_suspeita": [],
    }

    if not resultado["db_existe"]:
        resultado["origem_suspeita"].append("Banco não existe — dados vêm 100% da API/memória")
        return resultado

    try:
        conn = _get_conn()

        sessao = conn.execute("SELECT usuario_nome, username, role FROM sessao_local WHERE id = 1").fetchone()
        if sessao:
            resultado["sessao"] = dict(sessao)

        resultado["total_produtos"] = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        resultado["total_vendas_pendentes"] = conn.execute(
            "SELECT COUNT(*) FROM vendas_local WHERE sincronizado = 0"
        ).fetchone()[0]
        resultado["total_sync_pendentes"] = conn.execute(
            "SELECT COUNT(*) FROM sync_queue WHERE status = 'PENDENTE'"
        ).fetchone()[0]
        resultado["total_sync_conflitos"] = conn.execute(
            "SELECT COUNT(*) FROM sync_queue WHERE status = 'CONFLITO'"
        ).fetchone()[0]

        meta = conn.execute(
            "SELECT valor FROM sync_meta WHERE chave = 'ultima_sync_produtos'"
        ).fetchone()
        resultado["ultima_sync_produtos"] = meta["valor"] if meta else None

        conn.close()
    except Exception as ex:
        resultado["origem_suspeita"].append(f"Erro ao ler banco: {ex}")

    # ── Diagnóstico de origens suspeitas ────────────────────────────────────
    if resultado["wal_existe"]:
        resultado["origem_suspeita"].append(
            "Arquivo -wal existe: dados podem estar no WAL e não foram "
            "commitados/removidos antes do delete do .db"
        )
    if resultado["total_produtos"] > 0 and resultado["ultima_sync_produtos"]:
        resultado["origem_suspeita"].append(
            f"Produtos foram sincronizados da API em: {resultado['ultima_sync_produtos']} — "
            "o sync_engine repopulou após o reset"
        )
    if resultado["sessao"]:
        resultado["origem_suspeita"].append(
            f"Sessão ativa para '{resultado['sessao']['username']}' — "
            "login ou restaurar_sessao_local() regravou após o reset"
        )

    return resultado