import flet as ft
from datetime import datetime
from app.views.styles.theme import Colors, Sizes, Styles
from app.api.relatorio_api import RelatorioAPI
from app.api.movimentacao_api import MovimentacaoAPI
from app.api.produtos_api import ProdutosAPI


def RelatoriosView(page: ft.Page):
    """Tela de Relatórios - PDV Santa Ana"""

    from datetime import date, timedelta
    _hoje = date.today()
    estado = {
        "tipo":         "vendas",
        "periodo":      "hoje",
        "data_inicio":  _hoje.strftime("%d/%m/%Y"),
        "data_fim":     _hoje.strftime("%d/%m/%Y"),
        "pode_exportar": False,
        "_dados_cache": None,   # guarda último resultado de gerar_relatorio_real
    }

    # =========================================================================
    # HELPERS DE UI
    # =========================================================================
    def card_metrica(icone, label, valor, cor, bgcolor_card):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Container(
                    content=ft.Icon(icone, color=Colors.TEXT_WHITE, size=22),
                    bgcolor=cor, border_radius=8, padding=8,
                )]),
                ft.Container(height=10),
                ft.Text(valor, size=22, weight=ft.FontWeight.BOLD, color=cor),
                ft.Text(label, size=12, color=Colors.TEXT_GRAY),
            ], spacing=2),
            bgcolor=bgcolor_card, border_radius=12, padding=20,
            border=ft.border.all(1, Colors.BORDER_LIGHT), expand=True,
        )

    def secao_titulo(texto, icone):
        return ft.Row([
            ft.Icon(icone, size=20, color=Colors.BRAND_RED),
            ft.Text(texto, size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_BLACK),
        ], spacing=8)

    def _header_tabela(colunas):
        return ft.Container(
            content=ft.Row([
                ft.Container(ft.Text(col, size=11, weight=ft.FontWeight.BOLD), width=w)
                for col, w in colunas
            ], spacing=0),
            bgcolor=Colors.BG_PINK_LIGHT,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
        )

    def _linha_vazia(msg="Dados carregados após gerar relatório"):
        return ft.Container(
            content=ft.Text(msg, size=12, color=Colors.TEXT_GRAY, italic=True, text_align=ft.TextAlign.CENTER),
            padding=20, alignment=ft.alignment.center,
        )

    def _linha_ranking(pos, nome, categoria, qtd, cor):
        icones_pos = {1: "🥇", 2: "🥈", 3: "🥉"}
        return ft.Container(
            content=ft.Row([
                ft.Text(icones_pos.get(pos, str(pos)), size=18, width=36),
                ft.Text(nome, size=13, expand=True),
                ft.Text(categoria, size=12, color=Colors.TEXT_GRAY, width=120),
                ft.Text(qtd, size=13, weight=ft.FontWeight.BOLD, color=cor, width=60, text_align=ft.TextAlign.RIGHT),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
        )

    def _tabela_demo(colunas, msg="Dados carregados após gerar relatório"):
        return ft.Container(
            content=ft.Column([
                _header_tabela(colunas),
                ft.Container(
                    content=_linha_vazia(msg),
                    border=ft.border.all(1, Colors.BORDER_LIGHT),
                    border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
                ),
            ], spacing=0),
        )

    def _grafico_pagamentos_demo():
        formas = [
            ("💵 Dinheiro", Colors.BRAND_GREEN),
            ("💳 Débito",   Colors.BRAND_BLUE),
            ("💳 Crédito",  "#9C27B0"),
            ("📱 Pix",      "#00BCD4"),
        ]
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(label, size=13, expand=True),
                    ft.Container(bgcolor=Colors.BORDER_LIGHT, border_radius=4, height=8, width=160),
                    ft.Text("R$ 0,00", size=12, color=Colors.TEXT_GRAY, width=80, text_align=ft.TextAlign.RIGHT),
                ], spacing=8)
                for label, cor in formas
            ], spacing=10),
            border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=10, padding=16,
        )

    # =========================================================================
    # PREVIEWS
    # =========================================================================
    preview_content = ft.Column(spacing=16, expand=True, scroll=ft.ScrollMode.AUTO)

    def preview_vendas(dados=None):
        fp = dados.get("por_forma_pagamento", {}) if dados else {}
        top = dados.get("produtos_mais_vendidos", []) if dados else []
        cores_rank = [Colors.BRAND_GREEN, Colors.BRAND_BLUE, Colors.BRAND_ORANGE]

        ranking_controls = []
        for i, p in enumerate(top[:3]):
            ranking_controls.append(
                _linha_ranking(i+1, p.get("nome","—"), "—",
                               f"{p.get('quantidade_total',0)} un.", cores_rank[i])
            )
        if not ranking_controls:
            for i in range(3):
                ranking_controls.append(_linha_ranking(i+1, "—", "—", "0 un.", cores_rank[i]))

        def fmt(v): return f"R$ {float(v):.2f}" if v is not None else "R$ 0,00"

        preview_content.controls = [
            secao_titulo("Resumo de Vendas", ft.icons.SHOPPING_BAG),
            ft.Row([
                card_metrica(ft.icons.RECEIPT_LONG,       "Total de Vendas", fmt(dados.get("total_vendas") if dados else None),   Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.NUMBERS,             "Nº Transações",  str(dados.get("num_transacoes", 0) if dados else 0),  Colors.BRAND_BLUE,   "#EFF6FF"),
                card_metrica(ft.icons.CONFIRMATION_NUMBER, "Ticket Médio",   fmt(dados.get("ticket_medio") if dados else None),    Colors.BRAND_ORANGE, "#FFF8F0"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo("Por Forma de Pagamento", ft.icons.PAYMENTS),
            ft.Row([
                card_metrica(ft.icons.MONEY,       "Dinheiro", fmt(fp.get("DINHEIRO")),      Colors.BRAND_GREEN, "#F1FFF3"),
                card_metrica(ft.icons.CREDIT_CARD, "Débito",   fmt(fp.get("CARTAO_DEBITO")), Colors.BRAND_BLUE,  "#EFF6FF"),
                card_metrica(ft.icons.CREDIT_CARD, "Crédito",  fmt(fp.get("CARTAO_CREDITO")),"#9C27B0",          "#F8F0FF"),
                card_metrica(ft.icons.PIX,         "Pix",      fmt(fp.get("PIX")),           "#00BCD4",          "#F0FCFF"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo("Produtos Mais Vendidos", ft.icons.STAR),
            ft.Container(
                content=ft.Column(ranking_controls, spacing=0),
                border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=10,
            ),
            ft.Text(
                "Dados atualizados!" if dados else "Clique em 'Gerar Relatório' para carregar os dados reais.",
                size=12, color=Colors.BRAND_GREEN if dados else Colors.TEXT_GRAY,
                italic=True, text_align=ft.TextAlign.CENTER,
            ),
        ]
        try: preview_content.update()
        except Exception: pass

    def preview_estoque(dados=None):
        filtro = estado.get("estoque_filtro", "completo")
        titulos_produto = {"completo":"Estoque Completo","ativos":"Produtos Ativos","inativos":"Produtos Inativos","baixo":"Alerta de Estoque Baixo"}
        titulos_mov     = {"mov_todas":"Todas as Movimentações","mov_entrada":"Somente Entradas","mov_saida":"Somente Saídas"}
        eh_movimentacao = filtro.startswith("mov_")

        def fmt(v): return f"R$ {float(v):.2f}" if v is not None else "R$ 0,00"

        if eh_movimentacao:
            titulo = titulos_mov.get(filtro, "Movimentações")
            # Movimentações via API
            movs = []
            if dados and isinstance(dados, dict):
                movs = dados.get("_movs", [])
            elif dados and isinstance(dados, list):
                movs = dados
            # Filtra por tipo se necessário
            tipo_mov_filtro = None
            if filtro == "mov_entrada": tipo_mov_filtro = "ENTRADA"
            elif filtro == "mov_saida":  tipo_mov_filtro = "SAIDA"
            if tipo_mov_filtro and movs:
                movs = [m for m in movs if (m.get("tipo") or "").upper() == tipo_mov_filtro]
            linhas_mov = []
            entradas = saidas = 0
            for m in movs:
                tipo = (m.get("tipo") or "").upper()
                if tipo == "ENTRADA": entradas += 1
                else: saidas += 1
                linhas_mov.append(ft.Container(
                    content=ft.Row([
                        ft.Container(ft.Text(str(m.get("id","")), size=11), width=50, alignment=ft.alignment.center),
                        ft.Container(ft.Text(m.get("_produto_nome") or str(m.get("produto_id","")), size=11), width=180),
                        ft.Container(ft.Text(tipo, size=11, color=Colors.BRAND_GREEN if tipo=="ENTRADA" else Colors.BRAND_RED, weight=ft.FontWeight.BOLD), width=90, alignment=ft.alignment.center),
                        ft.Container(ft.Text(m.get("motivo",""), size=11), width=120),
                        ft.Container(ft.Text(str(m.get("quantidade",0)), size=11, weight=ft.FontWeight.BOLD), width=60, alignment=ft.alignment.center),
                        ft.Container(ft.Text(str(m.get("data",""))[:16], size=11, color=Colors.TEXT_GRAY), width=140),
                    ], spacing=0),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
                ))
            header_mov = _header_tabela([("ID",50),("Produto",180),("Tipo",90),("Motivo",120),("Qtd",60),("Data",140)])
            tabela_mov = ft.Container(content=ft.Column([
                header_mov,
                ft.Container(
                    content=ft.Column(linhas_mov if linhas_mov else [_linha_vazia("Selecione e clique em 'Gerar Relatório'")], spacing=0, scroll=ft.ScrollMode.AUTO),
                    border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=ft.border_radius.only(bottom_left=8,bottom_right=8), height=250,
                ),
            ], spacing=0))
            preview_content.controls = [
                secao_titulo("Movimentações de Estoque", ft.icons.SWAP_VERT),
                ft.Row([
                    card_metrica(ft.icons.ARROW_DOWNWARD, "Entradas", str(entradas), Colors.BRAND_GREEN, "#F1FFF3"),
                    card_metrica(ft.icons.ARROW_UPWARD,   "Saídas",   str(saidas),   Colors.BRAND_RED,   "#FFF0F0"),
                    card_metrica(ft.icons.RECEIPT_LONG,   "Total",    str(len(movs)),Colors.BRAND_BLUE,  "#EFF6FF"),
                ], spacing=12),
                ft.Divider(height=8),
                secao_titulo(f"Listagem — {titulo}", ft.icons.SWAP_VERT),
                tabela_mov,
            ]
        else:
            titulo   = titulos_produto.get(filtro, "Estoque")
            listagem_ativos   = dados.get("listagem", []) if dados else []
            listagem_inativos = dados.get("_inativos", []) if dados else []

            # Filtra conforme filtro selecionado
            if filtro == "completo":
                # Ativos + inativos
                listagem = listagem_ativos + listagem_inativos
            elif filtro == "ativos":
                listagem = listagem_ativos
            elif filtro == "inativos":
                listagem = listagem_inativos
            elif filtro == "baixo":
                listagem = [p for p in listagem_ativos if int(p.get("estoque", 0)) <= int(p.get("estoque_minimo") or 5)]
            else:
                listagem = listagem_ativos

            linhas_est = []
            for p in listagem:
                estq = p.get("estoque", 0)
                emin = p.get("estoque_minimo") or 5
                cor_estq = Colors.BRAND_RED if estq == 0 else (Colors.BRAND_ORANGE if estq <= emin else Colors.BRAND_GREEN)
                linhas_est.append(ft.Container(
                    content=ft.Row([
                        ft.Container(ft.Text(str(p.get("id","")), size=11), width=50, alignment=ft.alignment.center),
                        ft.Container(ft.Text(p.get("nome",""), size=11), width=200),
                        ft.Container(ft.Text(p.get("categoria",""), size=11, color=Colors.TEXT_GRAY), width=150),
                        ft.Container(ft.Text(str(estq), size=11, weight=ft.FontWeight.BOLD, color=cor_estq), width=80, alignment=ft.alignment.center),
                        ft.Container(ft.Text(fmt(p.get("preco_compra")), size=11), width=100, alignment=ft.alignment.center),
                        ft.Container(ft.Text(fmt(p.get("preco_venda")), size=11), width=100, alignment=ft.alignment.center),
                    ], spacing=0),
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
                ))
            header_est = _header_tabela([("ID",50),("Produto",200),("Categoria",150),("Estoque",80),("Compra",100),("Venda",100)])
            tabela_est = ft.Container(content=ft.Column([
                header_est,
                ft.Container(
                    content=ft.Column(linhas_est if linhas_est else [_linha_vazia("Selecione um filtro e clique em 'Gerar Relatório'")], spacing=0, scroll=ft.ScrollMode.AUTO),
                    border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=ft.border_radius.only(bottom_left=8,bottom_right=8), height=250,
                ),
            ], spacing=0))
            preview_content.controls = [
                secao_titulo("Resumo de Estoque", ft.icons.INVENTORY_2),
                ft.Row([
                    card_metrica(ft.icons.INVENTORY_2,          "Produtos Ativos", str(dados.get("produtos_ativos",0) if dados else 0), Colors.BRAND_GREEN,  "#F1FFF3"),
                    card_metrica(ft.icons.REMOVE_SHOPPING_CART, "Inativos",        str(dados.get("inativos",0) if dados else 0),        Colors.TEXT_GRAY,    "#F5F5F5"),
                    card_metrica(ft.icons.WARNING_AMBER,        "Estoque Baixo",   str(dados.get("estoque_baixo",0) if dados else 0),   Colors.BRAND_ORANGE, "#FFF8F0"),
                ], spacing=12),
                ft.Divider(height=8),
                secao_titulo(f"Listagem — {titulo}", ft.icons.LIST_ALT),
                tabela_est,
                ft.Text(
                    "Dados atualizados!" if dados else "Selecione um filtro e clique em 'Gerar Relatório' para carregar os dados.",
                    size=12, color=Colors.BRAND_GREEN if dados else Colors.TEXT_GRAY, italic=True, text_align=ft.TextAlign.CENTER,
                ),
            ]
        try: preview_content.update()
        except Exception: pass

    def preview_margem(dados=None):
        def fmt(v): return f"R$ {float(v):.2f}" if v is not None else "R$ 0,00"
        det = dados.get("detalhamento", []) if dados else []

        # Tabela de detalhamento
        header_margem = _header_tabela([("Produto", 200), ("Qtd", 60), ("Receita", 110), ("Custo", 110), ("Lucro", 110), ("Margem%", 80)])
        if det:
            linhas = []
            for p in det:
                cor_lucro = Colors.BRAND_GREEN if float(p.get("lucro",0)) >= 0 else Colors.BRAND_RED
                linhas.append(ft.Container(
                    content=ft.Row([
                        ft.Container(ft.Text(p.get("nome","—"), size=12), width=200),
                        ft.Container(ft.Text(str(p.get("qtd_vendida",0)), size=12), width=60, alignment=ft.alignment.center),
                        ft.Container(ft.Text(fmt(p.get("receita")), size=12), width=110, alignment=ft.alignment.center),
                        ft.Container(ft.Text(fmt(p.get("custo")), size=12), width=110, alignment=ft.alignment.center),
                        ft.Container(ft.Text(fmt(p.get("lucro")), size=12, color=cor_lucro, weight=ft.FontWeight.BOLD), width=110, alignment=ft.alignment.center),
                        ft.Container(ft.Text(f"{p.get('margem_percentual',0):.1f}%", size=12, color=cor_lucro), width=80, alignment=ft.alignment.center),
                    ], spacing=0),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
                ))
            tabela_det = ft.Container(
                content=ft.Column([header_margem,
                    ft.Container(content=ft.Column(linhas, spacing=0, scroll=ft.ScrollMode.AUTO),
                                 border=ft.border.all(1, Colors.BORDER_LIGHT),
                                 border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8), height=200)
                ], spacing=0),
            )
        else:
            tabela_det = _tabela_demo([("Produto", 200), ("Qtd Vendida", 100), ("Receita", 120), ("Custo", 120), ("Lucro", 120), ("Margem%", 80)])

        preview_content.controls = [
            secao_titulo("Análise de Margem", ft.icons.TRENDING_UP),
            ft.Row([
                card_metrica(ft.icons.ATTACH_MONEY,  "Receita Bruta", fmt(dados.get("receita_bruta") if dados else None),    Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.SHOPPING_CART, "Custo Total",   fmt(dados.get("custo_total") if dados else None),      Colors.BRAND_RED,    "#FFF0F0"),
                card_metrica(ft.icons.TRENDING_UP,   "Lucro Bruto",   fmt(dados.get("lucro_bruto") if dados else None),      Colors.BRAND_BLUE,   "#EFF6FF"),
                card_metrica(ft.icons.PERCENT,       "Margem %",      f"{dados.get('margem_percentual',0):.1f}%" if dados else "0%", Colors.BRAND_ORANGE, "#FFF8F0"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo("Detalhamento por Produto", ft.icons.TABLE_CHART),
            tabela_det,
            ft.Text(
                "Dados atualizados!" if dados else "Clique em 'Gerar Relatório' para carregar os dados reais.",
                size=12, color=Colors.BRAND_GREEN if dados else Colors.TEXT_GRAY, italic=True, text_align=ft.TextAlign.CENTER,
            ),
        ]
        try: preview_content.update()
        except Exception: pass

    def preview_caixa(dados=None):
        def fmt(v): return f"R$ {float(v):.2f}" if v is not None else "R$ 0,00"
        historico = dados.get("historico", []) if dados else []

        linhas_turno = []
        for t in historico:
            dif = t.get("diferenca") or 0
            cor_dif = Colors.BRAND_GREEN if dif >= 0 else Colors.BRAND_RED
            sinal = "+" if dif >= 0 else ""
            def _fmt_caixa_dt(v):
                if not v: return "—"
                try:
                    from datetime import datetime as _dt, timedelta
                    d = _dt.fromisoformat(str(v).replace("Z","+00:00"))
                    d = d + timedelta(hours=-3)
                    return d.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    return str(v)[:16]
            ab  = _fmt_caixa_dt(t.get("abertura"))
            fec = _fmt_caixa_dt(t.get("fechamento"))
            linhas_turno.append(ft.Container(
                content=ft.Row([
                    ft.Container(ft.Text(f"#{t.get('id','')}", size=12, weight=ft.FontWeight.BOLD), width=60, alignment=ft.alignment.center),
                    ft.Container(ft.Text(ab, size=11, color=Colors.TEXT_GRAY), width=130, alignment=ft.alignment.center),
                    ft.Container(ft.Text(fec, size=11, color=Colors.TEXT_GRAY), width=130, alignment=ft.alignment.center),
                    ft.Container(ft.Text(fmt(t.get("valor_inicial")), size=12), width=100, alignment=ft.alignment.center),
                    ft.Container(ft.Text(fmt(t.get("total_faturado")), size=12, color=Colors.BRAND_GREEN, weight=ft.FontWeight.BOLD), width=100, alignment=ft.alignment.center),
                    ft.Container(ft.Text(f"{sinal}{fmt(abs(dif))}", size=12, color=cor_dif, weight=ft.FontWeight.BOLD), width=100, alignment=ft.alignment.center),
                ], spacing=0),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER_LIGHT)),
            ))

        header_caixa = _header_tabela([("#", 60), ("Abertura", 130), ("Fechamento", 130), ("Inicial", 100), ("Faturado", 100), ("Diferença", 100)])
        tabela_caixa = ft.Container(
            content=ft.Column([
                header_caixa,
                ft.Container(
                    content=ft.Column(linhas_turno if linhas_turno else [_linha_vazia()], spacing=0, scroll=ft.ScrollMode.AUTO),
                    border=ft.border.all(1, Colors.BORDER_LIGHT),
                    border_radius=ft.border_radius.only(bottom_left=8, bottom_right=8),
                    height=200,
                ),
            ], spacing=0),
        )

        dif_total = dados.get("diferenca_total", 0) if dados else 0
        cor_dif_total = Colors.BRAND_GREEN if dif_total >= 0 else Colors.BRAND_RED

        preview_content.controls = [
            secao_titulo("Resumo de Caixa por Turno", ft.icons.POINT_OF_SALE),
            ft.Row([
                card_metrica(ft.icons.PUNCH_CLOCK,            "Turnos no Período", str(dados.get("turnos_no_periodo",0) if dados else 0), Colors.BRAND_BLUE,   "#EFF6FF"),
                card_metrica(ft.icons.ACCOUNT_BALANCE_WALLET, "Total Faturado",    fmt(dados.get("total_faturado") if dados else None),    Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.COMPARE_ARROWS,         "Diferença Total",   fmt(dif_total),                                         cor_dif_total,       "#FFF8F0"),
            ], spacing=12),
            ft.Divider(height=8),
            secao_titulo("Histórico de Turnos", ft.icons.HISTORY),
            tabela_caixa,
            ft.Text(
                "Dados atualizados!" if dados else "Clique em 'Gerar Relatório' para carregar os dados reais.",
                size=12, color=Colors.BRAND_GREEN if dados else Colors.TEXT_GRAY, italic=True, text_align=ft.TextAlign.CENTER,
            ),
        ]
        try: preview_content.update()
        except Exception: pass

    def preview_geral(dados=None):
        def fmt(v): return f"R$ {float(v):.2f}" if v is not None else "R$ 0,00"
        fp   = dados.get("por_forma_pagamento", {}) if dados else {}
        top  = dados.get("top_produtos", []) if dados else []
        cores_rank = [Colors.BRAND_GREEN, Colors.BRAND_BLUE, Colors.BRAND_ORANGE]

        ranking_controls = []
        for i, p in enumerate(top[:3]):
            ranking_controls.append(_linha_ranking(i+1, p.get("nome","—"), "—", f"{p.get('quantidade_total',0)} un.", cores_rank[i]))
        if not ranking_controls:
            for i in range(3):
                ranking_controls.append(_linha_ranking(i+1, "—", "—", "0 un.", cores_rank[i]))

        # Gráfico de pagamentos com barras reais
        total_fp = sum(fp.values()) if fp else 1
        def barra_pag(label, chave, cor):
            val = float(fp.get(chave, 0))
            pct = val / total_fp if total_fp > 0 else 0
            return ft.Row([
                ft.Text(label, size=13, expand=True),
                ft.Container(
                    content=ft.Container(width=max(int(160*pct),0), bgcolor=cor, border_radius=4, height=8),
                    bgcolor=Colors.BORDER_LIGHT, border_radius=4, height=8, width=160,
                ),
                ft.Text(fmt(val), size=12, color=Colors.TEXT_GRAY, width=90, text_align=ft.TextAlign.RIGHT),
            ], spacing=8)

        grafico_pag = ft.Container(
            content=ft.Column([
                barra_pag("💵 Dinheiro",      "DINHEIRO",       Colors.BRAND_GREEN),
                barra_pag("💳 Débito",        "CARTAO_DEBITO",  Colors.BRAND_BLUE),
                barra_pag("💳 Crédito",       "CARTAO_CREDITO", "#9C27B0"),
                barra_pag("📱 Pix",           "PIX",            "#00BCD4"),
            ], spacing=10),
            border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=10, padding=16,
        )

        preview_content.controls = [
            secao_titulo("Visão Geral do Período", ft.icons.DASHBOARD),
            ft.Row([
                card_metrica(ft.icons.SHOPPING_BAG,        "Total Vendas",  fmt(dados.get("total_vendas") if dados else None),   Colors.BRAND_GREEN,  "#F1FFF3"),
                card_metrica(ft.icons.CONFIRMATION_NUMBER, "Ticket Médio",  fmt(dados.get("ticket_medio") if dados else None),   Colors.BRAND_BLUE,   "#EFF6FF"),
                card_metrica(ft.icons.TRENDING_UP,         "Lucro Bruto",   fmt(dados.get("lucro_bruto") if dados else None),    Colors.BRAND_ORANGE, "#FFF8F0"),
                card_metrica(ft.icons.STAR,                "Produto Top",   dados.get("produto_top","—") if dados else "—",       Colors.BRAND_RED,    "#FFF0F0"),
            ], spacing=12),
            ft.Divider(height=8),
            ft.Row([
                ft.Column([secao_titulo("Pagamentos", ft.icons.PAYMENTS), grafico_pag], expand=True, spacing=8),
                ft.Column([
                    secao_titulo("Top Produtos", ft.icons.STAR),
                    ft.Container(content=ft.Column(ranking_controls, spacing=0), border=ft.border.all(1, Colors.BORDER_LIGHT), border_radius=10),
                ], expand=True, spacing=8),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Text(
                "Dados atualizados!" if dados else "Clique em 'Gerar Relatório' para carregar os dados reais.",
                size=12, color=Colors.BRAND_GREEN if dados else Colors.TEXT_GRAY, italic=True, text_align=ft.TextAlign.CENTER,
            ),
        ]
        try: preview_content.update()
        except Exception: pass

    def atualizar_preview(dados=None):
        """Se dados=None mostra preview demo, se dados=dict mostra dados reais"""
        # Cacheia os dados para uso na exportação
        if dados is not None:
            estado["_dados_cache"] = dados
        tipo = estado["tipo"]
        if tipo == "vendas":
            preview_vendas(dados)
        elif tipo == "estoque":
            preview_estoque(dados)
        elif tipo == "margem":
            preview_margem(dados)
        elif tipo == "caixa":
            preview_caixa(dados)
        elif tipo == "geral":
            preview_geral(dados)

    def gerar_relatorio_real():
        """Busca dados da API e atualiza o preview"""
        ini = estado.get("data_inicio")
        fim = estado.get("data_fim")
        tipo = estado["tipo"]

        if not ini or not fim:
            # Estoque não precisa de período
            if tipo == "estoque":
                ini = fim = __import__("datetime").datetime.now().strftime("%d/%m/%Y")
            else:
                atualizar_preview()
                return

        try:
            if tipo == "vendas":
                dados = RelatorioAPI.vendas(ini, fim)
            elif tipo == "estoque":
                filtro = estado.get("estoque_filtro", "completo")
                if filtro.startswith("mov_"):
                    # Movimentações — agrega por todos os produtos ativos,
                    # pois a API não tem rota geral de listagem
                    tipo_mov = None
                    if filtro == "mov_entrada": tipo_mov = "ENTRADA"
                    elif filtro == "mov_saida":  tipo_mov = "SAIDA"
                    from app.api.movimentacao_api import MovimentacaoAPI as MovAPI
                    produtos_ativos = ProdutosAPI.listar_produtos() or []
                    mov_list = []
                    for prod in produtos_ativos:
                        pid = prod.get("id")
                        if not pid:
                            continue
                        movs_prod = MovAPI.listar_por_produto(pid) or []
                        # Injeta nome do produto em cada movimentação para exibição
                        for m in movs_prod:
                            m["_produto_nome"] = prod.get("nome", f"ID {pid}")
                        mov_list.extend(movs_prod)
                    # Ordena por data decrescente (mais recentes primeiro)
                    mov_list.sort(key=lambda m: m.get("data", "") or "", reverse=True)
                    dados = {"_movs": mov_list, "_tipo_mov": tipo_mov}
                else:
                    # Busca dados base do back
                    dados_base = RelatorioAPI.estoque() or {}
                    # Busca inativos separado para completo e inativos
                    if filtro in ("completo", "inativos"):
                        inativos = ProdutosAPI.listar_inativos() or []
                        dados_base["_inativos"] = inativos
                    dados = dados_base
            elif tipo == "margem":
                dados = RelatorioAPI.margem(ini, fim)
            elif tipo == "caixa":
                dados = RelatorioAPI.caixa(ini, fim)
            elif tipo == "geral":
                dados = RelatorioAPI.geral(ini, fim)
            else:
                dados = None
            atualizar_preview(dados)
        except Exception as ex:
            print(f"Erro ao gerar relatório: {ex}")
            atualizar_preview()

    # =========================================================================
    # CHIPS DE PERÍODO
    # =========================================================================
    # Chips de período (para relatórios com filtro temporal)
    periodos = [
        ("Hoje", "hoje"), ("Semana", "semana"), ("Mês", "mes"),
        ("Bimestre", "bimestre"), ("Semestre", "semestre"), ("Ano", "ano"),
    ]

    chips_row = ft.Row(spacing=8, wrap=True)

    def chip_periodo(label, valor):
        selecionado = estado["periodo"] == valor
        def selecionar(e):
            from datetime import date, timedelta
            hoje = date.today()
            deltas = {
                "hoje":     (hoje, hoje),
                "semana":   (hoje - timedelta(days=7), hoje),
                "mes":      (hoje - timedelta(days=30), hoje),
                "bimestre": (hoje - timedelta(days=60), hoje),
                "semestre": (hoje - timedelta(days=180), hoje),
                "ano":      (hoje - timedelta(days=365), hoje),
            }
            ini, fim = deltas.get(valor, (hoje, hoje))
            estado["periodo"]     = valor
            estado["data_inicio"] = ini.strftime("%d/%m/%Y")
            estado["data_fim"]    = fim.strftime("%d/%m/%Y")
            rebuild_chips()
            gerar_relatorio_real()
        return ft.ElevatedButton(
            label,
            style=ft.ButtonStyle(
                bgcolor=Colors.BRAND_RED if selecionado else "#F5F5F5",
                color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_GRAY,
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                elevation=2 if selecionado else 0,
            ),
            on_click=selecionar, height=36,
        )

    def rebuild_chips():
        chips_row.controls = [chip_periodo(l, v) for l, v in periodos]
        try: chips_row.update()
        except Exception: pass

    # Filtros de estoque
    estado["estoque_filtro"] = "completo"

    def btn_estoque_filtro(label, valor, icone, cor):
        selecionado = estado["estoque_filtro"] == valor
        def selecionar(e):
            estado["estoque_filtro"] = valor
            rebuild_filtros_estoque()
            # Gera automaticamente ao clicar em qualquer filtro
            page.run_thread(gerar_relatorio_real)
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, size=16, color=Colors.TEXT_WHITE if selecionado else cor),
                ft.Text(label, size=13, weight=ft.FontWeight.BOLD if selecionado else ft.FontWeight.W_400,
                        color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_BLACK),
            ], spacing=8),
            bgcolor=cor if selecionado else Colors.BG_WHITE,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border=ft.border.all(1, cor),
            ink=True, on_click=selecionar,
        )

    filtros_estoque_col = ft.Column(spacing=6)

    def rebuild_filtros_estoque():
        filtros_estoque_col.controls = [
            ft.Text("LISTAGEM", size=10, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
            btn_estoque_filtro("Estoque Completo",  "completo",   ft.icons.LIST_ALT,               Colors.BRAND_BLUE),
            btn_estoque_filtro("Produtos Ativos",   "ativos",     ft.icons.CHECK_CIRCLE_OUTLINE,   Colors.BRAND_GREEN),
            btn_estoque_filtro("Produtos Inativos", "inativos",   ft.icons.REMOVE_CIRCLE_OUTLINE,  Colors.TEXT_GRAY),
            btn_estoque_filtro("Estoque Baixo",     "baixo",      ft.icons.WARNING_AMBER,          Colors.BRAND_ORANGE),
            ft.Divider(height=8),
            ft.Text("MOVIMENTAÇÕES", size=10, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
            btn_estoque_filtro("Todas",    "mov_todas",   ft.icons.SWAP_VERT,     Colors.BRAND_BLUE),
            btn_estoque_filtro("Entradas", "mov_entrada", ft.icons.ARROW_DOWNWARD, Colors.BRAND_GREEN),
            btn_estoque_filtro("Saídas",   "mov_saida",   ft.icons.ARROW_UPWARD,  Colors.BRAND_RED),
        ]
        try: filtros_estoque_col.update()
        except Exception: pass

    # Área de filtros dinâmica (muda conforme tipo selecionado)
    area_filtros = ft.Column(spacing=4)

    def rebuild_area_filtros():
        area_filtros.controls.clear()
        if estado["tipo"] == "estoque":
            area_filtros.controls = [
                ft.Text("FILTRO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                ft.Container(height=4),
                filtros_estoque_col,
            ]
        else:
            area_filtros.controls = [
                ft.Text("PERÍODO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
                ft.Container(height=4),
                chips_row,
            ]
        try: area_filtros.update()
        except Exception: pass

    # Popula sem .update()
    chips_row.controls = [chip_periodo(l, v) for l, v in periodos]
    filtros_estoque_col.controls = [
        ft.Text("LISTAGEM", size=10, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
        btn_estoque_filtro("Estoque Completo",  "completo",   ft.icons.LIST_ALT,               Colors.BRAND_BLUE),
        btn_estoque_filtro("Produtos Ativos",   "ativos",     ft.icons.CHECK_CIRCLE_OUTLINE,   Colors.BRAND_GREEN),
        btn_estoque_filtro("Produtos Inativos", "inativos",   ft.icons.REMOVE_CIRCLE_OUTLINE,  Colors.TEXT_GRAY),
        btn_estoque_filtro("Estoque Baixo",     "baixo",      ft.icons.WARNING_AMBER,          Colors.BRAND_ORANGE),
        ft.Divider(height=8),
        ft.Text("MOVIMENTAÇÕES", size=10, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
        btn_estoque_filtro("Todas",    "mov_todas",   ft.icons.SWAP_VERT,      Colors.BRAND_BLUE),
        btn_estoque_filtro("Entradas", "mov_entrada", ft.icons.ARROW_DOWNWARD, Colors.BRAND_GREEN),
        btn_estoque_filtro("Saídas",   "mov_saida",   ft.icons.ARROW_UPWARD,   Colors.BRAND_RED),
    ]
    area_filtros.controls = [
        ft.Text("PERÍODO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
        ft.Container(height=4),
        chips_row,
    ]

    # =========================================================================
    # MENU LATERAL
    # =========================================================================
    tipos = [
        ("Vendas",  "vendas",  ft.icons.SHOPPING_BAG),
        ("Estoque", "estoque", ft.icons.INVENTORY_2),
        ("Margem",  "margem",  ft.icons.TRENDING_UP),
        ("Caixa",   "caixa",   ft.icons.POINT_OF_SALE),
        ("Geral",   "geral",   ft.icons.DASHBOARD),
    ]

    menu_col = ft.Column(spacing=4)

    def btn_tipo(label, valor, icone):
        selecionado = estado["tipo"] == valor
        def selecionar(e):
            estado["tipo"] = valor
            rebuild_menu()
            rebuild_area_filtros()
            _atualizar_visibilidade_botoes()
            atualizar_preview()  # mostra demo imediatamente
            page.run_thread(gerar_relatorio_real)  # carrega dados reais em background
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, size=18, color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_GRAY),
                ft.Text(label, size=14,
                        weight=ft.FontWeight.BOLD if selecionado else ft.FontWeight.W_400,
                        color=Colors.TEXT_WHITE if selecionado else Colors.TEXT_BLACK),
            ], spacing=10),
            bgcolor=Colors.BRAND_RED if selecionado else Colors.BG_WHITE,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            ink=True, on_click=selecionar,
            border=ft.border.all(1, Colors.BORDER_LIGHT if not selecionado else Colors.BRAND_RED),
        )

    def rebuild_menu():
        menu_col.controls = [
            ft.Text("TIPO DE RELATÓRIO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
            ft.Container(height=4),
            *[btn_tipo(l, v, i) for l, v, i in tipos],
        ]
        try: menu_col.update()
        except Exception: pass
        rebuild_area_filtros()

    # Popula menu sem .update()
    menu_col.controls = [
        ft.Text("TIPO DE RELATÓRIO", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_GRAY),
        ft.Container(height=4),
        *[btn_tipo(l, v, i) for l, v, i in tipos],
    ]

    # =========================================================================
    # MODAL DE PERÍODO PERSONALIZADO
    # =========================================================================
    def abrir_modal_periodo():
        from datetime import date
        hoje = date.today()

        data_ini_input = ft.TextField(
            label="Data Início (DD/MM/AAAA)", width=180,
            border_color=Colors.BORDER_GRAY,
            hint_text="ex: 01/03/2026",
            keyboard_type=ft.KeyboardType.DATETIME,
        )
        data_fim_input = ft.TextField(
            label="Data Fim (DD/MM/AAAA)", width=180,
            border_color=Colors.BORDER_GRAY,
            hint_text=f"ex: {hoje.strftime('%d/%m/%Y')}",
            keyboard_type=ft.KeyboardType.DATETIME,
        )

        def confirmar(e):
            ini = data_ini_input.value.strip()
            fim = data_fim_input.value.strip()
            ok = True
            if not ini:
                data_ini_input.border_color = Colors.BRAND_RED
                data_ini_input.error_text = "Obrigatório"
                ok = False
            else:
                data_ini_input.border_color = Colors.BORDER_GRAY
                data_ini_input.error_text = None
            if not fim:
                data_fim_input.border_color = Colors.BRAND_RED
                data_fim_input.error_text = "Obrigatório"
                ok = False
            else:
                data_fim_input.border_color = Colors.BORDER_GRAY
                data_fim_input.error_text = None
            if not ok:
                page.update()
                return
            # Salva período personalizado e gera
            estado["periodo"]       = "personalizado"
            estado["data_inicio"]   = ini
            estado["data_fim"]      = fim
            estado["pode_exportar"] = True
            modal.open = False
            page.update()
            gerar_relatorio_real()

        def fechar(e):
            modal.open = False
            page.update()

        modal = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=12),
            title=ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.DATE_RANGE, color=Colors.TEXT_WHITE, size=22),
                    ft.Text("Período do Relatório", size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_WHITE),
                ], spacing=8),
                bgcolor=Colors.BRAND_RED,
                padding=ft.padding.symmetric(horizontal=20, vertical=16),
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
                margin=ft.margin.only(left=-24, right=-24, top=-24, bottom=0),
            ),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    tight=True, spacing=16,
                    controls=[
                        ft.Container(height=4),
                        ft.Text("Selecione o período para geração do relatório:", size=13, color=Colors.TEXT_GRAY),
                        ft.Row([data_ini_input, ft.Text("→", size=18, color=Colors.TEXT_GRAY), data_fim_input], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=4),
                        ft.Text("Ou use um período rápido:", size=12, color=Colors.TEXT_GRAY),
                        ft.Row([
                            _chip_rapido("Hoje",    "hoje",     data_ini_input, data_fim_input),
                            _chip_rapido("Semana",  "semana",   data_ini_input, data_fim_input),
                            _chip_rapido("Mês",     "mes",      data_ini_input, data_fim_input),
                            _chip_rapido("Semestre","semestre", data_ini_input, data_fim_input),
                            _chip_rapido("Ano",     "ano",      data_ini_input, data_fim_input),
                        ], spacing=6, wrap=True),
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton(
                    "Gerar",
                    bgcolor=Colors.BRAND_RED, color=Colors.TEXT_WHITE,
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

    def _chip_rapido(label, valor, ini_field, fim_field):
        from datetime import date, timedelta
        def preencher(e):
            hoje = date.today()
            deltas = {
                "hoje":     (hoje, hoje),
                "semana":   (hoje - timedelta(days=7), hoje),
                "mes":      (hoje - timedelta(days=30), hoje),
                "bimestre": (hoje - timedelta(days=60), hoje),
                "semestre": (hoje - timedelta(days=180), hoje),
                "ano":      (hoje - timedelta(days=365), hoje),
            }
            ini, fim = deltas.get(valor, (hoje, hoje))
            ini_field.value = ini.strftime("%d/%m/%Y")
            fim_field.value = fim.strftime("%d/%m/%Y")
            ini_field.border_color = Colors.BORDER_GRAY
            fim_field.border_color = Colors.BORDER_GRAY
            ini_field.error_text = None
            fim_field.error_text = None
            page.update()
        return ft.ElevatedButton(
            label,
            style=ft.ButtonStyle(
                bgcolor="#F5F5F5", color=Colors.TEXT_GRAY,
                shape=ft.RoundedRectangleBorder(radius=16),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                elevation=0,
            ),
            on_click=preencher, height=32,
        )

    # =========================================================================
    # LAYOUT
    # =========================================================================

    def exportar_excel(e):
        import os
        from app.api.auth_api import request_com_auth
        tipo = estado["tipo"]
        ini  = estado.get("data_inicio")
        fim  = estado.get("data_fim")

        def _fmt_ini(d): return __import__("datetime").datetime.strptime(d, "%d/%m/%Y").strftime("%Y-%m-%dT00:00:00")
        def _fmt_fim(d): return __import__("datetime").datetime.strptime(d, "%d/%m/%Y").strftime("%Y-%m-%dT23:59:59")

        def _exportar():
            try:
                conteudo     = None
                nome_arquivo = f"relatorio_{tipo}.xlsx"
                BASE_URL     = "http://localhost:8000"

                if tipo in ("vendas", "margem"):
                    if not ini or not fim:
                        page.snack_bar = ft.SnackBar(content=ft.Text("Selecione o período antes de exportar."), bgcolor=Colors.BRAND_ORANGE)
                        page.snack_bar.open = True
                        page.update()
                        return
                    rota = f"{BASE_URL}/relatorios/{tipo}/exportar"
                    resp = request_com_auth("GET", rota,
                        params={"data_inicio": _fmt_ini(ini), "data_fim": _fmt_fim(fim)}, timeout=30)
                    if resp.status_code == 200:
                        conteudo = resp.content
                        nome_arquivo = f"relatorio_{tipo}.xlsx"

                elif tipo == "estoque":
                    filtro_est = estado.get("estoque_filtro", "completo")
                    if filtro_est.startswith("mov_"):
                        # Movimentações — usa rota dedicada do back
                        tipo_mov = None
                        if filtro_est == "mov_entrada": tipo_mov = "ENTRADA"
                        elif filtro_est == "mov_saida":  tipo_mov = "SAIDA"
                        conteudo = MovimentacaoAPI.exportar(
                            data_inicio=ini and _fmt_ini(ini),
                            data_fim=fim and _fmt_fim(fim),
                            tipo=tipo_mov,
                        )
                        nome_arquivo = "movimentacoes.xlsx"
                    else:
                        # Gera CSV no front com os dados cacheados (sem dependências externas).
                        # O Excel abre CSV nativamente.
                        import csv, io

                        dados_cache = estado.get("_dados_cache") or {}
                        listagem_ativos   = dados_cache.get("listagem", [])
                        listagem_inativos = dados_cache.get("_inativos", [])

                        if filtro_est == "completo":
                            listagem = listagem_ativos + listagem_inativos
                        elif filtro_est == "ativos":
                            listagem = listagem_ativos
                        elif filtro_est == "inativos":
                            listagem = listagem_inativos
                        elif filtro_est == "baixo":
                            listagem = [p for p in listagem_ativos
                                        if int(p.get("estoque", 0)) <= int(p.get("estoque_minimo") or 5)]
                        else:
                            listagem = listagem_ativos

                        if not listagem:
                            page.snack_bar = ft.SnackBar(
                                content=ft.Text("Gere o relatório antes de exportar."),
                                bgcolor=Colors.BRAND_ORANGE,
                            )
                            page.snack_bar.open = True
                            page.update()
                            return

                        buf = io.StringIO()
                        writer = csv.writer(buf, delimiter=";")
                        writer.writerow(["ID", "Produto", "Categoria", "Estoque", "Estoque Min.", "Preco Compra", "Preco Venda"])
                        for p in listagem:
                            writer.writerow([
                                p.get("id", ""),
                                p.get("nome", ""),
                                p.get("categoria") or p.get("categoria_nome", ""),
                                int(p.get("estoque", 0)),
                                int(p.get("estoque_minimo") or 5),
                                f"{float(p.get('preco_compra') or 0):.2f}",
                                f"{float(p.get('preco_venda') or 0):.2f}",
                            ])
                        conteudo = buf.getvalue().encode("utf-8-sig")  # BOM para Excel abrir com acentos
                        nome_arquivo = f"estoque_{filtro_est}.csv"

                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Exportação Excel não disponível para o relatório selecionado."),
                        bgcolor=Colors.BRAND_ORANGE,
                    )
                    page.snack_bar.open = True
                    page.update()
                    return

                if conteudo and isinstance(conteudo, bytes):
                    caminho = os.path.join(os.path.expanduser("~"), "Downloads", nome_arquivo)
                    with open(caminho, "wb") as f_out:
                        f_out.write(conteudo)
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"✓ Arquivo salvo em Downloads/{nome_arquivo}"),
                        bgcolor=Colors.BRAND_GREEN,
                    )
                else:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("Erro ao exportar. Tente novamente."),
                        bgcolor=Colors.BRAND_RED,
                    )
                page.snack_bar.open = True
                page.update()

            except Exception as ex:
                print(f"Erro exportar: {ex}")
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Erro ao exportar: {ex}"), bgcolor=Colors.BRAND_RED)
                page.snack_bar.open = True
                page.update()

        page.run_thread(_exportar)

    def _atualizar_visibilidade_botoes():
        """Mostra/esconde Exportar e Gerar Relatório conforme tipo e filtro"""
        tipo   = estado["tipo"]
        filtro = estado.get("estoque_filtro", "completo")

        # Exportar: disponível para vendas, margem e estoque. Não para caixa/geral
        btn_exportar.visible = tipo in ("vendas", "margem", "estoque")

        # Gerar Relatório:
        # - estoque listagem → desnecessário (auto ao clicar filtro), mas mantém visível pra forçar refresh
        # - estoque movimentação → necessário para abrir modal de período
        # - outros tipos → necessário para abrir modal de período
        btn_gerar_ref.visible = True

        try:
            btn_exportar.update()
            btn_gerar_ref.update()
        except Exception:
            pass

    def _on_click_gerar():
        """Lógica do botão Gerar Relatório:
        - Outros tipos → abre modal de período
        - Estoque listagem → gera direto (já acontece ao selecionar o filtro, mas mantém como atalho)
        - Estoque movimentação → abre modal de período para filtrar por data
        """
        tipo    = estado["tipo"]
        filtro  = estado.get("estoque_filtro", "completo")
        if tipo != "estoque":
            abrir_modal_periodo()
        elif filtro.startswith("mov_"):
            abrir_modal_periodo()   # movimentações usam o modal de período
        else:
            gerar_relatorio_real()  # listagem gera direto


    # =========================================================================
    # ATALHOS DE TECLADO — RELATÓRIOS
    # F5   Gerar relatório (equivale a clicar em "Gerar Relatório")
    # F6   Exportar Excel
    # F12  Voltar ao Menu Principal
    # =========================================================================
    def _on_keyboard(e: ft.KeyboardEvent):
        if page.route != "/relatorios":
            return
        k = e.key
        if k == "F5":
            _on_click_gerar()
        elif k == "F6":
            if btn_exportar.visible:
                exportar_excel(None)
        elif k == "Escape":
            page.on_keyboard_event = None
            page.go("/")

    page.on_keyboard_event = _on_keyboard

    btn_gerar_ref = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.icons.BAR_CHART, color=Colors.TEXT_WHITE, size=18),
            ft.Text("Gerar Relatório - F5", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
        ], spacing=8, tight=True),
        bgcolor=Colors.BRAND_RED, height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=lambda _: _on_click_gerar(),
        width=220,
    )

    btn_exportar = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.icons.TABLE_VIEW, color=Colors.TEXT_WHITE, size=18),
            ft.Text("Exportar Excel - F6", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
        ], spacing=8, tight=True),
        bgcolor=Colors.BRAND_GREEN,
        height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=exportar_excel,
        width=220,
    )

    btn_menu_principal = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.icons.HOME, color=Colors.TEXT_WHITE, size=18),
            ft.Text("Menu Principal - ESC", color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD),
        ], spacing=8, tight=True),
        bgcolor=Colors.BRAND_RED, height=48,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=lambda _: (setattr(page, "on_keyboard_event", None), page.go("/")), width=220,
    )

    painel_esq = ft.Container(
        content=ft.Column([
            # Parte scrollável — menu + filtros
            ft.Container(
                content=ft.Column([
                    menu_col,
                    ft.Divider(height=20),
                    area_filtros,
                    ft.Divider(height=20),
                    btn_gerar_ref,
                    ft.Container(height=8),
                    btn_exportar,
                ], spacing=4, scroll=ft.ScrollMode.AUTO),
                expand=True,
            ),
            # Parte fixa no fundo
            ft.Divider(height=8),
            btn_menu_principal,
        ], spacing=0, expand=True),
        width=260, padding=20, bgcolor=Colors.BG_WHITE,
        border=ft.border.only(left=ft.BorderSide(2, Colors.BORDER_LIGHT)),
    )

    painel_dir = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("Preview do Relatório", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", size=12, color=Colors.TEXT_GRAY),
                ], spacing=2, expand=True),
            ]),
            ft.Divider(height=16),
            ft.Container(content=preview_content, expand=True),
        ], spacing=0, expand=True),
        expand=True, padding=24, bgcolor=Colors.BG_GRAY_LIGHT,
    )

    # Carrega preview demo imediatamente e dispara dados reais em background
    preview_vendas()
    _atualizar_visibilidade_botoes()
    page.run_thread(gerar_relatorio_real)

    return ft.Row(controls=[painel_dir, painel_esq], spacing=0, expand=True)