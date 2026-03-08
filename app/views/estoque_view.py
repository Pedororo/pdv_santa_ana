import flet as ft
from app.views.styles.theme import Colors, Sizes, Styles
from app.api.produtos_api import ProdutosAPI
from app.api.categorias_api import CategoriasAPI

def EstoqueView(page: ft.Page):
    """Tela de gerenciamento de estoque"""
    
    produto_selecionado = None
    linha_selecionada = None
    categorias_disponiveis = []
    ordem_id_crescente = True  # controla a ordenação da coluna ID

    # ============================================================================
    # FUNÇÃO PARA CARREGAR CATEGORIAS
    # ============================================================================
    
    def carregar_categorias():
        nonlocal categorias_disponiveis
        categorias = CategoriasAPI.listar_categorias()
        categorias_disponiveis = categorias
        return categorias
    
    # ============================================================================
    # FUNÇÃO PARA CARREGAR PRODUTOS COM FILTROS
    # ============================================================================
    
    def carregar_produtos(filtro_texto="", filtro_categoria="Todos"):
        produtos = ProdutosAPI.listar_produtos()
        items_list.controls.clear()
        
        if produtos:
            filtrados = []
            for produto in produtos:
                if not produto.get("ativo", True):
                    continue
                
                if filtro_texto:
                    filtro_lower = filtro_texto.lower()
                    nome = produto.get("nome", "").lower()
                    cod_barras = produto.get("codigo_barra", "").lower()
                    produto_id = str(produto.get("id", "")).lower()
                    if filtro_lower not in nome and filtro_lower not in cod_barras and filtro_lower not in produto_id:
                        continue
                
                if filtro_categoria != "Todos":
                    if produto.get("categoria_nome", "") != filtro_categoria:
                        continue
                
                filtrados.append(produto)
            
            # Ordena por ID conforme estado atual
            filtrados.sort(key=lambda p: p.get("id", 0), reverse=not ordem_id_crescente)
            
            for produto in filtrados:
                items_list.controls.append(criar_linha_produto(produto))
        
        if len(items_list.controls) == 0:
            items_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.icons.SEARCH_OFF, size=80, color=Colors.TEXT_GRAY),
                            ft.Text("Nenhum produto encontrado", size=Sizes.FONT_LARGE, color=Colors.TEXT_GRAY, weight=ft.FontWeight.BOLD),
                            ft.Text("Tente ajustar os filtros de busca", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY, italic=True),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=50,
                    alignment=ft.alignment.center,
                )
            )
        
        page.update()
    
    def buscar_produtos(e):
        carregar_produtos(
            filtro_texto=pesquisa_input.value.strip(),
            filtro_categoria=filtro_dropdown.value,
        )

    def toggle_ordem_id(e):
        """Alterna ordenação crescente/decrescente ao clicar no header ID"""
        nonlocal ordem_id_crescente
        ordem_id_crescente = not ordem_id_crescente
        # Atualiza ícone do header
        icone = ft.icons.ARROW_UPWARD if ordem_id_crescente else ft.icons.ARROW_DOWNWARD
        btn_header_id.icon = icone
        buscar_produtos(None)

    # ============================================================================
    # MODAIS
    # ============================================================================
    
    def modal_incluir_produto(e):
        categorias = carregar_categorias()
        
        input_cod_barras = ft.TextField(label="Código de Barras", width=300, border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER)
        input_descricao  = ft.TextField(label="Descrição (Nome)", width=300, border_color=Colors.BORDER_GRAY)
        dropdown_tipo    = ft.Dropdown(
            label="Categoria", width=300,
            options=[ft.dropdown.Option(text=cat["nome"], key=str(cat["id"])) for cat in categorias if cat.get("ativo", True)],
            border_color=Colors.BORDER_GRAY,
        )
        input_quantidade    = ft.TextField(label="Quantidade em Estoque", width=300, border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        input_preco_compra  = ft.TextField(label="Preço de Compra (R$)",  width=300, border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER, value="0.00")
        input_preco_venda   = ft.TextField(label="Preço de Venda (R$)",   width=300, border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER, value="0.00")
        
        def salvar_produto(e):
            if not all([input_cod_barras.value, input_descricao.value, dropdown_tipo.value,
                        input_quantidade.value, input_preco_compra.value, input_preco_venda.value]):
                page.snack_bar = ft.SnackBar(content=ft.Text("Por favor, preencha todos os campos!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()
                return
            
            resultado = ProdutosAPI.criar_produto({
                "nome": input_descricao.value,
                "preco_venda": float(input_preco_venda.value.replace(",", ".")),
                "preco_compra": float(input_preco_compra.value.replace(",", ".")),
                "categoria_id": int(dropdown_tipo.value),
                "codigo_barra": input_cod_barras.value,
                "estoque": int(input_quantidade.value),
            })
            
            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Produto '{input_descricao.value}' incluído com sucesso!"), bgcolor=Colors.BRAND_GREEN)
                page.snack_bar.open = True
                buscar_produtos(None)
            else:
                page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao incluir produto!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
            page.update()
        
        def fechar_modal(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Incluir Produto", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(controls=[input_cod_barras, input_descricao, dropdown_tipo, input_quantidade, input_preco_compra, input_preco_venda], spacing=Sizes.SPACING_MEDIUM, scroll=ft.ScrollMode.AUTO),
                width=400, height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                ft.ElevatedButton("Salvar", bgcolor=Colors.BRAND_GREEN, color=Colors.TEXT_WHITE, on_click=salvar_produto),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    def modal_alterar_produto(e):
        nonlocal produto_selecionado
        
        if not produto_selecionado:
            page.snack_bar = ft.SnackBar(content=ft.Text("Selecione um produto na tabela primeiro!"), bgcolor=Colors.BRAND_ORANGE)
            page.snack_bar.open = True
            page.update()
            return
        
        categorias = carregar_categorias()
        
        input_id           = ft.TextField(label="ID do Produto",         width=300, border_color=Colors.BORDER_GRAY, value=str(produto_selecionado.get("id", "")), read_only=True, filled=True)
        input_cod_barras   = ft.TextField(label="Código de Barras",      width=300, border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER, value=produto_selecionado.get("codigo_barra", ""))
        input_descricao    = ft.TextField(label="Descrição (Nome)",      width=300, border_color=Colors.BORDER_GRAY, value=produto_selecionado.get("nome", ""))
        dropdown_tipo      = ft.Dropdown(label="Categoria", width=300, options=[ft.dropdown.Option(text=cat["nome"], key=str(cat["id"])) for cat in categorias if cat.get("ativo", True)], border_color=Colors.BORDER_GRAY, value=str(produto_selecionado.get("categoria_id", "")))
        input_quantidade   = ft.TextField(label="Quantidade em Estoque", width=300, border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER, value=str(produto_selecionado.get("estoque", "0")), disabled=True, helper_text="Estoque atual (não editável)")
        input_preco_compra = ft.TextField(label="Preço de Compra (R$)", width=300, border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER, value=str(float(produto_selecionado.get("preco_compra", 0))))
        input_preco_venda  = ft.TextField(label="Preço de Venda (R$)",  width=300, border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER, value=str(float(produto_selecionado.get("preco_venda", 0))))
        checkbox_ativo     = ft.Checkbox(label="Produto Ativo", value=produto_selecionado.get("ativo", True))
        
        def salvar_alteracoes(e):
            if not all([input_cod_barras.value, input_descricao.value, dropdown_tipo.value, input_preco_compra.value, input_preco_venda.value]):
                page.snack_bar = ft.SnackBar(content=ft.Text("Por favor, preencha todos os campos!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()
                return
            
            resultado = ProdutosAPI.atualizar_produto(produto_selecionado.get("id"), {
                "nome": input_descricao.value,
                "preco_venda": float(input_preco_venda.value.replace(",", ".")),
                "preco_compra": float(input_preco_compra.value.replace(",", ".")),
                "categoria_id": int(dropdown_tipo.value),
                "codigo_barra": input_cod_barras.value,
                "ativo": checkbox_ativo.value,
            })
            
            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Produto '{input_descricao.value}' alterado com sucesso!"), bgcolor=Colors.BRAND_GREEN)
                page.snack_bar.open = True
                buscar_produtos(None)
            else:
                page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao alterar produto!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
            page.update()
        
        def fechar_modal(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Alterar Produto", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(controls=[input_id, input_cod_barras, input_descricao, dropdown_tipo, input_quantidade, input_preco_compra, input_preco_venda, checkbox_ativo], spacing=Sizes.SPACING_MEDIUM, scroll=ft.ScrollMode.AUTO),
                width=400, height=500,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                ft.ElevatedButton("Salvar Alterações", bgcolor=Colors.BRAND_ORANGE, color=Colors.TEXT_WHITE, on_click=salvar_alteracoes),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    def modal_excluir_produto(e):
        nonlocal produto_selecionado
        
        if not produto_selecionado:
            page.snack_bar = ft.SnackBar(content=ft.Text("Selecione um produto na tabela primeiro!"), bgcolor=Colors.BRAND_ORANGE)
            page.snack_bar.open = True
            page.update()
            return
        
        def confirmar_exclusao(e):
            nonlocal produto_selecionado, linha_selecionada
            sucesso = ProdutosAPI.deletar_produto(produto_selecionado.get("id"))
            
            if sucesso:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Produto '{produto_selecionado.get('nome', '')}' excluído!"), bgcolor=Colors.BRAND_GREEN)
                page.snack_bar.open = True
                produto_selecionado = None
                linha_selecionada = None
                buscar_produtos(None)
            else:
                page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao excluir produto!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
            page.update()
        
        def cancelar_exclusao(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Excluir Produto", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.icons.WARNING_AMBER, size=80, color=Colors.BRAND_RED),
                        ft.Text("Tem certeza que deseja excluir este produto?", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Divider(),
                        ft.Text(f"ID: {produto_selecionado.get('id', '')}", size=Sizes.FONT_MEDIUM),
                        ft.Text(f"Cód. Barras: {produto_selecionado.get('codigo_barra', '')}", size=Sizes.FONT_MEDIUM),
                        ft.Text(f"Descrição: {produto_selecionado.get('nome', '')}", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Categoria: {produto_selecionado.get('categoria_nome', '')}", size=Sizes.FONT_MEDIUM),
                        ft.Divider(),
                        ft.Text("Esta ação não pode ser desfeita!", size=Sizes.FONT_SMALL, color=Colors.BRAND_RED, italic=True, text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Sizes.SPACING_MEDIUM,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_exclusao),
                ft.ElevatedButton("Sim, Excluir", bgcolor=Colors.BRAND_RED, color=Colors.TEXT_WHITE, on_click=confirmar_exclusao),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    # ============================================================================
    # SELEÇÃO DE PRODUTO
    # ============================================================================
    
    def selecionar_produto(produto_data, linha_container):
        nonlocal produto_selecionado, linha_selecionada
        
        if linha_selecionada:
            linha_selecionada.bgcolor = Colors.BG_WHITE
            linha_selecionada.border = ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT))
        
        produto_selecionado = produto_data
        linha_selecionada = linha_container
        linha_container.bgcolor = "#E3F2FD"
        linha_container.border = ft.border.all(2, Colors.BRAND_BLUE)
        page.update()
    
    # ============================================================================
    # INTERFACE
    # ============================================================================
    
    pesquisa_input = Styles.text_field("Pesquisar por produto", Sizes.INPUT_XLARGE, on_submit=buscar_produtos)
    btn_localizar  = Styles.button_localizar(on_click=buscar_produtos)
    
    filtro_dropdown = ft.Dropdown(
        label="Filtro",
        options=[
            ft.dropdown.Option("Todos"),
            ft.dropdown.Option("Medicamentos & Saúde"),
            ft.dropdown.Option("Vitaminas & Suplementos"),
            ft.dropdown.Option("Beleza & Skincare"),
            ft.dropdown.Option("Higiene Pessoal"),
            ft.dropdown.Option("Bebê & Infantil"),
            ft.dropdown.Option("Nutrição & Esporte"),
            ft.dropdown.Option("Alimentação Saudável"),
            ft.dropdown.Option("Casa & Limpeza"),
            ft.dropdown.Option("Pet Care"),
            ft.dropdown.Option("Aparelhos & Dispositivos"),
            ft.dropdown.Option("Outros"),
        ],
        value="Todos",
        border_color=Colors.BORDER_GRAY,
        on_change=buscar_produtos,
    )
    
    top_section = Styles.search_section(pesquisa_input, btn_localizar, filtro_dropdown)

    # ============================================================================
    # HEADER COM BOTÃO CLICÁVEL NA COLUNA ID
    # ============================================================================

    btn_header_id = ft.IconButton(
        icon=ft.icons.ARROW_UPWARD,   # começa crescente
        icon_size=14,
        icon_color=Colors.TEXT_BLACK,
        tooltip="Ordenar por ID",
        on_click=toggle_ordem_id,
        padding=ft.padding.all(0),
    )

    header_id = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text("ID", weight=ft.FontWeight.BOLD, size=Sizes.FONT_MEDIUM),
                btn_header_id,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=2,
            tight=True,
        ),
        width=Sizes.TABLE_COL_SMALL,
        alignment=ft.alignment.center,
    )

    def make_header_cell(text, width=None):
        return ft.Container(
            ft.Text(text, weight=ft.FontWeight.BOLD, size=Sizes.FONT_MEDIUM, text_align=ft.TextAlign.CENTER),
            width=width,
            expand=(width is None),
            alignment=ft.alignment.center,
        )

    table_header = ft.Container(
        content=ft.Row(
            controls=[
                header_id,
                make_header_cell("Cód. Barras", Sizes.TABLE_COL_LARGE),
                make_header_cell("Descrição"),
                make_header_cell("Categoria",   Sizes.TABLE_COL_XLARGE),
                make_header_cell("Estoque",     Sizes.TABLE_COL_SMALL),
                make_header_cell("Compra",      Sizes.TABLE_COL_MEDIUM),
                make_header_cell("Venda",       Sizes.TABLE_COL_MEDIUM),
            ],
            spacing=0,
        ),
        bgcolor=Colors.BG_PINK_LIGHT,
        padding=10,
        border=ft.border.all(1, Colors.BORDER_BLACK),
    )

    # ============================================================================
    # LINHA DE PRODUTO
    # ============================================================================

    def criar_linha_produto(produto):
        linha = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Text(str(produto.get("id", "")),                                  size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_SMALL,  alignment=ft.alignment.center),
                    ft.Container(ft.Text(produto.get("codigo_barra", ""),                             size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_LARGE,  alignment=ft.alignment.center),
                    ft.Container(ft.Text(produto.get("nome", ""),                                     size=Sizes.FONT_SMALL), expand=True,                  alignment=ft.alignment.center),
                    ft.Container(ft.Text(produto.get("categoria_nome", ""),                           size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_XLARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(str(produto.get("estoque", 0)),                              size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_SMALL,  alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {float(produto.get('preco_compra', 0)):.2f}",           size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {float(produto.get('preco_venda',  0)):.2f}",           size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                ],
                spacing=0,
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
            padding=10,
            bgcolor=Colors.BG_WHITE,
            ink=True,
        )
        linha.on_click = lambda _, p=produto, l=linha: selecionar_produto(p, l)
        return linha

    items_list = ft.Column(controls=[], spacing=0, scroll=ft.ScrollMode.AUTO)

    table_container = ft.Container(
        content=ft.Column(
            controls=[
                table_header,
                ft.Container(content=items_list, expand=True, border=ft.border.all(1, Colors.BORDER_BLACK), bgcolor=Colors.BG_WHITE),
            ],
            spacing=0,
        ),
        expand=True,
        margin=ft.margin.only(top=Sizes.SPACING_LARGE),
    )

    btn_incluir   = Styles.button_primary("Incluir Produto", ft.icons.ADD_CIRCLE, modal_incluir_produto)
    btn_alterar   = Styles.button_warning("Alterar Produto", ft.icons.EDIT,       modal_alterar_produto)
    btn_excluir   = Styles.button_danger( "Excluir Produto", ft.icons.DELETE,     modal_excluir_produto)
    btn_atualizar = Styles.button_info(   "Atualizar Lista", ft.icons.REFRESH,    lambda _: buscar_produtos(None))
    btn_sair      = Styles.button_danger( "Menu Principal",  ft.icons.HOME,       lambda _: page.go("/"))

    sidebar = Styles.sidebar([
        btn_incluir,
        btn_alterar,
        btn_excluir,
        btn_atualizar,
        ft.Container(expand=True),
        btn_sair,
    ])

    main_content = ft.Container(
        content=ft.Column(controls=[top_section, table_container], spacing=0, expand=True),
        expand=True,
        padding=Sizes.SPACING_LARGE,
        bgcolor=Colors.BG_WHITE,
    )

    carregar_produtos()

    return ft.Row(controls=[main_content, sidebar], spacing=0, expand=True)