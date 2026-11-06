
"""Orquestração multiagente do Citizen Assist AI."""

import re
import unicodedata
from pathlib import Path

from agents import Agent, Runner, function_tool
from pydantic import BaseModel, Field

from Data.data_loader import carregar_ficha, montar_contexto
from LLM.guardrails import (
    bloquear_dados_sensiveis,
    bloquear_prompt_injection,
    validar_resposta,
    verificar_entrada,
    verificar_saida,
)
from LLM.prompt import (
    PROMPT_PRINCIPAL,
    PROMPT_TRIAGEM,
    PROMPT_ORIENTACAO,
    PROMPT_REVISAO,
)

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

MODELO = "gpt-4o-mini"
AVISO = "Este é um protótipo educacional, não um canal oficial."


class ResultadoTriagem(BaseModel):
    assunto: str = Field(description="Assunto principal identificado")
    fichas: list[str] = Field(description="IDs das fichas relacionadas")
    dentro_escopo: bool = Field(description="Se o tema está coberto pelas fichas")


class ResultadoRevisao(BaseModel):
    aprovado: bool
    justificativa: str
    resposta_corrigida: str


@function_tool
def consultar_ficha(codigo: str) -> str:
    """Consulta uma ficha de referência, usando códigos FC-01 a FC-07."""

    if not isinstance(codigo, str):
        return "Ficha não encontrada."

    codigo = codigo.strip().upper()

    if codigo not in FICHAS:
        return "Ficha não encontrada."

    conteudo = carregar_ficha(codigo)

    if conteudo is None:
        return "Arquivo da ficha indisponível."

    return f"Fonte: {codigo}\n\n{conteudo}"


agente_triagem = Agent(
    name="Agente de Triagem",
    model=MODELO,
    output_type=ResultadoTriagem,
    instructions=PROMPT_TRIAGEM,
)

agente_orientacao = Agent(
    name="Agente de Orientação",
    model=MODELO,
    tools=[consultar_ficha],
    instructions=PROMPT_ORIENTACAO,
)

agente_revisao = Agent(
    name="Agente de Revisão",
    model=MODELO,
    output_type=ResultadoRevisao,
    instructions=PROMPT_REVISAO,
)

agente_principal = Agent(
    name="Citizen Assist AI",
    model=MODELO,
    instructions=PROMPT_PRINCIPAL,
    input_guardrails=[
        bloquear_dados_sensiveis,
        bloquear_prompt_injection,
    ],
    output_guardrails=[
        validar_resposta,
    ],
)


def normalizar(texto: str) -> str:
    """Normaliza texto para identificação de assuntos."""

    texto = unicodedata.normalize("NFKD", texto.casefold())

    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )


def identificar_fichas_por_palavras(pergunta: str) -> list[str]:
    """Roteamento auxiliar sem gerar respostas factuais."""

    texto = normalizar(pergunta)

    regras = {
        "FC-01": (
            r"\brg\b",
            r"\bidentidade\b",
        ),
        "FC-02": (
            r"\bcpf\b",
            r"\bcadastro de pessoa fisica\b",
        ),
        "FC-03": (
            r"\bvoto\b",
            r"\bvotar\b",
            r"\bvotacao\b",
            r"\beleitor(?:al)?\b",
            r"\btitulo de eleitor\b",
        ),
        "FC-04": (
            r"\bctps\b",
            r"\bcarteira de trabalho\b",
        ),
        "FC-05": (
            r"\bcertid(?:ao|oes)\b",
        ),
        "FC-06": (
            r"\bcnh\b",
            r"\bhabilitacao\b",
        ),
        "FC-07": (
            r"\blibras\b",
            r"\binterprete\b",
            r"\bacessibilidade\b",
            r"\batendimento prioritario\b",
            r"\bhorario de atendimento\b",
        ),
    }

    return [
        codigo
        for codigo, padroes in regras.items()
        if any(re.search(padrao, texto) for padrao in padroes)
    ]


