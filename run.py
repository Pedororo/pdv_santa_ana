import flet as ft
import sys
import os

# Garante que o Python encontre a pasta 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# =========================================================================
# CLI — COMANDOS DE MANUTENÇÃO (rodam antes de qualquer boot do app)
# Uso: python run.py reset-local
# =========================================================================
if len(sys.argv) > 1:
    cmd = sys.argv[1].lower()

    if cmd == "reset-local":
        print("=" * 50)
        print("  PDV Santa Ana — Reset do Banco Local")
        print("=" * 50)

        from app.utils.local_db import resetar_banco, _DB_PATH
        resetar_banco(parar_sync=False)
        print(f"  ✓ Banco em: {_DB_PATH}")

        print("=" * 50)
        print("  Banco local zerado. Próximo login fará novo sync.")
        print("=" * 50)
        sys.exit(0)

    else:
        print(f"Comando desconhecido: '{cmd}'")
        print("Comandos disponíveis:")
        print("  reset-local   Apaga o banco SQLite local e recria vazio")
        sys.exit(1)

# =========================================================================
# BOOT — ORQUESTRAÇÃO DE SERVIÇOS CRÍTICOS
# Deve rodar ANTES de qualquer import de view ou API que use o SQLite.
# =========================================================================
from app.views.styles.theme import Colors
from app.api.turno_api import TurnoAPI
from app.api.auth_api import get_role
from app.utils.local_db import inicializar_banco
from app.api.auth_api import restaurar_sessao_local
from app.utils.connectivity import iniciar_monitor, checar_agora
from app.utils.sync_engine import sincronizar_em_background

inicializar_banco()        # 1. Cria tabelas se não existirem
restaurar_sessao_local()   # 2. Carrega tokens em memória para uso offline (não pula login)
checar_agora()             # 3. Determina estado online/offline imediatamente
iniciar_monitor()          # 4. Sobe thread daemon que verifica rede a cada 10s
sincronizar_em_background() # 5. Sobe a thread que gerencia o envio de vendas offline (Sync Engine)

# =========================================================================

from app.views.home_view import HomeView
from app.views.vendas_view import VendasView
from app.views.estoque_view import EstoqueView
from app.views.usuarios_view import UsuariosView
from app.views.historico_view import HistoricoView
from app.views.relatorios_view import RelatoriosView
from app.views.login_view import LoginView


