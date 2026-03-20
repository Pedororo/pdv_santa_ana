import flet as ft
import sys
import os
from app.views.styles.theme import Colors
from app.api.turno_api import TurnoAPI

# Garante que o Python encontre a pasta 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

        # Vendas exige turno ativo
        if page.route in ROTAS_REQUER_TURNO:
            try:
                turno_ativo = TurnoAPI.get_turno_ativo()
                if not turno_ativo:
                    # Permanece na home e mostra o modal
                    # Garante que a home está na view mesmo que já esteja
                    page.views.clear()
                    page.views.append(ft.View("/", controls=[HomeView(page)], padding=0))
                    page.update()
                    modal_sem_turno()
                    return
            except Exception:
                pass

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
    page.go("/login")  # ← inicia sempre pelo login

if __name__ == "__main__":
    ft.app(target=main)