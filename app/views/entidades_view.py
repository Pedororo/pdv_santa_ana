import flet as ft
from app.views.styles.theme import Colors, Sizes, Styles

def EntidadesView(page: ft.Page):
    """Tela de gerenciamento de entidades/usuários"""
    
    # Campo de pesquisa
    pesquisa_input = Styles.text_field("Pesquisar por usuário", Sizes.INPUT_XLARGE)
    
    # Botão Localizar
    btn_localizar = Styles.button_localizar(on_click=lambda _: print("Localizar usuário"))
    
    # Dropdown de filtro
    filtro_dropdown = Styles.dropdown(
        label="Filtro",
        options=["Todos", "Administrador", "Vendedor", "Estoquista"],
        value="Todos"
    )
    
    # Container superior com pesquisa e filtro
    top_section = Styles.search_section(pesquisa_input, btn_localizar, filtro_dropdown)
    
    # Cabeçalho da tabela
    table_header = Styles.table_header([
        ("ID", Sizes.TABLE_COL_MEDIUM),
        ("Nome de usuário", None),
        ("Adm", Sizes.TABLE_COL_MEDIUM),
        ("Vendedor", Sizes.TABLE_COL_LARGE),
        ("Estoquista", Sizes.TABLE_COL_LARGE),
    ])
    
    # Área de itens de usuários
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
    
    # Botões da sidebar
    btn_incluir = Styles.button_primary("Incluir Entidade", ft.icons.ADD_CIRCLE, lambda _: print("Incluir"))
    btn_alterar = Styles.button_warning("Alterar Entidade", ft.icons.EDIT, lambda _: print("Alterar"))
    btn_excluir = Styles.button_danger("Excluir Entidade", ft.icons.DELETE, lambda _: print("Excluir"))
    btn_sair = Styles.button_danger("Sair", ft.icons.LOGOUT, lambda _: page.go("/"))
    
    # Sidebar
    sidebar = Styles.sidebar([
        btn_incluir,
        btn_alterar,
        btn_excluir,
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