def main(page: ft.Page):
    page.title = "PDV Santa Ana"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.maximized = True
    page.padding = 0

    # Define a raiz para imagens
    page.assets_dir = "app"

    # =========================================================================
    # CONFIRMAÇÃO DE SAÍDA — X da janela e botão Sair
    # =========================================================================
    def confirmar_saida(e):
        if page.route == "/login":
            page.window.prevent_close = False
            page.window.close()
            return

        def sair(ev):
            modal.open = False
            page.update()
            page.window.prevent_close = False
            page.window.close()

        def cancelar(ev):
            modal.open = False
            page.window.prevent_close = True
            page.update()

        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=Colors.TEXT_WHITE, size=24),
                    ft.Text("Sair do Sistema", size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_RED,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            content=ft.Container(
                width=340,
                content=ft.Column(
                    tight=True, spacing=12,
                    controls=[
                        ft.Container(height=6),
                        ft.Text(
                            "Tem certeza que deseja sair?",
                            size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Certifique-se de que o turno foi fechado antes de sair.",
                            size=13, color=Colors.TEXT_GRAY, text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=cancelar,
                    style=ft.ButtonStyle(color=Colors.TEXT_GRAY),
                ),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.icons.LOGOUT, size=16, color=Colors.TEXT_WHITE),
                        ft.Text("Sim, sair", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
                    ], spacing=6, tight=True),
                    bgcolor=Colors.BRAND_RED,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=sair,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.window.prevent_close = True
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()

    page.window.prevent_close = True
    page.window.on_event = lambda e: confirmar_saida(e) if e.data == "close" else None
    page.confirmar_saida = confirmar_saida  # expõe para views

    # Apenas vendas exige turno aberto
    ROTAS_REQUER_TURNO = ["/vendas"]

    # Apenas admins podem acessar
    ROTAS_REQUER_ADMIN = ["/usuarios"]

    def modal_sem_permissao():
        def fechar(ev):
            modal.open = False
            page.route = "/"
            page.update()

        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.BLOCK, color=Colors.TEXT_WHITE, size=24),
                    ft.Text("Acesso Negado", size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_RED,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True, spacing=12,
                    controls=[
                        ft.Container(height=6),
                        ft.Icon(ft.icons.LOCK, size=48, color=Colors.BRAND_RED),
                        ft.Text(
                            "Você não tem permissão para acessar esta área.",
                            size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "O gerenciamento de usuários é restrito a administradores.",
                            size=13, color=Colors.TEXT_GRAY, text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            actions=[
                ft.ElevatedButton(
                    "Entendido",
                    bgcolor=Colors.BRAND_RED, color=Colors.TEXT_WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=fechar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()

    def modal_sem_turno():
        def fechar(ev):
            modal.open = False
            page.route = "/"
            page.update()

        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.PUNCH_CLOCK, color=Colors.TEXT_WHITE, size=24),
                    ft.Text("Nenhum Turno Aberto", size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_ORANGE,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True, spacing=12,
                    controls=[
                        ft.Container(height=6),
                        ft.Icon(ft.icons.LOCK_CLOCK, size=48, color=Colors.BRAND_ORANGE),
                        ft.Text(
                            "É necessário abrir um turno antes de realizar vendas.",
                            size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Acesse o Menu Principal e clique em 'Abrir Turno'.",
                            size=13, color=Colors.TEXT_GRAY, text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            actions=[
                ft.ElevatedButton(
                    "Entendido",
                    bgcolor=Colors.BRAND_ORANGE, color=Colors.TEXT_WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=fechar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()

    def route_change(e):
        page.views.clear()

        # Vendas exige turno ativo (só verifica se estiver online)
        if page.route in ROTAS_REQUER_TURNO:
            from app.utils.connectivity import esta_online
            if esta_online():
                try:
                    turno_ativo = TurnoAPI.get_turno_ativo()
                    if not turno_ativo or (turno_ativo.get("status") or "").upper() != "ABERTO":
                        page.views.clear()
                        page.views.append(ft.View("/", controls=[HomeView(page)], padding=0))
                        page.update()
                        modal_sem_turno()
                        return
                except Exception:
                    pass
            # Offline: permite entrar em vendas (badge já avisa o estado)

        # Usuários exige role admin
        if page.route in ROTAS_REQUER_ADMIN:
            if (get_role() or "").lower() not in ("admin", "gerente"):
                page.views.clear()
                page.views.append(ft.View("/", controls=[HomeView(page)], padding=0))
                page.update()
                modal_sem_permissao()
                return

        # Rota Login
        if page.route == "/login":
            page.views.append(
                ft.View(
                    "/login",
                    controls=[LoginView(page)],
                    padding=0,
                )
            )

        # Rota Home
        elif page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    controls=[HomeView(page)],
                    padding=0,
                )
            )

        # Rota Vendas
        elif page.route == "/vendas":
            page.views.append(
                ft.View(
                    "/vendas",
                    controls=[VendasView(page)],
                    padding=0,
                )
            )

        # Rota Estoque
        elif page.route == "/estoque":
            page.views.append(
                ft.View(
                    "/estoque",
                    controls=[EstoqueView(page)],
                    padding=0,
                )
            )

        # Rota Usuários
        elif page.route == "/usuarios":
            page.views.append(
                ft.View(
                    "/usuarios",
                    controls=[UsuariosView(page)],
                    padding=0,
                )
            )

        # Rota Histórico
        elif page.route == "/historico":
            page.views.append(
                ft.View(
                    "/historico",
                    controls=[HistoricoView(page)],
                    padding=0,
                )
            )

        # Rota Relatórios
        elif page.route == "/relatorios":
            page.views.append(
                ft.View(
                    "/relatorios",
                    controls=[RelatoriosView(page)],
                    padding=0,
                )
            )

        page.update()

    page.on_route_change = route_change
    page.go("/login")  # Sempre exige login — sessão local só serve para uso offline após autenticação

if __name__ == "__main__":
    ft.app(target=main)