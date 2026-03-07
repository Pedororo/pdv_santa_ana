import flet as ft
from datetime import datetime
import time
import threading
from app.views.styles.theme import Colors, Sizes, Styles

def VendasView(page: ft.Page):
    """Tela de registro de vendas"""
    
    # ============================================================================
    # VARIÁVEIS DE CONTROLE
    # ============================================================================
    
    valor_total = 0.0
    desconto_aplicado = 0.0
    acrescimo_aplicado = 0.0
    valor_recebido = 0.0
    
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
    
    def atualizar_totais():
        """Atualiza os campos de totais"""
        txt_subtotal.value = f"R$ {valor_total:.2f}"
        txt_desconto_valor.value = f"- R$ {desconto_aplicado:.2f}"
        txt_acrescimo_valor.value = f"+ R$ {acrescimo_aplicado:.2f}"
        txt_total_final.value = f"R$ {calcular_valor_final():.2f}"
        
        # Atualiza o troco
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
    # FUNÇÕES DE AÇÃO
    # ============================================================================
    
    def limpar_venda_atual(e):
        """Limpa a venda atual"""
        items_list.controls.clear()
        
        nonlocal valor_total, desconto_aplicado, acrescimo_aplicado, valor_recebido
        valor_total = 0.0
        desconto_aplicado = 0.0
        acrescimo_aplicado = 0.0
        valor_recebido = 0.0
        
        input_desconto.value = "0.00"
        input_acrescimo.value = "0.00"
        input_valor_recebido.value = "0.00"
        produto_input.value = ""
        
        atualizar_totais()
        
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Venda atual cancelada!"),
            bgcolor=Colors.BRAND_GREEN,
        )
        page.snack_bar.open = True
        page.update()
        
        print("Venda atual limpa")
    
    def cancelar_venda_concluida_modal(e):
        """Abre modal para cancelar venda concluída"""
        
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
            
            id_venda = input_id_venda.value
            
            modal.open = False
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Venda #{id_venda} do Turno 1 cancelada!"),
                bgcolor=Colors.BRAND_GREEN,
            )
            page.snack_bar.open = True
            page.update()
            
            print(f"Venda concluída #{id_venda} cancelada")
        
        def fechar_modal(e):
            modal.open = False
            page.update()
        
        modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Cancelar Venda Concluída", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.icons.WARNING, size=60, color=Colors.BRAND_RED),
                        ft.Text(
                            "Esta ação irá cancelar uma venda já concluída!",
                            size=Sizes.FONT_MEDIUM,
                            color=Colors.BRAND_RED,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Divider(),
                        ft.Text("Informe o ID da venda:", size=Sizes.FONT_MEDIUM),
                        input_id_venda,
                        ft.Text(
                            f"Turno atual: Turno 1",
                            size=Sizes.FONT_SMALL,
                            color=Colors.TEXT_GRAY,
                            italic=True,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Sizes.SPACING_MEDIUM,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_modal),
                ft.ElevatedButton(
                    "Confirmar",
                    bgcolor=Colors.BRAND_RED,
                    color=Colors.TEXT_WHITE,
                    on_click=confirmar_cancelamento,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.overlay.append(modal)
        modal.open = True
        page.update()
    
    # ============================================================================
    # HEADER - BUSCA DE PRODUTO
    # ============================================================================
    
    produto_input = Styles.text_field("Produto", Sizes.INPUT_LARGE)
    data_input = Styles.text_field("Data", Sizes.INPUT_MEDIUM, value=get_data_atual(), read_only=True)
    hora_input = Styles.text_field("Hora", Sizes.INPUT_SMALL, value=get_hora_atual(), read_only=True)
    
    # Thread para atualizar a hora
    def atualizar_hora_thread():
        while True:
            try:
                hora_input.value = get_hora_atual()
                page.update()
                time.sleep(1)
            except:
                break
    
    thread = threading.Thread(target=atualizar_hora_thread, daemon=True)
    thread.start()
    
    top_section = ft.Container(
        content=ft.Row(
            controls=[produto_input, data_input, hora_input],
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
        ("Nº", Sizes.TABLE_COL_SMALL),
        ("ID", Sizes.TABLE_COL_SMALL),
        ("Descrição", None),
        ("Quant.", Sizes.TABLE_COL_MEDIUM),
        ("Valor.Uni", Sizes.TABLE_COL_LARGE),
        ("Valor total", Sizes.TABLE_COL_LARGE),
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
    
    # --- INFORMAÇÕES DA VENDA ---
    info_venda = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("INFORMAÇÕES", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                ft.Row(
                    controls=[
                        ft.Text("ID:", size=Sizes.FONT_SMALL, weight=ft.FontWeight.W_500),
                        ft.Text("#001", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_BLUE),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    controls=[
                        ft.Text("Turno:", size=Sizes.FONT_SMALL, weight=ft.FontWeight.W_500),
                        ft.Text("Turno 1", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=Sizes.SPACING_SMALL,
        ),
        padding=Sizes.SPACING_MEDIUM,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor=Colors.BG_WHITE,
    )
    
    # --- TOTALIZADORES ---
    txt_subtotal = ft.Text("R$ 0,00", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK)
    txt_desconto_valor = ft.Text("- R$ 0,00", size=Sizes.FONT_SMALL, color=Colors.BRAND_RED)
    txt_acrescimo_valor = ft.Text("+ R$ 0,00", size=Sizes.FONT_SMALL, color=Colors.BRAND_GREEN)
    txt_total_final = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN)
    
    input_desconto = ft.TextField(
        label="Desconto (R$)",
        width=220,
        height=45,
        border_color=Colors.BORDER_GRAY,
        keyboard_type=ft.KeyboardType.NUMBER,
        value="0.00",
        on_change=aplicar_desconto,
        text_size=Sizes.FONT_SMALL,
    )
    
    input_acrescimo = ft.TextField(
        label="Acréscimo (R$)",
        width=220,
        height=45,
        border_color=Colors.BORDER_GRAY,
        keyboard_type=ft.KeyboardType.NUMBER,
        value="0.00",
        on_change=aplicar_acrescimo,
        text_size=Sizes.FONT_SMALL,
    )
    
    totalizadores = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("TOTALIZADORES", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                
                ft.Row(
                    controls=[
                        ft.Text("Subtotal:", size=Sizes.FONT_SMALL, weight=ft.FontWeight.W_500),
                        txt_subtotal,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(color=Colors.BORDER_LIGHT),
                
                input_desconto,
                ft.Row(
                    controls=[
                        ft.Text("Desconto:", size=Sizes.FONT_SMALL),
                        txt_desconto_valor,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                
                input_acrescimo,
                ft.Row(
                    controls=[
                        ft.Text("Acréscimo:", size=Sizes.FONT_SMALL),
                        txt_acrescimo_valor,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                
                ft.Row(
                    controls=[
                        ft.Text("TOTAL:", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD),
                        txt_total_final,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=Sizes.SPACING_SMALL,
        ),
        padding=Sizes.SPACING_MEDIUM,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor="#F0F8FF",
        margin=ft.margin.only(top=Sizes.SPACING_SMALL),
    )
    
    # --- FORMA DE PAGAMENTO ---
    forma_pagamento = Styles.dropdown(
        label="Forma de Pagamento",
        options=["Dinheiro", "Débito", "Crédito", "PIX", "Boleto"],
        width=220,
        value="Dinheiro"
    )
    
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
    
    # --- CALCULADORA DE TROCO ---
    input_valor_recebido = ft.TextField(
        label="Valor Recebido (R$)",
        width=220,
        height=45,
        border_color=Colors.BORDER_GRAY,
        keyboard_type=ft.KeyboardType.NUMBER,
        value="0.00",
        on_change=aplicar_valor_recebido,
        text_size=Sizes.FONT_SMALL,
    )
    
    txt_troco = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN)
    
    troco_section = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("TROCO", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED),
                ft.Divider(color=Colors.BORDER_MEDIUM, thickness=2),
                input_valor_recebido,
                ft.Divider(color=Colors.BORDER_LIGHT),
                ft.Row(
                    controls=[
                        ft.Text("Troco:", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.BOLD),
                        txt_troco,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=Sizes.SPACING_SMALL,
        ),
        padding=Sizes.SPACING_MEDIUM,
        border=ft.border.all(2, Colors.BORDER_BLACK),
        border_radius=Sizes.BORDER_RADIUS_SMALL,
        bgcolor="#FFFACD",
        margin=ft.margin.only(top=Sizes.SPACING_SMALL),
    )
    
    # --- BOTÕES DE AÇÃO (COMPACTOS) ---
    
    # Botão personalizado compacto
    def create_compact_button(text, icon, on_click, bgcolor):
        return ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=18, color=Colors.TEXT_WHITE),
                    ft.Text(text, size=13, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=bgcolor,
            width=260,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
            on_click=on_click
        )
    
    btn_concluir = create_compact_button("Concluir Venda", ft.icons.CHECK, lambda _: print("Concluir"), Colors.BRAND_GREEN)
    btn_limpar_atual = create_compact_button("Limpar Venda Atual", ft.icons.CLEAR_ALL, limpar_venda_atual, Colors.BRAND_ORANGE)
    btn_cancelar_concluida = create_compact_button("Cancelar Concluída", ft.icons.RECEIPT_LONG, cancelar_venda_concluida_modal, Colors.BRAND_RED)
    btn_historico = create_compact_button("Histórico", ft.icons.HISTORY, lambda _: page.go("/historico"), Colors.BRAND_BLUE)
    btn_sair = create_compact_button("Sair", ft.icons.LOGOUT, lambda _: page.go("/"), Colors.BRAND_RED)
    
    # --- SIDEBAR COMPLETA ---
    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                # Área com scroll
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
                # Botão Sair fixo
                ft.Container(
                    content=btn_sair,
                    padding=ft.padding.only(top=8),
                ),
            ],
            spacing=0,
        ),
        width=300,
        padding=Sizes.SPACING_MEDIUM,
        bgcolor=Colors.BG_GRAY_LIGHT,
    )
    
    # ============================================================================
    # LAYOUT PRINCIPAL
    # ============================================================================
    
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
    
    return ft.Row(
        controls=[main_content, sidebar],
        spacing=0,
        expand=True,
    )