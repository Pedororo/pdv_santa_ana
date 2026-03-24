import flet as ft
from datetime import datetime, timedelta
from app.views.styles.theme import Colors, Sizes, Styles, HistoricoVendasCols, HistoricoTurnosCols
from app.api.vendas_api import VendasAPI
from app.api.turno_api import TurnoAPI
from app.api.usuarios_api import UsuariosAPI
from app.utils.printer import imprimir_cupom_venda, imprimir_resumo_turno


def HistoricoView(page: ft.Page):
    """Tela de histórico de vendas"""

    todas_vendas = []

    # UTC-3 Fortaleza
    _UTC_OFFSET = timedelta(hours=-3)

    def utc_to_local(data_str):
        """Converte string UTC para horário de Fortaleza (UTC-3)"""
        try:
            dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            dt_local = dt + _UTC_OFFSET
            return dt_local
        except Exception:
            return None

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
                dt_local = utc_to_local(data_str)
                data_venda = dt_local.date() if dt_local else datetime.fromisoformat(data_str[:10]).date()
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
            def _match(v):
                # Busca por ID ou nome do vendedor
                vendedor = (
                    v.get("usuario_nome") or
                    (v.get("usuario", {}).get("nome") if isinstance(v.get("usuario"), dict) else None) or
                    v.get("vendedor") or ""
                ).lower()
                return texto in str(v.get("id", "")).lower() or texto in vendedor
            vendas = [v for v in vendas if _match(v)]

        renderizar_tabela(vendas)

    # ============================================================================
    # MODAIS DE AÇÃO
    # ============================================================================

    def modal_cancelar(venda):
        venda_id = venda.get("id")
        total    = float(venda.get("total") or venda.get("valor_total") or 0)

        # Verifica se a venda tem mais de 20 minutos
        data_str = venda.get("data_venda") or venda.get("created_at") or ""
        venda_expirada = False
        if data_str:
            try:
                dt_local = utc_to_local(data_str)
                if dt_local and (datetime.now() - dt_local.replace(tzinfo=None)).total_seconds() > 1200:
                    venda_expirada = True
            except Exception:
                pass

        if venda_expirada:
            def fechar_exp(e):
                modal_exp.open = False
                page.update()

            modal_exp = ft.AlertDialog(
                modal=True,
                title=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.BLOCK, color=Colors.BRAND_RED, size=20),
                        ft.Text("Cancelamento bloqueado", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=8,
                ),
                content=ft.Container(
                    width=300,
                    content=ft.Column(
                        tight=True,
                        spacing=8,
                        controls=[
                            ft.Text(
                                f"A venda #{venda_id} não pode ser cancelada pois já tem mais de 20 minutos.",
                                size=Sizes.FONT_SMALL,
                                color=Colors.BRAND_ORANGE,
                            ),
                            ft.Divider(height=1),
                            ft.Row(
                                controls=[
                                    ft.Text("Venda Nº:", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY),
                                    ft.Text(f"#{venda_id}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Text("Valor Total:", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY),
                                    ft.Text(f"R$ {total:.2f}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                        ],
                    ),
                ),
                actions=[ft.ElevatedButton("Entendido", bgcolor=Colors.BRAND_RED, color=Colors.TEXT_WHITE, on_click=fechar_exp, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.clear()
            page.overlay.append(modal_exp)
            modal_exp.open = True
            page.update()
            return

        def confirmar(e):
            btn_confirmar.disabled = True
            btn_confirmar.text = "Cancelando..."
            page.update()

            resultado = VendasAPI.cancelar_venda(venda_id)

            if resultado and "erro" in resultado:
                detalhe = resultado["erro"]
                msg = "Esta venda já foi cancelada." if "cancelad" in detalhe.lower() else                       f"Não foi possível cancelar: {detalhe}"
                btn_confirmar.disabled = False
                btn_confirmar.text = "Sim, Cancelar"
                page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=Colors.BRAND_ORANGE)
                page.snack_bar.open = True
                page.update()
            elif resultado:
                modal.open = False
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Venda #{venda_id} cancelada!"), bgcolor=Colors.BRAND_GREEN)
                page.snack_bar.open = True
                carregar_vendas()
            else:
                btn_confirmar.disabled = False
                btn_confirmar.text = "Sim, Cancelar"
                page.snack_bar = ft.SnackBar(content=ft.Text("Erro ao cancelar venda. Tente novamente."), bgcolor=Colors.BRAND_RED)
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
            title=ft.Row(
                controls=[
                    ft.Icon(ft.icons.WARNING_AMBER, size=20, color=Colors.BRAND_RED),
                    ft.Text("Cancelar Venda", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Container(
                width=300,
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.Text(
                            "Esta ação não pode ser desfeita!",
                            size=Sizes.FONT_SMALL,
                            color=Colors.BRAND_RED,
                        ),
                        ft.Divider(height=1),
                        ft.Row(
                            controls=[
                                ft.Text("Venda Nº:", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY),
                                ft.Text(f"#{venda_id}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text("Valor Total:", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY),
                                ft.Text(f"R$ {total:.2f}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_RED),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Voltar", on_click=fechar),
                btn_confirmar,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.clear()
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
            width=220,
            border_color=Colors.BORDER_GRAY,
            options=[ft.dropdown.Option(o) for o in ["Dinheiro", "Débito", "Crédito", "PIX"]],
        )

        def salvar(e):
            if not input_pagamento.value:
                page.snack_bar = ft.SnackBar(content=ft.Text("Selecione a forma de pagamento!"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()
                return

            btn_salvar.disabled = True
            btn_salvar.text = "Salvando..."
            page.update()

            try:
                tipo_normalizado = VendasAPI.normalizar_pagamento(input_pagamento.value)

                vr_hist = float(venda.get("valor_recebido") or 0)
                if vr_hist <= 0:
                    vr_hist = float(venda.get("total") or venda.get("valor_total") or 0)
                vr_hist = max(round(vr_hist, 2), 0.01)

                payload = {"tipo": tipo_normalizado, "valor_recebido": vr_hist}

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
                        content=ft.Text("Erro ao atualizar pagamento! Verifique se a venda está finalizada."),
                        bgcolor=Colors.BRAND_RED,
                    )
                    page.snack_bar.open = True
                    page.update()
            except Exception as err:
                print(f"Erro ao salvar pagamento: {err}")
                btn_salvar.disabled = False
                btn_salvar.text = "Salvar"
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Erro inesperado: {err}"),
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
                    ft.Icon(ft.icons.EDIT, color=Colors.BRAND_BLUE, size=20),
                    ft.Text(f"Pagamento #{venda_id}", size=Sizes.FONT_LARGE, weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Container(
                width=260,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[input_pagamento],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                btn_salvar,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.overlay.clear()
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
            dt_local = utc_to_local(data_str)
            data_fmt = dt_local.strftime("%d/%m/%Y %H:%M:%S") if dt_local else data_str
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
            page.update()

            def _print():
                itens_fmt = []
                for item in itens:
                    pid = item.get("produto_id")
                    itens_fmt.append({
                        "nome":          produtos_map.get(pid) or f"Produto #{pid}",
                        "quantidade":    item.get("quantidade", 1),
                        "preco_unitario": float(item.get("preco_unitario", 0)),
                        "subtotal":      float(item.get("subtotal", 0)),
                    })

                fp_obj = venda.get("forma_pagamento") or {}
                troco_val = float(fp_obj.get("troco") or 0) if isinstance(fp_obj, dict) else 0.0
                vr_val    = float(fp_obj.get("valor_recebido") or 0) if isinstance(fp_obj, dict) else 0.0

                sucesso, msg = imprimir_cupom_venda(
                    venda_id=venda_id,
                    data_fmt=data_fmt,
                    itens=itens_fmt,
                    subtotal=subtotal,
                    desconto=desconto,
                    acrescimo=acrescimo,
                    total=total,
                    pagamento=pagamento,
                    troco=troco_val,
                    valor_recebido=vr_val,
                )
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(msg),
                    bgcolor=Colors.BRAND_GREEN if sucesso else Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()

            page.run_thread(_print)

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
        status_venda = (venda.get("status") or "").upper()
        ja_cancelada  = status_venda == "CANCELADA"
        esta_aberta   = status_venda == "ABERTA"
        pode_cancelar = status_venda == "CONCLUIDA"

        def fechar(e):
            menu.open = False
            page.update()

        def acao_editar(e):
            menu.open = False
            page.update()
            if ja_cancelada:
                page.snack_bar = ft.SnackBar(content=ft.Text("Não é possível editar pagamento de venda cancelada."), bgcolor=Colors.BRAND_ORANGE)
                page.snack_bar.open = True
                page.update()
                return
            if esta_aberta:
                page.snack_bar = ft.SnackBar(content=ft.Text("Não é possível editar pagamento de venda ainda em aberto."), bgcolor=Colors.BRAND_ORANGE)
                page.snack_bar.open = True
                page.update()
                return
            modal_editar_pagamento(venda)

        def acao_cancelar(e):
            menu.open = False
            page.update()
            if ja_cancelada:
                page.snack_bar = ft.SnackBar(content=ft.Text("Esta venda já está cancelada."), bgcolor=Colors.BRAND_ORANGE)
                page.snack_bar.open = True
                page.update()
                return
            if esta_aberta:
                page.snack_bar = ft.SnackBar(content=ft.Text("Vendas em aberto não podem ser canceladas pelo histórico."), bgcolor=Colors.BRAND_ORANGE)
                page.snack_bar.open = True
                page.update()
                return
            if not pode_cancelar:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Venda com status '{status_venda}' não pode ser cancelada."), bgcolor=Colors.BRAND_ORANGE)
                page.snack_bar.open = True
                page.update()
                return
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
            dt_local = utc_to_local(data_str)
            data_fmt = dt_local.strftime("%d/%m/%Y") if dt_local else data_str[:10]
            hora_fmt = dt_local.strftime("%H:%M:%S") if dt_local else (data_str[11:19] if len(data_str) > 10 else "")
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
                    ft.Container(ft.Text(str(venda.get("id", "")), size=Sizes.FONT_SMALL), width=HistoricoVendasCols.ID, alignment=ft.alignment.center),
                    ft.Container(ft.Text(data_fmt, size=Sizes.FONT_SMALL), width=HistoricoVendasCols.DATA, alignment=ft.alignment.center),
                    ft.Container(ft.Text(hora_fmt, size=Sizes.FONT_SMALL), width=HistoricoVendasCols.HORA, alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {total:.2f}", size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN), width=HistoricoVendasCols.TOTAL, alignment=ft.alignment.center),
                    ft.Container(ft.Text(pagamento_label, size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_BLUE), width=HistoricoVendasCols.PAGAMENTO, alignment=ft.alignment.center),
                    ft.Container(ft.Text(status.capitalize(), size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=status_cor(status)), width=HistoricoVendasCols.STATUS, alignment=ft.alignment.center),
                    ft.Container(
                        content=ft.Text(
                            f"#{venda.get('turno_id')}" if venda.get("turno_id") else "—",
                            size=Sizes.FONT_SMALL,
                            color=Colors.BRAND_BLUE if venda.get("turno_id") else Colors.TEXT_GRAY,
                            weight=ft.FontWeight.BOLD if venda.get("turno_id") else ft.FontWeight.W_400,
                        ),
                        width=HistoricoVendasCols.TURNO, alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        ft.Text(
                            venda.get("usuario_nome") or
                            (venda.get("usuario", {}).get("nome") if isinstance(venda.get("usuario"), dict) else None) or
                            venda.get("vendedor") or "—",
                            size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY,
                        ),
                        width=HistoricoVendasCols.VENDEDOR, alignment=ft.alignment.center,
                    ),
                    ft.Container(btn_menu, width=HistoricoVendasCols.ACOES, alignment=ft.alignment.center),
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

        vendas = sorted(VendasAPI.listar_vendas(), key=lambda v: v.get("id", 0))

        # Monta mapa id → nome para injetar usuario_nome nas vendas que vierem None
        try:
            usuarios = UsuariosAPI.listar_usuarios() or []
            mapa_usuarios = {u.get("id"): u.get("nome") or u.get("username") for u in usuarios}
        except Exception:
            mapa_usuarios = {}

        for v in vendas:
            if not v.get("usuario_nome"):
                uid = v.get("usuario_id")
                if uid and uid in mapa_usuarios:
                    v["usuario_nome"] = mapa_usuarios[uid]

        todas_vendas = vendas
        aplicar_filtros()

    # ============================================================================
    # COMPONENTES — ABA VENDAS
    # ============================================================================

    pesquisa_input = Styles.text_field("Pesquisar por ID ou vendedor", Sizes.INPUT_XLARGE)
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
        ("ID",          HistoricoVendasCols.ID),
        ("Data",        HistoricoVendasCols.DATA),
        ("Hora",        HistoricoVendasCols.HORA),
        ("Valor Total", HistoricoVendasCols.TOTAL),
        ("Pagamento",   HistoricoVendasCols.PAGAMENTO),
        ("Status",      HistoricoVendasCols.STATUS),
        ("Turno",       HistoricoVendasCols.TURNO),
        ("Vendedor",    HistoricoVendasCols.VENDEDOR),
        ("Ações",       HistoricoVendasCols.ACOES),
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

    aba_vendas = ft.Container(
        content=ft.Column(
            controls=[top_section, table_container],
            spacing=0, expand=True,
        ),
        expand=True,
        padding=Sizes.SPACING_LARGE,
        visible=True,
    )

    # ============================================================================
    # ABA TURNOS
    # ============================================================================

    turnos_list = ft.Column(controls=[], spacing=0, scroll=ft.ScrollMode.AUTO)

    turnos_header = Styles.table_header([
        ("#",           HistoricoTurnosCols.ID),
        ("Usuário",     HistoricoTurnosCols.USUARIO),
        ("Abertura",    HistoricoTurnosCols.ABERTURA),
        ("Fechamento",  HistoricoTurnosCols.FECHAMENTO),
        ("Vendas",      HistoricoTurnosCols.VENDAS),
        ("Total",       HistoricoTurnosCols.TOTAL),
        ("Esperado",    HistoricoTurnosCols.ESPERADO),
        ("Informado",   HistoricoTurnosCols.INFORMADO),
        ("Diferença",   HistoricoTurnosCols.DIFERENCA),
        ("Status",      HistoricoTurnosCols.STATUS),
    ])

    def fmt_dt(data_str):
        if not data_str:
            return "—"
        try:
            dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            dt_local = dt + _UTC_OFFSET
            return dt_local.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return data_str[:16] if len(data_str) >= 16 else data_str

    def criar_linha_turno(turno):
        status = (turno.get("status") or "").upper()
        cor_status = Colors.BRAND_GREEN if status == "FECHADO" else Colors.BRAND_ORANGE
        label_status = "Fechado" if status == "FECHADO" else "Aberto"

        diferenca = turno.get("diferenca")
        if diferenca is not None:
            cor_dif = Colors.BRAND_GREEN if diferenca >= 0 else Colors.BRAND_RED
            sinal   = "+" if diferenca >= 0 else ""
            txt_dif = f"{sinal}R$ {abs(diferenca):.2f}"
        else:
            cor_dif = Colors.TEXT_GRAY
            txt_dif = "—"

        def ver_detalhes(e, t=turno):
            modal_detalhe_turno(t)

        # Nome do usuário — campo usuario_nome quando back implementar
        _u = turno.get("usuario")
        usuario_nome = (
            turno.get("usuario_nome") or
            (_u.get("nome") if isinstance(_u, dict) else None) or
            "—"
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(ft.Text(str(turno.get("id", "")),                              size=Sizes.FONT_SMALL), width=HistoricoTurnosCols.ID,         alignment=ft.alignment.center),
                    ft.Container(ft.Text(usuario_nome,                                          size=Sizes.FONT_SMALL, color=Colors.BRAND_BLUE, weight=ft.FontWeight.BOLD), width=HistoricoTurnosCols.USUARIO, alignment=ft.alignment.center),
                    ft.Container(ft.Text(fmt_dt(turno.get("data_abertura")),                    size=Sizes.FONT_SMALL), width=HistoricoTurnosCols.ABERTURA,   alignment=ft.alignment.center),
                    ft.Container(ft.Text(fmt_dt(turno.get("data_fechamento")),                  size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY), width=HistoricoTurnosCols.FECHAMENTO, alignment=ft.alignment.center),
                    ft.Container(ft.Text(str(turno.get("quantidade_vendas", 0)),                size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD), width=HistoricoTurnosCols.VENDAS,    alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {float(turno.get('total_vendas', 0)):.2f}",      size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=Colors.BRAND_GREEN), width=HistoricoTurnosCols.TOTAL,     alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {float(turno.get('valor_esperado') or 0):.2f}",  size=Sizes.FONT_SMALL), width=HistoricoTurnosCols.ESPERADO,   alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"R$ {float(turno.get('valor_informado') or 0):.2f}", size=Sizes.FONT_SMALL), width=HistoricoTurnosCols.INFORMADO,  alignment=ft.alignment.center),
                    ft.Container(ft.Text(txt_dif,                                               size=Sizes.FONT_SMALL, weight=ft.FontWeight.BOLD, color=cor_dif), width=HistoricoTurnosCols.DIFERENCA,  alignment=ft.alignment.center),
                    ft.Container(
                        content=ft.Container(
                            content=ft.Text(label_status, size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                            bgcolor=cor_status, border_radius=12,
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        ),
                        width=HistoricoTurnosCols.STATUS,    alignment=ft.alignment.center,
                    ),
                ],
                spacing=0,
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            bgcolor=Colors.BG_WHITE,
            ink=True,
            on_click=ver_detalhes,
        )

    def modal_detalhe_turno(turno):
        turno_id = turno.get("id")
        _u = turno.get("usuario")
        usuario_nome = (
            turno.get("usuario_nome") or
            (_u.get("nome") if isinstance(_u, dict) else None) or
            "—"
        )
        diferenca = turno.get("diferenca")
        cor_dif = Colors.BRAND_GREEN if (diferenca or 0) >= 0 else Colors.BRAND_RED
        sinal   = "+" if (diferenca or 0) >= 0 else ""

        # Busca por_forma_pagamento calculando a partir das vendas do turno
        # O historico pode não retornar esse campo — calculamos via vendas
        fp = turno.get("por_forma_pagamento") or {}

        # Se fp está vazio, tenta calcular a partir das vendas do histórico
        if not any(fp.values()) if fp else True:
            try:
                todas = VendasAPI.listar_vendas() or []
                vendas_turno = [v for v in todas if v.get("turno_id") == turno_id
                                and (v.get("status") or "").upper() == "CONCLUIDA"]
                mapa = {
                    "DINHEIRO":      "Dinheiro",
                    "CARTAO_DEBITO": "Cartão Débito",
                    "CARTAO_CREDITO":"Cartão Crédito",
                    "PIX":           "Pix",
                }
                fp = {"Dinheiro": 0.0, "Cartão Débito": 0.0, "Cartão Crédito": 0.0, "Pix": 0.0}
                for v in vendas_turno:
                    pg = v.get("forma_pagamento")
                    if isinstance(pg, dict):
                        tipo = (pg.get("tipo") or "").upper()
                        chave = mapa.get(tipo)
                        if chave:
                            fp[chave] += float(v.get("total") or 0)
            except Exception:
                pass

        def fechar(e):
            modal.open = False
            page.update()

        def imprimir(e):
            modal.open = False
            page.update()

            def _print():
                sucesso, msg = imprimir_resumo_turno(
                    turno_id=turno_id,
                    usuario=usuario_nome,
                    abertura=fmt_dt(turno.get("data_abertura")),
                    fechamento=fmt_dt(turno.get("data_fechamento")),
                    qtd_vendas=turno.get("quantidade_vendas", 0),
                    total_vendas=float(turno.get("total_vendas", 0)),
                    por_forma=fp,
                    valor_inicial=float(turno.get("valor_inicial", 0)),
                    valor_esperado=float(turno.get("valor_esperado") or 0),
                    valor_informado=float(turno.get("valor_informado") or 0),
                    diferenca=float(diferenca or 0),
                    observacoes=turno.get("observacoes") or "",
                )
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(msg),
                    bgcolor=Colors.BRAND_GREEN if sucesso else Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()

            page.run_thread(_print)

        def linha(label, valor, cor=Colors.TEXT_BLACK, bold=False):
            return ft.Row([
                ft.Text(label, size=13, color=Colors.TEXT_GRAY, expand=True),
                ft.Text(valor, size=13, color=cor, weight=ft.FontWeight.BOLD if bold else ft.FontWeight.W_400),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.PUNCH_CLOCK, color=Colors.TEXT_WHITE, size=22),
                    ft.Text(f"Turno #{turno_id}", size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_BLUE,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    tight=True, spacing=6, scroll=ft.ScrollMode.AUTO, height=400,
                    controls=[
                        ft.Container(height=8),
                        ft.Text("PERÍODO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                        linha("Usuário",    usuario_nome, Colors.BRAND_BLUE, bold=True),
                        linha("Abertura",   fmt_dt(turno.get("data_abertura"))),
                        linha("Fechamento", fmt_dt(turno.get("data_fechamento"))),
                        ft.Divider(height=12),
                        ft.Text("VENDAS", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                        linha("Quantidade de vendas", str(turno.get("quantidade_vendas", 0))),
                        linha("Total faturado", f"R$ {float(turno.get('total_vendas', 0)):.2f}", Colors.BRAND_GREEN, bold=True),
                        ft.Divider(height=12),
                        ft.Text("POR FORMA DE PAGAMENTO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                        linha("💵 Dinheiro",       f"R$ {float(fp.get('Dinheiro', 0)):.2f}"),
                        linha("💳 Cartão Débito",  f"R$ {float(fp.get('Cartão Débito', 0)):.2f}"),
                        linha("💳 Cartão Crédito", f"R$ {float(fp.get('Cartão Crédito', 0)):.2f}"),
                        linha("📱 Pix",            f"R$ {float(fp.get('Pix', 0)):.2f}"),
                        ft.Divider(height=12),
                        ft.Text("CONFERÊNCIA DE CAIXA", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                        linha("Valor inicial",   f"R$ {float(turno.get('valor_inicial', 0)):.2f}"),
                        linha("Valor esperado",  f"R$ {float(turno.get('valor_esperado') or 0):.2f}", Colors.TEXT_BLACK, bold=True),
                        linha("Valor informado", f"R$ {float(turno.get('valor_informado') or 0):.2f}"),
                        ft.Container(
                            content=linha("Diferença", f"{sinal}R$ {abs(diferenca or 0):.2f}", cor_dif, bold=True),
                            bgcolor="#F5F5F5", padding=ft.padding.symmetric(horizontal=12, vertical=8), border_radius=8,
                        ),
                        *([] if not turno.get("observacoes") else [
                            ft.Divider(height=8),
                            ft.Text("Observações:", size=12, color=Colors.TEXT_GRAY),
                            ft.Text(turno.get("observacoes", ""), size=12, italic=True),
                        ]),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Fechar", on_click=fechar),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.icons.PRINT, size=16, color=Colors.TEXT_WHITE),
                        ft.Text("Imprimir", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
                    ], spacing=6, tight=True),
                    bgcolor=Colors.BRAND_BLUE, color=Colors.TEXT_WHITE,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=imprimir,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.clear()
        page.overlay.append(modal)
        modal.open = True
        page.update()

    def carregar_turnos():
        turnos_list.controls.clear()
        turnos_list.controls.append(
            ft.Container(
                content=ft.Row([ft.ProgressRing(width=24, height=24), ft.Text("Carregando turnos...")],
                               alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                padding=40, alignment=ft.alignment.center,
            )
        )
        page.update()

        historico = TurnoAPI.historico_todos()

        turnos_list.controls.clear()
        if not historico:
            turnos_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.PUNCH_CLOCK, size=60, color=Colors.TEXT_GRAY),
                        ft.Text("Nenhum turno registrado", size=Sizes.FONT_LARGE, color=Colors.TEXT_GRAY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=50, alignment=ft.alignment.center,
                )
            )
        else:
            for t in sorted(historico, key=lambda x: x.get("id", 0), reverse=True):
                turnos_list.controls.append(criar_linha_turno(t))
        page.update()

    aba_turnos = ft.Container(
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column([
                        turnos_header,
                        ft.Container(
                            content=turnos_list,
                            expand=True,
                            border=ft.border.all(1, Colors.BORDER_BLACK),
                            bgcolor=Colors.BG_WHITE,
                        ),
                    ], spacing=0),
                    expand=True,
                    margin=ft.margin.only(top=Sizes.SPACING_LARGE),
                ),
            ],
            spacing=0, expand=True,
        ),
        expand=True,
        padding=Sizes.SPACING_LARGE,
        visible=False,
    )

    # ============================================================================
    # TABS — alternância entre Vendas e Turnos
    # ============================================================================
    aba_atual = {"valor": "vendas"}

    def btn_aba(label, valor, icone):
        selecionado = aba_atual["valor"] == valor
        def selecionar(e):
            aba_atual["valor"] = valor
            rebuild_tabs()
            aba_vendas.visible  = valor == "vendas"
            aba_turnos.visible  = valor == "turnos"
            if valor == "turnos":
                carregar_turnos()
            aba_vendas.update()
            aba_turnos.update()
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, size=16, color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_GRAY),
                ft.Text(label, size=14,
                        weight=ft.FontWeight.BOLD if selecionado else ft.FontWeight.W_400,
                        color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_BLACK),
            ], spacing=8, tight=True),
            bgcolor=Colors.BRAND_RED if selecionado else Colors.BG_WHITE,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            ink=True, on_click=selecionar,
            border=ft.border.all(1, Colors.BORDER_LIGHT if not selecionado else Colors.BRAND_RED),
        )

    tabs_row = ft.Row(spacing=8)

    def rebuild_tabs():
        tabs_row.controls = [
            btn_aba("Vendas",  "vendas",  ft.icons.RECEIPT_LONG),
            btn_aba("Turnos",  "turnos",  ft.icons.PUNCH_CLOCK),
        ]
        try: tabs_row.update()
        except Exception: pass

    tabs_row.controls = [
        btn_aba("Vendas",  "vendas",  ft.icons.RECEIPT_LONG),
        btn_aba("Turnos",  "turnos",  ft.icons.PUNCH_CLOCK),
    ]

    btn_sair = Styles.button_danger("Menu Principal", ft.icons.HOME, lambda _: page.go("/"))

    def btn_aba_sidebar(label, valor, icone):
        selecionado = aba_atual["valor"] == valor
        def selecionar(e):
            aba_atual["valor"] = valor
            rebuild_tabs()
            aba_vendas.visible = valor == "vendas"
            aba_turnos.visible = valor == "turnos"
            if valor == "turnos":
                carregar_turnos()
            try:
                aba_vendas.update()
                aba_turnos.update()
            except Exception:
                pass
        return ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(icone, size=18, color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_GRAY),
                ft.Text(label, size=14,
                        weight=ft.FontWeight.BOLD if selecionado else ft.FontWeight.W_400,
                        color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_BLACK,
                        no_wrap=True),
            ], spacing=8, tight=True),
            bgcolor=Colors.BRAND_RED if selecionado else "#F5F5F5",
            width=Sizes.BUTTON_WIDTH,
            height=Sizes.BUTTON_HEIGHT,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE),
                side=ft.BorderSide(1, Colors.BORDER_LIGHT if not selecionado else Colors.BRAND_RED),
            ),
            on_click=selecionar,
        )

    btn_tab_vendas = btn_aba_sidebar("Vendas",  "vendas", ft.icons.RECEIPT_LONG)
    btn_tab_turnos = btn_aba_sidebar("Turnos",  "turnos", ft.icons.PUNCH_CLOCK)

    sidebar_tabs = [btn_tab_vendas, btn_tab_turnos]

    def rebuild_tabs():
        # Atualiza aparência dos botões da sidebar
        for btn, valor in [(btn_tab_vendas, "vendas"), (btn_tab_turnos, "turnos")]:
            selecionado = aba_atual["valor"] == valor
            btn.bgcolor = Colors.BRAND_RED if selecionado else "#F5F5F5"
            btn.content.controls[0].color = Colors.TEXT_WHITE if selecionado else Colors.TEXT_GRAY
            btn.content.controls[1].color = Colors.TEXT_WHITE if selecionado else Colors.TEXT_BLACK
            btn.content.controls[1].weight = ft.FontWeight.BOLD if selecionado else ft.FontWeight.W_400
            try: btn.update()
            except Exception: pass

    sidebar = Styles.sidebar([
        btn_tab_vendas,
        btn_tab_turnos,
        ft.Container(expand=True),
        btn_sair,
    ])

    main_content = ft.Container(
        content=ft.Column(
            controls=[
                ft.Stack(controls=[aba_vendas, aba_turnos], expand=True),
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=Colors.BG_WHITE,
    )

    carregar_vendas()

    return ft.Row(
        controls=[main_content, sidebar],
        spacing=0,
        expand=True,
    )