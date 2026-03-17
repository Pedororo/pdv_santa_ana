import flet as ft
from datetime import datetime
from app.views.styles.theme import Colors, Sizes, Styles

def HomeView(page: ft.Page):
    """Tela principal do PDV Santa Ana"""
    
    turno_aberto = False
    
    def abrir_turno_modal(e):
        valor_inicial_input = Styles.text_field(
            "Valor inicial do caixa (R$)",
            300,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="R$ "
        )
        
        def confirmar_abertura(e):
            if not valor_inicial_input.value or valor_inicial_input.value.strip() == "":
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Por favor, informe o valor inicial!"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()
                return
            
            print(f"Turno aberto com R$ {valor_inicial_input.value}")
            modal.open = False
            page.update()
        
        def cancelar(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Abrir Turno", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"Data: {datetime.now().strftime('%d/%m/%Y')}", size=Sizes.FONT_MEDIUM),
                        ft.Text(f"Hora: {datetime.now().strftime('%H:%M:%S')}", size=Sizes.FONT_MEDIUM),
                        ft.Divider(),
                        valor_inicial_input,
                    ],
                    tight=True,
                    spacing=Sizes.SPACING_MEDIUM,
                ),
                width=400,
            ),
            actions=[
                ft.ElevatedButton("Cancelar", bgcolor=Colors.BRAND_RED, color=Colors.TEXT_WHITE, on_click=cancelar),
                ft.ElevatedButton("Confirmar", bgcolor=Colors.BRAND_GREEN, color=Colors.TEXT_WHITE, on_click=confirmar_abertura),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    def nav_button(text, icon, route=None, on_click_custom=None):
        def on_click(e):
            if on_click_custom:
                on_click_custom(e)
            elif route:
                page.go(route)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, color=Colors.TEXT_WHITE, size=Sizes.ICON_LARGE),
                    ft.Text(text, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD, size=Sizes.FONT_MEDIUM, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Sizes.SPACING_MEDIUM,
            ),
            bgcolor=Colors.BRAND_RED,
            width=190,
            height=100,
            border_radius=Sizes.BORDER_RADIUS_XLARGE,
            ink=True,
            on_click=on_click,
        )

    header = ft.Container(
        content=ft.Row(
            controls=[
                nav_button("Vendas",             ft.icons.SHOPPING_BAG,  route="/vendas"),
                nav_button("Estoque",            ft.icons.INVENTORY_2,   route="/estoque"),
                nav_button("Abrir/fechar Turno", ft.icons.LOGIN,         on_click_custom=abrir_turno_modal),
                nav_button("Relatórios",         ft.icons.BAR_CHART,     route="/relatorios"),
                nav_button("Usuários",           ft.icons.PEOPLE,        route="/usuarios"),
                nav_button("Histórico",          ft.icons.HISTORY,       route="/historico"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=Sizes.SPACING_LARGE,
        ),
        padding=ft.padding.only(top=40, bottom=30, left=Sizes.SPACING_LARGE, right=Sizes.SPACING_LARGE),
        border=ft.border.only(bottom=ft.BorderSide(2, Colors.BORDER_MEDIUM)),
    )

    body = ft.Container(
        content=ft.Image(
            src="app/views/assets/logo_santa_ana.png",
            width=450,
            fit=ft.ImageFit.CONTAIN,
        ),
        expand=True,
        alignment=ft.alignment.center,
    )

    data_atual = datetime.now().strftime("%d/%m/%Y")

    footer = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Usuário: Fulano",       size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.W_400, color=Colors.TEXT_BLACK),
                        ft.Text(f"Data: {data_atual}",   size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.W_400, color=Colors.TEXT_BLACK),
                        ft.Text("Turno: Aberto",         size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.W_400, color=Colors.TEXT_BLACK),
                    ],
                    spacing=Sizes.SPACING_XLARGE,
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.LOGOUT, size=Sizes.ICON_SMALL, color=Colors.TEXT_WHITE),
                            ft.Text("Sair", size=Sizes.FONT_MEDIUM, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=Sizes.SPACING_MEDIUM,
                    ),
                    bgcolor=Colors.BRAND_RED,
                    color=Colors.TEXT_WHITE,
                    height=50,
                    width=120,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_MEDIUM)),
                    on_click=lambda _: page.go("/login"),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(horizontal=Sizes.SPACING_XLARGE, vertical=25),
        border=ft.border.only(top=ft.BorderSide(2, Colors.BORDER_MEDIUM)),
    )

    return ft.Container(
        content=ft.Column(
            controls=[header, body, footer],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=Colors.BG_WHITE,
    )