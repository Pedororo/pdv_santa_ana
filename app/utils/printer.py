"""
Módulo de impressão ESC/POS — PDV Santa Ana
Suporta impressoras térmicas de cupom via USB, rede (TCP) ou serial.

Dependência:
    pip install python-escpos

Detecção automática de impressora:
    1. Tenta USB (VID/PID configuráveis)
    2. Tenta rede (IP/porta configuráveis)
    3. Fallback: salva .txt na pasta Downloads e avisa o usuário
"""

from datetime import datetime

# ============================================================================
# CONFIGURAÇÃO — ajuste conforme sua impressora
# ============================================================================

# USB — rode `lsusb` (Linux) ou Device Manager (Windows) para encontrar os IDs
PRINTER_USB_VENDOR  = 0x04b8   # Epson padrão — troque pelo seu
PRINTER_USB_PRODUCT = 0x0202   # modelo específico

# Rede (TCP)
PRINTER_NET_HOST = "192.168.1.100"
PRINTER_NET_PORT = 9100

# Largura do papel em caracteres (57mm ≈ 32 chars | 80mm ≈ 48 chars)
PAPER_WIDTH = 48


# ============================================================================
# HELPERS DE FORMATAÇÃO DE TEXTO (sem depender da lib)
# ============================================================================

def _linha(texto: str, largura: int = PAPER_WIDTH) -> str:
    return texto[:largura].ljust(largura)

def _centralizar(texto: str, largura: int = PAPER_WIDTH) -> str:
    return texto.center(largura)

def _dividir(largura: int = PAPER_WIDTH) -> str:
    return "-" * largura

def _col2(esq: str, dir: str, largura: int = PAPER_WIDTH) -> str:
    """Dois campos: esquerda e direita na mesma linha."""
    espaco = largura - len(esq) - len(dir)
    if espaco < 1:
        espaco = 1
    return esq + " " * espaco + dir

def _col4(desc: str, qtd: str, unit: str, total: str, largura: int = PAPER_WIDTH) -> str:
    """Quatro colunas para itens de venda."""
    # Reserva espaço fixo para qtd, unit, total
    w_qtd   = 4
    w_unit  = 8
    w_total = 9
    w_desc  = largura - w_qtd - w_unit - w_total - 3  # 3 espaços separadores
    desc_fmt  = desc[:w_desc].ljust(w_desc)
    qtd_fmt   = qtd[:w_qtd].rjust(w_qtd)
    unit_fmt  = unit[:w_unit].rjust(w_unit)
    total_fmt = total[:w_total].rjust(w_total)
    return f"{desc_fmt} {qtd_fmt} {unit_fmt} {total_fmt}"


# ============================================================================
# MONTAGEM DAS LINHAS DO CUPOM (texto puro — independente da lib)
# ============================================================================

def _cupom_venda(
    venda_id: int,
    data_fmt: str,
    itens: list,       # lista de dicts: {nome, quantidade, preco_unitario, subtotal}
    subtotal: float,
    desconto: float,
    acrescimo: float,
    total: float,
    pagamento: str,
    troco: float = 0.0,
    valor_recebido: float = 0.0,
    usuario: str = "",
) -> list[str]:
    """Retorna lista de linhas prontas para impressão."""
    W = PAPER_WIDTH
    linhas = [
        _centralizar("FARMACIA SANTA ANA", W),
        _dividir(W),
        _centralizar("CUPOM NAO FISCAL", W),
        _dividir(W),
        _col2(f"Venda #: {venda_id}", data_fmt, W),
    ]
    if usuario:
        linhas.append(_col2("Operador:", usuario, W))
    linhas += [
        _dividir(W),
        _col4("DESCRICAO", "QTD", "UNIT.", "TOTAL", W),
        _dividir(W),
    ]
    for item in itens:
        nome    = str(item.get("nome") or item.get("descricao") or f"Produto #{item.get('produto_id','')}")
        qtd     = str(item.get("quantidade", 1))
        unit    = f"R${float(item.get('preco_unitario', 0)):.2f}"
        subtot  = f"R${float(item.get('subtotal', 0)):.2f}"
        linhas.append(_col4(nome, qtd, unit, subtot, W))
    linhas += [
        _dividir(W),
        _col2("Subtotal:", f"R$ {subtotal:.2f}", W),
    ]
    if desconto > 0:
        linhas.append(_col2("Desconto:", f"-R$ {desconto:.2f}", W))
    if acrescimo > 0:
        linhas.append(_col2("Acrescimo:", f"+R$ {acrescimo:.2f}", W))
    linhas += [
        _dividir(W),
        _col2("TOTAL:", f"R$ {total:.2f}", W),
        _dividir(W),
        _col2("Pagamento:", pagamento, W),
    ]
    if valor_recebido > 0:
        linhas.append(_col2("Valor recebido:", f"R$ {valor_recebido:.2f}", W))
    if troco > 0:
        linhas.append(_col2("Troco:", f"R$ {troco:.2f}", W))
    linhas += [
        _dividir(W),
        _centralizar("Obrigado pela preferencia!", W),
        _centralizar(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), W),
        "",
        "",
        "",
    ]
    return linhas