async def executar_agentes(pergunta: str) -> str:
    """
    Fluxo:
    Entrada segura -> Triagem -> Documentos ->
    Orientação -> Revisão -> Saída segura.
    """

    # 1. VALIDAR ENTRADA

    if not isinstance(pergunta, str) or not pergunta.strip():
        return (
            "Não entendi sua pergunta. "
            f"Por favor, reformule sua dúvida. {AVISO}"
        )

    pergunta = pergunta.strip()

    motivo_entrada = verificar_entrada(pergunta)

    if motivo_entrada == "dados_pessoais":
        return (
            "Por segurança, não informe dados pessoais neste chat. "
            "Não realizo consultas cadastrais nem agendamentos. "
            "Utilize os canais oficiais do órgão competente. "
            f"{AVISO}"
        )

    if motivo_entrada == "prompt_injection":
        return (
            "Não posso seguir instruções que alterem as regras "
            "do assistente ou revelem instruções internas. "
            f"{AVISO}"
        )

    # 2. TRIAGEM

    triagem_run = await Runner.run(
        agente_triagem,
        pergunta,
    )

    triagem = triagem_run.final_output

    assunto = (triagem.assunto or "").strip().lower()

    print(
        "[Triagem]",
        assunto,
        triagem.fichas,
        triagem.dentro_escopo,
    )

    if assunto == "entrada_invalida":
        return (
            "Não entendi sua pergunta. "
            f"Pode reformulá-la? {AVISO}"
        )

    if assunto == "aviso_de_limitacao":
        return (
            "O Citizen Assist AI não é um canal oficial. "
            "Confirme as informações no órgão competente. "
            f"{AVISO}"
        )

    # 3. IDENTIFICAR FICHAS

    fichas_detectadas = identificar_fichas_por_palavras(pergunta)

    fichas_validas = list(
        dict.fromkeys(
            codigo.strip().upper()
            for codigo in triagem.fichas
            if (
                isinstance(codigo, str)
                and codigo.strip().upper() in FICHAS
            )
        )
    )

    # Recupera fichas que a triagem eventualmente omitiu.

    for codigo in fichas_detectadas:
        if codigo not in fichas_validas:
            fichas_validas.append(codigo)

    if not fichas_validas or (
        not triagem.dentro_escopo
        and not fichas_detectadas
    ):
        return (
            "Não encontrei essa informação nas fichas do projeto. "
            f"Consulte o órgão competente. {AVISO}"
        )

    # 4. CARREGAR DOCUMENTOS

    fichas_disponiveis = [
        codigo
        for codigo in fichas_validas
        if carregar_ficha(codigo) is not None
    ]

    if not fichas_disponiveis:
        return (
            "As fichas necessárias não estão disponíveis. "
            "Não posso confirmar a informação solicitada. "
            f"{AVISO}"
        )

    contexto = montar_contexto(fichas_disponiveis)

    # 5. ORIENTAÇÃO

    orientacao_run = await Runner.run(
        agente_orientacao,
        (
            f"Pergunta do cidadão:\n{pergunta}\n\n"
            f"Fichas autorizadas: {fichas_disponiveis}\n\n"
            "Consulte consultar_ficha para as fichas relevantes "
            "antes de responder. Não invente informações "
            "nem use outras fichas."
        ),
    )

    resposta_orientacao = str(
        orientacao_run.final_output or ""
    ).strip()

    if not resposta_orientacao:
        return (
            "Não foi possível gerar uma orientação. "
            f"Consulte o órgão competente. {AVISO}"
        )

    # 6. REVISÃO

    revisao_run = await Runner.run(
        agente_revisao,
        (
            f"Pergunta original:\n{pergunta}\n\n"
            "Resposta do agente de orientação:\n"
            f"{resposta_orientacao}\n\n"
            f"Fichas autorizadas:\n{contexto}\n\n"
            "Revise exatidão, completude, segurança e fontes. "
            "Preencha resposta_corrigida mesmo se a resposta "
            "original for aprovada."
        ),
    )

    revisao = revisao_run.final_output

    resposta_final = (
        revisao.resposta_corrigida or ""
    ).strip()

    if not resposta_final:
        return (
            "Não foi possível validar a resposta. "
            f"Consulte o órgão competente. {AVISO}"
        )

    # 7. GUARDRAIL DE SAÍDA

    motivo_saida = verificar_saida(resposta_final)

    if motivo_saida:
        print(
            "[Guardrail de saída]",
            motivo_saida,
        )

        return (
            "Não foi possível fornecer uma resposta segura. "
            f"Consulte o órgão competente. {AVISO}"
        )

    # A resposta revisada é devolvida diretamente.
    return resposta_final
