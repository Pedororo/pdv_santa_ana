import flet as ft
from app.views.styles.theme import Colors, Sizes, Styles
from app.api.produtos_api import ProdutosAPI
from app.api.categorias_api import CategoriasAPI
from app.api.movimentacao_api import MovimentacaoAPI

def EstoqueView(page: ft.Page):
    """Tela de gerenciamento de estoque"""
    
    produto_selecionado = None
    linha_selecionada = None
    categorias_disponiveis = []
    ordem_id_crescente = True  # controla a ordenação da coluna ID
    modo_inativos = {"ativo": False}  # toggle entre tabela ativa/inativa
    cache_inativos = {"lista": []}    # cache dos produtos inativos para validação

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
    
    def reativar_produto(prod):
        """Reativa um produto inativo e volta para a tabela de ativos"""
        resultado = ProdutosAPI.atualizar_produto(prod.get("id"), {
            "nome":         prod.get("nome"),
            "preco_venda":  float(prod.get("preco_venda") or 0),
            "preco_compra": float(prod.get("preco_compra") or 0),
            "categoria_id": prod.get("categoria_id"),
            "codigo_barra": prod.get("codigo_barra", ""),
            "estoque":      prod.get("estoque", 0),
            "ativo":        True,
        })
        if resultado:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✓ Produto '{prod.get('nome')}' reativado com sucesso!"),
                bgcolor=Colors.BRAND_GREEN,
            )
            page.snack_bar.open = True
            carregar_inativos_na_tabela()
        else:
            page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao reativar produto!"), bgcolor=Colors.BRAND_RED)
            page.snack_bar.open = True
        page.update()

    def carregar_inativos_na_tabela():
        """Carrega produtos inativos na tabela principal"""
        todos = ProdutosAPI.listar_produtos() or []
        inativos = [p for p in todos if not p.get("ativo", True)]
        cache_inativos["lista"] = inativos  # atualiza cache para validação de cod. barras
        items_list.controls.clear()

        if not inativos:
            items_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.CHECK_CIRCLE_OUTLINE, size=80, color=Colors.BRAND_GREEN),
                        ft.Text("Nenhum produto inativo!", size=Sizes.FONT_LARGE, color=Colors.TEXT_GRAY, weight=ft.FontWeight.BOLD),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=50, alignment=ft.alignment.center,
                )
            )
        else:
            for prod in inativos:
                def _reativar(e, p=prod):
                    reativar_produto(p)

                linha = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(ft.Text(str(prod.get("id", "")), size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY), width=Sizes.TABLE_COL_SMALL),
                            ft.Container(ft.Text(prod.get("codigo_barra", ""), size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_XLARGE),
                            ft.Container(ft.Text(prod.get("nome", ""), size=Sizes.FONT_SMALL), expand=True),
                            ft.Container(ft.Text(prod.get("categoria_nome", ""), size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY), width=Sizes.TABLE_COL_LARGE),
                            ft.Container(
                                content=ft.ElevatedButton(
                                    content=ft.Row([
                                        ft.Icon(ft.icons.RESTORE, size=14, color=Colors.TEXT_WHITE),
                                        ft.Text("Reativar", size=12, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
                                    ], spacing=4, tight=True),
                                    bgcolor=Colors.BRAND_GREEN,
                                    height=34,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6)),
                                    on_click=_reativar,
                                ),
                                width=Sizes.TABLE_COL_LARGE,
                                alignment=ft.alignment.center,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    padding=ft.padding.symmetric(horizontal=Sizes.SPACING_LARGE, vertical=12),
                    border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
                    bgcolor="#FFF8F6",
                )
                items_list.controls.append(linha)
        page.update()

    def toggle_inativos(e):
        modo_inativos["ativo"] = not modo_inativos["ativo"]
        if modo_inativos["ativo"]:
            # Entra no modo inativos
            btn_inativos.content = ft.Row([
                ft.Icon(ft.icons.ARROW_BACK, size=18, color=Colors.TEXT_WHITE),
                ft.Text("Ver Ativos", size=13, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
            ], spacing=6, tight=True)
            btn_inativos.bgcolor = Colors.TEXT_GRAY
            btn_inativos.style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE),
            )
            # Troca header para modo inativo
            table_header.content.controls[-1] = ft.Container(
                ft.Text("Ação", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK),
                width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center,
            )
            carregar_inativos_na_tabela()
        else:
            # Volta ao modo ativos
            btn_inativos.content = ft.Row([
                ft.Icon(ft.icons.INVENTORY_2_OUTLINED, size=18, color=Colors.TEXT_WHITE),
                ft.Text("Inativos", size=13, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
            ], spacing=6, tight=True)
            btn_inativos.bgcolor = Colors.TEXT_GRAY
            btn_inativos.style = ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE),
            )
            carregar_produtos()
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
        
        ja_salvando = {"valor": False}  # flag anti-duplo-clique/duplo-submit

        def salvar_produto(e):
            # Evita cadastro duplo
            if ja_salvando["valor"]:
                return
            # Desabilita botão imediatamente para evitar duplo clique
            btn_salvar_prod.disabled = True
            btn_salvar_prod.text = "Salvando..."
            page.update()
            # Validação campo a campo com destaque visual
            campos_ok = True

            if not input_cod_barras.value or not input_cod_barras.value.strip():
                input_cod_barras.border_color = Colors.BRAND_RED
                input_cod_barras.error_text = "Obrigatório"
                campos_ok = False
            else:
                input_cod_barras.border_color = Colors.BORDER_GRAY
                input_cod_barras.error_text = None

            if not input_descricao.value or not input_descricao.value.strip():
                input_descricao.border_color = Colors.BRAND_RED
                input_descricao.error_text = "Obrigatório"
                campos_ok = False
            else:
                input_descricao.border_color = Colors.BORDER_GRAY
                input_descricao.error_text = None

            if not dropdown_tipo.value:
                dropdown_tipo.border_color = Colors.BRAND_RED
                campos_ok = False
            else:
                dropdown_tipo.border_color = Colors.BORDER_GRAY

            try:
                qtd_val = int(input_quantidade.value or "")
                input_quantidade.border_color = Colors.BORDER_GRAY
                input_quantidade.error_text = None
            except ValueError:
                input_quantidade.border_color = Colors.BRAND_RED
                input_quantidade.error_text = "Número inválido"
                campos_ok = False

            try:
                pc_val = float(input_preco_compra.value.replace(",", ".") or "")
                input_preco_compra.border_color = Colors.BORDER_GRAY
                input_preco_compra.error_text = None
            except ValueError:
                input_preco_compra.border_color = Colors.BRAND_RED
                input_preco_compra.error_text = "Valor inválido"
                campos_ok = False

            try:
                pv_val = float(input_preco_venda.value.replace(",", ".") or "")
                input_preco_venda.border_color = Colors.BORDER_GRAY
                input_preco_venda.error_text = None
            except ValueError:
                input_preco_venda.border_color = Colors.BRAND_RED
                input_preco_venda.error_text = "Valor inválido"
                campos_ok = False

            if not campos_ok:
                btn_salvar_prod.disabled = False
                btn_salvar_prod.text = "Salvar"
                page.snack_bar = ft.SnackBar(content=ft.Text("Preencha todos os campos obrigatórios!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()
                return

            # Verifica código de barras duplicado (ativos e inativos)
            cod = input_cod_barras.value.strip()
            todos_ativos = ProdutosAPI.listar_produtos() or []

            # Busca em ativos
            duplicado_ativo  = next((p for p in todos_ativos if p.get("codigo_barra", "").strip() == cod), None)
            # Busca em inativos via cache (populado quando toggle de inativos é acionado)
            duplicado_inativo = next((p for p in cache_inativos["lista"] if p.get("codigo_barra", "").strip() == cod), None)

            if duplicado_ativo:
                input_cod_barras.border_color = Colors.BRAND_ORANGE
                input_cod_barras.error_text   = f"Já em uso por: {duplicado_ativo.get('nome', 'outro produto')}"
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"⚠ Código de barras já cadastrado no produto '{duplicado_ativo.get('nome')}'!"),
                    bgcolor=Colors.BRAND_ORANGE,
                )
                page.snack_bar.open = True
                btn_salvar_prod.disabled = False
                btn_salvar_prod.text = "Salvar"
                page.update()
                return
            elif duplicado_inativo:
                input_cod_barras.border_color = Colors.BRAND_RED
                input_cod_barras.error_text   = f"Inativo: {duplicado_inativo.get('nome', 'produto inativo')}"
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"⚠ Este código pertence ao produto INATIVO '{duplicado_inativo.get('nome')}'. Reative-o em vez de cadastrar um novo!"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                btn_salvar_prod.disabled = False
                btn_salvar_prod.text = "Salvar"
                page.update()
                return

            ja_salvando["valor"] = True
            try:
                # O backend (service.create) já registra CADASTRO_INICIAL
                # automaticamente se estoque > 0 — não precisa registrar no front
                resultado = ProdutosAPI.criar_produto({
                    "nome": input_descricao.value.strip(),
                    "preco_venda": pv_val,
                    "preco_compra": pc_val,
                    "categoria_id": int(dropdown_tipo.value),
                    "codigo_barra": cod,
                    "estoque": qtd_val,
                })

                if resultado:
                    modal.open = False
                    page.snack_bar = ft.SnackBar(content=ft.Text(f"Produto '{input_descricao.value.strip()}' incluído com sucesso!"), bgcolor=Colors.BRAND_GREEN)
                    page.snack_bar.open = True
                    buscar_produtos(None)
                else:
                    ja_salvando["valor"] = False
                    btn_salvar_prod.disabled = False
                    btn_salvar_prod.text = "Salvar"
                    page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao incluir produto!"), bgcolor=Colors.BRAND_RED)
                    page.snack_bar.open = True
            except Exception as err:
                ja_salvando["valor"] = False
                btn_salvar_prod.disabled = False
                btn_salvar_prod.text = "Salvar"
                print(f"Erro inesperado ao salvar produto: {err}")
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro inesperado: {err}"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
            page.update()
        
        def fechar_modal(e):
            modal.open = False
            page.update()

        btn_salvar_prod = ft.ElevatedButton(
            "Salvar",
            bgcolor=Colors.BRAND_GREEN,
            color=Colors.TEXT_WHITE,
            on_click=salvar_produto,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Incluir Produto", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(controls=[input_cod_barras, input_descricao, dropdown_tipo, input_quantidade, input_preco_compra, input_preco_venda], spacing=Sizes.SPACING_MEDIUM, scroll=ft.ScrollMode.AUTO),
                width=400, height=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                btn_salvar_prod,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.clear()
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
        page.overlay.clear()
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
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Row(controls=[
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, size=22, color=Colors.BRAND_RED),
                ft.Text("Excluir Produto", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
            ], spacing=6),
            content=ft.Container(
                width=360,
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        ft.Text("Tem certeza que deseja excluir este produto?", size=Sizes.FONT_SMALL, text_align=ft.TextAlign.CENTER, color=Colors.TEXT_GRAY),
                        ft.Divider(height=6),
                        ft.Text(f"ID: {produto_selecionado.get('id', '')}", size=Sizes.FONT_SMALL),
                        ft.Text(f"Cód. Barras: {produto_selecionado.get('codigo_barra', '')}", size=Sizes.FONT_SMALL),
                        ft.Text(f"Descrição: {produto_selecionado.get('nome', '')}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Categoria: {produto_selecionado.get('categoria_nome', '')}", size=Sizes.FONT_SMALL),
                        ft.Divider(height=6),
                        ft.Text("Esta ação não pode ser desfeita!", size=Sizes.FONT_SMALL, color=Colors.BRAND_RED, italic=True),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_exclusao),
                ft.ElevatedButton(
                    "Sim, Excluir",
                    bgcolor=Colors.BRAND_RED,
                    color=Colors.TEXT_WHITE,
                    on_click=confirmar_exclusao,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    # ============================================================================
    # MODAL MOVIMENTAR ESTOQUE
    # ============================================================================

    def modal_movimentar_estoque(e):
        nonlocal produto_selecionado

        if not produto_selecionado:
            page.snack_bar = ft.SnackBar(content=ft.Text("Selecione um produto na tabela primeiro!"), bgcolor=Colors.BRAND_ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        estoque_atual = int(produto_selecionado.get("estoque", 0))
        pid           = produto_selecionado.get("id")
        nome_produto  = produto_selecionado.get("nome", "")

        tipo_selecionado = {"valor": "ENTRADA"}

        MOTIVOS_ENTRADA = ["COMPRA", "DEVOLUCAO", "CADASTRO_INICIAL", "AJUSTE"]
        MOTIVOS_SAIDA   = ["VENDA", "PERDA", "AJUSTE"]

        # ── Controles ─────────────────────────────────────────────────────────
        # Estoque atual em destaque
        estoque_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.INVENTORY_2, size=16, color=Colors.BRAND_BLUE),
                    ft.Text(
                        f"{estoque_atual} unidades em estoque",
                        size=Sizes.FONT_SMALL,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.BRAND_BLUE,
                    ),
                ],
                spacing=6,
                tight=True,
            ),
            bgcolor="#E3F2FD",
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=20,
            border=ft.border.all(1, "#90CAF9"),
        )

        dropdown_motivo = ft.Dropdown(
            label="Motivo",
            width=440,
            border_color=Colors.BORDER_GRAY,
            options=[ft.dropdown.Option(key=m, text=m.replace("_", " ").title()) for m in MOTIVOS_ENTRADA],
            value=MOTIVOS_ENTRADA[0],
        )

        input_quantidade = ft.TextField(
            value="1",
            width=90,
            height=52,
            text_align=ft.TextAlign.CENTER,
            border_color=Colors.BRAND_BLUE,
            focused_border_color=Colors.BRAND_BLUE,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=22,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=10,
        )

        btn_entrada = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.icons.ARROW_UPWARD, color=Colors.TEXT_WHITE, size=16),
                ft.Text("Entrada", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
            ], spacing=6, tight=True),
            bgcolor=Colors.BRAND_GREEN,
            width=200,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        btn_saida = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.icons.ARROW_DOWNWARD, color=Colors.TEXT_BLACK, size=16),
                ft.Text("Saída", color=Colors.TEXT_BLACK, weight=ft.FontWeight.BOLD),
            ], spacing=6, tight=True),
            bgcolor="#F0F0F0",
            width=200,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        def set_tipo(tipo):
            tipo_selecionado["valor"] = tipo
            if tipo == "ENTRADA":
                btn_entrada.bgcolor = Colors.BRAND_GREEN
                btn_entrada.content.controls[0].color = Colors.TEXT_WHITE
                btn_entrada.content.controls[1].color = Colors.TEXT_WHITE
                btn_saida.bgcolor   = "#F0F0F0"
                btn_saida.content.controls[0].color   = Colors.TEXT_BLACK
                btn_saida.content.controls[1].color   = Colors.TEXT_BLACK
                dropdown_motivo.options = [ft.dropdown.Option(key=m, text=m.replace("_", " ").title()) for m in MOTIVOS_ENTRADA]
                dropdown_motivo.value   = MOTIVOS_ENTRADA[0]
            else:
                btn_saida.bgcolor   = Colors.BRAND_RED
                btn_saida.content.controls[0].color   = Colors.TEXT_WHITE
                btn_saida.content.controls[1].color   = Colors.TEXT_WHITE
                btn_entrada.bgcolor = "#F0F0F0"
                btn_entrada.content.controls[0].color = Colors.TEXT_BLACK
                btn_entrada.content.controls[1].color = Colors.TEXT_BLACK
                dropdown_motivo.options = [ft.dropdown.Option(key=m, text=m.replace("_", " ").title()) for m in MOTIVOS_SAIDA]
                dropdown_motivo.value   = MOTIVOS_SAIDA[0]
            page.update()

        btn_entrada.on_click = lambda _: set_tipo("ENTRADA")
        btn_saida.on_click   = lambda _: set_tipo("SAIDA")

        def dec_qtd(e):
            try:
                v = int(input_quantidade.value or 1)
                if v > 1:
                    input_quantidade.value = str(v - 1)
                    page.update()
            except Exception:
                input_quantidade.value = "1"
                page.update()

        def inc_qtd(e):
            try:
                v = int(input_quantidade.value or 0)
                input_quantidade.value = str(v + 1)
                page.update()
            except Exception:
                input_quantidade.value = "1"
                page.update()

        btn_dec = ft.Container(
            content=ft.Text("−", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
            width=52, height=52,
            bgcolor=Colors.BRAND_RED,
            border_radius=10,
            alignment=ft.alignment.center,
            ink=True,
            on_click=dec_qtd,
            shadow=ft.BoxShadow(blur_radius=4, color="#33000000", offset=ft.Offset(0, 2)),
        )

        btn_inc = ft.Container(
            content=ft.Text("+", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
            width=52, height=52,
            bgcolor=Colors.BRAND_GREEN,
            border_radius=10,
            alignment=ft.alignment.center,
            ink=True,
            on_click=inc_qtd,
            shadow=ft.BoxShadow(blur_radius=4, color="#33000000", offset=ft.Offset(0, 2)),
        )

        def confirmar(e):
            try:
                qtd = int(input_quantidade.value or 0)
                if qtd <= 0:
                    raise ValueError
            except Exception:
                page.snack_bar = ft.SnackBar(content=ft.Text("Informe uma quantidade válida!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()
                return

            tipo   = tipo_selecionado["valor"]
            motivo = dropdown_motivo.value or "AJUSTE"

            nova_qtd = estoque_atual + qtd if tipo == "ENTRADA" else estoque_atual - qtd
            if nova_qtd < 0:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Estoque insuficiente! Atual: {estoque_atual}"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()
                return

            btn_confirmar.disabled = True
            btn_confirmar.text = "Salvando..."
            page.update()

            # Registra movimentação (não bloqueia se falhar)
            # O backend atualiza o estoque automaticamente ao registrar movimentação
            # NÃO chamar atualizar_produto — evita dupla contagem
            resultado_mov = MovimentacaoAPI.registrar_movimentacao({
                "tipo":       tipo,
                "motivo":     motivo,
                "quantidade": qtd,
                "produto_id": pid,
                "venda_id":   None,
            })

            if resultado_mov:
                modal.open = False
                sinal = f"+{qtd}" if tipo == "ENTRADA" else f"-{qtd}"
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Estoque atualizado! ({sinal} unidades)"),
                    bgcolor=Colors.BRAND_GREEN,
                )
                page.snack_bar.open = True
                buscar_produtos(None)
            else:
                btn_confirmar.disabled = False
                btn_confirmar.text = "Confirmar"
                page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao atualizar estoque!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()

        def fechar(e):
            modal.open = False
            page.update()

        btn_confirmar = ft.ElevatedButton(
            "Confirmar",
            bgcolor=Colors.BRAND_GREEN,
            color=Colors.TEXT_WHITE,
            width=180, height=48,
            on_click=confirmar,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        btn_cancelar = ft.OutlinedButton(
            "Cancelar",
            width=180, height=48,
            on_click=fechar,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Container(
                content=ft.Row(controls=[
                    ft.Icon(ft.icons.SWAP_VERT, color=Colors.TEXT_WHITE, size=22),
                    ft.Text("Movimentação de Estoque", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_GREEN,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            shape=ft.RoundedRectangleBorder(radius=10),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    tight=True,
                    spacing=16,
                    controls=[
                        ft.Container(height=2),
                        # Produto + badge estoque
                        ft.Column(spacing=6, controls=[
                            ft.Text("PRODUTO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Text(nome_produto, size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, expand=True),
                                        estoque_badge,
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                bgcolor="#F5F5F5",
                                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                                border_radius=8,
                                border=ft.border.all(1, Colors.BORDER_LIGHT),
                                width=480,
                            ),
                        ]),
                        # Tipo
                        ft.Column(spacing=6, controls=[
                            ft.Text("TIPO DE MOVIMENTAÇÃO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                            ft.Row(controls=[btn_entrada, btn_saida], spacing=12),
                        ]),
                        # Motivo
                        ft.Column(spacing=4, controls=[
                            ft.Text("MOTIVO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                            dropdown_motivo,
                        ]),
                        # Quantidade
                        ft.Column(spacing=8, controls=[
                            ft.Text("QUANTIDADE", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                            ft.Row(
                                controls=[btn_dec, input_quantidade, btn_inc],
                                spacing=10,
                                tight=True,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ]),
                    ],
                ),
            ),
            actions=[btn_cancelar, btn_confirmar],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.clear()
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
    
    btn_inativos = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.icons.INVENTORY_2_OUTLINED, size=18, color=Colors.TEXT_WHITE),
            ft.Text("Inativos", size=13, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
        ], spacing=6, tight=True),
        bgcolor=Colors.TEXT_GRAY,
        height=Sizes.BUTTON_HEIGHT,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
        on_click=toggle_inativos,
    )

    top_section = ft.Container(
        content=ft.Row(
            controls=[pesquisa_input, btn_localizar, filtro_dropdown, btn_inativos],
            spacing=Sizes.SPACING_LARGE,
            alignment=ft.MainAxisAlignment.START,
        ),
        padding=Sizes.SPACING_LARGE,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
    )

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
    btn_movimentar = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.icons.SWAP_VERT, size=20, color=Colors.TEXT_WHITE),
                ft.Text("Movimentar Estoque", size=14, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD, no_wrap=True),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
            tight=True,
        ),
        bgcolor=Colors.BRAND_BLUE,
        width=Sizes.BUTTON_WIDTH,
        height=Sizes.BUTTON_HEIGHT,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
        on_click=modal_movimentar_estoque,
    )
    btn_sair       = Styles.button_danger("Menu Principal",   ft.icons.HOME,      lambda _: page.go("/"))

    sidebar = Styles.sidebar([
        btn_incluir,
        btn_alterar,
        btn_excluir,
        btn_movimentar,
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
    carregar_inativos_na_tabela()  # popula cache de inativos para validação de cod. barras
    if not modo_inativos["ativo"]:
        carregar_produtos()  # volta para ativos após popular o cache

    return ft.Row(controls=[main_content, sidebar], spacing=0, expand=True)