import flet as ft
from datetime import datetime
from app.views.styles.theme import Colors, Sizes, Styles
from app.api.vendas_api import VendasAPI
from app.api.turno_api import TurnoAPI
from app.api.auth_api import get_username
from app.utils import connectivity  # ← badge online/offline

def HomeView(page: ft.Page):
    """Tela principal do PDV Santa Ana"""

    turno = {
        "aberto":        False,
        "turno_id":      None,
        "valor_inicial": 0.0,
        "hora_abertura": None,
    }

    def sincronizar_turno():
        """Verifica no back se há turno ativo e sincroniza o estado"""
        try:
            ativo = TurnoAPI.get_turno_ativo()
            if ativo:
                turno["aberto"]        = True
                turno["turno_id"]      = ativo.get("id")
                turno["valor_inicial"] = float(ativo.get("valor_inicial", 0))
                # Converte data_abertura para hora local
                from datetime import timedelta
                data_str = ativo.get("data_abertura", "")
                try:
                    from datetime import timezone
                    dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
                    dt_local = dt + timedelta(hours=-3)
                    turno["hora_abertura"] = dt_local.strftime("%H:%M")
                except Exception:
                    data_str = data_str or ""
                    turno["hora_abertura"] = data_str[11:16] if len(data_str) > 10 else "—"
            else:
                turno["aberto"]   = False
                turno["turno_id"] = None
        except Exception as ex:
            print(f"[Home] Erro ao sincronizar turno: {ex}")

    # =========================================================================
    # INDICADOR DE TURNO NO FOOTER (referência mutável)
    # =========================================================================
    indicador_turno = ft.Row(
        controls=[
            ft.Container(
                width=10, height=10,
                bgcolor=Colors.BRAND_RED,
                border_radius=5,
            ),
            ft.Text("Turno: Fechado", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.W_400, color=Colors.TEXT_BLACK),
        ],
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def atualizar_indicador():
        dot   = indicador_turno.controls[0]
        label = indicador_turno.controls[1]
        if turno["aberto"]:
            dot.bgcolor   = Colors.BRAND_GREEN
            label.value   = f"Turno: Aberto  ({turno['hora_abertura']})"
            label.color   = Colors.BRAND_GREEN
            label.weight  = ft.FontWeight.BOLD
        else:
            dot.bgcolor   = Colors.BRAND_RED
            label.value   = "Turno: Fechado"
            label.color   = Colors.TEXT_BLACK
            label.weight  = ft.FontWeight.W_400
        try:
            indicador_turno.update()
        except Exception:
            pass  # Ainda não está na página

    # =========================================================================
    # BADGE ONLINE / OFFLINE NO FOOTER
    # =========================================================================
    _badge_dot = ft.Container(
        width=10, height=10,
        bgcolor=Colors.BRAND_GREEN,
        border_radius=5,
    )
    _badge_txt = ft.Text(
        "Online",
        size=Sizes.FONT_MEDIUM,
        weight=ft.FontWeight.W_400,
        color=Colors.BRAND_GREEN,
    )
    indicador_conexao = ft.Row(
        controls=[_badge_dot, _badge_txt],
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def _atualizar_badge_conexao():
        """Atualiza o badge sem causar crash se o widget não estiver na página."""
        online = connectivity.esta_online()
        _badge_dot.bgcolor = Colors.BRAND_GREEN if online else Colors.BRAND_RED
        _badge_txt.value   = "Online" if online else "Offline"
        _badge_txt.color   = Colors.BRAND_GREEN if online else Colors.BRAND_RED
        _badge_txt.weight  = ft.FontWeight.W_400 if online else ft.FontWeight.BOLD
        try:
            indicador_conexao.update()
        except Exception:
            pass

    # Registra callbacks do monitor de conectividade para atualizar o badge
    connectivity.ao_voltar_online(_atualizar_badge_conexao)
    connectivity.ao_ficar_offline(_atualizar_badge_conexao)

    def atualizar_botao_turno():
        """Troca ícone/texto do botão de turno no header"""
        if turno["aberto"]:
            btn_turno_ref.content.controls[0].name  = ft.icons.TIMER_OFF
            btn_turno_ref.content.controls[1].value = "Fechar Turno - F3"
            btn_turno_ref.bgcolor                   = Colors.BRAND_ORANGE
        else:
            btn_turno_ref.content.controls[0].name  = ft.icons.PUNCH_CLOCK
            btn_turno_ref.content.controls[1].value = "Abrir Turno - F3"
            btn_turno_ref.bgcolor                   = Colors.BRAND_RED
        try:
            btn_turno_ref.update()
        except Exception:
            pass  # Ainda não está na página

    # =========================================================================
    # MODAL ABRIR TURNO
    # =========================================================================
    def abrir_turno_modal(e):
        if turno["aberto"]:
            fechar_turno_modal(e)
            return

        valor_input = Styles.text_field(
            "Valor inicial do caixa (R$)", 300,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="R$ ",
        )

        def confirmar(e):
            if not valor_input.value or not valor_input.value.strip():
                valor_input.border_color = Colors.BRAND_RED
                valor_input.error_text   = "Obrigatório"
                page.update()
                return
            try:
                val = float(valor_input.value.replace(",", "."))
            except ValueError:
                valor_input.border_color = Colors.BRAND_RED
                valor_input.error_text   = "Valor inválido"
                page.update()
                return

            resultado = TurnoAPI.abrir_turno(val)
            if not resultado:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Erro ao abrir turno! Tente novamente."),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()
                return

            turno["aberto"]        = True
            turno["turno_id"]      = resultado.get("id")
            turno["valor_inicial"] = val
            turno["hora_abertura"] = datetime.now().strftime("%H:%M")

            modal.open = False
            atualizar_indicador()
            atualizar_botao_turno()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✓ Turno aberto com R$ {val:.2f}"),
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
            title=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.PUNCH_CLOCK, color=Colors.TEXT_WHITE, size=22),
                    ft.Text("Abrir Turno", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_GREEN,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            content=ft.Container(
                width=380,
                content=ft.Column(
                    tight=True, spacing=14,
                    controls=[
                        ft.Container(height=4),
                        ft.Row([
                            ft.Icon(ft.icons.CALENDAR_TODAY, size=16, color=Colors.TEXT_GRAY),
                            ft.Text(datetime.now().strftime("%d/%m/%Y"), size=Sizes.FONT_MEDIUM, color=Colors.TEXT_GRAY),
                            ft.Container(width=16),
                            ft.Icon(ft.icons.ACCESS_TIME, size=16, color=Colors.TEXT_GRAY),
                            ft.Text(datetime.now().strftime("%H:%M:%S"), size=Sizes.FONT_MEDIUM, color=Colors.TEXT_GRAY),
                        ], spacing=6),
                        ft.Divider(height=1),
                        valor_input,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Confirmar Abertura",
                    bgcolor=Colors.BRAND_GREEN, color=Colors.TEXT_WHITE,
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

    # =========================================================================
    # MODAL FECHAR TURNO
    # =========================================================================
    def fechar_turno_modal(e):
        if not turno["aberto"]:
            return

        hora_fechamento = datetime.now().strftime("%H:%M")

        # Busca vendas do turno atual — filtra por turno_id e status CONCLUIDA
        try:
            todas_vendas = VendasAPI.listar_vendas() or []
            vendas_turno = [
                v for v in todas_vendas
                if (v.get("status") or "").upper() == "CONCLUIDA"
                and v.get("turno_id") == turno["turno_id"]
            ]
        except Exception:
            vendas_turno = []

        # Calcula totais por forma de pagamento
        totais = {"DINHEIRO": 0.0, "CARTAO_DEBITO": 0.0, "CARTAO_CREDITO": 0.0, "PIX": 0.0}
        total_geral = 0.0
        for v in vendas_turno:
            fp = v.get("forma_pagamento")
            if fp:
                tipo = (fp.get("tipo") or "").upper()
                val  = float(fp.get("valor_recebido") or 0)
                if tipo in totais:
                    totais[tipo] += val
            total_geral += float(v.get("total") or 0)

        valor_input = Styles.text_field(
            "Valor em caixa no fechamento (R$)", 340,
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="R$ ",
        )
        obs_input = ft.TextField(
            label="Observações (opcional)",
            width=340,
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=Colors.BORDER_GRAY,
        )

        def confirmar(e):
            if not valor_input.value or not valor_input.value.strip():
                valor_input.border_color = Colors.BRAND_RED
                valor_input.error_text   = "Obrigatório"
                page.update()
                return
            try:
                val_final = float(valor_input.value.replace(",", "."))
            except ValueError:
                valor_input.border_color = Colors.BRAND_RED
                valor_input.error_text   = "Valor inválido"
                page.update()
                return

            # Fecha turno no back
            resultado_fechamento = TurnoAPI.fechar_turno(
                valor_informado=val_final,
                observacoes=obs_input.value.strip() if obs_input.value else None,
            )
            if not resultado_fechamento:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Erro ao fechar turno! Tente novamente."),
                    bgcolor=Colors.BRAND_RED,
                )
                page.snack_bar.open = True
                page.update()
                return

            # Usa dados reais do back se disponíveis
            total_faturado = resultado_fechamento.get("total_vendas", sum(totais.values()))
            esperado       = resultado_fechamento.get("valor_esperado", turno["valor_inicial"] + total_faturado)
            diferenca      = resultado_fechamento.get("diferenca", val_final - esperado)
            sinal     = "+" if diferenca >= 0 else ""
            cor_dif   = Colors.BRAND_GREEN if diferenca >= 0 else Colors.BRAND_RED

            turno["aberto"] = False
            modal.open = False

            obs_text = obs_input.value.strip() if obs_input.value else ""

            def linha(label, valor, cor=Colors.TEXT_BLACK, bold=False):
                return _resumo_linha(label, valor, cor, bold)

            resumo_controls = [
                ft.Container(height=8),
                # Período
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.ACCESS_TIME, size=14, color=Colors.TEXT_GRAY),
                        ft.Text(f"Abertura: {turno['hora_abertura']}  →  Fechamento: {hora_fechamento}",
                                size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY),
                    ], spacing=6),
                    bgcolor="#F5F5F5", padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=8,
                ),
                ft.Container(height=4),
                # Vendas do turno
                ft.Text("FATURAMENTO DO TURNO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                ft.Container(height=2),
                linha(f"Total de vendas ({len(vendas_turno)})", f"R$ {total_geral:.2f}", Colors.BRAND_GREEN, bold=True),
                ft.Divider(height=12),
                # Por forma de pagamento
                ft.Text("POR FORMA DE PAGAMENTO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                ft.Container(height=2),
                linha("💵  Dinheiro",       f"R$ {totais['DINHEIRO']:.2f}"),
                linha("💳  Cartão Débito",  f"R$ {totais['CARTAO_DEBITO']:.2f}"),
                linha("💳  Cartão Crédito", f"R$ {totais['CARTAO_CREDITO']:.2f}"),
                linha("📱  Pix",            f"R$ {totais['PIX']:.2f}"),
                ft.Divider(height=12),
                # Conferência de caixa
                ft.Text("CONFERÊNCIA DE CAIXA", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                ft.Container(height=2),
                linha("Valor inicial",  f"R$ {turno['valor_inicial']:.2f}"),
                linha("(+) Total faturado", f"R$ {total_faturado:.2f}"),
                linha("Esperado em caixa", f"R$ {esperado:.2f}", Colors.TEXT_BLACK, bold=True),
                linha("Informado pelo operador", f"R$ {val_final:.2f}"),
                ft.Container(
                    content=linha("Diferença", f"{sinal}R$ {abs(diferenca):.2f}", cor_dif, bold=True),
                    bgcolor="#F5F5F5",
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border_radius=8,
                ),
            ]

            if obs_text:
                resumo_controls += [
                    ft.Container(height=4),
                    ft.Text("Observações:", size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY),
                    ft.Text(obs_text, size=Sizes.FONT_SMALL, italic=True),
                ]

            resumo = ft.AlertDialog(
                modal=True,
                shape=ft.RoundedRectangleBorder(radius=12),
                title=ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.TIMER_OFF, color=Colors.TEXT_WHITE, size=22),
                        ft.Text("Resumo do Turno", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                    ], spacing=8),
                    bgcolor=Colors.BRAND_ORANGE,
                    padding=ft.padding.symmetric(horizontal=20, vertical=16),
                    border_radius=ft.border_radius.only(top_left=10, top_right=10),
                    margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
                ),
                content=ft.Container(
                    width=420,
                    content=ft.Column(
                        tight=True, spacing=4,
                        scroll=ft.ScrollMode.AUTO,
                        controls=resumo_controls,
                        height=400,
                    ),
                ),
                actions=[
                    ft.ElevatedButton(
                        "Fechar",
                        bgcolor=Colors.BRAND_RED, color=Colors.TEXT_WHITE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        on_click=lambda _: fechar_resumo(),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.CENTER,
            )

            def fechar_resumo():
                resumo.open = False
                turno["aberto"]   = False
                turno["turno_id"] = None
                atualizar_indicador()
                atualizar_botao_turno()
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Turno fechado com sucesso!"),
                    bgcolor=Colors.BRAND_ORANGE,
                )
                page.snack_bar.open = True
                page.update()

            page.overlay.clear()
            page.overlay.append(resumo)
            resumo.open = True
            page.update()

        def cancelar(e):
            modal.open = False
            page.update()

        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.TIMER_OFF, color=Colors.TEXT_WHITE, size=22),
                    ft.Text("Fechar Turno", size=Sizes.FONT_XLARGE, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_ORANGE,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    tight=True, spacing=14,
                    controls=[
                        ft.Container(height=4),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.INFO_OUTLINE, size=16, color=Colors.BRAND_ORANGE),
                                ft.Text(
                                    f"Aberto às {turno['hora_abertura']}  •  Caixa inicial: R$ {turno['valor_inicial']:.2f}  •  {len(vendas_turno)} venda(s)",
                                    size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY,
                                ),
                            ], spacing=6),
                            bgcolor="#FFF8F0",
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            border_radius=8,
                            border=ft.border.all(1, "#FFE0B2"),
                        ),
                        ft.Divider(height=1),
                        valor_input,
                        obs_input,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton(
                    "Confirmar Fechamento",
                    bgcolor=Colors.BRAND_ORANGE, color=Colors.TEXT_WHITE,
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

    # =========================================================================
    # HELPER LINHA DO RESUMO
    # =========================================================================
    def _resumo_linha(label, valor, cor_valor, bold=False):
        return ft.Row(
            controls=[
                ft.Text(label, size=Sizes.FONT_SMALL, color=Colors.TEXT_GRAY, expand=True),
                ft.Text(
                    valor, size=Sizes.FONT_SMALL, color=cor_valor,
                    weight=ft.FontWeight.BOLD if bold else ft.FontWeight.W_400,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    # =========================================================================
    # BOTÕES DE NAVEGAÇÃO
    # =========================================================================
    def _navegar(route):
        """Limpa o handler de teclado antes de navegar para evitar atalhos vazando."""
        page.on_keyboard_event = None
        page.go(route)

    def nav_button(text, icon, route=None, on_click_custom=None, shortcut=""):
        def on_click(e):
            if on_click_custom:
                on_click_custom(e)
            elif route:
                _navegar(route)

        label = f"{text} - {shortcut}" if shortcut else text
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, color=Colors.TEXT_WHITE, size=34),
                    ft.Text(
                        label,
                        color=Colors.TEXT_WHITE,
                        weight=ft.FontWeight.BOLD,
                        size=15,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
            bgcolor=Colors.BRAND_RED,
            width=190,
            height=100,
            border_radius=Sizes.BORDER_RADIUS_XLARGE,
            ink=True,
            on_click=on_click,
        )

    # Botão de turno com referência mutável
    btn_turno_ref = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.icons.PUNCH_CLOCK, color=Colors.TEXT_WHITE, size=34),
                ft.Text(
                    "Abrir Turno - F3",
                    color=Colors.TEXT_WHITE,
                    weight=ft.FontWeight.BOLD,
                    size=15,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
        bgcolor=Colors.BRAND_RED,
        width=190,
        height=100,
        border_radius=Sizes.BORDER_RADIUS_XLARGE,
        ink=True,
        on_click=abrir_turno_modal,
    )

    header = ft.Container(
        content=ft.Row(
            controls=[
                nav_button("Vendas",      ft.icons.SHOPPING_BAG, route="/vendas",      shortcut="F1"),
                nav_button("Estoque",     ft.icons.INVENTORY_2,  route="/estoque",     shortcut="F2"),
                btn_turno_ref,
                nav_button("Relatórios",  ft.icons.BAR_CHART,    route="/relatorios",  shortcut="F4"),
                nav_button("Usuários",    ft.icons.PEOPLE,       route="/usuarios",    shortcut="F5"),
                nav_button("Histórico",   ft.icons.HISTORY,      route="/historico",   shortcut="F6"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=Sizes.SPACING_LARGE,
        ),
        padding=ft.padding.only(top=40, bottom=30, left=Sizes.SPACING_LARGE, right=Sizes.SPACING_LARGE),
        border=ft.border.only(bottom=ft.BorderSide(2, Colors.BORDER_MEDIUM)),
    )

    body = ft.Container(
        content=ft.Image(
            src="views/assets/logo_santa_ana.png",
            width=450,
            fit=ft.ImageFit.CONTAIN,
        ),
        expand=True,
        alignment=ft.alignment.center,
    )

    footer = ft.Container(
        content=ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(f"Usuário: {get_username() or '—'}", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.W_400, color=Colors.TEXT_BLACK),
                        ft.Text(f"Data: {datetime.now().strftime('%d/%m/%Y')}", size=Sizes.FONT_MEDIUM, weight=ft.FontWeight.W_400, color=Colors.TEXT_BLACK),
                        indicador_turno,
                        indicador_conexao,  # ← badge online/offline
                    ],
                    spacing=Sizes.SPACING_XLARGE,
                ),
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.icons.LOGOUT, size=Sizes.ICON_SMALL, color=Colors.TEXT_WHITE),
                            ft.Text("Sair - F12", size=Sizes.FONT_MEDIUM, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=Sizes.SPACING_MEDIUM,
                    ),
                    bgcolor=Colors.BRAND_RED,
                    color=Colors.TEXT_WHITE,
                    height=50,
                    width=160,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_MEDIUM)),
                    on_click=lambda e: (setattr(page, "on_keyboard_event", None), page.confirmar_saida(e)),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(horizontal=Sizes.SPACING_XLARGE, vertical=25),
        border=ft.border.only(top=ft.BorderSide(2, Colors.BORDER_MEDIUM)),
    )


    # =========================================================================
    # ATALHOS DE TECLADO — HOME
    # F1  Vendas        F2  Estoque     F3  Abrir/Fechar Turno
    # F4  Relatórios    F5  Usuários    F6  Histórico
    # F12 Sair (logout)
    # =========================================================================
    def _on_keyboard(e: ft.KeyboardEvent):
        if page.route != "/":
            return
        k = e.key
        if k == "F1":
            page.go("/vendas")
        elif k == "F2":
            page.go("/estoque")
        elif k == "F3":
            abrir_turno_modal(None)
        elif k == "F4":
            page.go("/relatorios")
        elif k == "F5":
            page.go("/usuarios")
        elif k == "F6":
            page.go("/historico")
        elif k == "F12":
            try:
                page.confirmar_saida(None)
            except Exception:
                pass

    page.on_keyboard_event = _on_keyboard

    def inicializar(e=None):
        sincronizar_turno()
        atualizar_indicador()
        atualizar_botao_turno()
        _atualizar_badge_conexao()  # ← estado inicial do badge
        try: page.update()
        except Exception: pass

    # Agenda sincronização após a view estar na página
    page.run_thread(inicializar)

    return ft.Container(
        content=ft.Column(
            controls=[header, body, footer],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=Colors.BG_WHITE,
    )