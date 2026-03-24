import flet as ft
from datetime import datetime, timedelta
import time
import threading
from app.views.styles.theme import Colors, Sizes, Styles, VendasCols
from app.api.produtos_api import ProdutosAPI
from app.api.turno_api import TurnoAPI
from app.api.categorias_api import CategoriasAPI
from app.api.vendas_api import VendasAPI
from app.api.movimentacao_api import MovimentacaoAPI
from app.utils.printer import imprimir_cupom_venda
from app.api.auth_api import get_username

def VendasView(page: ft.Page):
    """Tela de registro de vendas"""
    
    # ============================================================================
    # VARIÁVEIS DE CONTROLE
    # ============================================================================
    
    venda_id_atual  = None
    turno_id_atual  = None
    valor_total = 0.0
    desconto_aplicado = 0.0
    acrescimo_aplicado = 0.0
    valor_recebido = 0.0
    numero_item = 0
    itens_venda = []  # Lista de itens na venda
    item_selecionado = None
    linha_selecionada_tabela = None

    # UTC-3 Fortaleza
    _UTC_OFFSET = timedelta(hours=-3)

    def utc_to_local(data_str):
        """Converte string UTC para horário de Fortaleza (UTC-3)"""
        try:
            dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            return dt + _UTC_OFFSET
        except Exception:
            return None
    
    # ============================================================================
    # FUNÇÕES AUXILIARES
    # ============================================================================
    
    def get_data_atual():
        return datetime.now().strftime("%d/%m/%Y")
    
    def get_hora_atual():
        return datetime.now().strftime("%H:%M:%S")
    
    def calcular_valor_final():
        """Calcula o valor final com desconto e acréscimo"""
        return valor_total - desconto_aplicado + acrescimo_aplicado
    
    def calcular_troco():
        """Calcula o troco"""
        return valor_recebido - calcular_valor_final()
    
    def recalcular_total_venda():
        """Recalcula o total da venda baseado nos itens"""
        nonlocal valor_total
        valor_total = sum(item.get("subtotal", 0) for item in itens_venda)
        atualizar_totais()
    
    def atualizar_totais():
        """Atualiza os campos de totais"""
        txt_subtotal.value = f"R$ {valor_total:.2f}"
        txt_desconto_valor.value = f"- R$ {desconto_aplicado:.2f}"
        txt_acrescimo_valor.value = f"+ R$ {acrescimo_aplicado:.2f}"
        txt_total_final.value = f"R$ {calcular_valor_final():.2f}"
        
        troco = calcular_troco()
        if troco >= 0:
            txt_troco.value = f"R$ {troco:.2f}"
            txt_troco.color = Colors.BRAND_GREEN
        else:
            txt_troco.value = f"R$ {abs(troco):.2f} (Falta)"
            txt_troco.color = Colors.BRAND_RED
        
        page.update()
    
    def aplicar_desconto(e):
        try:
            nonlocal desconto_aplicado
            valor = e.control.value.replace(",", ".")
            desconto_aplicado = float(valor) if valor else 0.0
            atualizar_totais()
        except:
            pass
    
    def aplicar_acrescimo(e):
        try:
            nonlocal acrescimo_aplicado
            valor = e.control.value.replace(",", ".")
            acrescimo_aplicado = float(valor) if valor else 0.0
            atualizar_totais()
        except:
            pass
    
    def aplicar_valor_recebido(e):
        try:
            nonlocal valor_recebido
            valor = e.control.value.replace(",", ".")
            valor_recebido = float(valor) if valor else 0.0
            atualizar_totais()
        except:
            pass
    
    # ============================================================================
    # FUNÇÕES DE GERENCIAMENTO DE ITENS
    # ============================================================================

    def buscar_e_adicionar_produto(e):
        """Busca produto por código/ID e adiciona automaticamente"""
        codigo = produto_input.value.strip()
        
        if not codigo:
            return
        
        produtos = ProdutosAPI.listar_produtos()
        produto_encontrado = None
        
        for produto in produtos:
            if str(produto.get("id")) == codigo or produto.get("codigo_barra") == codigo:
                produto_encontrado = produto
                break
        
        if produto_encontrado:
            adicionar_item_tabela(produto_encontrado)
            produto_input.value = ""
            page.update()
        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Produto '{codigo}' não encontrado!"),
                bgcolor=Colors.BRAND_RED,
            )
            page.snack_bar.open = True
            page.update()

    def adicionar_item_tabela(produto):
        """Adiciona um produto como item na tabela de vendas"""
        nonlocal numero_item, itens_venda

        numero_item += 1

        item = {
            "numero": numero_item,
            "id": produto.get("id"),
            "produto_id": produto.get("id"),
            "descricao": produto.get("nome", ""),
            "quantidade": 1,
            "preco_unitario": float(produto.get("preco_venda", 0)),
            "subtotal": float(produto.get("preco_venda", 0)),
        }

        itens_venda.append(item)
        atualizar_tabela_itens()
        recalcular_total_venda()
    
    def selecionar_linha_item(item_data, linha_container):
        """Destaca visualmente o item selecionado na tabela"""
        nonlocal item_selecionado, linha_selecionada_tabela

        # Remove highlight anterior
        if linha_selecionada_tabela:
            linha_selecionada_tabela.content.bgcolor = Colors.BG_WHITE
            linha_selecionada_tabela.content.border = ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT))

        item_selecionado = item_data
        linha_selecionada_tabela = linha_container

        # Aplica highlight azul claro
        linha_container.content.bgcolor = "#E3F2FD"
        linha_container.content.border = ft.border.all(2, Colors.BRAND_BLUE)
        page.update()

    def criar_linha_item(item):
        """Cria uma linha visual para um item na tabela"""
        
        def mostrar_menu_contexto(e):
            
            def editar_item(e):
                modal_editar_item(item)
                page.close_bottom_sheet()
            
            def remover_item(e):
                confirmar_remocao_item(item)
                page.close_bottom_sheet()
            
            menu = ft.AlertDialog(
                modal=False,
                shape=ft.RoundedRectangleBorder(radius=12),
                title=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.RECEIPT_LONG, size=16, color=Colors.TEXT_WHITE),
                        ft.Text(
                            item["descricao"],
                            size=Sizes.FONT_SMALL,
                            color=Colors.TEXT_WHITE,
                            weight=ft.FontWeight.BOLD,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                        ),
                    ], spacing=8),
                    bgcolor=Colors.BRAND_RED,
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                    margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
                ),
                content=ft.Container(
                    width=280,
                    padding=ft.padding.only(top=12, bottom=4),
                    content=ft.Column(
                        tight=True,
                        spacing=6,
                        controls=[
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.icons.EDIT_OUTLINED, size=18, color=Colors.BRAND_BLUE),
                                        width=36, height=36,
                                        bgcolor="#E3F2FD",
                                        border_radius=8,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Text("Editar Item", size=Sizes.FONT_MEDIUM, color=Colors.BRAND_BLUE, weight=ft.FontWeight.BOLD),
                                ], spacing=12),
                                padding=ft.padding.symmetric(horizontal=8, vertical=10),
                                border_radius=8,
                                border=ft.border.all(1, "#E3F2FD"),
                                bgcolor=Colors.BG_WHITE,
                                ink=True,
                                on_click=lambda e: (setattr(menu, "open", False), page.update(), editar_item(e)),
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(ft.icons.DELETE_OUTLINE, size=18, color=Colors.BRAND_RED),
                                        width=36, height=36,
                                        bgcolor="#FFEBEE",
                                        border_radius=8,
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Text("Remover Item", size=Sizes.FONT_MEDIUM, color=Colors.BRAND_RED, weight=ft.FontWeight.BOLD),
                                ], spacing=12),
                                padding=ft.padding.symmetric(horizontal=8, vertical=10),
                                border_radius=8,
                                border=ft.border.all(1, "#FFEBEE"),
                                bgcolor=Colors.BG_WHITE,
                                ink=True,
                                on_click=lambda e: (setattr(menu, "open", False), page.update(), remover_item(e)),
                            ),
                        ],
                    ),
                ),
                actions=[],
            )
            page.overlay.append(menu)
            menu.open = True
            page.update()
        
        row_content = ft.Row(
            controls=[
                ft.Container(
                    ft.Text(str(item["numero"]), size=Sizes.FONT_SMALL),
                    width=VendasCols.NUMERO,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Text(str(item["id"]), size=Sizes.FONT_SMALL),
                    width=VendasCols.ID,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Text(item["descricao"], size=Sizes.FONT_SMALL),
                    expand=True,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Text(str(item["quantidade"]), size=Sizes.FONT_SMALL),
                    width=VendasCols.QUANTIDADE,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Text(f"R$ {item['preco_unitario']:.2f}", size=Sizes.FONT_SMALL),
                    width=VendasCols.PRECO_UNI,
                    alignment=ft.alignment.center
                ),
                ft.Container(
                    ft.Text(f"R$ {item['subtotal']:.2f}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN),
                    width=VendasCols.TOTAL,
                    alignment=ft.alignment.center
                ),
            ],
            spacing=0,
        )

        linha = ft.GestureDetector(
            content=ft.Container(
                content=row_content,
                border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
                padding=10,
                bgcolor=Colors.BG_WHITE,
            ),
            on_tap=lambda e, i=item: selecionar_linha_item(i, e.control),
            on_long_press_start=mostrar_menu_contexto,
            on_secondary_tap_up=mostrar_menu_contexto,
        )
        
        return linha
    
    def atualizar_tabela_itens():
        """Atualiza a tabela visual de itens"""
        nonlocal item_selecionado, linha_selecionada_tabela
        items_list.controls.clear()
        item_selecionado = None
        linha_selecionada_tabela = None
        for item in itens_venda:
            items_list.controls.append(criar_linha_item(item))
        page.update()
    
    def modal_editar_item(item):
        """Modal para editar quantidade e preço de um item"""
        
        input_quantidade = ft.TextField(
            label="Quantidade",
            value=str(item["quantidade"]),
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=Colors.BORDER_GRAY,
        )
        
        input_preco = ft.TextField(
            label="Preço Unitário (R$)",
            value=str(item["preco_unitario"]),
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=Colors.BORDER_GRAY,
            prefix_text="R$ ",
        )
        
        txt_subtotal_modal = ft.Text(
            f"Subtotal: R$ {item['subtotal']:.2f}",
            size=Sizes.FONT_LARGE,
            weight=ft.FontWeight.BOLD,
            color=Colors.BRAND_GREEN,
        )
        
        def atualizar_subtotal(e):
            try:
                qtd = float(input_quantidade.value) if input_quantidade.value else 0
                preco = float(input_preco.value.replace(",", ".")) if input_preco.value else 0
                txt_subtotal_modal.value = f"Subtotal: R$ {qtd * preco:.2f}"
                page.update()
            except:
                pass
        
        input_quantidade.on_change = atualizar_subtotal
        input_preco.on_change = atualizar_subtotal
        
        def salvar_edicao(e):
            try:
                qtd = int(input_quantidade.value)
                preco = float(input_preco.value.replace(",", "."))
                
                if qtd <= 0 or preco <= 0:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Quantidade e preço devem ser maiores que zero!"),
                        bgcolor=Colors.BRAND_RED,
                    )
                    page.snack_bar.open = True
                    page.update()
                    return
                
                item["quantidade"] = qtd
                item["preco_unitario"] = preco
                item["subtotal"] = qtd * preco
                
                if venda_id_atual and item.get("item_id"):
                    VendasAPI.atualizar_item(venda_id_atual, item["item_id"], {
                        "quantidade": qtd,
                        "preco_unitario": preco,
                        "subtotal": item["subtotal"],
                    })
                
                atualizar_tabela_itens()
                recalcular_total_venda()
                
                modal.open = False
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Item atualizado com sucesso!"),
                    bgcolor=Colors.BRAND_GREEN,
                )
                page.snack_bar.open = True
                page.update()
                
            except Exception as ex:
                print(f"Erro ao salvar: {ex}")
        
        def fechar_modal(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Row(controls=[
                ft.Icon(ft.icons.EDIT_OUTLINED, size=22, color=Colors.BRAND_BLUE),
                ft.Text("Editar Item", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
            ], spacing=8),
            content=ft.Container(
                width=340,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        ft.Container(
                            content=ft.Text(item['descricao'], size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD),
                            bgcolor="#F5F5F5",
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            border_radius=8,
                            border=ft.border.all(1, Colors.BORDER_LIGHT),
                        ),
                        ft.Divider(height=4),
                        input_quantidade,
                        input_preco,
                        ft.Divider(height=4),
                        txt_subtotal_modal,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                ft.ElevatedButton(
                    "Salvar",
                    bgcolor=Colors.BRAND_GREEN,
                    color=Colors.TEXT_WHITE,
                    on_click=salvar_edicao,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    def confirmar_remocao_item(item):
        """Modal de confirmação para remover item"""
        
        def remover(e):
            nonlocal itens_venda
            itens_venda = [i for i in itens_venda if i["numero"] != item["numero"]]
            
            if venda_id_atual and item.get("item_id"):
                VendasAPI.deletar_item(venda_id_atual, item["item_id"])
            
            atualizar_tabela_itens()
            recalcular_total_venda()
            
            modal.open = False
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Item removido da venda!"),
                bgcolor=Colors.BRAND_GREEN,
            )
            page.snack_bar.open = True
            page.update()
        
        def cancelar(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Row(controls=[
                ft.Icon(ft.icons.DELETE_OUTLINE, size=22, color=Colors.BRAND_RED),
                ft.Text("Remover Item", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
            ], spacing=8),
            content=ft.Container(
                width=320,
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.Text(
                            "Deseja remover este item da venda?",
                            size=Sizes.FONT_SMALL,
                            color=Colors.TEXT_GRAY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(height=6),
                        ft.Container(
                            content=ft.Column(
                                tight=True,
                                spacing=4,
                                controls=[
                                    ft.Text(item['descricao'], size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Quantidade: {item['quantidade']}", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY),
                                    ft.Text(f"Valor: R$ {item['subtotal']:.2f}", size=Sizes.FONT_SMALL, color=Colors.BRAND_RED, weight=ft.FontWeight.BOLD),
                                ],
                            ),
                            bgcolor="#FFF8F8",
                            border=ft.border.all(1, "#FFCDD2"),
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Sim, Remover",
                    bgcolor=Colors.BRAND_RED,
                    color=Colors.TEXT_WHITE,
                    on_click=remover,
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
    # MODAL DE BUSCA DE PRODUTOS
    # ============================================================================
    
    def modal_buscar_produto(e):
        """Modal para buscar produtos por nome"""
        
        produtos_filtrados = []
        produto_selecionado_modal = None
        linha_selecionada_modal = None
        
        pesquisa_modal = ft.TextField(
            label="Pesquisar produto",
            width=350,
            border_color=Colors.BORDER_GRAY,
            height=50,
        )
        
        filtro_modal = ft.Dropdown(
            label="Categoria",
            width=250,
            height=50,
            border_color=Colors.BORDER_GRAY,
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
        )
        
        lista_produtos_modal = ft.Column(
            controls=[],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )
        
        def selecionar_produto_modal(produto_data, linha_container):
            nonlocal produto_selecionado_modal, linha_selecionada_modal
            
            if linha_selecionada_modal:
                linha_selecionada_modal.bgcolor = Colors.BG_WHITE
                linha_selecionada_modal.border = ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT))
            
            produto_selecionado_modal = produto_data
            linha_selecionada_modal = linha_container
            
            linha_container.bgcolor = "#E3F2FD"
            linha_container.border = ft.border.all(2, Colors.BRAND_BLUE)
            
            page.update()
        
        def criar_linha_produto_modal(produto):
            linha = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            ft.Text(str(produto.get("id", "")), size=Sizes.FONT_SMALL),
                            width=Sizes.TABLE_COL_SMALL,
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            ft.Text(produto.get("codigo_barra", ""), size=Sizes.FONT_SMALL),
                            width=Sizes.TABLE_COL_LARGE,
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            ft.Text(produto.get("nome", ""), size=Sizes.FONT_SMALL),
                            expand=True,
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            ft.Text(produto.get("categoria_nome", ""), size=Sizes.FONT_SMALL),
                            width=Sizes.TABLE_COL_XLARGE,
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            ft.Text(str(produto.get("estoque", 0)), size=Sizes.FONT_SMALL,
                                color=Colors.BRAND_GREEN if produto.get("estoque", 0) > 0 else Colors.BRAND_RED,
                                weight=ft.FontWeight.BOLD),
                            width=Sizes.TABLE_COL_SMALL,
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            ft.Text(f"R$ {float(produto.get('preco_venda', 0)):.2f}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN),
                            width=Sizes.TABLE_COL_MEDIUM,
                            alignment=ft.alignment.center
                        ),
                    ],
                    spacing=0,
                ),
                border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
                padding=10,
                bgcolor=Colors.BG_WHITE,
                ink=True,
            )
            
            linha.on_click = lambda _, p=produto, l=linha: selecionar_produto_modal(p, l)
            return linha
        
        def carregar_produtos_modal(filtro_texto="", filtro_categoria="Todos"):
            nonlocal produtos_filtrados
            
            produtos = ProdutosAPI.listar_produtos()
            lista_produtos_modal.controls.clear()
            produtos_filtrados = []
            
            if produtos:
                filtrados_temp = []
                for produto in produtos:
                    if not produto.get("ativo", True):
                        continue
                    
                    if filtro_texto:
                        filtro_lower = filtro_texto.lower()
                        nome = produto.get("nome", "").lower()
                        cod_barras = produto.get("codigo_barra", "").lower()
                        
                        if filtro_lower not in nome and filtro_lower not in cod_barras:
                            continue
                    
                    if filtro_categoria != "Todos":
                        if produto.get("categoria_nome", "") != filtro_categoria:
                            continue
                    
                    filtrados_temp.append(produto)

                # Ordena por ID crescente
                filtrados_temp.sort(key=lambda p: p.get("id", 0))

                for produto in filtrados_temp:
                    produtos_filtrados.append(produto)
                    lista_produtos_modal.controls.append(criar_linha_produto_modal(produto))
            
            if len(lista_produtos_modal.controls) == 0:
                lista_produtos_modal.controls.append(
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
        
        def buscar_produtos_modal(e):
            carregar_produtos_modal(
                filtro_texto=pesquisa_modal.value.strip(),
                filtro_categoria=filtro_modal.value,
            )
        
        def adicionar_produto_venda(e):
            nonlocal produto_selecionado_modal
            
            if not produto_selecionado_modal:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Selecione um produto!"),
                    bgcolor=Colors.BRAND_ORANGE,
                )
                page.snack_bar.open = True
                page.update()
                return
            
            produto_input.value = str(produto_selecionado_modal.get("id", ""))
            modal.open = False
            buscar_e_adicionar_produto(None)
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Produto '{produto_selecionado_modal.get('nome', '')}' adicionado!"),
                bgcolor=Colors.BRAND_GREEN,
            )
            page.snack_bar.open = True
            page.update()
        
        def fechar_modal(e):
            modal.open = False
            page.update()
        
        header_modal = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Text("ID", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Cód. Barras", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Descrição", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK), expand=True, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Categoria", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK), width=Sizes.TABLE_COL_XLARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Estoque", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Preço", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                ],
                spacing=0,
            ),
            bgcolor=Colors.BG_PINK_LIGHT,
            padding=10,
        )
        
        filtro_modal.on_change = buscar_produtos_modal
        pesquisa_modal.on_submit = buscar_produtos_modal
        
        btn_buscar_modal = ft.ElevatedButton(
            "Buscar",
            icon=ft.icons.SEARCH,
            on_click=buscar_produtos_modal,
            bgcolor=Colors.BRAND_BLUE,
            color=Colors.TEXT_WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
        )
        
        search_section_modal = ft.Container(
            content=ft.Row(
                controls=[pesquisa_modal, btn_buscar_modal, filtro_modal],
                spacing=Sizes.SPACING_MEDIUM,
            ),
            padding=Sizes.SPACING_MEDIUM,
            border=ft.border.all(2, Colors.BORDER_BLACK),
            border_radius=Sizes.BORDER_RADIUS_SMALL,
            bgcolor=Colors.BG_WHITE,
        )
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Buscar Produto", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        search_section_modal,
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    header_modal,
                                    ft.Container(
                                        content=lista_produtos_modal,
                                        height=400,
                                        border=ft.border.all(1, Colors.BORDER_BLACK),
                                        bgcolor=Colors.BG_WHITE,
                                    ),
                                ],
                                spacing=0,
                            ),
                            margin=ft.margin.only(top=Sizes.SPACING_LARGE),
                        ),
                    ],
                    spacing=0,
                ),
                width=900,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                ft.ElevatedButton(
                    "Adicionar à Venda",
                    icon=ft.icons.ADD_SHOPPING_CART,
                    bgcolor=Colors.BRAND_GREEN,
                    color=Colors.TEXT_WHITE,
                    on_click=adicionar_produto_venda,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        carregar_produtos_modal()
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    # ============================================================================
    # FUNÇÃO DE CONCLUSÃO DE VENDA
    # ============================================================================

    def concluir_venda(e):
        """Abre modal de confirmação com itens listados e registra a venda na API"""

        if not itens_venda:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Adicione pelo menos um item antes de concluir!"),
                bgcolor=Colors.BRAND_ORANGE,
            )
            page.snack_bar.open = True
            page.update()
            return

        valor_final = calcular_valor_final()

        # ------------------------------------------------------------------ #
        # MODAL DE NOTA FISCAL
        # ------------------------------------------------------------------ #
        def modal_nota_fiscal(venda_id, itens, subtotal, desconto, acrescimo, total, pagamento, troco):

            def fechar_nota(e):
                nota.open = False
                page.update()

            def imprimir_nota(e):
                nota.open = False
                page.update()

                def _print():
                    data_fmt = datetime.now().strftime("%d/%m/%Y %H:%M")
                    sucesso, msg = imprimir_cupom_venda(
                        venda_id=venda_id,
                        data_fmt=data_fmt,
                        itens=itens,
                        subtotal=subtotal,
                        desconto=desconto,
                        acrescimo=acrescimo,
                        total=total,
                        pagamento=pagamento,
                        troco=troco,
                        valor_recebido=troco + total,
                        usuario=get_username() or "",
                    )
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(msg),
                        bgcolor=Colors.BRAND_GREEN if sucesso else Colors.BRAND_RED,
                    )
                    page.snack_bar.open = True
                    page.update()

                page.run_thread(_print)

            linhas_itens = []
            for item in itens:
                linhas_itens.append(
                    ft.Row(
                        controls=[
                            ft.Text(item["descricao"], size=11, expand=True),
                            ft.Text(f"{item['quantidade']}x", size=11, width=35, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"R$ {item['preco_unitario']:.2f}", size=11, width=80, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"R$ {item['subtotal']:.2f}", size=11, width=80, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
                        ],
                        spacing=4,
                    )
                )

            nota = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.RECEIPT, color=Colors.BRAND_GREEN, size=28),
                        ft.Text("Venda Concluída!", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
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
                                content=ft.Row(
                                    controls=[
                                        ft.Text("DESCRIÇÃO", size=10, weight=ft.FontWeight.BOLD, expand=True),
                                        ft.Text("QTD", size=10, weight=ft.FontWeight.BOLD, width=35, text_align=ft.TextAlign.RIGHT),
                                        ft.Text("UNIT.", size=10, weight=ft.FontWeight.BOLD, width=80, text_align=ft.TextAlign.RIGHT),
                                        ft.Text("TOTAL", size=10, weight=ft.FontWeight.BOLD, width=80, text_align=ft.TextAlign.RIGHT),
                                    ],
                                    spacing=4,
                                ),
                                bgcolor="#F5F5F5",
                                padding=ft.padding.symmetric(horizontal=4, vertical=6),
                            ),
                            ft.Divider(height=1, color=Colors.BORDER_LIGHT),
                            ft.Container(
                                content=ft.Column(controls=linhas_itens, spacing=6),
                                padding=ft.padding.symmetric(horizontal=4, vertical=8),
                            ),
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
                                        ft.Row(controls=[ft.Text("Troco:", size=12), ft.Text(f"R$ {max(troco, 0):.2f}", size=12, weight=ft.FontWeight.BOLD, color=Colors.BRAND_BLUE)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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
                    ft.TextButton("Fechar", on_click=fechar_nota),
                    ft.ElevatedButton(
                        "Imprimir",
                        icon=ft.icons.PRINT,
                        bgcolor=Colors.BRAND_BLUE,
                        color=Colors.TEXT_WHITE,
                        on_click=imprimir_nota,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            page.overlay.append(nota)
            nota.open = True
            page.update()

        # ------------------------------------------------------------------ #
        # MODAL DE CONFIRMAÇÃO
        # ------------------------------------------------------------------ #

        header_itens = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("Descrição", size=11, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text("Qtd", size=11, weight=ft.FontWeight.BOLD, width=40, text_align=ft.TextAlign.CENTER),
                    ft.Text("Unit.", size=11, weight=ft.FontWeight.BOLD, width=75, text_align=ft.TextAlign.RIGHT),
                    ft.Text("Subtotal", size=11, weight=ft.FontWeight.BOLD, width=75, text_align=ft.TextAlign.RIGHT),
                ],
                spacing=4,
            ),
            bgcolor="#F0F0F0",
            padding=ft.padding.symmetric(horizontal=6, vertical=6),
            border_radius=4,
        )

        linhas_confirmacao = []
        for item in itens_venda:
            linhas_confirmacao.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(item["descricao"], size=11, expand=True),
                            ft.Text(str(item["quantidade"]), size=11, width=40, text_align=ft.TextAlign.CENTER),
                            ft.Text(f"R$ {item['preco_unitario']:.2f}", size=11, width=75, text_align=ft.TextAlign.RIGHT),
                            ft.Text(f"R$ {item['subtotal']:.2f}", size=11, width=75, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN, text_align=ft.TextAlign.RIGHT),
                        ],
                        spacing=4,
                    ),
                    border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
                    padding=ft.padding.symmetric(horizontal=6, vertical=5),
                )
            )

        def confirmar(e):
            tipo_pagamento = VendasAPI.normalizar_pagamento(forma_pagamento.value or "Dinheiro")

            # Validação: dinheiro exige valor recebido preenchido e suficiente
            if tipo_pagamento == "DINHEIRO":
                if valor_recebido <= 0:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Informe o valor recebido em dinheiro antes de finalizar!"),
                        bgcolor=Colors.BRAND_RED,
                    )
                    page.snack_bar.open = True
                    page.update()
                    return
                valor_final_atual = calcular_valor_final()
                if valor_recebido < valor_final_atual:
                    falta = valor_final_atual - valor_recebido
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Valor insuficiente! Faltam R$ {falta:.2f}"),
                        bgcolor=Colors.BRAND_RED,
                    )
                    page.snack_bar.open = True
                    page.update()
                    return

            btn_confirmar.disabled = True
            btn_confirmar.text = "Registrando..."
            page.update()

            try:
                # Verifica turno ativo antes de criar venda
                turno_ativo = TurnoAPI.get_turno_ativo()
                if not turno_ativo:
                    btn_confirmar.disabled = False
                    btn_confirmar.text = "Registrar Venda"
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("⚠ Nenhum turno aberto! Abra um turno antes de realizar vendas."),
                        bgcolor=Colors.BRAND_ORANGE,
                    )
                    page.snack_bar.open = True
                    page.update()
                    return

                tipo_pagamento = VendasAPI.normalizar_pagamento(forma_pagamento.value or "Dinheiro")

                # 1. Cria a venda — VendaCreate é vazio no backend
                venda_criada = VendasAPI.criar_venda({})
                if not venda_criada:
                    raise Exception("Falha ao criar venda na API")

                venda_id = venda_criada.get("id")
                nonlocal venda_id_atual, turno_id_atual
                venda_id_atual  = venda_id
                turno_id_atual  = venda_criada.get("turno_id") or (turno_ativo.get("id") if turno_ativo else None)
                atualizar_info_venda()

                # 2. Adiciona cada item — ItemVendaCreate só aceita produto_id e quantidade
                for item in itens_venda:
                    resultado_item = VendasAPI.adicionar_item(venda_id, {
                        "produto_id": item["produto_id"],
                        "quantidade": item["quantidade"],
                    })
                    if resultado_item is None or "erro" in (resultado_item or {}):
                        msg_erro = (resultado_item or {}).get("erro", "Erro desconhecido")
                        # Cancela a venda criada para não deixar lixo no banco
                        VendasAPI.cancelar_venda(venda_id)
                        raise Exception(f"Erro no item '{item['descricao']}': {msg_erro}")

                # 3. Recalcula subtotal dos itens no backend
                VendasAPI.recalcular_total(venda_id)

                # 3b. Aplica desconto/acréscimo DEPOIS dos itens estarem salvos
                if desconto_aplicado > 0 or acrescimo_aplicado > 0:
                    VendasAPI.atualizar_venda(venda_id, {
                        "desconto": round(desconto_aplicado, 2),
                        "acrescimo": round(acrescimo_aplicado, 2),
                    })

                # 3c. Recalcula total final já com desconto/acréscimo aplicados
                venda_atualizada = VendasAPI.recalcular_total(venda_id)
                total_real = float(
                    (venda_atualizada or {}).get("total") or valor_final
                )

                # Arredonda pra cima com 2 casas para evitar erro de float
                # (ex: 101.00000000000003 → 101.01 garante valor_recebido >= total)
                import math
                total_ceil = math.ceil(total_real * 100) / 100

                # Para dinheiro usa o que o usuário digitou (se >= total),
                # para outros meios usa o total arredondado pra cima
                if tipo_pagamento == "DINHEIRO" and valor_recebido >= total_ceil:
                    vr = round(valor_recebido, 2)
                else:
                    vr = total_ceil

                pag_result = VendasAPI.registrar_pagamento(venda_id, {
                    "tipo": tipo_pagamento,
                    "valor_recebido": vr,
                })
                if not pag_result:
                    raise Exception("Falha ao registrar pagamento (verifique o tipo e valor)")

                # 4. Finaliza a venda
                final_result = VendasAPI.finalizar_venda(venda_id)
                if not final_result:
                    raise Exception("Falha ao finalizar venda")

                # 4b. Registra movimentação SAIDA/VENDA para cada item
                try:
                    for item in itens_venda:
                        MovimentacaoAPI.registrar_movimentacao({
                            "tipo":       "SAIDA",
                            "motivo":     "VENDA",
                            "quantidade": item["quantidade"],
                            "produto_id": item["produto_id"],
                            "venda_id":   venda_id,
                        })
                except Exception as mov_err:
                    print(f"Aviso: falha ao registrar movimentação de venda: {mov_err}")

                # 5. Snapshot para a nota
                itens_snapshot  = list(itens_venda)
                subtotal_snap   = valor_total
                desconto_snap   = desconto_aplicado
                acrescimo_snap  = acrescimo_aplicado
                total_snap      = valor_final
                pagamento_snap  = forma_pagamento.value
                troco_snap      = calcular_troco()

                # 6. Fecha modal e limpa tela
                modal.open = False
                venda_id_concluida = venda_id  # preserva antes de limpar
                limpar_venda_atual(None)
                # Mostra o ID da última venda concluída na sidebar
                txt_venda_id.value = f"#{venda_id_concluida}"
                txt_venda_id.color = Colors.BRAND_GREEN
                try: txt_venda_id.update()
                except Exception: pass
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("✓ Venda concluída com sucesso!"),
                    bgcolor=Colors.BRAND_GREEN,
                )
                page.snack_bar.open = True

                # 7. Nota fiscal
                modal_nota_fiscal(
                    venda_id,
                    itens_snapshot,
                    subtotal_snap,
                    desconto_snap,
                    acrescimo_snap,
                    total_snap,
                    pagamento_snap,
                    troco_snap,
                )

            except Exception as ex:
                btn_confirmar.disabled = False
                btn_confirmar.text = "Confirmar"
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Erro ao registrar venda: {ex}"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()

        def fechar_modal(e):
            modal.open = False
            page.update()

        btn_confirmar = ft.ElevatedButton(
            "Confirmar",
            bgcolor=Colors.BRAND_GREEN,
            color=Colors.TEXT_WHITE,
            on_click=confirmar,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Venda", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=480,
                content=ft.Column(
                    spacing=Sizes.SPACING_SMALL,
                    controls=[
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=50, color=Colors.BRAND_GREEN),
                        ft.Text("Deseja registrar esta venda?", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        ft.Divider(),
                        header_itens,
                        ft.Container(
                            content=ft.Column(controls=linhas_confirmacao, spacing=0, scroll=ft.ScrollMode.AUTO),
                            border=ft.border.all(1, Colors.BORDER_LIGHT),
                            border_radius=4,
                            height=min(len(itens_venda) * 32 + 10, 200),
                        ),
                        ft.Divider(),
                        ft.Row(controls=[ft.Text("Subtotal:", size=Sizes.FONT_SMALL), ft.Text(f"R$ {valor_total:.2f}", size=Sizes.FONT_SMALL)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row(controls=[ft.Text("Desconto:", size=Sizes.FONT_SMALL, color=Colors.BRAND_RED), ft.Text(f"- R$ {desconto_aplicado:.2f}", size=Sizes.FONT_SMALL, color=Colors.BRAND_RED)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row(controls=[ft.Text("Acréscimo:", size=Sizes.FONT_SMALL, color=Colors.BRAND_ORANGE), ft.Text(f"+ R$ {acrescimo_aplicado:.2f}", size=Sizes.FONT_SMALL, color=Colors.BRAND_ORANGE)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(height=1),
                        ft.Row(controls=[ft.Text("TOTAL:", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD), ft.Text(f"R$ {valor_final:.2f}", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row(controls=[ft.Text("Pagamento:", size=Sizes.FONT_SMALL), ft.Text(forma_pagamento.value, size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row(controls=[ft.Text("Troco:", size=Sizes.FONT_SMALL), ft.Text(f"R$ {max(calcular_troco(), 0):.2f}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_BLUE)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                btn_confirmar,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()

    # ============================================================================
    # FUNÇÕES DE CANCELAMENTO
    # ============================================================================
    
    def limpar_venda_atual(e):
        """Limpa a venda atual"""
        items_list.controls.clear()

        nonlocal valor_total, desconto_aplicado, acrescimo_aplicado, valor_recebido, numero_item, itens_venda, venda_id_atual, turno_id_atual
        venda_id_atual = None
        turno_id_atual = None
        atualizar_info_venda()
        valor_total = 0.0
        desconto_aplicado = 0.0
        acrescimo_aplicado = 0.0
        valor_recebido = 0.0
        numero_item = 0
        itens_venda = []
        
        input_desconto.value = "0.00"
        input_acrescimo.value = "0.00"
        input_valor_recebido.value = "0.00"
        produto_input.value = ""
        
        atualizar_totais()
        
        page.update()
    
    def cancelar_venda_concluida_modal(e):
        """Abre modal para cancelar venda concluída pedindo ID"""
        
        input_id_venda = ft.TextField(
            label="ID da Venda",
            width=300,
            border_color=Colors.BORDER_GRAY,
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="Ex: 001",
            autofocus=True,
        )
        
        def confirmar_cancelamento(e):
            if not input_id_venda.value or input_id_venda.value.strip() == "":
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Por favor, informe o ID da venda!"),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()
                return
            
            venda_id_cancelar = int(input_id_venda.value)

            # Verifica status da venda antes de tentar cancelar
            try:
                todas = VendasAPI.listar_vendas()
                venda_alvo = next((v for v in (todas or []) if v.get("id") == venda_id_cancelar), None)
                if venda_alvo:
                    status_alvo = (venda_alvo.get("status") or "").upper()
                    if status_alvo == "CANCELADA":
                        page.snack_bar = ft.SnackBar(content=ft.Text(f"Venda #{venda_id_cancelar} já está cancelada!"), bgcolor=Colors.BRAND_ORANGE)
                        page.snack_bar.open = True
                        page.update()
                        return
                    if status_alvo == "ABERTA":
                        page.snack_bar = ft.SnackBar(content=ft.Text(f"Venda #{venda_id_cancelar} ainda está em aberto."), bgcolor=Colors.BRAND_ORANGE)
                        page.snack_bar.open = True
                        page.update()
                        return
                    if status_alvo != "CONCLUIDA":
                        page.snack_bar = ft.SnackBar(content=ft.Text(f"Status '{status_alvo}' não permite cancelamento."), bgcolor=Colors.BRAND_ORANGE)
                        page.snack_bar.open = True
                        page.update()
                        return
            except Exception:
                pass

            resultado = VendasAPI.cancelar_venda(venda_id_cancelar)

            if resultado and "erro" in resultado:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Não foi possível cancelar: {resultado['erro']}"), bgcolor=Colors.BRAND_ORANGE)
                page.snack_bar.open = True
                page.update()
            elif resultado:
                # Registra ENTRADA/DEVOLUCAO para cada item da venda cancelada
                try:
                    itens_cancelados = VendasAPI.listar_itens(venda_id_cancelar)
                    for item in itens_cancelados:
                        MovimentacaoAPI.registrar_movimentacao({
                            "tipo":       "ENTRADA",
                            "motivo":     "DEVOLUCAO",
                            "quantidade": item.get("quantidade", 1),
                            "produto_id": item.get("produto_id"),
                            "venda_id":   venda_id_cancelar,
                        })
                except Exception as mov_err:
                    print(f"Aviso: falha ao registrar movimentação de devolução: {mov_err}")

                modal.open = False
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Venda #{input_id_venda.value} cancelada com sucesso!"),
                    bgcolor=Colors.BRAND_GREEN,
                )
                page.snack_bar.open = True
                page.update()
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Erro ao cancelar venda. Tente novamente."),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()
        
        def fechar_modal(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cancelar Venda Concluída", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=300,
                content=ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Icon(ft.icons.WARNING, size=44, color=Colors.BRAND_RED),
                        ft.Text(
                            "Esta ação irá cancelar uma venda já concluída!",
                            size=Sizes.FONT_SMALL,
                            color=Colors.BRAND_RED,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(height=4),
                        ft.Text("Informe o ID da venda:", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY),
                        input_id_venda,
                        ft.Text(f"Turno: #{turno_id_atual}" if turno_id_atual else "Turno: —", size=11, color=Colors.TEXT_GRAY, italic=True),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Voltar", on_click=fechar_modal),
                ft.ElevatedButton(
                    "Confirmar",
                    bgcolor=Colors.BRAND_RED,
                    color=Colors.TEXT_WHITE,
                    on_click=confirmar_cancelamento,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    # ============================================================================
    # HEADER - BUSCA DE PRODUTO
    # ============================================================================

    produto_input = ft.TextField(
        label="Produto",
        width=Sizes.INPUT_LARGE,
        height=50,
        border_color=Colors.BORDER_GRAY,
        on_submit=buscar_e_adicionar_produto,
    )

    data_input = Styles.text_field("Data", Sizes.INPUT_MEDIUM, value=get_data_atual(), read_only=True)
    hora_input = Styles.text_field("Hora", Sizes.INPUT_SMALL, value=get_hora_atual(), read_only=True)
    
    btn_buscar_produto = ft.ElevatedButton(
        "Buscar por nome",
        icon=ft.icons.SEARCH,
        on_click=modal_buscar_produto,
        bgcolor=Colors.BRAND_BLUE,
        color=Colors.TEXT_WHITE,
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
    )
    
    def atualizar_hora_thread():
        while True:
            try:
                hora_input.value = get_hora_atual()
                page.update()
                time.sleep(1)
            except:
                break
    
    threading.Thread(target=atualizar_hora_thread, daemon=True).start()
    
    top_section = ft.Container(
        content=ft.Row(
            controls=[produto_input, btn_buscar_produto, data_input, hora_input],
            spacing=Sizes.SPACING_LARGE,
        ),
        padding=Sizes.SPACING_LARGE,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,
    )
    
    # ============================================================================
    # TABELA DE ITENS
    # ============================================================================
    
    table_header = Styles.table_header([
        ("Nº",         VendasCols.NUMERO),
        ("ID",         VendasCols.ID),
        ("Descrição",  None),
        ("Quant.",     VendasCols.QUANTIDADE),
        ("Valor.Uni",  VendasCols.PRECO_UNI),
        ("Valor total",VendasCols.TOTAL),
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
    
    # ============================================================================
    # SIDEBAR - INFORMAÇÕES E TOTALIZADORES
    # ============================================================================

    txt_venda_id = ft.Text("—", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_BLUE)
    txt_turno_id = ft.Text("—", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY)

    def atualizar_info_venda():
        txt_venda_id.value = f"#{venda_id_atual}" if venda_id_atual else "—"
        txt_venda_id.color = Colors.BRAND_BLUE if venda_id_atual else Colors.TEXT_GRAY
        txt_turno_id.value = f"Turno #{turno_id_atual}" if turno_id_atual else "—"
        txt_turno_id.color = Colors.BRAND_GREEN if turno_id_atual else Colors.TEXT_GRAY
        try:
            txt_venda_id.update()
            txt_turno_id.update()
        except Exception:
            pass

    info_venda = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("INFORMAÇÕES", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                ft.Row(controls=[ft.Text("Turno:", size=Sizes.FONT_SMALL, weight=ft.FontWeight.W_500), txt_turno_id], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=Sizes.SPACING_SMALL,
        ),
        padding=Sizes.SPACING_MEDIUM,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,
    )
    
    txt_subtotal = ft.Text("R$ 0,00", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK)
    txt_desconto_valor = ft.Text("- R$ 0,00", size=Sizes.FONT_SMALL, color=Colors.BRAND_RED)
    txt_acrescimo_valor = ft.Text("+ R$ 0,00", size=Sizes.FONT_SMALL, color=Colors.BRAND_GREEN)
    txt_total_final = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN)
    
    input_desconto = ft.TextField(
        label="Desconto (R$)", width=220, height=45,
        border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER,
        value="0.00", on_change=aplicar_desconto, text_size=Sizes.FONT_SMALL,
    )
    
    input_acrescimo = ft.TextField(
        label="Acréscimo (R$)", width=220, height=45,
        border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER,
        value="0.00", on_change=aplicar_acrescimo, text_size=Sizes.FONT_SMALL,
    )
    
    totalizadores = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("TOTALIZADORES", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                ft.Row(controls=[ft.Text("Subtotal:", size=Sizes.FONT_SMALL, weight=ft.FontWeight.W_500), txt_subtotal], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=Colors.BORDER_LIGHT),
                input_desconto,
                ft.Row(controls=[ft.Text("Desconto:", size=Sizes.FONT_SMALL), txt_desconto_valor], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                input_acrescimo,
                ft.Row(controls=[ft.Text("Acréscimo:", size=Sizes.FONT_SMALL), txt_acrescimo_valor], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                ft.Row(controls=[ft.Text("TOTAL:", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD), txt_total_final], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=Sizes.SPACING_SMALL,
        ),
        padding=Sizes.SPACING_MEDIUM,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor="#F0F8FF",
        margin=ft.margin.only(top=Sizes.SPACING_SMALL),
    )
    
    forma_pagamento = Styles.dropdown(
        label="Forma de Pagamento",
        options=["Dinheiro", "Débito", "Crédito", "PIX"],
        width=220,
        value="Dinheiro"
    )

    def on_forma_pagamento_change(e):
        troco_section.visible = forma_pagamento.value == "Dinheiro"
        page.update()

    forma_pagamento.on_change = on_forma_pagamento_change

    pagamento_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("PAGAMENTO", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                forma_pagamento,
            ],
            spacing=Sizes.SPACING_SMALL,
        ),
        padding=Sizes.SPACING_MEDIUM,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,
        margin=ft.margin.only(top=Sizes.SPACING_SMALL),
    )

    input_valor_recebido = ft.TextField(
        label="Valor Recebido (R$)", width=220, height=45,
        border_color=Colors.BORDER_GRAY, keyboard_type=ft.KeyboardType.NUMBER,
        value="0.00", on_change=aplicar_valor_recebido, text_size=Sizes.FONT_SMALL,
    )

    txt_troco = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN)

    troco_section = ft.Container(
        visible=True,
        content=ft.Column(
            controls=[
                ft.Text("TROCO", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                input_valor_recebido,
                ft.Divider(color=Colors.BORDER_LIGHT),
                ft.Row(controls=[ft.Text("Troco:", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD), txt_troco], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=Sizes.SPACING_SMALL,
        ),
        padding=Sizes.SPACING_MEDIUM,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor="#FFFACD",
        margin=ft.margin.only(top=Sizes.SPACING_SMALL),
    )
    
    def create_action_button(text, icon, on_click, bgcolor):
        return ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=20, color=Colors.TEXT_WHITE),
                    ft.Text(text, size=14, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD, no_wrap=False, text_align=ft.TextAlign.CENTER)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                tight=True,
            ),
            bgcolor=bgcolor,
            width=260,
            height=55,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
            on_click=on_click
        )
    
    btn_concluir          = create_action_button("Concluir Venda",  ft.icons.CHECK_CIRCLE,  concluir_venda,                Colors.BRAND_GREEN)
    def limpar_com_aviso(e):
        limpar_venda_atual(e)
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Venda atual limpa!"),
            bgcolor=Colors.BRAND_ORANGE,
        )
        page.snack_bar.open = True
        page.update()

    btn_limpar_atual      = create_action_button("Limpar Atual",    ft.icons.DELETE_SWEEP,  limpar_com_aviso,              Colors.BRAND_ORANGE)
    btn_cancelar_concluida = create_action_button("Cancelar Venda", ft.icons.CANCEL,        cancelar_venda_concluida_modal, Colors.BRAND_RED)
    
    def modal_historico_recente(e):
        """Abre modal com as vendas mais recentes"""

        lista_vendas_modal = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        [ft.ProgressRing(width=24, height=24), ft.Text("Carregando...")],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=30,
                    alignment=ft.alignment.center,
                )
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        def fechar_modal(e):
            modal.open = False
            page.update()

        header_modal = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Text("ID", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Data", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Hora", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Total", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Pagamento", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                    ft.Container(ft.Text("Status", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                ],
                spacing=0,
            ),
            bgcolor=Colors.BG_PINK_LIGHT,
            padding=10,
        )

        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Vendas Recentes", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        header_modal,
                        ft.Container(
                            content=lista_vendas_modal,
                            height=400,
                            border=ft.border.all(1, Colors.BORDER_BLACK),
                            bgcolor=Colors.BG_WHITE,
                        ),
                    ],
                    spacing=0,
                ),
                width=750,
            ),
            actions=[ft.TextButton("Fechar", on_click=fechar_modal)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()

        def status_cor(status):
            return {"finalizada": Colors.BRAND_GREEN, "cancelada": Colors.BRAND_RED, "pendente": Colors.BRAND_ORANGE}.get((status or "").lower(), Colors.TEXT_GRAY)

        vendas = VendasAPI.listar_vendas()
        lista_vendas_modal.controls.clear()

        # Ordena por ID decrescente — última venda aparece no topo
        vendas_sorted = sorted(vendas, key=lambda x: x.get("id", 0), reverse=True)
        recentes = vendas_sorted[:20]

        if not recentes:
            lista_vendas_modal.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.icons.RECEIPT_LONG, size=60, color=Colors.TEXT_GRAY),
                            ft.Text("Nenhuma venda encontrada", size=Sizes.FONT_MEDIUM, color=Colors.TEXT_GRAY),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                    alignment=ft.alignment.center,
                )
            )
        else:
            for venda in recentes:
                data_str = venda.get("data_venda") or venda.get("created_at") or ""
                try:
                    dt_local = utc_to_local(data_str)
                    data_fmt = dt_local.strftime("%d/%m/%Y") if dt_local else data_str[:10]
                    hora_fmt = dt_local.strftime("%H:%M:%S") if dt_local else (data_str[11:19] if len(data_str) > 10 else "")
                except Exception:
                    data_fmt = data_str[:10]
                    hora_fmt = data_str[11:19] if len(data_str) > 10 else ""

                status = venda.get("status", "—")
                total  = float(venda.get("total") or venda.get("valor_total") or 0)

                fp = venda.get("forma_pagamento")
                if isinstance(fp, dict):
                    pag_label = fp.get("tipo", "—").capitalize()
                elif isinstance(fp, str):
                    pag_label = fp.capitalize()
                else:
                    pag_label = "—"

                lista_vendas_modal.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(ft.Text(str(venda.get("id", "")), size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_SMALL, alignment=ft.alignment.center),
                                ft.Container(ft.Text(data_fmt, size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                                ft.Container(ft.Text(hora_fmt, size=Sizes.FONT_SMALL), width=Sizes.TABLE_COL_MEDIUM, alignment=ft.alignment.center),
                                ft.Container(ft.Text(f"R$ {total:.2f}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                                ft.Container(ft.Text(pag_label, size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_BLUE), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                                ft.Container(ft.Text(status.capitalize(), size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=status_cor(status)), width=Sizes.TABLE_COL_LARGE, alignment=ft.alignment.center),
                            ],
                            spacing=0,
                        ),
                        border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
                        padding=10,
                        bgcolor=Colors.BG_WHITE,
                    )
                )

        page.update()

    btn_historico = create_action_button("Histórico", ft.icons.HISTORY, modal_historico_recente, Colors.BRAND_BLUE)
    btn_sair      = create_action_button("Menu Principal", ft.icons.HOME, lambda _: page.go("/"), Colors.BRAND_RED)
    
    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                ft.Column(
                    controls=[
                        info_venda,
                        totalizadores,
                        pagamento_section,
                        troco_section,
                        ft.Container(height=10),
                        btn_concluir,
                        btn_limpar_atual,
                        btn_cancelar_concluida,
                        btn_historico,
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                ft.Container(content=btn_sair, padding=ft.padding.only(top=8)),
            ],
            spacing=0,
        ),
        width=300,
        padding=Sizes.SPACING_MEDIUM,
        bgcolor=Colors.BG_GRAY_LIGHT,
    )
    
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
    
    # Carrega turno ativo ao abrir a tela
    def init_turno():
        nonlocal turno_id_atual
        try:
            turno_ativo = TurnoAPI.get_turno_ativo()
            if turno_ativo:
                turno_id_atual = turno_ativo.get("id")
                atualizar_info_venda()
        except Exception as ex:
            print(f"[Vendas] Erro ao buscar turno: {ex}")

    page.run_thread(init_turno)

    return ft.Row(
        controls=[main_content, sidebar],
        spacing=0,
        expand=True,
    )