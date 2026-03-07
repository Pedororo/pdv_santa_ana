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
    BRAND_RED = "#E31D1A"
    BRAND_GREEN = "#4CAF50"
    BRAND_ORANGE = "#FF9800"
    BRAND_BLUE = "#2196F3"
    
    # Cores de background
    BG_WHITE = ft.colors.WHITE
    BG_GRAY_LIGHT = "#F5F5F5"
    BG_PINK_LIGHT = "#FFB3BA"
    
    # Cores de texto
    TEXT_BLACK = ft.colors.BLACK87
    TEXT_WHITE = ft.colors.WHITE
    TEXT_GRAY = ft.colors.BLACK54
    
    # Cores de borda
    BORDER_BLACK = ft.colors.BLACK87
    BORDER_GRAY = ft.colors.BLACK54
    BORDER_LIGHT = ft.colors.BLACK12
    BORDER_MEDIUM = ft.colors.BLACK26


# ============================================================================
# TAMANHOS E DIMENSÕES
# ============================================================================

class Sizes:
    """Tamanhos padrão de elementos da interface"""
    
    # Tamanhos de fonte
    FONT_SMALL = 14
    FONT_MEDIUM = 16
    FONT_LARGE = 18
    FONT_XLARGE = 20
    
    # Tamanhos de ícones
    ICON_SMALL = 20
    ICON_MEDIUM = 24
    ICON_LARGE = 40
    
    # Dimensões de botões
    BUTTON_HEIGHT = 60
    BUTTON_WIDTH = 240
    BUTTON_SMALL_HEIGHT = 50
    BUTTON_SMALL_WIDTH = 150
    
    # Dimensões da sidebar
    SIDEBAR_WIDTH = 260
    
    # Dimensões de inputs
    INPUT_SMALL = 100
    INPUT_MEDIUM = 120
    INPUT_LARGE = 250
    INPUT_XLARGE = 400
    
    # Dimensões de colunas de tabela
    TABLE_COL_SMALL = 80
    TABLE_COL_MEDIUM = 100
    TABLE_COL_LARGE = 120
    TABLE_COL_XLARGE = 150
    
    # Espaçamentos
    SPACING_SMALL = 5
    SPACING_MEDIUM = 15
    SPACING_LARGE = 20
    SPACING_XLARGE = 40
    
    # Raio de borda
    BORDER_RADIUS_SMALL = 5
    BORDER_RADIUS_MEDIUM = 8
    BORDER_RADIUS_LARGE = 10
    BORDER_RADIUS_XLARGE = 12


# ============================================================================
# ESTILOS DE COMPONENTES
# ============================================================================

class Styles:
    """Estilos prontos para componentes comuns"""
    
    @staticmethod
    def button_primary(text, icon, on_click, width=None, height=None):
        """Botão primário verde (ações positivas)"""
        return ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=Sizes.ICON_MEDIUM, color=Colors.TEXT_WHITE),
                    ft.Text(text, size=Sizes.FONT_LARGE, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=Sizes.SPACING_MEDIUM,
            ),
            bgcolor=Colors.BRAND_GREEN,
            width=width or Sizes.BUTTON_WIDTH,
            height=height or Sizes.BUTTON_HEIGHT,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
            on_click=on_click
        )
    
    @staticmethod
    def button_danger(text, icon, on_click, width=None, height=None):
        """Botão vermelho (ações destrutivas)"""
        return ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=Sizes.ICON_MEDIUM, color=Colors.TEXT_WHITE),
                    ft.Text(text, size=Sizes.FONT_LARGE, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=Sizes.SPACING_MEDIUM,
            ),
            bgcolor=Colors.BRAND_RED,
            width=width or Sizes.BUTTON_WIDTH,
            height=height or Sizes.BUTTON_HEIGHT,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
            on_click=on_click
        )
    
    @staticmethod
    def button_warning(text, icon, on_click, width=None, height=None):
        """Botão laranja (ações de edição)"""
        return ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=Sizes.ICON_MEDIUM, color=Colors.TEXT_WHITE),
                    ft.Text(text, size=Sizes.FONT_LARGE, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=Sizes.SPACING_MEDIUM,
            ),
            bgcolor=Colors.BRAND_ORANGE,
            width=width or Sizes.BUTTON_WIDTH,
            height=height or Sizes.BUTTON_HEIGHT,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
            on_click=on_click
        )
    
    @staticmethod
    def button_info(text, icon, on_click, width=None, height=None):
        """Botão azul (informações)"""
        return ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(icon, size=Sizes.ICON_MEDIUM, color=Colors.TEXT_WHITE),
                    ft.Text(text, size=Sizes.FONT_LARGE, color=Colors.TEXT_WHITE, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=Sizes.SPACING_MEDIUM,
            ),
            bgcolor=Colors.BRAND_BLUE,
            width=width or Sizes.BUTTON_WIDTH,
            height=height or Sizes.BUTTON_HEIGHT,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_LARGE)),
            on_click=on_click
        )
    
    @staticmethod
    def button_localizar(on_click):
        """Botão padrão 'Localizar'"""
        return ft.ElevatedButton(
            text="Localizar",
            width=Sizes.BUTTON_SMALL_WIDTH,
            height=Sizes.BUTTON_SMALL_HEIGHT,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS_SMALL),
                bgcolor=Colors.BG_WHITE,
                color=Colors.TEXT_BLACK,
            ),
            on_click=on_click
        )
    
    @staticmethod
    def text_field(label, width, **kwargs):
        """Campo de texto padrão"""
        return ft.TextField(
            label=label,
            width=width,
            border_color=Colors.BORDER_GRAY,
            **kwargs
        )
    
    @staticmethod
    def dropdown(label, options, width=None, value=None, **kwargs):
        """Dropdown padrão"""
        return ft.Dropdown(
            label=label,
            width=width or Sizes.INPUT_MEDIUM,
            options=[ft.dropdown.Option(opt) for opt in options],
            value=value,
            border_color=Colors.BORDER_GRAY,
            **kwargs
        )
    
    @staticmethod
    def table_header(columns):
        """Header padrão de tabela"""
        controls = []
        for text, width in columns:
            if width is None:
                controls.append(
                    ft.Container(
                        ft.Text(text, weight=ft.FontWeight.BOLD, size=Sizes.FONT_MEDIUM, text_align=ft.TextAlign.CENTER),
                        expand=True,
                        alignment=ft.alignment.center
                    )
                )
            else:
                controls.append(
                    ft.Container(
                        ft.Text(text, weight=ft.FontWeight.BOLD, size=Sizes.FONT_MEDIUM, text_align=ft.TextAlign.CENTER),
                        width=width,
                        alignment=ft.alignment.center
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
        """Seção de pesquisa padrão"""
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
        """Sidebar padrão"""
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