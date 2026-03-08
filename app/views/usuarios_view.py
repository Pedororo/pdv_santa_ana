import flet as ft
from app.views.styles.theme import Colors, Sizes, Styles
from app.api.usuarios_api import UsuariosAPI


def UsuariosView(page: ft.Page):
    """Tela de gerenciamento de usuários"""

    todos_usuarios = []
    usuario_selecionado = None

    # ============================================================================
    # FUNÇÕES AUXILIARES
    # ============================================================================

    def role_label(role: str) -> str:
        return {"ADMIN": "Administrador", "VENDEDOR": "Vendedor"}.get((role or "").upper(), role or "—")

    def aplicar_filtros():
        texto  = pesquisa_input.value.strip().lower()
        filtro = filtro_dropdown.value

        usuarios = todos_usuarios

        if filtro and filtro != "Todos":
            role_map = {"Administrador": "ADMIN", "Vendedor": "VENDEDOR"}
            role_key = role_map.get(filtro)
            if role_key:
                usuarios = [u for u in usuarios if (u.get("role") or "").upper() == role_key]

        if texto:
            usuarios = [u for u in usuarios if texto in (u.get("username") or "").lower() or texto in (u.get("nome") or "").lower()]

        renderizar_tabela(usuarios)

    # ============================================================================
    # MODAIS
    # ============================================================================

    def modal_incluir(e):
        input_nome     = ft.TextField(label="Nome completo", width=300, border_color=Colors.BORDER_GRAY)
        input_username = ft.TextField(label="Username", width=300, border_color=Colors.BORDER_GRAY)
        input_senha    = ft.TextField(label="Senha", width=300, border_color=Colors.BORDER_GRAY, password=True, can_reveal_password=True)
        input_role     = ft.Dropdown(
            label="Perfil",
            value="VENDEDOR",
            width=300,
            border_color=Colors.BORDER_GRAY,
            options=[ft.dropdown.Option("ADMIN", "Administrador"), ft.dropdown.Option("VENDEDOR", "Vendedor")],
        )
        erro_text = ft.Text("", color=Colors.BRAND_RED, size=Sizes.FONT_SMALL, visible=False)

        def salvar(e):
            if not input_nome.value.strip() or not input_username.value.strip() or not input_senha.value.strip():
                erro_text.value   = "Preencha todos os campos."
                erro_text.visible = True
                page.update()
                return

            btn_salvar.disabled = True
            btn_salvar.text = "Salvando..."
            page.update()

            resultado = UsuariosAPI.criar_usuario({
                "nome":     input_nome.value.strip(),
                "username": input_username.value.strip(),
                "senha":    input_senha.value.strip(),
                "role":     input_role.value,
            })

            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text("Usuário criado com sucesso!"), bgcolor=Colors.BRAND_GREEN)
                page.snack_bar.open = True
                carregar_usuarios()
            else:
                btn_salvar.disabled = False
                btn_salvar.text = "Salvar"
                erro_text.value   = "Erro ao criar usuário. Verifique os dados."
                erro_text.visible = True
                page.update()

        def fechar(e):
            modal.open = False
            page.update()

        btn_salvar = ft.ElevatedButton(
            "Salvar",
            bgcolor=Colors.BRAND_GREEN,
            color=Colors.TEXT_WHITE,
            on_click=salvar,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Row(controls=[ft.Icon(ft.icons.PERSON_ADD, color=Colors.BRAND_GREEN, size=24), ft.Text("Incluir Usuário", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD)], spacing=8),
            content=ft.Container(
                width=320,
                content=ft.Column(spacing=Sizes.SPACING_MEDIUM, controls=[
                    ft.Divider(),
                    input_nome,
                    input_username,
                    input_senha,
                    input_role,
                    erro_text,
                ]),
            ),
            actions=[ft.TextButton("Cancelar", on_click=fechar), btn_salvar],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(modal)
        modal.open = True
        page.update()

    def modal_alterar(e):
        if not usuario_selecionado:
            page.snack_bar = ft.SnackBar(content=ft.Text("Selecione um usuário para alterar."), bgcolor=Colors.BRAND_ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        uid  = usuario_selecionado.get("id")
        input_nome     = ft.TextField(label="Nome completo", value=usuario_selecionado.get("nome", ""), width=300, border_color=Colors.BORDER_GRAY)
        input_username = ft.TextField(label="Username", value=usuario_selecionado.get("username", ""), width=300, border_color=Colors.BORDER_GRAY)
        input_senha    = ft.TextField(label="Nova senha (deixe em branco para manter)", width=300, border_color=Colors.BORDER_GRAY, password=True, can_reveal_password=True)
        erro_text      = ft.Text("", color=Colors.BRAND_RED, size=Sizes.FONT_SMALL, visible=False)

        def salvar(e):
            btn_salvar.disabled = True
            btn_salvar.text = "Salvando..."
            page.update()

            payload = {
                "nome":     input_nome.value.strip(),
                "username": input_username.value.strip(),
            }
            if input_senha.value.strip():
                payload["senha"] = input_senha.value.strip()

            resultado = UsuariosAPI.atualizar_usuario(uid, payload)

            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text("Usuário atualizado!"), bgcolor=Colors.BRAND_GREEN)
                page.snack_bar.open = True
                carregar_usuarios()
            else:
                btn_salvar.disabled = False
                btn_salvar.text = "Salvar"
                erro_text.value   = "Erro ao atualizar usuário."
                erro_text.visible = True
                page.update()

        def fechar(e):
            modal.open = False
            page.update()

        btn_salvar = ft.ElevatedButton(
            "Salvar",
            bgcolor=Colors.BRAND_GREEN,
            color=Colors.TEXT_WHITE,
            on_click=salvar,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Row(controls=[ft.Icon(ft.icons.EDIT, color=Colors.BRAND_BLUE, size=24), ft.Text(f"Alterar Usuário #{uid}", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD)], spacing=8),
            content=ft.Container(
                width=320,
                content=ft.Column(spacing=Sizes.SPACING_MEDIUM, controls=[ft.Divider(), input_nome, input_username, input_senha, erro_text]),
            ),
            actions=[ft.TextButton("Cancelar", on_click=fechar), btn_salvar],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(modal)
        modal.open = True
        page.update()

    def modal_desativar(e):
        if not usuario_selecionado:
            page.snack_bar = ft.SnackBar(content=ft.Text("Selecione um usuário."), bgcolor=Colors.BRAND_ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        uid  = usuario_selecionado.get("id")
        ativo = usuario_selecionado.get("ativo", True)

        if not ativo:
            page.snack_bar = ft.SnackBar(content=ft.Text("Este usuário já está inativo!"), bgcolor=Colors.BRAND_ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        def confirmar(e):
            btn_confirmar.disabled = True
            page.update()
            resultado = UsuariosAPI.desativar_usuario(uid)
            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Usuário #{uid} desativado!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                carregar_usuarios()
            else:
                btn_confirmar.disabled = False
                page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao desativar usuário!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()

        def fechar(e):
            modal.open = False
            page.update()

        btn_confirmar = ft.ElevatedButton(
            "Sim, Desativar",
            bgcolor=Colors.BRAND_RED,
            color=Colors.TEXT_WHITE,
            on_click=confirmar,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Desativar Usuário", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=320,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Sizes.SPACING_MEDIUM,
                    controls=[
                        ft.Icon(ft.icons.BLOCK, size=60, color=Colors.BRAND_RED),
                        ft.Text(f"Deseja desativar o usuário #{uid}?", size=Sizes.FONT_MEDIUM, text_align=ft.TextAlign.CENTER),
                        ft.Text(usuario_selecionado.get("nome", ""), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ],
                ),
            ),
            actions=[ft.TextButton("Voltar", on_click=fechar), btn_confirmar],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(modal)
        modal.open = True
        page.update()

    def modal_reativar(e):
        if not usuario_selecionado:
            page.snack_bar = ft.SnackBar(content=ft.Text("Selecione um usuário."), bgcolor=Colors.BRAND_ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        uid  = usuario_selecionado.get("id")
        ativo = usuario_selecionado.get("ativo", True)

        if ativo:
            page.snack_bar = ft.SnackBar(content=ft.Text("Este usuário já está ativo!"), bgcolor=Colors.BRAND_ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        def confirmar(e):
            btn_confirmar.disabled = True
            page.update()
            resultado = UsuariosAPI.reativar_usuario(uid)
            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Usuário #{uid} reativado!"), bgcolor=Colors.BRAND_GREEN)
                page.snack_bar.open = True
                carregar_usuarios()
            else:
                btn_confirmar.disabled = False
                page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao reativar usuário!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()

        def fechar(e):
            modal.open = False
            page.update()

        btn_confirmar = ft.ElevatedButton(
            "Sim, Reativar",
            bgcolor=Colors.BRAND_GREEN,
            color=Colors.TEXT_WHITE,
            on_click=confirmar,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reativar Usuário", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=320,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Sizes.SPACING_MEDIUM,
                    controls=[
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=60, color=Colors.BRAND_GREEN),
                        ft.Text(f"Deseja reativar o usuário #{uid}?", size=Sizes.FONT_MEDIUM, text_align=ft.TextAlign.CENTER),
                        ft.Text(usuario_selecionado.get("nome", ""), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ],
                ),
            ),
            actions=[ft.TextButton("Voltar", on_click=fechar), btn_confirmar],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(modal)
        modal.open = True
        page.update()

    # ============================================================================
    # RENDERIZAÇÃO
    # ============================================================================

    def criar_linha_usuario(usuario):
        nonlocal usuario_selecionado

        uid    = usuario.get("id", "")
        nome   = usuario.get("nome", "")
        uname  = usuario.get("username", "")
        role   = role_label(usuario.get("role", ""))
        ativo  = usuario.get("ativo", True)

        cor_status = Colors.BRAND_GREEN if ativo else Colors.BRAND_RED
        txt_status = "Ativo" if ativo else "Inativo"

        linha = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Text(str(uid), size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                    ft.Container(ft.Text(nome, size=Sizes.FONT_SMALL), expand=True, alignment=ft.alignment.center_left),
                    ft.Container(ft.Text(uname, size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(role, size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_BLUE), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(txt_status, size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=cor_status), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                ],
                spacing=0,
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=Colors.BG_WHITE,
            ink=True,
        )

        def selecionar(e, u=usuario, l=linha):
            nonlocal usuario_selecionado
            # Reset linha anterior
            for ctrl in items_list.controls:
                ctrl.bgcolor = Colors.BG_WHITE
                ctrl.border  = ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT))
            usuario_selecionado = u
            l.bgcolor = "#E3F2FD"
            l.border  = ft.border.all(1, Colors.BRAND_BLUE)
            page.update()

        linha.on_click = selecionar
        return linha

    def renderizar_tabela(usuarios):
        items_list.controls.clear()

        if not usuarios:
            items_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.icons.PEOPLE, size=80, color=Colors.TEXT_GRAY),
                            ft.Text("Nenhum usuário encontrado", size=Sizes.FONT_LARGE, color=Colors.TEXT_GRAY, weight=ft.FontWeight.BOLD),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=50,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for u in usuarios:
                items_list.controls.append(criar_linha_usuario(u))

        page.update()

    def carregar_usuarios():
        nonlocal todos_usuarios, usuario_selecionado
        usuario_selecionado = None

        items_list.controls.clear()
        items_list.controls.append(
            ft.Container(
                content=ft.Row([ft.ProgressRing(width=30, height=30), ft.Text("Carregando usuários...")], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                padding=50,
                alignment=ft.alignment.center,
            )
        )
        page.update()

        todos_usuarios = UsuariosAPI.listar_usuarios()
        aplicar_filtros()

    # ============================================================================
    # COMPONENTES
    # ============================================================================

    pesquisa_input = Styles.text_field("Pesquisar por nome ou username", Sizes.INPUT_XLARGE)
    pesquisa_input.on_submit = lambda _: aplicar_filtros()

    btn_localizar = Styles.button_localizar(on_click=lambda _: aplicar_filtros())

    filtro_dropdown = Styles.dropdown(
        label="Filtro",
        options=["Todos", "Administrador", "Vendedor"],
        value="Todos",
    )
    filtro_dropdown.on_change = lambda _: aplicar_filtros()

    top_section = ft.Container(
        content=ft.Row(controls=[pesquisa_input, btn_localizar, filtro_dropdown], spacing=Sizes.SPACING_MEDIUM),
        padding=Sizes.SPACING_LARGE,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,
    )

    table_header = Styles.table_header([
        ("ID",       Sizes.TABLE_COL_SMALL),
        ("Nome",     None),
        ("Username", Sizes.TABLE_COL_LARGE),
        ("Perfil",   Sizes.TABLE_COL_LARGE),
        ("Status",   Sizes.TABLE_COL_MEDIUM),
    ])

    items_list = ft.Column(controls=[], spacing=0, scroll=ft.ScrollMode.AUTO)

    table_container = ft.Container(
        content=ft.Column(
            controls=[
                table_header,
                ft.Container(
                    content=items_list,
                    expand=True,
                    border=ft.border.all(1, Colors.BORDER_BLACK),
                    bgcolor=Colors.BG_WHITE,
                ),
            ],
            spacing=0,
        ),
        expand=True,
        margin=ft.margin.only(top=Sizes.SPACING_LARGE),
    )

    btn_incluir   = Styles.button_primary("Incluir Usuário",  ft.icons.PERSON_ADD,    modal_incluir)
    btn_alterar   = Styles.button_warning("Alterar Usuário",  ft.icons.EDIT,          modal_alterar)
    btn_desativar = Styles.button_danger("Desativar Usuário", ft.icons.BLOCK,         modal_desativar)
    btn_reativar  = Styles.button_primary("Reativar Usuário", ft.icons.CHECK_CIRCLE,  modal_reativar)
    btn_sair      = Styles.button_danger("Menu Principal",    ft.icons.HOME,          lambda _: page.go("/"))

    sidebar = Styles.sidebar([
        btn_incluir,
        btn_alterar,
        btn_desativar,
        btn_reativar,
        ft.Container(expand=True),
        btn_sair,
    ])

    main_content = ft.Container(
        content=ft.Column(controls=[top_section, table_container], spacing=0, expand=True),
        expand=True,
        padding=Sizes.SPACING_LARGE,
    )

    carregar_usuarios()

    return ft.Row(controls=[main_content, sidebar], spacing=0, expand=True)