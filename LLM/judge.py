
"""
Citizen Assist AI - LLM-as-a-Judge

Responsável pela avaliação das respostas
produzidas pelos agentes do chatbot.

Modelo: GPT-4o-mini
Framework: OpenAI Agents SDK
"""

import json

from agents import Agent, Runner
from pydantic import BaseModel, Field

from Data.data_loader import montar_contexto
from LLM.prompt import PROMPT_JUIZ


# ==========================================
# CONFIGURAÇÕES
# ==========================================

MODELO_JUIZ = "gpt-4o-mini"


# ==========================================
# MODELO DE AVALIAÇÃO
# ==========================================

class ResultadoAvaliacao(BaseModel):

    fidelidade: int = Field(
        ge=0,
        le=5,
        description="Fidelidade às fichas, de 0 a 5."
    )

    completude: int = Field(
        ge=0,
        le=5,
        description="Completude da resposta, de 0 a 5."
    )

    seguranca: int = Field(
        ge=0,
        le=5,
        description="Segurança da resposta, de 0 a 5."
    )

    clareza: int = Field(
        ge=0,
        le=5,
        description="Clareza da resposta, de 0 a 5."
    )

    fontes_corretas: bool = Field(
        description="Se as fontes citadas estão corretas."
    )

    justificativa: str = Field(
        description="Justificativa das notas atribuídas."
    )


# ==========================================
# AGENTE AVALIADOR
# ==========================================

agente_juiz = Agent(
    name="LLM-as-a-Judge Citizen Assist AI",
    model=MODELO_JUIZ,
    instructions=PROMPT_JUIZ,
    output_type=ResultadoAvaliacao,
)


# ==========================================
# AVALIAÇÃO DE UMA RESPOSTA
# ==========================================

async def avaliar_resposta(
    caso: dict,
    resposta_obtida: str
) -> dict:

    """
    Avalia uma resposta do Citizen Assist AI.

    Parâmetros:
        caso: registro do Golden Dataset.
        resposta_obtida: resposta gerada pelo chatbot.

    Retorno:
        Dicionário contendo notas, média,
        aprovação e justificativa.
    """

    fontes = caso.get("fonte", [])

    # Recupera as fichas relacionadas ao caso.
    if fontes:
        contexto = montar_contexto(fontes)
    else:
        contexto = "Nenhuma ficha exigida."

    # Organiza os dados para o avaliador.
    dados_avaliacao = {
        "id": caso["id"],
        "pergunta": caso["pergunta"],
        "tipo": caso["tipo"],
        "resposta_esperada": caso["resposta_esperada"],
        "resposta_obtida": resposta_obtida,
        "fontes_esperadas": fontes,
        "fichas_autorizadas": contexto,
    }

    entrada = json.dumps(
        dados_avaliacao,
        ensure_ascii=False,
        indent=2
    )

    # Executa o agente juiz.
    resultado = await Runner.run(
        agente_juiz,
        entrada
    )

    avaliacao = resultado.final_output

    # Calcula a média dos critérios.
    notas = [
        avaliacao.fidelidade,
        avaliacao.completude,
        avaliacao.seguranca,
        avaliacao.clareza
    ]

    media = round(
        sum(notas) / len(notas),
        2
    )

    # Aprovação: todas as notas >= 4
    # e fontes consideradas corretas.
    aprovado = (
        all(nota >= 4 for nota in notas)
        and avaliacao.fontes_corretas
    )

    # Retorna o resultado estruturado.
    return {
        "id": caso["id"],
        "tipo": caso["tipo"],
        "fidelidade": avaliacao.fidelidade,
        "completude": avaliacao.completude,
        "seguranca": avaliacao.seguranca,
        "clareza": avaliacao.clareza,
        "fontes_corretas": avaliacao.fontes_corretas,
        "media": media,
        "aprovado": aprovado,
        "justificativa": avaliacao.justificativa
    }


# ==========================================
# COMPATIBILIDADE COM EVALUATE.PY
# ==========================================

async def avaliar_caso(
    caso: dict,
    resposta: str
) -> dict:
    """
    Permite chamar o avaliador usando
    o nome avaliar_caso().
    """
    return await avaliar_resposta(caso, resposta)
