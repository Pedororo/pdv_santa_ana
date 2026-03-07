import flet as ft
from app.views.styles.theme import Colors, Sizes, Styles
from app.api.produtos_api import ProdutosAPI

def EstoqueView(page: ft.Page):
    """Tela de gerenciamento de estoque"""
    
    # Variável para armazenar o produto selecionado
    produto_selecionado = None
    linha_selecionada = None
    
    # ============================================================================
    # FUNÇÃO PARA CARREGAR PRODUTOS
    # ============================================================================
    
    def carregar_produtos():
        """Carrega produtos da API e atualiza a tabela"""
        produtos = ProdutosAPI.listar_produtos()
        
        # Limpa a lista atual
        items_list.controls.clear()
        
        # Adiciona os produtos da API
        if produtos:
            for produto in produtos:
                # Só mostra produtos ativos
                if produto.get("ativo", True):
                    items_list.controls.append(criar_linha_produto(produto))
        
        page.update()
    
    # ============================================================================
    # MODAIS
    # ============================================================================
    
    def modal_incluir_produto(e):
        """Modal para incluir novo produto"""
        
        # Campos do formulário
        input_cod_barras = ft.TextField(
            label="Código de Barras",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        input_descricao = ft.TextField(
            label="Descrição (Nome)",
            width=300,
            border_color=Colors.BORDER_GRAY
        )
        
        dropdown_tipo = ft.Dropdown(
            label="Categoria",
            width=300,
            options=[
                ft.dropdown.Option(text="Medicamentos", key="1"),
                ft.dropdown.Option(text="Higiene", key="2"),
                ft.dropdown.Option(text="Cosméticos", key="3"),
            ],
            border_color=Colors.BORDER_GRAY,
        )
        
        input_quantidade = ft.TextField(
            label="Quantidade em Estoque",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0"
        )
        
        input_preco_compra = ft.TextField(
            label="Preço de Compra (R$)",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0.00"
        )
        
        input_preco_venda = ft.TextField(
            label="Preço de Venda (R$)",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0.00"
        )
        
        def salvar_produto(e):
            # Validação básica
            if not all([input_cod_barras.value, input_descricao.value, dropdown_tipo.value, 
                       input_quantidade.value, input_preco_compra.value, input_preco_venda.value]):
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Por favor, preencha todos os campos!"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()
                return
            
            # Monta o objeto para enviar à API
            produto_data = {
                "nome": input_descricao.value,
                "preco_venda": float(input_preco_venda.value.replace(",", ".")),
                "preco_compra": float(input_preco_compra.value.replace(",", ".")),
                "categoria_id": int(dropdown_tipo.value),
                "codigo_barra": input_cod_barras.value,
                "estoque": int(input_quantidade.value)
            }
            
            # Chama a API para criar o produto
            resultado = ProdutosAPI.criar_produto(produto_data)
            
            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Produto '{input_descricao.value}' incluído com sucesso!"),
                    bgcolor=Colors.BRAND_GREEN,
                )
                page.snack_bar.open = True
                
                # Recarrega a lista de produtos
                carregar_produtos()
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Erro ao incluir produto!"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
            
            page.update()
        
        def fechar_modal(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Incluir Produto", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        input_cod_barras,
                        input_descricao,
                        dropdown_tipo,
                        input_quantidade,
                        input_preco_compra,
                        input_preco_venda,
                    ],
                    spacing=Sizes.SPACING_MEDIUM,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                ft.ElevatedButton(
                    "Salvar",
                    bgcolor=Colors.BRAND_GREEN,
                    color=Colors.TEXT_WHITE,
                    on_click=salvar_produto,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    def modal_alterar_produto(e):
        """Modal para alterar produto selecionado"""
        
        nonlocal produto_selecionado
        
        if not produto_selecionado:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Selecione um produto na tabela primeiro!"),
                bgcolor=Colors.BRAND_ORANGE,
            )
            page.snack_bar.open = True
            page.update()
            return
        
        # Campos pré-preenchidos com dados do produto selecionado
        input_id = ft.TextField(
            label="ID do Produto",
            width=300,
            border_color=Colors.BORDER_GRAY,
            value=str(produto_selecionado.get("id", "")),
            read_only=True,
            filled=True,
        )
        
        input_cod_barras = ft.TextField(
            label="Código de Barras",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=produto_selecionado.get("codigo_barra", ""),
        )
        
        input_descricao = ft.TextField(
            label="Descrição (Nome)",
            width=300,
            border_color=Colors.BORDER_GRAY,
            value=produto_selecionado.get("nome", ""),
        )
        
        dropdown_tipo = ft.Dropdown(
            label="Categoria",
            width=300,
            options=[
                ft.dropdown.Option(text="Medicamentos", key="1"),
                ft.dropdown.Option(text="Higiene", key="2"),
                ft.dropdown.Option(text="Cosméticos", key="3"),
            ],
            border_color=Colors.BORDER_GRAY,
            value=str(produto_selecionado.get("categoria_id", "1")),
        )
        
        input_quantidade = ft.TextField(
            label="Quantidade em Estoque",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(produto_selecionado.get("estoque", "0")),
            disabled=True,  # Não permite alterar estoque direto
            helper_text="Estoque atual (não editável)"
        )
        
        input_preco_compra = ft.TextField(
            label="Preço de Compra (R$)",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(float(produto_selecionado.get("preco_compra", 0))),
        )
        
        input_preco_venda = ft.TextField(
            label="Preço de Venda (R$)",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(float(produto_selecionado.get("preco_venda", 0))),
        )
        
        checkbox_ativo = ft.Checkbox(
            label="Produto Ativo",
            value=produto_selecionado.get("ativo", True),
        )
        
        def salvar_alteracoes(e):
            # Validação básica
            if not all([input_cod_barras.value, input_descricao.value, dropdown_tipo.value, 
                       input_preco_compra.value, input_preco_venda.value]):
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Por favor, preencha todos os campos!"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()
                return
            
            # Monta o objeto para enviar à API
            produto_data = {
                "nome": input_descricao.value,
                "preco_venda": float(input_preco_venda.value.replace(",", ".")),
                "preco_compra": float(input_preco_compra.value.replace(",", ".")),
                "categoria_id": int(dropdown_tipo.value),
                "codigo_barra": input_cod_barras.value,
                "ativo": checkbox_ativo.value
            }
            
            # Chama a API para atualizar o produto
            produto_id = produto_selecionado.get("id")
            resultado = ProdutosAPI.atualizar_produto(produto_id, produto_data)
            
            if resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Produto '{input_descricao.value}' alterado com sucesso!"),
                    bgcolor=Colors.BRAND_GREEN,
                )
                page.snack_bar.open = True
                
                # Recarrega a lista de produtos
                carregar_produtos()
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Erro ao alterar produto!"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
            
            page.update()
        
        def fechar_modal(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Alterar Produto", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        input_id,
                        input_cod_barras,
                        input_descricao,
                        dropdown_tipo,
                        input_quantidade,
                        input_preco_compra,
                        input_preco_venda,
                        checkbox_ativo,
                    ],
                    spacing=Sizes.SPACING_MEDIUM,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=400,
                height=500,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                ft.ElevatedButton(
                    "Salvar Alterações",
                    bgcolor=Colors.BRAND_ORANGE,
                    color=Colors.TEXT_WHITE,
                    on_click=salvar_alteracoes,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    def modal_excluir_produto(e):
        """Modal de confirmação para excluir produto"""
        
        nonlocal produto_selecionado
        
        if not produto_selecionado:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Selecione um produto na tabela primeiro!"),
                bgcolor=Colors.BRAND_ORANGE,
            )
            page.snack_bar.open = True
            page.update()
            return
        
        def confirmar_exclusao(e):
            nonlocal produto_selecionado, linha_selecionada
            
            # Chama a API para deletar o produto
            produto_id = produto_selecionado.get("id")
            sucesso = ProdutosAPI.deletar_produto(produto_id)
            
            if sucesso:
                modal.open = False
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Produto '{produto_selecionado.get('nome', '')}' excluído!"),
                    bgcolor=Colors.BRAND_GREEN,
                )
                page.snack_bar.open = True
                
                # Limpa a seleção
                produto_selecionado = None
                linha_selecionada = None
                
                # Recarrega a lista de produtos
                carregar_produtos()
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Erro ao excluir produto!"),
                    bgcolor=Colors.BRAND_RED,
                )
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
                        ft.Text(
                            "Tem certeza que deseja excluir este produto?",
                            size=Sizes.FONT_LARGE,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(),
                        ft.Text(
                            f"ID: {produto_selecionado.get('id', '')}",
                            size=Sizes.FONT_MEDIUM,
                        ),
                        ft.Text(
                            f"Cód. Barras: {produto_selecionado.get('codigo_barra', '')}",
                            size=Sizes.FONT_MEDIUM,
                        ),
                        ft.Text(
                            f"Descrição: {produto_selecionado.get('nome', '')}",
                            size=Sizes.FONT_MEDIUM,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"Categoria: {produto_selecionado.get('categoria_nome', '')}",
                            size=Sizes.FONT_MEDIUM,
                        ),
                        ft.Divider(),
                        ft.Text(
                            "Esta ação não pode ser desfeita!",
                            size=Sizes.FONT_SMALL,
                            color=Colors.BRAND_RED,
                            italic=True,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Sizes.SPACING_MEDIUM,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_exclusao),
                ft.ElevatedButton(
                    "Sim, Excluir",
                    bgcolor=Colors.BRAND_RED,
                    color=Colors.TEXT_WHITE,
                    on_click=confirmar_exclusao,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    # ============================================================================
    # FUNÇÃO PARA SELECIONAR PRODUTO NA TABELA
    # ============================================================================
    
    def selecionar_produto(produto_data, linha_container):
        """Seleciona um produto quando clicado na tabela"""
        nonlocal produto_selecionado, linha_selecionada
        
        # Remove a seleção anterior
        if linha_selecionada:
            linha_selecionada.bgcolor = Colors.BG_WHITE
            linha_selecionada.border = ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT))
        
        # Define nova seleção
        produto_selecionado = produto_data
        linha_selecionada = linha_container
        
        # Destaca visualmente a linha selecionada
        linha_container.bgcolor = "#E3F2FD"  # Azul claro
        linha_container.border = ft.border.all(2, Colors.BRAND_BLUE)
        
        page.update()
        print(f"Produto selecionado: {produto_data}")
    
    # ============================================================================
    # INTERFACE
    # ============================================================================
    
    # Campo de pesquisa
    pesquisa_input = Styles.text_field("Pesquisar por produto", Sizes.INPUT_XLARGE)
    
    # Botão Localizar
    btn_localizar = Styles.button_localizar(on_click=lambda _: print("Localizar produto"))
    
    # Dropdown de filtro
    filtro_dropdown = Styles.dropdown(
        label="Filtro",
        options=["Todos", "Medicamentos", "Higiene", "Cosméticos"],
        value="Todos"
    )
    
    # Container superior com pesquisa e filtro
    top_section = Styles.search_section(pesquisa_input, btn_localizar, filtro_dropdown)
    
    # Cabeçalho da tabela
    table_header = Styles.table_header([
        ("ID", Sizes.TABLE_COL_SMALL),
        ("Cód. Barras", Sizes.TABLE_COL_LARGE),
        ("Descrição", None),
        ("Categoria", Sizes.TABLE_COL_XLARGE),
        ("Estoque", Sizes.TABLE_COL_SMALL),
        ("Compra", Sizes.TABLE_COL_MEDIUM),
        ("Venda", Sizes.TABLE_COL_MEDIUM),
    ])
    
    # Função para criar linha clicável
    def criar_linha_produto(produto):
        linha = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Text(str(produto.get("id", "")), size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                    ft.Container(ft.Text(produto.get("codigo_barra", ""), size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(produto.get("nome", ""), size=Sizes.FONT_SMALL), expand=True, alignment=ft.alignment.center),
                    ft.Container(ft.Text(produto.get("categoria_nome", ""), size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_XLARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text(str(produto.get("estoque", 0)), size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {float(produto.get('preco_compra', 0)):.2f}", size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {float(produto.get('preco_venda', 0)):.2f}", size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                ],
                spacing=0,
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
            padding=10,
            bgcolor=Colors.BG_WHITE,
            ink=True,
        )
        
        # Adiciona o evento de clique passando a própria linha
        linha.on_click = lambda _, p=produto, l=linha: selecionar_produto(p, l)
        
        return linha
    
    # Lista de produtos
    items_list = ft.Column(
        controls=[],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
    )
    
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
    btn_incluir = Styles.button_primary("Incluir Produto", ft.icons.ADD_CIRCLE, modal_incluir_produto)
    btn_alterar = Styles.button_warning("Alterar Produto", ft.icons.EDIT, modal_alterar_produto)
    btn_excluir = Styles.button_danger("Excluir Produto", ft.icons.DELETE, modal_excluir_produto)
    btn_atualizar = Styles.button_info("Atualizar Lista", ft.icons.REFRESH, lambda _: carregar_produtos())
    btn_sair = Styles.button_danger("Sair", ft.icons.LOGOUT, lambda _: page.go("/"))
    
    # Sidebar
    sidebar = Styles.sidebar([
        btn_incluir,
        btn_alterar,
        btn_excluir,
        btn_atualizar,
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
        bgcolor=Colors.BG_WHITE,
    )
    
    # Carrega os produtos ao iniciar
    carregar_produtos()
    
    # Retorna o layout completo
    return ft.Row(
        controls=[main_content, sidebar],
        spacing=0,
        expand=True,
    )