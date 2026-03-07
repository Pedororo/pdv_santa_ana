import flet as ft
from datetime import datetime
from app.views.styles.theme import Colors, Sizes, Styles

def HistoricoView(page: ft.Page):
    """Tela de histórico de vendas"""
    
    # Campo de pesquisa
    pesquisa_input = Styles.text_field("Pesquisar venda", Sizes.INPUT_XLARGE)
    
    # Botão Localizar
    btn_localizar = Styles.button_localizar(on_click=lambda _: print("Localizar venda"))
    
    # Dropdown de filtro por período
    filtro_dropdown = Styles.dropdown(
        label="Filtro",
        options=["Hoje", "Semana", "Mês", "3 Meses", "Todos"],
        value="Hoje"
    )
    
    # Container superior com pesquisa e filtro
    top_section = Styles.search_section(pesquisa_input, btn_localizar, filtro_dropdown)
    
    # Cabeçalho da tabela
    table_header = Styles.table_header([
        ("ID", Sizes.TABLE_COL_SMALL),
        ("Data", Sizes.TABLE_COL_LARGE),
        ("Hora", Sizes.TABLE_COL_MEDIUM),
        ("Vendedor", Sizes.TABLE_COL_XLARGE),
        ("Cliente", Sizes.TABLE_COL_XLARGE),
        ("Itens", Sizes.TABLE_COL_SMALL),
        ("Valor Total", Sizes.TABLE_COL_LARGE),
        ("Status", Sizes.TABLE_COL_LARGE),
    ])
    
    # Área de vendas do histórico
    items_list = ft.Column(controls=[], spacing=0, scroll=ft.ScrollMode.AUTO)
    
    # Container da tabela
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
    
    # Botão Sair
    btn_sair = Styles.button_danger("Sair", ft.icons.LOGOUT, lambda _: page.go("/"))
    
    # Sidebar
    sidebar = Styles.sidebar([
        ft.Container(expand=True),
        btn_sair,
    ])
    
    # Layout principal
    main_content = ft.Container(
        content=ft.Column(
            controls=[top_section, table_container],
            spacing=0,
            expand=True,
        ),
        expand=True,
        padding=Sizes.SPACING_LARGE,
    )
    
    # Retorna o layout completo
    return ft.Row(
        controls=[main_content, sidebar],
        spacing=0,
        expand=True,
    )