def _cupom_turno(
    turno_id: int,
    usuario: str,
    abertura: str,
    fechamento: str,
    qtd_vendas: int,
    total_vendas: float,
    por_forma: dict,   # {"Dinheiro": 0.0, "Cartão Débito": 0.0, ...}
    valor_inicial: float,
    valor_esperado: float,
    valor_informado: float,
    diferenca: float,
    observacoes: str = "",
) -> list[str]:
    W = PAPER_WIDTH
    sinal = "+" if diferenca >= 0 else ""
    linhas = [
        _centralizar("FARMACIA SANTA ANA", W),
        _dividir(W),
        _centralizar(f"RESUMO DE TURNO #{turno_id}", W),
        _dividir(W),
        _col2("Operador:", usuario, W),
        _col2("Abertura:", abertura, W),
        _col2("Fechamento:", fechamento, W),
        _dividir(W),
        _centralizar("VENDAS DO TURNO", W),
        _dividir(W),
        _col2("Quantidade:", str(qtd_vendas), W),
        _col2("Total faturado:", f"R$ {total_vendas:.2f}", W),
        _dividir(W),
        _centralizar("POR FORMA DE PAGAMENTO", W),
        _dividir(W),
    ]
    for forma, valor in por_forma.items():
        linhas.append(_col2(f"{forma}:", f"R$ {float(valor):.2f}", W))
    linhas += [
        _dividir(W),
        _centralizar("CONFERENCIA DE CAIXA", W),
        _dividir(W),
        _col2("Valor inicial:", f"R$ {valor_inicial:.2f}", W),
        _col2("Esperado:", f"R$ {valor_esperado:.2f}", W),
        _col2("Informado:", f"R$ {valor_informado:.2f}", W),
        _col2("Diferenca:", f"{sinal}R$ {abs(diferenca):.2f}", W),
    ]
    if observacoes:
        linhas += [
            _dividir(W),
            "Obs: " + observacoes,
        ]
    linhas += [
        _dividir(W),
        _centralizar(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), W),
        "",
        "",
        "",
    ]
    return linhas


# ============================================================================
# IMPRESSÃO REAL
# ============================================================================

def _get_printer():
    """
    Tenta obter uma impressora ESC/POS.
    Ordem: USB → Rede → None (fallback texto).
    Retorna instância da impressora ou None.
    """
    try:
        from escpos.printer import Usb, Network
        # Tenta USB primeiro
        try:
            p = Usb(PRINTER_USB_VENDOR, PRINTER_USB_PRODUCT, timeout=0, in_ep=0x82, out_ep=0x01)
            return p
        except Exception:
            pass
        # Tenta rede
        try:
            p = Network(PRINTER_NET_HOST, PRINTER_NET_PORT, timeout=5)
            return p
        except Exception:
            pass
    except ImportError:
        pass
    return None


def _imprimir_linhas(linhas: list[str]) -> tuple[bool, str]:
    """
    Envia linhas para a impressora.
    Retorna (sucesso: bool, mensagem: str).
    """
    printer = _get_printer()

    if printer:
        try:
            printer.set(align="left", font="a", bold=False, underline=0, width=1, height=1)
            for linha in linhas:
                printer.text(linha + "\n")
            printer.cut()
            try:
                printer.close()
            except Exception:
                pass
            return True, "Impresso com sucesso!"
        except Exception as e:
            try:
                printer.close()
            except Exception:
                pass
            return False, f"Erro na impressora: {e}"
    else:
        # Fallback — salva .txt na pasta Downloads
        return _salvar_txt(linhas)


def _salvar_txt(linhas: list[str]) -> tuple[bool, str]:
    """Fallback: salva cupom como .txt na pasta Downloads."""
    import os
    try:
        nome = f"cupom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        caminho = os.path.join(os.path.expanduser("~"), "Downloads", nome)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("\n".join(linhas))
        return True, f"Impressora não encontrada. Cupom salvo em Downloads/{nome}"
    except Exception as e:
        return False, f"Erro ao salvar cupom: {e}"


# ============================================================================
# API PÚBLICA — funções chamadas pelas views
# ============================================================================

def imprimir_cupom_venda(
    venda_id: int,
    data_fmt: str,
    itens: list,
    subtotal: float,
    desconto: float,
    acrescimo: float,
    total: float,
    pagamento: str,
    troco: float = 0.0,
    valor_recebido: float = 0.0,
    usuario: str = "",
) -> tuple[bool, str]:
    """Imprime cupom de venda. Retorna (sucesso, mensagem)."""
    linhas = _cupom_venda(
        venda_id=venda_id,
        data_fmt=data_fmt,
        itens=itens,
        subtotal=subtotal,
        desconto=desconto,
        acrescimo=acrescimo,
        total=total,
        pagamento=pagamento,
        troco=troco,
        valor_recebido=valor_recebido,
        usuario=usuario,
    )
    return _imprimir_linhas(linhas)


def imprimir_resumo_turno(
    turno_id: int,
    usuario: str,
    abertura: str,
    fechamento: str,
    qtd_vendas: int,
    total_vendas: float,
    por_forma: dict,
    valor_inicial: float,
    valor_esperado: float,
    valor_informado: float,
    diferenca: float,
    observacoes: str = "",
) -> tuple[bool, str]:
    """Imprime resumo de turno. Retorna (sucesso, mensagem)."""
    linhas = _cupom_turno(
        turno_id=turno_id,
        usuario=usuario,
        abertura=abertura,
        fechamento=fechamento,
        qtd_vendas=qtd_vendas,
        total_vendas=total_vendas,
        por_forma=por_forma,
        valor_inicial=valor_inicial,
        valor_esperado=valor_esperado,
        valor_informado=valor_informado,
        diferenca=diferenca,
        observacoes=observacoes,
    )
    return _imprimir_linhas(linhas)