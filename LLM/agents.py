
import json
from pathlib import Path

from agents import Agent, Runner, function_tool
from pydantic import BaseModel, Field

from Data.data_loader import (
    carregar_ficha,
    montar_contexto,
)

from LLM.guardrails import (
    bloquear_dados_sensiveis,
    bloquear_prompt_injection,
    validar_resposta,
)

from LLM.prompt import (
    PROMPT_PRINCIPAL,
    PROMPT_TRIAGEM,
    PROMPT_ORIENTACAO,
    PROMPT_REVISAO,
)

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

MODELO = "gpt-4o-mini"


# ==========================================
# MODELOS DE DADOS
# ==========================================

class ResultadoTriagem(BaseModel):
    assunto: str = Field(
        description="Assunto principal identificado"
    )
    fichas: list[str] = Field(
        description="IDs das fichas relacionadas"
    )
    dentro_escopo: bool = Field(
        description="Se o assunto está coberto pelas fichas"
    )


class ResultadoRevisao(BaseModel):
    aprovado: bool
    justificativa: str
    resposta_corrigida: str


# ==========================================
# FERRAMENTA DE CONSULTA
# ==========================================

@function_tool
def consultar_ficha(codigo: str) -> str:
    """
    Consulta uma ficha de referência do projeto.
    Aceita códigos FC-01 até FC-07.
    """

    codigo = codigo.strip().upper()

    if codigo not in FICHAS:
        return "Ficha não encontrada."

    caminho = DOCUMENTS_DIR / FICHAS[codigo]

    if not caminho.is_file():
        return "Arquivo da ficha indisponível."

    conteudo = caminho.read_text(encoding="utf-8")

    return f"Fonte: {codigo}\n\n{conteudo}"


# ==========================================
# AGENTE 1 - TRIAGEM
# ==========================================

agente_triagem = Agent(
    name="Agente de Triagem",
    model=MODELO,
    output_type=ResultadoTriagem,
    instructions=PROMPT_TRIAGEM,
)

# ==========================================
# AGENTE 2 - ORIENTAÇÃO
# ==========================================

agente_orientacao = Agent(
    name="Agente de Orientação",
    model=MODELO,
    tools=[consultar_ficha],
    instructions=PROMPT_ORIENTACAO,
)


# ==========================================
# AGENTE 3 - REVISÃO
# ==========================================

agente_revisao = Agent(
    name="Agente de Revisão",
    model=MODELO,
    output_type=ResultadoRevisao,
    instructions=PROMPT_REVISAO,
)

# ==========================================
# AGENTE PRINCIPAL - COORDENADOR
# ==========================================

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

# ==========================================
# ORQUESTRAÇÃO DOS AGENTES
# ==========================================

async def executar_agentes(pergunta: str) -> str:
    """
    Executa triagem, orientação e revisão.

    Os guardrails de entrada são executados
    antes da primeira chamada aos especialistas.
    """

    # Primeira execução: aplica os guardrails de entrada.
    entrada = await Runner.run(
        agente_principal,
        pergunta,
    )

    # A triagem recebe somente a entrada já validada.
    triagem_run = await Runner.run(
        agente_triagem,
        pergunta,
    )
    triagem = triagem_run.final_output

    if not triagem.dentro_escopo:
        return (
            "Não encontrei essa informação nas fichas "
            "do projeto. Consulte o órgão competente. "
            "Este é um protótipo educacional, "
            "não um canal oficial."
        )

    fichas_validas = [
        codigo
        for codigo in triagem.fichas
        if codigo in FICHAS
    ]

    # O conteúdo autorizado é carregado localmente.
    referencias = []

    for codigo in fichas_validas:
        caminho = DOCUMENTS_DIR / FICHAS[codigo]

        if caminho.is_file():
            referencias.append(
                f"[{codigo}]\n"
                + caminho.read_text(encoding="utf-8")
            )

    contexto = "\n\n".join(referencias)

    if not contexto:
        return (
            "As fichas necessárias não estão disponíveis. "
            "Não posso confirmar a informação."
        )

    # O especialista consulta as fichas.
    orientacao_run = await Runner.run(
        agente_orientacao,
        (
            f"Pergunta:\n{pergunta}\n\n"
            f"Fichas selecionadas: {fichas_validas}\n"
            "Consulte as fichas antes de responder."
        ),
    )

    resposta = str(orientacao_run.final_output)

    # O revisor confere a resposta contra as fontes.
    revisao_run = await Runner.run(
        agente_revisao,
        (
            f"Pergunta:\n{pergunta}\n\n"
            f"Resposta:\n{resposta}\n\n"
            f"Fichas autorizadas:\n{contexto}"
        ),
    )

    revisao = revisao_run.final_output

    resposta_final = revisao.resposta_corrigida

    # A resposta final passa pelo guardrail de saída
    # do agente principal antes de ser devolvida.
    saida = await Runner.run(
        agente_principal,
        (
            "Reproduza a resposta aprovada abaixo, "
            "sem acrescentar informações:\n\n"
            f"{resposta_final}"
        ),
    )

    return str(saida.final_output)
