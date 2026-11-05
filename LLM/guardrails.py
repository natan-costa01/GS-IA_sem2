
import re
from typing import Union

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)


# ==========================================
# FUNÇÃO AUXILIAR
# ==========================================

def extrair_texto(entrada) -> str:
    """Extrai texto de entradas simples ou estruturadas."""
    if isinstance(entrada, str):
        return entrada

    partes = []

    for item in entrada:
        if isinstance(item, dict):
            conteudo = item.get("content", "")

            if isinstance(conteudo, str):
                partes.append(conteudo)

            elif isinstance(conteudo, list):
                for bloco in conteudo:
                    if isinstance(bloco, dict):
                        if bloco.get("type") == "input_text":
                            partes.append(bloco.get("text", ""))

    return "\n".join(partes)


# ==========================================
# GUARDRAIL 1 - DADOS PESSOAIS
# ==========================================

@input_guardrail(run_in_parallel=False)
def bloquear_dados_sensiveis(
    ctx: RunContextWrapper,
    agent: Agent,
    user_input: Union[str, list[TResponseInputItem]],
) -> GuardrailFunctionOutput:

    texto = extrair_texto(user_input)

    padroes = {
        "CPF": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
        "E-mail": r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
        "Telefone": r"(?<!\d)(?:\+55\s?)?\(?\d{2}\)?[\s-]?9?\d{4}[\s-]?\d{4}(?!\d)",
        "Senha": r"(?i)\b(?:minha\s+)?senha\s*(?:é|:|=)\s*\S+",
    }

    encontrados = [
        nome
        for nome, padrao in padroes.items()
        if re.search(padrao, texto)
    ]

    bloqueado = bool(encontrados)

    return GuardrailFunctionOutput(
        output_info={
            "guardrail": "dados_pessoais",
            "motivo": "Dados pessoais detectados" if bloqueado else "Entrada permitida",
            "categorias": encontrados,
        },
        tripwire_triggered=bloqueado,
    )


# ==========================================
# GUARDRAIL 2 - PROMPT INJECTION
# ==========================================

@input_guardrail(run_in_parallel=False)
def bloquear_prompt_injection(
    ctx: RunContextWrapper,
    agent: Agent,
    user_input: Union[str, list[TResponseInputItem]],
) -> GuardrailFunctionOutput:

    texto = extrair_texto(user_input).lower()

    padroes_suspeitos = [
        r"ignore (todas )?as instruções anteriores",
        r"ignore (all )?previous instructions",
        r"mostre (seu|o) prompt de sistema",
        r"revele (suas|as) instruções internas",
        r"system prompt",
        r"\[sistema\]",
        r"\[system\]",
        r"nova regra:",
        r"modo desenvolvedor",
        r"developer mode",
    ]

    encontrou = any(
        re.search(padrao, texto)
        for padrao in padroes_suspeitos
    )

    return GuardrailFunctionOutput(
        output_info={
            "guardrail": "prompt_injection",
            "motivo": (
                "Tentativa de manipulação detectada"
                if encontrou
                else "Entrada permitida"
            ),
        },
        tripwire_triggered=encontrou,
    )


# ==========================================
# GUARDRAIL 3 - SEGURANÇA DA RESPOSTA
# ==========================================

@output_guardrail
def validar_resposta(
    ctx: RunContextWrapper,
    agent: Agent,
    agent_output: str,
) -> GuardrailFunctionOutput:

    texto = str(agent_output)
    texto_lower = texto.lower()

    # Detecta possíveis vazamentos de informações internas.
    termos_internos = [
        "segredo_interno",
        "openai_api_key",
        "sk-proj-",
        "sk-",
        "begin system prompt",
    ]

    vazamento = any(
        termo in texto_lower
        for termo in termos_internos
    )

    # Detecta números com formato de CPF na resposta.
    cpf_exposto = bool(
        re.search(
            r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            texto,
        )
    )

    # Detecta afirmações incompatíveis com a FC-01
    # quando se referem à segunda via do RG.
    rg_gratuito = bool(
        re.search(
            r"segunda via do rg.{0,80}"
            r"(?:é gratuita|é grátis|não tem custo)",
            texto_lower,
        )
        or re.search(
            r"(?:gratuita|grátis|sem custo).{0,80}"
            r"segunda via do rg",
            texto_lower,
        )
    )

    bloqueado = vazamento or cpf_exposto or rg_gratuito

    motivos = []

    if vazamento:
        motivos.append("Possível vazamento de informação interna")

    if cpf_exposto:
        motivos.append("Possível exposição de CPF")

    if rg_gratuito:
        motivos.append("Informação incompatível com FC-01")

    return GuardrailFunctionOutput(
        output_info={
            "guardrail": "seguranca_saida",
            "motivos": motivos,
            "status": "Bloqueado" if bloqueado else "Permitido",
        },
        tripwire_triggered=bloqueado,
    )
