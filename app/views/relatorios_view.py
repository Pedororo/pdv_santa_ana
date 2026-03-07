import flet as ft
from datetime import datetime
from app.views.styles.theme import Colors, Sizes, Styles

def RelatoriosView(page: ft.Page):
    """Tela de geração e visualização de relatórios"""
    
    # ============================================================================
    # SEÇÃO DE SELEÇÃO DE RELATÓRIO
    # ============================================================================
    
    # Dropdown de tipo de relatório
    tipo_relatorio = Styles.dropdown(
        label="Tipo de Relatório",
        options=[
            "Relatório de Lucro",
            "Relatório de Estoque",
            "Relatório de Caixa",
            "Relatório de Vendas",
            "Relatório Geral"
        ],
        width=300,
        value="Relatório de Lucro"
    )
    
    # Dropdown de período
    periodo_dropdown = Styles.dropdown(
        label="Período",
        options=["Hoje", "Semana", "Mês", "3 Meses", "6 Meses", "Ano", "Personalizado"],
        width=200,
        value="Mês"
    )
    
    # Campos de data personalizada (inicialmente ocultos)
    data_inicio = Styles.text_field("Data Início", 150, value="01/01/2026")
    data_fim = Styles.text_field("Data Fim", 150, value=datetime.now().strftime("%d/%m/%Y"))
    
    # Container de datas personalizadas
    datas_personalizadas = ft.Container(
        content=ft.Row(
            controls=[data_inicio, data_fim],
            spacing=Sizes.SPACING_MEDIUM,
        ),
        visible=False,
    )
    
    # Função para mostrar/ocultar datas personalizadas
    def on_periodo_change(e):
        if periodo_dropdown.value == "Personalizado":
            datas_personalizadas.visible = True
        else:
            datas_personalizadas.visible = False
        page.update()
    
    periodo_dropdown.on_change = on_periodo_change
    
    # Botão Gerar Relatório
    btn_gerar = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.ASSESSMENT, size=Sizes.ICON_MEDIUM, color=Colors.TEXT_WHITE),
                ft.Text("Gerar Relatório", size=Sizes.FONT_LARGE, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=Sizes.SPACING_MEDIUM,
        ),
        bgcolor=Colors.BRAND_BLUE,
        width=250,
        height=Sizes.BUTTON_SMALL_HEIGHT,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
        on_click=lambda _: print(f"Gerar: {tipo_relatorio.value} - {periodo_dropdown.value}")
    )
    
    # Container de seleção de relatório
    selecao_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[tipo_relatorio, periodo_dropdown, btn_gerar],
                    spacing=Sizes.SPACING_LARGE,
                    alignment=ft.MainAxisAlignment.START,
                ),
                datas_personalizadas,
            ],
            spacing=Sizes.SPACING_MEDIUM,
        ),
        padding=Sizes.SPACING_LARGE,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,  # ← ADICIONADO
    )
    
    # ============================================================================
    # SEÇÃO DE PREVIEW DO RELATÓRIO
    # ============================================================================
    
    # Cards de resumo (exemplo)
    def create_summary_card(titulo, valor, cor, icone):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icone, size=40, color=cor),
                    ft.Text(titulo, size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY, text_align=ft.TextAlign.CENTER),
                    ft.Text(valor, size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD, color=cor, text_align=ft.TextAlign.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Sizes.SPACING_SMALL,
            ),
            width=200,
            height=150,
            bgcolor=Colors.BG_WHITE,
            border=ft.border.all(2, cor),
            border_radius=Sizes.BORDER_RADIUS_LARGE,
            padding=Sizes.SPACING_LARGE,
        )
    
    # Cards de exemplo
    cards_resumo = ft.Row(
        controls=[
            create_summary_card("Total de Vendas", "R$ 15.450,00", Colors.BRAND_GREEN, ft.icons.SHOPPING_CART),
            create_summary_card("Lucro Líquido", "R$ 4.320,00", Colors.BRAND_BLUE, ft.icons.TRENDING_UP),
            create_summary_card("Despesas", "R$ 2.130,00", Colors.BRAND_RED, ft.icons.MONEY_OFF),
            create_summary_card("Margem", "28%", Colors.BRAND_ORANGE, ft.icons.PERCENT),
        ],
        spacing=Sizes.SPACING_LARGE,
        wrap=True,
    )
    
    # Preview do relatório
    preview_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Preview do Relatório", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
                ft.Divider(color=Colors.BORDER_MEDIUM),
                cards_resumo,
                ft.Container(height=20),
                ft.Text("Dados detalhados aparecerão aqui após gerar o relatório...", size=Sizes.FONT_MEDIUM, color=Colors.TEXT_GRAY, italic=True),
            ],
            spacing=Sizes.SPACING_LARGE,
        ),
        padding=Sizes.SPACING_LARGE,
        border=ft.border.all(2, Colors.BORDER_BLACK),  # ← MUDADO
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,
        margin=ft.margin.only(top=Sizes.SPACING_LARGE),  # ← ADICIONADO
    )
    
    # ============================================================================
    # SEÇÃO DE RELATÓRIOS SALVOS
    # ============================================================================
    
    # Cabeçalho da tabela de relatórios salvos
    table_header = Styles.table_header([
        ("ID", Sizes.TABLE_COL_SMALL),
        ("Tipo", 200),
        ("Período", Sizes.TABLE_COL_LARGE),
        ("Data de Geração", Sizes.TABLE_COL_XLARGE),
        ("Ações", Sizes.TABLE_COL_LARGE),
    ])
    
    # Função para criar linha de relatório salvo
    def create_relatorio_row(id, tipo, periodo, data_geracao):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Text(id, size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                    ft.Container(ft.Text(tipo, size=Sizes.FONT_SMALL), width=200, alignment=ft.alignment.center),
                    ft.Container(ft.Text(periodo, size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(data_geracao, size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_XLARGE, alignment=ft.alignment.center),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.VISIBILITY,
                                    icon_color=Colors.BRAND_BLUE,
                                    tooltip="Visualizar",
                                    icon_size=20,
                                    on_click=lambda _, i=id: print(f"Visualizar relatório {i}")
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DOWNLOAD,
                                    icon_color=Colors.BRAND_GREEN,
                                    tooltip="Baixar PDF",
                                    icon_size=20,
                                    on_click=lambda _, i=id: print(f"Baixar relatório {i}")
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color=Colors.BRAND_RED,
                                    tooltip="Excluir",
                                    icon_size=20,
                                    on_click=lambda _, i=id: print(f"Excluir relatório {i}")
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=0,
                        ),
                        width=Sizes.TABLE_COL_LARGE,
                        alignment=ft.alignment.center
                    ),
                ],
                spacing=0,
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
            padding=10,
            bgcolor=Colors.BG_WHITE,  # ← ADICIONADO
        )
    
    # Lista de relatórios salvos (exemplo)
    relatorios_salvos = ft.Column(
        controls=[
            create_relatorio_row("001", "Relatório de Lucro", "Mês", "27/01/2026 14:30"),
            create_relatorio_row("002", "Relatório de Estoque", "Semana", "25/01/2026 10:15"),
            create_relatorio_row("003", "Relatório de Caixa", "Hoje", "27/01/2026 16:45"),
        ],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
    )
    
    # Container de relatórios salvos
    relatorios_salvos_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Relatórios Salvos", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
                ft.Divider(color=Colors.BORDER_MEDIUM),
                table_header,
                ft.Container(
                    content=relatorios_salvos,
                    height=250,
                    border=ft.border.all(1, Colors.BORDER_BLACK),
                    bgcolor=Colors.BG_WHITE,
                ),
            ],
            spacing=Sizes.SPACING_MEDIUM,
        ),
        padding=Sizes.SPACING_LARGE,
        border=ft.border.all(2, Colors.BORDER_BLACK),  # ← MUDADO
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,  # ← ADICIONADO
        margin=ft.margin.only(top=Sizes.SPACING_LARGE),
    )
    
    # ============================================================================
    # SIDEBAR COM BOTÕES
    # ============================================================================
    
    btn_exportar_pdf = Styles.button_danger("Exportar PDF", ft.icons.PICTURE_AS_PDF, lambda _: print("Exportar PDF"))
    btn_exportar_excel = Styles.button_primary("Exportar Excel", ft.icons.TABLE_CHART, lambda _: print("Exportar Excel"))
    btn_imprimir = Styles.button_info("Imprimir", ft.icons.PRINT, lambda _: print("Imprimir"))
    btn_sair = Styles.button_danger("Sair", ft.icons.LOGOUT, lambda _: page.go("/"))
    
    # Sidebar
    sidebar = Styles.sidebar([
        btn_exportar_pdf,
        btn_exportar_excel,
        btn_imprimir,
        ft.Container(expand=True),
        btn_sair,
    ])
    
    # ============================================================================
    # LAYOUT PRINCIPAL
    # ============================================================================
    
    main_content = ft.Container(
        content=ft.Column(
            controls=[
                selecao_section,
                preview_container,
                relatorios_salvos_container,
            ],
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        padding=Sizes.SPACING_LARGE,
        bgcolor=Colors.BG_WHITE,  # ← ADICIONADO - IMPORTANTE!
    )
    
    # Retorna o layout completo
    return ft.Row(
        controls=[main_content, sidebar],
        spacing=0,
        expand=True,
    )