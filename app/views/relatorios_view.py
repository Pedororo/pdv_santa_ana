import flet as ft
from datetime import datetime
from app.views.styles.theme import Colors, Sizes, Styles


def RelatoriosView(page: ft.Page):
    """Tela de Relatórios - PDV Santa Ana"""

    estado = {
        "tipo":         "vendas",
        "periodo":      "mes",
        "data_inicio":  None,
        "data_fim":     None,
        "pode_exportar": False,
    }

    # =========================================================================
    # HELPERS DE UI
    # =========================================================================
    def card_metrica(icone, label, valor, cor, bgcolor_card):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Container(
                    content=ft.Icon(icone, color=Colors.TEXT_WHITE, size=22),
                    bgcolor=cor, border_radius=8, padding=8,
                )]),
                ft.Container(height=10),
                ft.Text(valor, size=22, weight=ft.FontWeight.BOLD, color=cor),
                ft.Text(label, size=12, color=Colors.TEXT_GRAY),
            ], spacing=2),
            bgcolor=bgcolor_card, border_radius=12, padding=20,
            border=ft.border.all(1, Colors.BORDER_LIGHT), expand=True,
        )

    def secao_titulo(texto, icone):
        return ft.Row([
            ft.Icon(icone, size=20, color=Colors.BRAND_RED),
            ft.Text(texto, size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK),
        ], spacing=8)

    def _header_tabela(colunas):
        return ft.Container(
            content=ft.Row([
                ft.Container(ft.Text(col, size=11, weight=ft.FontWeight.BOLD), width=w)
                for col, w in colunas
            ], spacing=0),
            bgcolor=Colors.BG_PINK_LIGHT,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
        )

    def _linha_vazia(msg="Dados carregados após gerar relatório"):
        return ft.Container(
            content=ft.Text(msg, size=12, color=Colors.TEXT_GRAY, italic=True, text_align=ft.TextAlign.CENTER),
            padding=20, alignment=ft.alignment.center,
        )

    def _linha_ranking(pos, nome, categoria, qtd, cor):
        icones_pos = {1: "🥇", 2: "🥈", 3: "🥉"}
        return ft.Container(
            content=ft.Row([
                ft.Text(icones_pos.get(pos, str(pos)), size=18, width=36),
                ft.Text(nome, size=13, expand=True),
                ft.Text(categoria, size=12, color=Colors.TEXT_GRAY, width=120),
                ft.Text(qtd, size=13, weight=ft.FontWeight.BOLD, color=cor, width=60, text_align=ft.TextAlign.RIGHT),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
        )

    def _tabela_demo(colunas, msg="Dados carregados após gerar relatório"):
        return ft.Container(
            content=ft.Column([
                _header_tabela(colunas),
                ft.Container(
                    content=_linha_vazia(msg),
                    border=ft.border.all(1, Colors.BORDER_LIGHT),
                    border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
                ),
            ], spacing=0),
        )

    def _grafico_pagamentos_demo():
        formas = [
            ("💵 Dinheiro", Colors.BRAND_GREEN),
            ("💳 Débito",   Colors.BRAND_BLUE),
            ("💳 Crédito",  "#9C27B0"),
            ("📱 Pix",      "#00BCD4"),
        ]
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(label, size=13, expand=True),
                    ft.Container(bgcolor=Colors.BORDER_LIGHT, border_radius=4, height=8, width=160),
                    ft.Text("R$ 0,00", size=12, color=Colors.TEXT_GRAY, width=80, text_align=ft.TextAlign.RIGHT),
                ], spacing=8)
                for label, cor in formas
            ], spacing=10),
            border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=10, padding=16,
        )

    # =========================================================================
    # PREVIEWS
    # =========================================================================
    preview_content = ft.Column(spacing=16, expand=True, scroll=ft.ScrollMode.AUTO)

    def preview_vendas():
        preview_content.controls = [
            secao_titulo("Resumo de Vendas", ft.icons.SHOPPING_BAG),
            ft.Row([
                card_metrica(ft.icons.RECEIPT_LONG,        "Total de Vendas",  "R$ 0,00", Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.NUMBERS,              "Nº Transações",    "0",       Colors.BRAND_BLUE,   "#EFF6FF"),
                card_metrica(ft.icons.CONFIRMATION_NUMBER,  "Ticket Médio",     "R$ 0,00", Colors.BRAND_ORANGE, "#FFF8F0"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo("Por Forma de Pagamento", ft.icons.PAYMENTS),
            ft.Row([
                card_metrica(ft.icons.MONEY,       "Dinheiro", "R$ 0,00", Colors.BRAND_GREEN, "#F1FFF3"),
                card_metrica(ft.icons.CREDIT_CARD, "Débito",   "R$ 0,00", Colors.BRAND_BLUE,  "#EFF6FF"),
                card_metrica(ft.icons.CREDIT_CARD, "Crédito",  "R$ 0,00", "#9C27B0",          "#F8F0FF"),
                card_metrica(ft.icons.PIX,         "Pix",      "R$ 0,00", "#00BCD4",          "#F0FCFF"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo("Produtos Mais Vendidos", ft.icons.STAR),
            ft.Container(
                content=ft.Column([
                    _linha_ranking(1, "—", "—", "0 un.", Colors.BRAND_GREEN),
                    _linha_ranking(2, "—", "—", "0 un.", Colors.BRAND_BLUE),
                    _linha_ranking(3, "—", "—", "0 un.", Colors.BRAND_ORANGE),
                ], spacing=0),
                border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=10,
            ),
            ft.Text("Clique em 'Gerar Relatório' para carregar os dados reais.", size=12, color=Colors.TEXT_GRAY, italic=True, text_align=ft.TextAlign.CENTER),
        ]
        try: preview_content.update()
        except Exception: pass

    def preview_estoque():
        filtro = estado.get("estoque_filtro", "completo")
        titulos = {
            "completo": "Estoque Completo",
            "ativos":   "Produtos Ativos",
            "inativos": "Produtos Inativos",
            "baixo":    "Alerta de Estoque Baixo",
        }
        titulo_filtro = titulos.get(filtro, "Estoque")
        preview_content.controls = [
            secao_titulo("Resumo de Estoque", ft.icons.INVENTORY_2),
            ft.Row([
                card_metrica(ft.icons.INVENTORY_2,          "Produtos Ativos",  "0", Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.REMOVE_SHOPPING_CART, "Inativos",         "0", Colors.TEXT_GRAY,    "#F5F5F5"),
                card_metrica(ft.icons.WARNING_AMBER,        "Estoque Baixo",    "0", Colors.BRAND_ORANGE, "#FFF8F0"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo(f"Listagem — {titulo_filtro}", ft.icons.LIST_ALT),
            _tabela_demo([("ID", 50), ("Produto", 200), ("Categoria", 150), ("Estoque", 80), ("Compra", 100), ("Venda", 100)],
                         "Selecione um filtro e clique em 'Gerar Relatório' para carregar os dados."),
        ]
        try: preview_content.update()
        except Exception: pass

    def preview_margem():
        preview_content.controls = [
            secao_titulo("Análise de Margem", ft.icons.TRENDING_UP),
            ft.Row([
                card_metrica(ft.icons.ATTACH_MONEY,  "Receita Bruta", "R$ 0,00", Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.SHOPPING_CART, "Custo Total",   "R$ 0,00", Colors.BRAND_RED,    "#FFF0F0"),
                card_metrica(ft.icons.TRENDING_UP,   "Lucro Bruto",   "R$ 0,00", Colors.BRAND_BLUE,   "#EFF6FF"),
                card_metrica(ft.icons.PERCENT,       "Margem %",      "0%",       Colors.BRAND_ORANGE, "#FFF8F0"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo("Detalhamento por Produto", ft.icons.TABLE_CHART),
            _tabela_demo([("Produto", 200), ("Qtd Vendida", 100), ("Receita", 120), ("Custo", 120), ("Lucro", 120), ("Margem%", 80)]),
            ft.Text("Clique em 'Gerar Relatório' para carregar os dados reais.", size=12, color=Colors.TEXT_GRAY, italic=True, text_align=ft.TextAlign.CENTER),
        ]
        try: preview_content.update()
        except Exception: pass

    def preview_caixa():
        preview_content.controls = [
            secao_titulo("Resumo de Caixa por Turno", ft.icons.POINT_OF_SALE),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.INFO_OUTLINE, size=16, color=Colors.BRAND_ORANGE),
                    ft.Text("O relatório de caixa será alimentado pelos dados de abertura e fechamento de turno.", size=13, color=Colors.TEXT_GRAY),
                ], spacing=6),
                bgcolor="#FFF8F0", padding=ft.padding.symmetric(horizontal=16, vertical=12),
                border_radius=8, border=ft.border.all(1, "#FFE0B2"),
            ),
            ft.Row([
                card_metrica(ft.icons.PUNCH_CLOCK,             "Turnos no Período", "0",       Colors.BRAND_BLUE,   "#EFF6FF"),
                card_metrica(ft.icons.ACCOUNT_BALANCE_WALLET,  "Total Faturado",    "R$ 0,00", Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.COMPARE_ARROWS,          "Diferença Total",   "R$ 0,00", Colors.BRAND_ORANGE, "#FFF8F0"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo("Histórico de Turnos", ft.icons.HISTORY),
            _tabela_demo(
                [("Turno", 60), ("Abertura", 100), ("Fechamento", 100), ("Inicial", 100), ("Faturado", 100), ("Diferença", 100)],
                "Disponível após implementação de persistência de turnos",
            ),
        ]
        try: preview_content.update()
        except Exception: pass

    def preview_geral():
        preview_content.controls = [
            secao_titulo("Visão Geral do Período", ft.icons.DASHBOARD),
            ft.Row([
                card_metrica(ft.icons.SHOPPING_BAG,        "Total Vendas",  "R$ 0,00", Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.CONFIRMATION_NUMBER, "Ticket Médio",  "R$ 0,00", Colors.BRAND_BLUE,   "#EFF6FF"),
                card_metrica(ft.icons.TRENDING_UP,         "Lucro Bruto",   "R$ 0,00", Colors.BRAND_ORANGE, "#FFF8F0"),
                card_metrica(ft.icons.STAR,                "Produto Top",   "—",        Colors.BRAND_RED,    "#FFF0F0"),
            ], spacing=12),
            ft.Divider(height=8),
            ft.Row([
                ft.Column([
                    secao_titulo("Pagamentos", ft.icons.PAYMENTS),
                    _grafico_pagamentos_demo(),
                ], expand=True, spacing=8),
                ft.Column([
                    secao_titulo("Top Produtos", ft.icons.STAR),
                    ft.Container(
                        content=ft.Column([
                            _linha_ranking(1, "—", "—", "0 un.", Colors.BRAND_GREEN),
                            _linha_ranking(2, "—", "—", "0 un.", Colors.BRAND_BLUE),
                            _linha_ranking(3, "—", "—", "0 un.", Colors.BRAND_ORANGE),
                        ], spacing=0),
                        border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=10,
                    ),
                ], expand=True, spacing=8),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
        ]
        try: preview_content.update()
        except Exception: pass

    def atualizar_preview():
        mapa = {
            "vendas":  preview_vendas,
            "estoque": preview_estoque,
            "margem":  preview_margem,
            "caixa":   preview_caixa,
            "geral":   preview_geral,
        }
        mapa.get(estado["tipo"], preview_vendas)()

    # =========================================================================
    # CHIPS DE PERÍODO
    # =========================================================================
    # Chips de período (para relatórios com filtro temporal)
    periodos = [
        ("Hoje", "hoje"), ("Semana", "semana"), ("Mês", "mes"),
        ("Bimestre", "bimestre"), ("Semestre", "semestre"), ("Ano", "ano"),
    ]

    chips_row = ft.Row(spacing=8, wrap=True)

    def chip_periodo(label, valor):
        selecionado = estado["periodo"] == valor
        def selecionar(e):
            estado["periodo"] = valor
            rebuild_chips()
            atualizar_preview()
        return ft.ElevatedButton(
            label,
            style=ft.ButtonStyle(
                bgcolor=Colors.BRAND_RED if selecionado else "#F5F5F5",
                color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_GRAY,
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                elevation=2 if selecionado else 0,
            ),
            on_click=selecionar, height=36,
        )

    def rebuild_chips():
        chips_row.controls = [chip_periodo(l, v) for l, v in periodos]
        try: chips_row.update()
        except Exception: pass

    # Filtros de estoque
    estado["estoque_filtro"] = "completo"

    def btn_estoque_filtro(label, valor, icone, cor):
        selecionado = estado["estoque_filtro"] == valor
        def selecionar(e):
            estado["estoque_filtro"] = valor
            rebuild_filtros_estoque()
            # preview só gerado ao clicar em Gerar Relatório
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, size=16, color=Colors.TEXT_WHITE if selecionado else cor),
                ft.Text(label, size=13, weight=ft.FontWeight.BOLD if selecionado else ft.FontWeight.W_400,
                        color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_BLACK),
            ], spacing=8),
            bgcolor=cor if selecionado else Colors.BG_WHITE,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border=ft.border.all(1, cor),
            ink=True, on_click=selecionar,
        )

    filtros_estoque_col = ft.Column(spacing=6)

    def rebuild_filtros_estoque():
        filtros_estoque_col.controls = [
            btn_estoque_filtro("Estoque Completo",  "completo", ft.icons.LIST_ALT,               Colors.BRAND_BLUE),
            btn_estoque_filtro("Produtos Ativos",   "ativos",   ft.icons.CHECK_CIRCLE_OUTLINE,   Colors.BRAND_GREEN),
            btn_estoque_filtro("Produtos Inativos", "inativos", ft.icons.REMOVE_CIRCLE_OUTLINE,  Colors.TEXT_GRAY),
            btn_estoque_filtro("Estoque Baixo",     "baixo",    ft.icons.WARNING_AMBER,          Colors.BRAND_ORANGE),
        ]
        try: filtros_estoque_col.update()
        except Exception: pass

    # Área de filtros dinâmica (muda conforme tipo selecionado)
    area_filtros = ft.Column(spacing=4)

    def rebuild_area_filtros():
        area_filtros.controls.clear()
        if estado["tipo"] == "estoque":
            area_filtros.controls = [
                ft.Text("FILTRO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                ft.Container(height=4),
                filtros_estoque_col,
            ]
        else:
            area_filtros.controls = [
                ft.Text("PERÍODO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                ft.Container(height=4),
                chips_row,
            ]
        try: area_filtros.update()
        except Exception: pass

    # Popula sem .update()
    chips_row.controls = [chip_periodo(l, v) for l, v in periodos]
    filtros_estoque_col.controls = [
        btn_estoque_filtro("Estoque Completo",  "completo", ft.icons.LIST_ALT,              Colors.BRAND_BLUE),
        btn_estoque_filtro("Produtos Ativos",   "ativos",   ft.icons.CHECK_CIRCLE_OUTLINE,  Colors.BRAND_GREEN),
        btn_estoque_filtro("Produtos Inativos", "inativos", ft.icons.REMOVE_CIRCLE_OUTLINE, Colors.TEXT_GRAY),
        btn_estoque_filtro("Estoque Baixo",     "baixo",    ft.icons.WARNING_AMBER,         Colors.BRAND_ORANGE),
    ]
    area_filtros.controls = [
        ft.Text("PERÍODO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
        ft.Container(height=4),
        chips_row,
    ]

    # =========================================================================
    # MENU LATERAL
    # =========================================================================
    tipos = [
        ("Vendas",  "vendas",  ft.icons.SHOPPING_BAG),
        ("Estoque", "estoque", ft.icons.INVENTORY_2),
        ("Margem",  "margem",  ft.icons.TRENDING_UP),
        ("Caixa",   "caixa",   ft.icons.POINT_OF_SALE),
        ("Geral",   "geral",   ft.icons.DASHBOARD),
    ]

    menu_col = ft.Column(spacing=4)

    def btn_tipo(label, valor, icone):
        selecionado = estado["tipo"] == valor
        def selecionar(e):
            estado["tipo"] = valor
            rebuild_menu()
            atualizar_preview()
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, size=18, color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_GRAY),
                ft.Text(label, size=14,
                        weight=ft.FontWeight.BOLD if selecionado else ft.FontWeight.W_400,
                        color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_BLACK),
            ], spacing=10),
            bgcolor=Colors.BRAND_RED if selecionado else Colors.BG_WHITE,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ink=True, on_click=selecionar,
            border=ft.border.all(1, Colors.BORDER_LIGHT if not selecionado else Colors.BRAND_RED),
        )

    def rebuild_menu():
        menu_col.controls = [
            ft.Text("TIPO DE RELATÓRIO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
            ft.Container(height=4),
            *[btn_tipo(l, v, i) for l, v, i in tipos],
        ]
        try: menu_col.update()
        except Exception: pass
        rebuild_area_filtros()

    # Popula menu sem .update()
    menu_col.controls = [
        ft.Text("TIPO DE RELATÓRIO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
        ft.Container(height=4),
        *[btn_tipo(l, v, i) for l, v, i in tipos],
    ]

    # =========================================================================
    # MODAL DE PERÍODO PERSONALIZADO
    # =========================================================================
    def abrir_modal_periodo():
        from datetime import date
        hoje = date.today()

        data_ini_input = ft.TextField(
            label="Data Início (DD/MM/AAAA)", width=180,
            border_color=Colors.BORDER_GRAY,
            hint_text="ex: 01/03/2026",
            keyboard_type=ft.KeyboardType.DATETIME,
        )
        data_fim_input = ft.TextField(
            label="Data Fim (DD/MM/AAAA)", width=180,
            border_color=Colors.BORDER_GRAY,
            hint_text=f"ex: {hoje.strftime('%d/%m/%Y')}",
            keyboard_type=ft.KeyboardType.DATETIME,
        )

        def confirmar(e):
            ini = data_ini_input.value.strip()
            fim = data_fim_input.value.strip()
            ok = True
            if not ini:
                data_ini_input.border_color = Colors.BRAND_RED
                data_ini_input.error_text = "Obrigatório"
                ok = False
            else:
                data_ini_input.border_color = Colors.BORDER_GRAY
                data_ini_input.error_text = None
            if not fim:
                data_fim_input.border_color = Colors.BRAND_RED
                data_fim_input.error_text = "Obrigatório"
                ok = False
            else:
                data_fim_input.border_color = Colors.BORDER_GRAY
                data_fim_input.error_text = None
            if not ok:
                page.update()
                return
            # Salva período personalizado e gera
            estado["periodo"]       = "personalizado"
            estado["data_inicio"]   = ini
            estado["data_fim"]      = fim
            estado["pode_exportar"] = True
            modal.open = False
            atualizar_preview()
            page.update()

        def fechar(e):
            modal.open = False
            page.update()

        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.DATE_RANGE, color=Colors.TEXT_WHITE, size=22),
                    ft.Text("Período do Relatório", size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_RED,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    tight=True, spacing=16,
                    controls=[
                        ft.Container(height=4),
                        ft.Text("Selecione o período para geração do relatório:", size=13, color=Colors.TEXT_GRAY),
                        ft.Row([data_ini_input, ft.Text("→", size=18, color=Colors.TEXT_GRAY), data_fim_input], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=4),
                        ft.Text("Ou use um período rápido:", size=12, color=Colors.TEXT_GRAY),
                        ft.Row([
                            _chip_rapido("Hoje",    "hoje",     data_ini_input, data_fim_input),
                            _chip_rapido("Semana",  "semana",   data_ini_input, data_fim_input),
                            _chip_rapido("Mês",     "mes",      data_ini_input, data_fim_input),
                            _chip_rapido("Semestre","semestre", data_ini_input, data_fim_input),
                            _chip_rapido("Ano",     "ano",      data_ini_input, data_fim_input),
                        ], spacing=6, wrap=True),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton(
                    "Gerar",
                    bgcolor=Colors.BRAND_RED, color=Colors.TEXT_WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=confirmar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()

    def _chip_rapido(label, valor, ini_field, fim_field):
        from datetime import date, timedelta
        def preencher(e):
            hoje = date.today()
            deltas = {
                "hoje":     (hoje, hoje),
                "semana":   (hoje - timedelta(days=7), hoje),
                "mes":      (hoje - timedelta(days=30), hoje),
                "bimestre": (hoje - timedelta(days=60), hoje),
                "semestre": (hoje - timedelta(days=180), hoje),
                "ano":      (hoje - timedelta(days=365), hoje),
            }
            ini, fim = deltas.get(valor, (hoje, hoje))
            ini_field.value = ini.strftime("%d/%m/%Y")
            fim_field.value = fim.strftime("%d/%m/%Y")
            ini_field.border_color = Colors.BORDER_GRAY
            fim_field.border_color = Colors.BORDER_GRAY
            ini_field.error_text = None
            fim_field.error_text = None
            page.update()
        return ft.ElevatedButton(
            label,
            style=ft.ButtonStyle(
                bgcolor="#F5F5F5", color=Colors.TEXT_GRAY,
                shape=ft.RoundedRectangleBorder(radius=16),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                elevation=0,
            ),
            on_click=preencher, height=32,
        )

    # =========================================================================
    # LAYOUT
    # =========================================================================

    def exportar_excel(e):
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Exportando Excel... (implementação pendente)"),
            bgcolor=Colors.BRAND_GREEN,
        )
        page.snack_bar.open = True
        page.update()

    btn_gerar_ref = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.icons.BAR_CHART, color=Colors.TEXT_WHITE, size=18),
            ft.Text("Gerar Relatório", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
        ], spacing=8, tight=True),
        bgcolor=Colors.BRAND_RED, height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=lambda _: abrir_modal_periodo() if estado["tipo"] != "estoque" else atualizar_preview(),
        width=220,
    )

    btn_exportar = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.icons.TABLE_VIEW, color=Colors.TEXT_WHITE, size=18),
            ft.Text("Exportar Excel", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
        ], spacing=8, tight=True),
        bgcolor=Colors.BRAND_GREEN,
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=exportar_excel,
        width=220,
    )

    painel_esq = ft.Container(
        content=ft.Column([
            menu_col,
            ft.Divider(height=20),
            area_filtros,
            ft.Divider(height=20),
            btn_gerar_ref,
            ft.Container(height=8),
            btn_exportar,
            ft.Container(expand=True),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.icons.HOME, color=Colors.TEXT_WHITE, size=18),
                    ft.Text("Menu Principal", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
                ], spacing=8, tight=True),
                bgcolor=Colors.BRAND_RED, height=48,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                on_click=lambda _: page.go("/"), width=220,
            ),
        ], spacing=4, expand=True),
        width=260, padding=20, bgcolor=Colors.BG_WHITE,
        border=ft.border.only(left=ft.BorderSide(2, Colors.BORDER_LIGHT)),
    )

    painel_dir = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Preview do Relatório", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", size=12, color=Colors.TEXT_GRAY),
                ], spacing=2, expand=True),
            ]),
            ft.Divider(height=16),
            ft.Container(content=preview_content, expand=True),
        ], spacing=0, expand=True),
        expand=True, padding=24, bgcolor=Colors.BG_GRAY_LIGHT,
    )

    preview_vendas()

    return ft.Row(controls=[painel_dir, painel_esq], spacing=0, expand=True)