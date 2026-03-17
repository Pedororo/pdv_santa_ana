import requests
from typing import List, Dict, Optional


class MovimentacaoAPI:
    """Classe para gerenciar requisições à API de movimentações de estoque"""

    BASE_URL = "http://localhost:8000"

    # ── Tipos ──────────────────────────────────────────────────────────────────
    TIPO_ENTRADA = "ENTRADA"
    TIPO_SAIDA   = "SAIDA"

    # ── Motivos ────────────────────────────────────────────────────────────────
    MOTIVO_CADASTRO_INICIAL = "CADASTRO_INICIAL"
    MOTIVO_COMPRA           = "COMPRA"
    MOTIVO_VENDA            = "VENDA"
    MOTIVO_AJUSTE           = "AJUSTE"
    MOTIVO_PERDA            = "PERDA"
    MOTIVO_DEVOLUCAO        = "DEVOLUCAO"
    MOTIVO_INVENTARIO       = "INVENTARIO"

    # Motivos válidos por tipo (para uso nos dropdowns)
    MOTIVOS_ENTRADA = ["COMPRA", "DEVOLUCAO", "INVENTARIO", "CADASTRO_INICIAL"]
    MOTIVOS_SAIDA   = ["VENDA", "PERDA", "AJUSTE", "INVENTARIO"]

    @staticmethod
    def registrar_movimentacao(movimentacao_data: Dict) -> Optional[Dict]:
        """
        Registra uma movimentação de estoque.

        movimentacao_data deve conter:
        - tipo: "ENTRADA" | "SAIDA"
        - motivo: "CADASTRO_INICIAL" | "COMPRA" | "VENDA" | "AJUSTE" |
                  "PERDA" | "DEVOLUCAO" | "INVENTARIO"
        - quantidade: int (> 0)
        - produto_id: int
        - venda_id: int  (0 se não vinculado a venda)

        Uso automático:
        - Finalizar venda  → tipo=SAIDA,   motivo=VENDA,            venda_id=<id>
        - Cancelar venda   → tipo=ENTRADA, motivo=DEVOLUCAO,        venda_id=<id>
        - Cadastrar produto→ tipo=ENTRADA, motivo=CADASTRO_INICIAL, venda_id=0
        """
        try:
            response = requests.post(
                f"{MovimentacaoAPI.BASE_URL}/movimentacoes/",
                json=movimentacao_data,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao registrar movimentação: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except Exception:
                    detail = e.response.text
                print(f"Detalhes: {detail}")
            return None

    @staticmethod
    def listar_por_produto(produto_id: int) -> List[Dict]:
        """Lista todas as movimentações de um produto específico."""
        try:
            response = requests.get(
                f"{MovimentacaoAPI.BASE_URL}/movimentacoes/produto/{produto_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar movimentações do produto {produto_id}: {e}")
            return []

    @staticmethod
    def listar_por_venda(venda_id: int) -> List[Dict]:
        """Lista todas as movimentações vinculadas a uma venda."""
        try:
            response = requests.get(
                f"{MovimentacaoAPI.BASE_URL}/movimentacoes/venda/{venda_id}"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao listar movimentações da venda {venda_id}: {e}")
            return []

    @staticmethod
    def exportar(
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        tipo: Optional[str] = None,
        salvar_em: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Exporta movimentações em Excel via GET /movimentacoes/exportar

        Parâmetros:
        - data_inicio: str  formato "YYYY-MM-DD"  (opcional)
        - data_fim:    str  formato "YYYY-MM-DD"  (opcional)
        - tipo:        str  "ENTRADA" | "SAIDA"   (opcional)
        - salvar_em:   str  caminho para salvar o arquivo .xlsx (opcional)

        Retorna os bytes do arquivo Excel, ou None em caso de erro.

        Exemplos de uso:
            # Exportar tudo
            MovimentacaoAPI.exportar()

            # Por período
            MovimentacaoAPI.exportar(data_inicio="2026-01-01", data_fim="2026-03-31")

            # Apenas entradas do mês
            MovimentacaoAPI.exportar(data_inicio="2026-03-01", data_fim="2026-03-31", tipo="ENTRADA")

            # Salvar direto em arquivo
            MovimentacaoAPI.exportar(data_inicio="2026-03-01", salvar_em="/tmp/mov.xlsx")
        """
        params = {}
        if data_inicio:
            params["data_inicio"] = data_inicio
        if data_fim:
            params["data_fim"] = data_fim
        if tipo and tipo in (MovimentacaoAPI.TIPO_ENTRADA, MovimentacaoAPI.TIPO_SAIDA):
            params["tipo"] = tipo

        try:
            response = requests.get(
                f"{MovimentacaoAPI.BASE_URL}/movimentacoes/exportar",
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            conteudo = response.content

            if salvar_em:
                with open(salvar_em, "wb") as f:
                    f.write(conteudo)
                print(f"Exportação salva em: {salvar_em}")

            return conteudo

        except requests.exceptions.RequestException as e:
            print(f"Erro ao exportar movimentações: {e}")
            if hasattr(e, "response") and e.response is not None:
                try:
                    detail = e.response.json().get("detail", e.response.text)
                except Exception:
                    detail = e.response.text
                print(f"Detalhes: {detail}")
            return None