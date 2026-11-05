
from pathlib import Path
from typing import Optional


# ==========================================
# CONFIGURAÇÕES
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = BASE_DIR / "Documents"

FICHAS = {
    "FC-01": "FC-01_rg_segunda_via.md",
    "FC-02": "FC-02_cpf.md",
    "FC-03": "FC-03_titulo_de_eleitor.md",
    "FC-04": "FC-04_carteira_de_trabalho.md",
    "FC-05": "FC-05_certidoes.md",
    "FC-06": "FC-06_cnh_renovacao.md",
    "FC-07": "FC-07_regras_gerais.md",
}


# ==========================================
# CARREGAMENTO DE FICHAS
# ==========================================

def carregar_ficha(codigo: str) -> Optional[str]:
    """
    Carrega o conteúdo de uma ficha autorizada.

    Retorna:
        str: conteúdo da ficha.
        None: ficha inválida, ausente ou vazia.
    """

    if not isinstance(codigo, str):
        return None

    codigo = codigo.strip().upper()

    if codigo not in FICHAS:
        return None

    caminho = DOCUMENTS_DIR / FICHAS[codigo]

    if not caminho.is_file():
        return None

    try:
        conteudo = caminho.read_text(encoding="utf-8")

        if not conteudo.strip():
            return None

        return conteudo

    except (OSError, UnicodeError):
        return None


# ==========================================
# CARREGAR TODAS AS FICHAS
# ==========================================

def carregar_todas_fichas() -> dict[str, str]:
    """
    Carrega todas as fichas disponíveis.

    Retorna um dicionário:
        {
            "FC-01": "conteúdo...",
            "FC-02": "conteúdo..."
        }
    """

    documentos = {}

    for codigo in FICHAS:
        conteudo = carregar_ficha(codigo)

        if conteudo is not None:
            documentos[codigo] = conteudo

    return documentos


# ==========================================
# CARREGAR FICHAS SELECIONADAS
# ==========================================

def carregar_fichas_selecionadas(
    codigos: list[str],
) -> dict[str, str]:
    """
    Carrega apenas as fichas solicitadas.

    Ignora códigos inválidos e evita duplicatas.
    """

    documentos = {}

    for codigo in codigos:
        if not isinstance(codigo, str):
            continue

        codigo = codigo.strip().upper()

        if codigo in documentos:
            continue

        conteudo = carregar_ficha(codigo)

        if conteudo is not None:
            documentos[codigo] = conteudo

    return documentos


# ==========================================
# FORMATAR CONTEXTO PARA O AGENTE
# ==========================================

def montar_contexto(codigos: list[str]) -> str:
    """
    Prepara o conteúdo das fichas selecionadas
    para ser utilizado pelos agentes.
    """

    documentos = carregar_fichas_selecionadas(codigos)

    if not documentos:
        return "Nenhuma ficha autorizada disponível."

    partes = []

    for codigo, conteudo in documentos.items():
        partes.append(
            f"===== INÍCIO {codigo} =====\n"
            f"{conteudo}\n"
            f"===== FIM {codigo} ====="
        )

    return "\n\n".join(partes)


# ==========================================
# LISTAR FICHAS DISPONÍVEIS
# ==========================================

def listar_fichas() -> list[dict]:
    """
    Retorna informações sobre as fichas,
    sem expor seu conteúdo.
    """

    resultado = []

    for codigo, nome_arquivo in FICHAS.items():
        caminho = DOCUMENTS_DIR / nome_arquivo

        resultado.append({
            "codigo": codigo,
            "arquivo": nome_arquivo,
            "disponivel": (
                carregar_ficha(codigo) is not None
            ),
        })

    return resultado


# ==========================================
# TESTE LOCAL
# ==========================================

if __name__ == "__main__":
    print("Citizen Assist AI - Data Loader\n")

    for ficha in listar_fichas():
        status = (
            "OK"
            if ficha["disponivel"]
            else "INDISPONÍVEL"
        )

        print(
            f"{ficha['codigo']} | "
            f"{ficha['arquivo']} | "
            f"{status}"
        )

    documentos = carregar_todas_fichas()

    print(
        f"\nFichas carregadas: "
        f"{len(documentos)}/{len(FICHAS)}"
    )
