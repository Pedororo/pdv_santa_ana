"""
Arquivo de estilos e temas do PDV Santa Ana
Este arquivo centraliza todas as cores, tamanhos e estilos usados na aplicação
para facilitar manutenção e garantir consistência visual
"""

import flet as ft

# ============================================================================
# CORES DA APLICAÇÃO
# ============================================================================

class Colors:
    """Paleta de cores do PDV Santa Ana"""

    # Cores principais da marca
    BRAND_RED    = "#E31D1A"
    BRAND_GREEN  = "#4CAF50"
    BRAND_ORANGE = "#FF9800"
    BRAND_BLUE   = "#2196F3"

    # Cores de background
    BG_WHITE      = ft.colors.WHITE
    BG_GRAY_LIGHT = "#F5F5F5"
    BG_PINK_LIGHT = "#FFB3BA"

    # Cores de texto
    TEXT_BLACK = ft.colors.BLACK87
    TEXT_WHITE = ft.colors.WHITE
    TEXT_GRAY  = ft.colors.BLACK54

    # Cores de borda
    BORDER_BLACK  = ft.colors.BLACK87
    BORDER_GRAY   = ft.colors.BLACK54
    BORDER_LIGHT  = ft.colors.BLACK12
    BORDER_MEDIUM = ft.colors.BLACK26


# ============================================================================
# TAMANHOS E DIMENSÕES GLOBAIS
# ============================================================================

class Sizes:
    """Tamanhos padrão de elementos da interface"""

    # Tamanhos de fonte
    FONT_SMALL  = 13
    FONT_MEDIUM = 14
    FONT_LARGE  = 16
    FONT_XLARGE = 18

    # Tamanhos de ícones
    ICON_SMALL  = 20
    ICON_MEDIUM = 24
    ICON_LARGE  = 40

    # Dimensões de botões
    BUTTON_HEIGHT       = 60
    BUTTON_WIDTH        = 216
    BUTTON_SMALL_HEIGHT = 50
    BUTTON_SMALL_WIDTH  = 150

    # Dimensões da sidebar
    SIDEBAR_WIDTH = 260

    # Dimensões de inputs
    INPUT_SMALL  = 100
    INPUT_MEDIUM = 120
    INPUT_LARGE  = 250
    INPUT_XLARGE = 400

    # Colunas genéricas (fallback — prefira usar as constantes por tela abaixo)
    TABLE_COL_SMALL  = 60
    TABLE_COL_MEDIUM = 100
    TABLE_COL_LARGE  = 130
    TABLE_COL_XLARGE = 160

    # Espaçamentos
    SPACING_SMALL  = 5
    SPACING_MEDIUM = 15
    SPACING_LARGE  = 20
    SPACING_XLARGE = 40

    # Raio de borda
    BORDER_RADIUS_SMALL  = 5
    BORDER_RADIUS_MEDIUM = 8
    BORDER_RADIUS_LARGE  = 10
    BORDER_RADIUS_XLARGE = 12


# ============================================================================
# COLUNAS DE TABELA — ESTOQUE
# Colunas: ID | Cód.Barras | Descrição(expand) | Categoria | Estoque | Compra | Venda
# ============================================================================

class EstoqueCols:
    ID        = 55    # "#"
    COD_BARRA = 140   # código de barras
    # Descrição usa expand=True
    CATEGORIA = 170   # nome da categoria
    ESTOQUE   = 80    # qtd em estoque (com ícone de alerta)
    COMPRA    = 110   # preço de compra
    VENDA     = 110   # preço de venda


# ============================================================================
# COLUNAS DE TABELA — HISTÓRICO DE VENDAS
# Colunas: ID | Data | Hora | Valor Total | Pagamento | Status | Turno | Vendedor | Ações
# ============================================================================

class HistoricoVendasCols:
    ID         = 55   # id da venda
    DATA       = 105  # dd/mm/aaaa
    HORA       = 85   # hh:mm:ss
    TOTAL      = 110  # R$ valor
    PAGAMENTO  = 120  # forma de pagamento
    STATUS     = 100  # Concluída / Cancelada
    TURNO      = 70   # #N
    VENDEDOR   = 130  # nome do usuário
    ACOES      = 50   # botão ⋮


# ============================================================================
# COLUNAS DE TABELA — HISTÓRICO DE TURNOS
# Colunas: # | Usuário | Abertura | Fechamento | Vendas | Total | Esperado | Informado | Diferença | Status
# ============================================================================

class HistoricoTurnosCols:
    ID         = 55   # id do turno
    USUARIO    = 130  # nome do usuário
    ABERTURA   = 140  # data/hora abertura
    FECHAMENTO = 140  # data/hora fechamento
    VENDAS     = 65   # quantidade de vendas
    TOTAL      = 110  # total faturado
    ESPERADO   = 110  # valor esperado
    INFORMADO  = 110  # valor informado
    DIFERENCA  = 110  # diferença
    STATUS     = 90   # badge Aberto/Fechado


# ============================================================================
# COLUNAS DE TABELA — USUÁRIOS
# Colunas: ID | Nome(expand) | Username | Perfil | Status
# ============================================================================

