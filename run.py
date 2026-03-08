import flet as ft
import sys
import os

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

    def route_change(e):
        page.views.clear()

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