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

"""
Citizen Assist AI
Pacote responsável pelos agentes de IA,
guardrails e avaliação do sistema.
"""

from .agents import (
    agente_principal,
    agente_triagem,
    agente_orientacao,
    agente_revisao,
    executar_agentes,
)

from .guardrails import (
    bloquear_dados_sensiveis,
    bloquear_prompt_injection,
    validar_resposta,
)