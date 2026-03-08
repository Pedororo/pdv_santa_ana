import flet as ft
from datetime import datetime, timedelta
from app.views.styles.theme import Colors, Sizes, Styles
from app.api.vendas_api import VendasAPI


def HistoricoView(page: ft.Page):
    """Tela de histórico de vendas"""

    todas_vendas = []

    # ============================================================================
    # FUNÇÕES AUXILIARES
    # ============================================================================

    def status_cor(status: str) -> str:
        mapa = {
            "finalizada": Colors.BRAND_GREEN,
            "cancelada":  Colors.BRAND_RED,
            "pendente":   Colors.BRAND_ORANGE,
        }
        return mapa.get((status or "").lower(), Colors.TEXT_GRAY)

    def filtrar_por_periodo(vendas, periodo):
        hoje = datetime.now().date()
        limites = {
            "Hoje":    hoje,
            "Semana":  hoje - timedelta(days=7),
            "Mês":     hoje - timedelta(days=30),
            "3 Meses": hoje - timedelta(days=90),
        }
        limite = limites.get(periodo)
        if limite is None:
            return vendas

        resultado = []
        for v in vendas:
            data_str = v.get("data_venda") or v.get("created_at") or ""
            try:
                data_venda = datetime.fromisoformat(data_str[:10]).date()
                if data_venda >= limite:
                    resultado.append(v)
            except Exception:
                resultado.append(v)
        return resultado

    def aplicar_filtros():
        texto   = pesquisa_input.value.strip().lower()
        periodo = filtro_dropdown.value
        vendas  = filtrar_por_periodo(todas_vendas, periodo)

        if texto:
            vendas = [v for v in vendas if texto in str(v.get("id", "")).lower()]

        renderizar_tabela(vendas)

    # ============================================================================
    # MODAIS DE AÇÃO
    # ============================================================================

    def modal_cancelar(venda):
        venda_id = venda.get("id")
        total    = float(venda.get("total") or venda.get("valor_total") or 0)

        def confirmar(e):
            btn_confirmar.disabled = True
            btn_confirmar.text = "Cancelando..."
            page.update()

            resultado = VendasAPI.cancelar_venda(venda_id)
            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Venda #{venda_id} cancelada!"), bgcolor=Colors.BRAND_GREEN)
                page.snack_bar.open = True
                carregar_vendas()
            else:
                btn_confirmar.disabled = False
                btn_confirmar.text = "Sim, Cancelar"
                page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao cancelar venda!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()

        def fechar(e):
            modal.open = False
            page.update()

        btn_confirmar = ft.ElevatedButton(
            "Sim, Cancelar",
            bgcolor=Colors.BRAND_RED,
            color=Colors.TEXT_WHITE,
            on_click=confirmar,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cancelar Venda", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Sizes.SPACING_MEDIUM,
                    controls=[
                        ft.Icon(ft.icons.WARNING_AMBER, size=70, color=Colors.BRAND_RED),
                        ft.Text("Esta ação não pode ser desfeita!", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED, text_align=ft.TextAlign.CENTER),
                        ft.Divider(),
                        ft.Row(controls=[ft.Text("Venda Nº:"), ft.Text(f"#{venda_id}", weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row(controls=[ft.Text("Valor Total:"), ft.Text(f"R$ {total:.2f}", weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Voltar", on_click=fechar),
                btn_confirmar,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(modal)
        modal.open = True
        page.update()

    def modal_editar_pagamento(venda):
        """Edita a forma de pagamento via VendasAPI.atualizar_pagamento (PUT /vendas/{id}/pagamento)"""
        venda_id = venda.get("id")

        # Label atual da venda para pre-selecionar o dropdown
        pagamento_atual = venda.get("forma_pagamento") or "Dinheiro"

        input_pagamento = ft.Dropdown(
            label="Forma de Pagamento",
            value=pagamento_atual,
            width=250,
            border_color=Colors.BORDER_GRAY,
            options=[ft.dropdown.Option(o) for o in ["Dinheiro", "Débito", "Crédito", "PIX"]],
        )

        def salvar(e):
            btn_salvar.disabled = True
            btn_salvar.text = "Salvando..."
            page.update()

            tipo_normalizado = VendasAPI.normalizar_pagamento(input_pagamento.value)

            # Usa atualizar_pagamento (PUT /vendas/{id}/pagamento)
            # valor_recebido deve ser > 0 — usa total como fallback se não houver
            vr_hist = float(venda.get("valor_recebido") or 0)
            if vr_hist <= 0:
                vr_hist = float(venda.get("total") or venda.get("valor_total") or 0)
            # garante pelo menos 0.01 para não violar o gt=0 do schema
            vr_hist = max(round(vr_hist, 2), 0.01)

            payload = {
                "tipo": tipo_normalizado,
                "valor_recebido": vr_hist,
            }

            # Tenta atualizar (PUT); se não existir pagamento, registra (POST)
            resultado = VendasAPI.atualizar_pagamento(venda_id, payload)
            if not resultado:
                resultado = VendasAPI.registrar_pagamento(venda_id, payload)

            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Pagamento da venda #{venda_id} atualizado!"),
                    bgcolor=Colors.BRAND_GREEN,
                )
                page.snack_bar.open = True
                carregar_vendas()
            else:
                btn_salvar.disabled = False
                btn_salvar.text = "Salvar"
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Erro ao atualizar pagamento!"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
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
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.EDIT, color=Colors.BRAND_BLUE, size=24),
                    ft.Text(f"Editar Pagamento #{venda_id}", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Container(
                width=320,
                content=ft.Column(
                    spacing=Sizes.SPACING_MEDIUM,
                    controls=[ft.Divider(), input_pagamento],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                btn_salvar,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(modal)
        modal.open = True
        page.update()

    def modal_reimprimir(venda):
        venda_id  = venda.get("id")
        total     = float(venda.get("total") or venda.get("valor_total") or 0)
        desconto  = float(venda.get("desconto") or 0)
        acrescimo = float(venda.get("acrescimo") or 0)
        subtotal  = total - acrescimo + desconto

        data_str = venda.get("data_venda") or venda.get("created_at") or ""
        try:
            dt = datetime.fromisoformat(data_str)
            data_fmt = dt.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            data_fmt = data_str

        # Extrai só o tipo do objeto forma_pagamento
        fp = venda.get("forma_pagamento")
        if isinstance(fp, dict):
            pagamento = fp.get("tipo", "—").capitalize()
        elif isinstance(fp, str):
            pagamento = fp.capitalize()
        else:
            pagamento = "—"

        itens = VendasAPI.listar_itens(venda_id)

        # Monta dicionário produto_id -> nome para exibir na nota
        from app.api.produtos_api import ProdutosAPI
        produtos_map = {}
        try:
            for p in ProdutosAPI.listar_produtos():
                produtos_map[p.get("id")] = p.get("nome", f"Produto #{p.get('id')}")
        except Exception:
            pass

        linhas_itens = []
        for item in itens:
            pid = item.get("produto_id")
            nome_item = produtos_map.get(pid) or f"Produto #{pid}"
            linhas_itens.append(
                ft.Row(
                    controls=[
                        ft.Text(nome_item, size=11, expand=True),
                        ft.Text(f"{item.get('quantidade', 1)}x", size=11, width=35, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"R$ {float(item.get('preco_unitario', 0)):.2f}", size=11, width=80, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"R$ {float(item.get('subtotal', 0)):.2f}", size=11, width=80, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
                    ],
                    spacing=4,
                )
            )

        if not linhas_itens:
            linhas_itens.append(ft.Text("Nenhum item encontrado", size=11, color=Colors.TEXT_GRAY, italic=True))

        def fechar(e):
            nota.open = False
            page.update()

        def imprimir(e):
            nota.open = False
            page.snack_bar = ft.SnackBar(content=ft.Text("🖨️ Enviando para impressão..."), bgcolor=Colors.BRAND_BLUE)
            page.snack_bar.open = True
            page.update()

        nota = ft.AlertDialog(
            modal=True,
            title=ft.Row(controls=[ft.Icon(ft.icons.RECEIPT, color=Colors.BRAND_GREEN, size=28), ft.Text(f"Venda #{venda_id}", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD)], spacing=8),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=0,
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("FARMÁCIA SANTA ANA", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                            ),
                            padding=ft.padding.only(bottom=8),
                        ),
                        ft.Divider(thickness=2, color=Colors.BORDER_MEDIUM),
                        ft.Container(
                            content=ft.Row(controls=[
                                ft.Text("DESCRIÇÃO", size=10, weight=ft.FontWeight.BOLD, expand=True),
                                ft.Text("QTD",   size=10, weight=ft.FontWeight.BOLD, width=35, text_align=ft.TextAlign.RIGHT),
                                ft.Text("UNIT.", size=10, weight=ft.FontWeight.BOLD, width=80, text_align=ft.TextAlign.RIGHT),
                                ft.Text("TOTAL", size=10, weight=ft.FontWeight.BOLD, width=80, text_align=ft.TextAlign.RIGHT),
                            ], spacing=4),
                            bgcolor="#F5F5F5",
                            padding=ft.padding.symmetric(horizontal=4, vertical=6),
                        ),
                        ft.Divider(height=1, color=Colors.BORDER_LIGHT),
                        ft.Container(content=ft.Column(controls=linhas_itens, spacing=6), padding=ft.padding.symmetric(horizontal=4, vertical=8)),
                        ft.Divider(thickness=2, color=Colors.BORDER_MEDIUM),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Row(controls=[ft.Text("Subtotal:", size=12), ft.Text(f"R$ {subtotal:.2f}", size=12)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    ft.Row(controls=[ft.Text("Desconto:", size=12, color=Colors.BRAND_RED), ft.Text(f"- R$ {desconto:.2f}", size=12, color=Colors.BRAND_RED)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    ft.Row(controls=[ft.Text("Acréscimo:", size=12, color=Colors.BRAND_ORANGE), ft.Text(f"+ R$ {acrescimo:.2f}", size=12, color=Colors.BRAND_ORANGE)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    ft.Divider(height=1, color=Colors.BORDER_LIGHT),
                                    ft.Row(controls=[ft.Text("TOTAL:", size=15, weight=ft.FontWeight.BOLD), ft.Text(f"R$ {total:.2f}", size=15, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                    ft.Divider(height=1, color=Colors.BORDER_LIGHT),
                                    ft.Row(controls=[ft.Text("Pagamento:", size=12), ft.Text(pagamento, size=12, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ],
                                spacing=6,
                            ),
                            padding=ft.padding.symmetric(horizontal=4, vertical=8),
                        ),
                        ft.Divider(thickness=2, color=Colors.BORDER_MEDIUM),
                        ft.Container(
                            content=ft.Text("Obrigado pela preferência!", size=11, italic=True, color=Colors.TEXT_GRAY, text_align=ft.TextAlign.CENTER),
                            padding=ft.padding.only(top=6),
                            alignment=ft.alignment.center,
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Fechar", on_click=fechar),
                ft.ElevatedButton("Imprimir", icon=ft.icons.PRINT, bgcolor=Colors.BRAND_BLUE, color=Colors.TEXT_WHITE, on_click=imprimir, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(nota)
        nota.open = True
        page.update()

    def abrir_menu_acoes(venda):
        """Abre dialog com as ações da venda"""
        ja_cancelada = (venda.get("status") or "").lower() == "cancelada"

        def fechar(e):
            menu.open = False
            page.update()

        def acao_editar(e):
            menu.open = False
            page.update()
            modal_editar_pagamento(venda)

        def acao_cancelar(e):
            if ja_cancelada:
                return
            menu.open = False
            page.update()
            modal_cancelar(venda)

        def acao_reimprimir(e):
            menu.open = False
            page.update()
            modal_reimprimir(venda)

        menu = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.RECEIPT_LONG, color=Colors.BRAND_BLUE, size=22),
                    ft.Text(f"Venda #{venda.get('id')}", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Container(
                width=300,
                content=ft.Column(
                    tight=True,
                    spacing=0,
                    controls=[
                        ft.Divider(height=1),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.EDIT, color=Colors.BRAND_BLUE),
                            title=ft.Text("Editar Forma de Pagamento"),
                            on_click=acao_editar,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.PRINT, color=Colors.BRAND_BLUE),
                            title=ft.Text("Reimprimir Nota"),
                            on_click=acao_reimprimir,
                        ),
                        ft.ListTile(
                            leading=ft.Icon(
                                ft.icons.CANCEL,
                                color=Colors.BRAND_RED if not ja_cancelada else Colors.TEXT_GRAY,
                            ),
                            title=ft.Text(
                                "Cancelar Venda",
                                color=Colors.BRAND_RED if not ja_cancelada else Colors.TEXT_GRAY,
                            ),
                            on_click=acao_cancelar if not ja_cancelada else None,
                        ),
                    ],
                ),
            ),
            actions=[ft.TextButton("Fechar", on_click=fechar)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.append(menu)
        menu.open = True
        page.update()

    # ============================================================================
    # RENDERIZAÇÃO
    # ============================================================================

    def criar_linha_venda(venda):
        data_str = venda.get("data_venda") or venda.get("created_at") or ""
        try:
            dt = datetime.fromisoformat(data_str)
            data_fmt = dt.strftime("%d/%m/%Y")
            hora_fmt = dt.strftime("%H:%M:%S")
        except Exception:
            data_fmt = data_str[:10]
            hora_fmt = data_str[11:19] if len(data_str) > 10 else ""

        status = venda.get("status", "—")
        total  = float(venda.get("total") or venda.get("valor_total") or 0)

        # forma_pagamento vem como objeto {tipo, valor_recebido, troco} ou None
        fp = venda.get("forma_pagamento")
        if isinstance(fp, dict):
            pagamento_label = fp.get("tipo", "—").capitalize()
        elif isinstance(fp, str):
            pagamento_label = fp.capitalize()
        else:
            pagamento_label = "—"

        btn_menu = ft.IconButton(
            icon=ft.icons.MORE_VERT,
            icon_color=Colors.TEXT_GRAY,
            icon_size=20,
            tooltip="Ações",
            on_click=lambda _, v=venda: abrir_menu_acoes(v),
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Text(str(venda.get("id", "")), size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                    ft.Container(ft.Text(data_fmt, size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(hora_fmt, size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {total:.2f}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(pagamento_label, size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_BLUE), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(status.capitalize(), size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=status_cor(status)), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(btn_menu, width=60, alignment=ft.alignment.center),
                ],
                spacing=0,
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
            padding=ft.padding.symmetric(horizontal=10, vertical=2),
            bgcolor=Colors.BG_WHITE,
            ink=True,
        )

    def renderizar_tabela(vendas):
        items_list.controls.clear()

        if not vendas:
            items_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.icons.RECEIPT_LONG, size=80, color=Colors.TEXT_GRAY),
                            ft.Text("Nenhuma venda encontrada", size=Sizes.FONT_LARGE, color=Colors.TEXT_GRAY, weight=ft.FontWeight.BOLD),
                            ft.Text("Tente ajustar os filtros de busca", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY, italic=True),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=50,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for venda in vendas:
                items_list.controls.append(criar_linha_venda(venda))

        page.update()

    def carregar_vendas():
        nonlocal todas_vendas

        items_list.controls.clear()
        items_list.controls.append(
            ft.Container(
                content=ft.Row(
                    [ft.ProgressRing(width=30, height=30), ft.Text("Carregando vendas...")],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=50,
                alignment=ft.alignment.center,
            )
        )
        page.update()

        todas_vendas = sorted(VendasAPI.listar_vendas(), key=lambda v: v.get("id", 0))
        aplicar_filtros()

    # ============================================================================
    # COMPONENTES
    # ============================================================================

    pesquisa_input = Styles.text_field("Pesquisar venda", Sizes.INPUT_XLARGE)
    pesquisa_input.on_submit = lambda _: aplicar_filtros()

    btn_localizar = Styles.button_localizar(on_click=lambda _: aplicar_filtros())

    filtro_dropdown = Styles.dropdown(
        label="Filtro",
        options=["Hoje", "Semana", "Mês", "3 Meses", "Todos"],
        value="Todos",
    )
    filtro_dropdown.on_change = lambda _: aplicar_filtros()

    top_section = ft.Container(
        content=ft.Row(
            controls=[pesquisa_input, btn_localizar, filtro_dropdown],
            spacing=Sizes.SPACING_MEDIUM,
        ),
        padding=Sizes.SPACING_LARGE,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,
    )

    table_header = Styles.table_header([
        ("ID",          Sizes.TABLE_COL_SMALL),
        ("Data",        Sizes.TABLE_COL_LARGE),
        ("Hora",        Sizes.TABLE_COL_MEDIUM),
        ("Valor Total", Sizes.TABLE_COL_LARGE),
        ("Pagamento",   Sizes.TABLE_COL_LARGE),
        ("Status",      Sizes.TABLE_COL_LARGE),
        ("Ações",       60),
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

    btn_sair = Styles.button_danger("Menu Principal", ft.icons.HOME, lambda _: page.go("/"))

    sidebar = Styles.sidebar([
        ft.Container(expand=True),
        btn_sair,
    ])

    main_content = ft.Container(
        content=ft.Column(
            controls=[top_section, table_container],
            spacing=0,
            expand=True,
        ),
        expand=True,
        padding=Sizes.SPACING_LARGE,
    )

    carregar_vendas()

    return ft.Row(
        controls=[main_content, sidebar],
        spacing=0,
        expand=True,
    )