class UsuariosCols:
    ID       = 55   # id
    # Nome usa expand=True
    USERNAME = 150  # login
    PERFIL   = 130  # Administrador / Vendedor
    STATUS   = 90   # Ativo / Inativo


# ============================================================================
# COLUNAS DE TABELA — VENDAS (tela de PDV)
# Colunas: Nº | ID | Descrição(expand) | Quant. | Valor.Uni | Valor Total
# ============================================================================

class VendasCols:
    NUMERO     = 45   # número do item na venda
    ID         = 55   # id do produto
    # Descrição usa expand=True
    QUANTIDADE = 75   # quantidade
    PRECO_UNI  = 120  # preço unitário
    TOTAL      = 120  # subtotal


# ============================================================================
# HELPER INTERNO
# ============================================================================

def _make_button(text, icon, on_click, bgcolor, width, height):
    """Cria botão padrão da sidebar com texto que nunca transborda."""
    return ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(icon, size=Sizes.ICON_MEDIUM, color=Colors.TEXT_WHITE),
                ft.Text(
                    text,
                    size=Sizes.FONT_LARGE,
                    color=Colors.TEXT_WHITE,
                    weight=ft.FontWeight.BOLD,
                    no_wrap=False,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=Sizes.SPACING_SMALL,
            tight=True,
        ),
        bgcolor=bgcolor,
        width=width or Sizes.BUTTON_WIDTH,
        height=height or Sizes.BUTTON_HEIGHT,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
        on_click=on_click,
    )


# ============================================================================
# ESTILOS DE COMPONENTES
# ============================================================================

class Styles:
    """Estilos prontos para componentes comuns"""

    @staticmethod
    def button_primary(text, icon, on_click, width=None, height=None):
        return _make_button(text, icon, on_click, Colors.BRAND_GREEN, width, height)

    @staticmethod
    def button_danger(text, icon, on_click, width=None, height=None):
        return _make_button(text, icon, on_click, Colors.BRAND_RED, width, height)

    @staticmethod
    def button_warning(text, icon, on_click, width=None, height=None):
        return _make_button(text, icon, on_click, Colors.BRAND_ORANGE, width, height)

    @staticmethod
    def button_info(text, icon, on_click, width=None, height=None):
        return _make_button(text, icon, on_click, Colors.BRAND_BLUE, width, height)

    @staticmethod
    def button_localizar(on_click):
        return ft.ElevatedButton(
            text="Localizar",
            width=Sizes.BUTTON_SMALL_WIDTH,
            height=Sizes.BUTTON_SMALL_HEIGHT,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_SMALL),
                bgcolor=Colors.BG_WHITE,
                color=Colors.TEXT_BLACK,
            ),
            on_click=on_click,
        )

    @staticmethod
    def text_field(label, width, **kwargs):
        return ft.TextField(
            label=label,
            width=width,
            border_color=Colors.BORDER_GRAY,
            **kwargs,
        )

    @staticmethod
    def dropdown(label, options, width=None, value=None, **kwargs):
        return ft.Dropdown(
            label=label,
            width=width or Sizes.INPUT_MEDIUM,
            options=[ft.dropdown.Option(opt) for opt in options],
            value=value,
            border_color=Colors.BORDER_GRAY,
            **kwargs,
        )

    @staticmethod
    def table_header(columns):
        """Header padrão de tabela. columns = lista de (label, width | None para expand)"""
        controls = []
        for text, width in columns:
            if width is None:
                controls.append(
                    ft.Container(
                        ft.Text(text, weight=ft.FontWeight.BOLD, size=Sizes.FONT_MEDIUM,
                                text_align=ft.TextAlign.CENTER),
                        expand=True,
                        alignment=ft.alignment.center,
                    )
                )
            else:
                controls.append(
                    ft.Container(
                        ft.Text(text, weight=ft.FontWeight.BOLD, size=Sizes.FONT_MEDIUM,
                                text_align=ft.TextAlign.CENTER),
                        width=width,
                        alignment=ft.alignment.center,
                    )
                )

        return ft.Container(
            content=ft.Row(controls=controls, spacing=0),
            bgcolor=Colors.BG_PINK_LIGHT,
            padding=10,
            border=ft.border.all(1, Colors.BORDER_BLACK),
        )

    @staticmethod
    def search_section(pesquisa_input, btn_localizar, filtro_dropdown):
        return ft.Container(
            content=ft.Row(
                controls=[pesquisa_input, btn_localizar, filtro_dropdown],
                spacing=Sizes.SPACING_LARGE,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=Sizes.SPACING_LARGE,
            border=ft.border.all(2, Colors.BORDER_BLACK),
            border_radius=Sizes.BORDER_RADIUS_SMALL,
        )

    @staticmethod
    def sidebar(buttons):
        return ft.Container(
            content=ft.Column(
                controls=buttons,
                spacing=Sizes.SPACING_LARGE,
                alignment=ft.MainAxisAlignment.START,
            ),
            width=Sizes.SIDEBAR_WIDTH,
            padding=Sizes.SPACING_LARGE,
            bgcolor=Colors.BG_GRAY_LIGHT,
        )