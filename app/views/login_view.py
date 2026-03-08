import flet as ft
from app.views.styles.theme import Colors, Sizes, Styles


def LoginView(page: ft.Page):
    """Tela de login do PDV Santa Ana"""

    erro_text = ft.Text("", color=Colors.BRAND_RED, size=Sizes.FONT_SMALL, visible=False)

    # Credenciais simples (futuramente virá do banco)
    USUARIOS = {
        "admin": "1234",
        "caixa": "1234",
    }

    def fazer_login(e):
        usuario = input_usuario.value.strip()
        senha   = input_senha.value.strip()

        if not usuario or not senha:
            erro_text.value   = "Preencha usuário e senha."
            erro_text.visible = True
            page.update()
            return

        if USUARIOS.get(usuario) == senha:
            erro_text.visible = False
            page.go("/")
        else:
            erro_text.value   = "Usuário ou senha incorretos."
            erro_text.visible = True
            input_senha.value = ""
            page.update()

    # ── Inputs ───────────────────────────────────────────────────────────────
    input_usuario = ft.TextField(
        label="Usuário",
        width=340,
        border_color=Colors.BORDER_GRAY,
        prefix_icon=ft.icons.PERSON_OUTLINE,
        on_submit=fazer_login,
        autofocus=True,
    )

    input_senha = ft.TextField(
        label="Senha",
        width=340,
        border_color=Colors.BORDER_GRAY,
        prefix_icon=ft.icons.LOCK_OUTLINE,
        password=True,
        can_reveal_password=True,
        on_submit=fazer_login,
    )

    btn_entrar = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.LOGIN, color=Colors.TEXT_WHITE, size=20),
                ft.Text("Entrar", size=Sizes.FONT_LARGE, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        bgcolor=Colors.BRAND_RED,
        width=340,
        height=55,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_MEDIUM)),
        on_click=fazer_login,
    )

    # ── Painel esquerdo — identidade visual ──────────────────────────────────
    painel_esquerdo = ft.Container(
        content=ft.Column(
            controls=[
                ft.Image(
                    src="app/views/assets/logo_santa_ana2.png",
                    width=260,
                    fit=ft.ImageFit.CONTAIN,
                    error_content=ft.Text("Logo não encontrada", color=Colors.TEXT_WHITE),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
        ),
        bgcolor=Colors.BRAND_RED,
        width=360,
        expand=False,
        padding=Sizes.SPACING_XLARGE,
    )

    # ── Painel direito — formulário ──────────────────────────────────────────
    painel_direito = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Bem-vindo!",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_BLACK,
                ),
                ft.Text(
                    "Faça login para acessar o sistema",
                    size=Sizes.FONT_SMALL,
                    color=Colors.TEXT_GRAY,
                ),
                ft.Container(height=30),
                input_usuario,
                ft.Container(height=10),
                input_senha,
                ft.Container(height=6),
                erro_text,
                ft.Container(height=20),
                btn_entrar,
                ft.Container(height=20),
                ft.Text(
                    "© 2026 Farmácia Santa Ana — Todos os direitos reservados",
                    size=11,
                    color=Colors.TEXT_GRAY,
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
        ),
        expand=True,
        padding=Sizes.SPACING_XLARGE,
        bgcolor=Colors.BG_WHITE,
    )

    # ── Layout principal ─────────────────────────────────────────────────────
    return ft.Container(
        content=ft.Row(
            controls=[painel_esquerdo, painel_direito],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=Colors.BG_WHITE,
    )