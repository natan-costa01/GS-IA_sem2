
import json
from pathlib import Path

from agents import Agent, Runner, function_tool
from pydantic import BaseModel, Field
from LLM.guardrails import verificar_saida
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
    Executa o fluxo completo do Citizen Assist AI:

    1. Validação de entrada
    2. Triagem
    3. Carregamento das fichas
    4. Orientação
    5. Revisão
    6. Validação de saída
    7. Resposta final
    """

    # ======================================
    # 1. VALIDAÇÃO DA ENTRADA
    # ======================================

    if not isinstance(pergunta, str) or not pergunta.strip():
        return (
            "Não entendi sua pergunta. "
            "Por favor, reformule sua dúvida. "
            "Este é um protótipo educacional, não um canal oficial."
        )

    pergunta = pergunta.strip()

    # Verificação de segurança antes de chamar a API
    from LLM.guardrails import verificar_entrada, verificar_saida

    motivo_entrada = verificar_entrada(pergunta)

    if motivo_entrada == "dados_pessoais":
        return (
            "Por segurança, não informe dados pessoais neste chat. "
            "Não realizo consultas cadastrais nem agendamentos. "
            "Utilize os canais oficiais do órgão competente. "
            "Este é um protótipo educacional, não um canal oficial."
        )

    if motivo_entrada == "prompt_injection":
        return (
            "Não posso seguir instruções que alterem as regras "
            "do assistente ou revelem instruções internas. "
            "Posso ajudar com orientações sobre documentos. "
            "Este é um protótipo educacional, não um canal oficial."
        )

    # ======================================
    # 2. AGENTE DE TRIAGEM
    # ======================================

    triagem_run = await Runner.run(
        agente_triagem,
        pergunta
    )

    triagem = triagem_run.final_output

    print("\n=== DEBUG TRIAGEM ===")
    print("Assunto:", triagem.assunto)
    print("Fichas:", triagem.fichas)
    print("Dentro do escopo:", triagem.dentro_escopo)

    if triagem.assunto.lower().strip() == "entrada_invalida":
        return (
            "Não entendi sua pergunta. Pode reformulá-la? "
            "Por exemplo: Quanto custa a segunda via do RG? "
            "Este é um protótipo educacional, não um canal oficial."
        )

    if triagem.assunto.lower().strip() == "aviso_de_limitacao":
        return (
            "Não, o Citizen Assist AI não é um canal oficial. "
            "Este é um protótipo educacional. "
            "Confirme as informações no órgão competente."
        )

    if not triagem.dentro_escopo:
        return (
            "Não encontrei essa informação nas fichas do projeto. "
            "Consulte o órgão competente. "
            "Este é um protótipo educacional, não um canal oficial."
        )

    # ======================================
    # 3. SELEÇÃO DAS FICHAS
    # ======================================

    fichas_validas = list(dict.fromkeys(
        codigo
        for codigo in triagem.fichas
        if codigo in FICHAS
    ))

    referencias = []

    for codigo in fichas_validas:

        caminho = DOCUMENTS_DIR / FICHAS[codigo]

        if caminho.is_file():

            conteudo = caminho.read_text(
                encoding="utf-8"
            )

            referencias.append(
                f"[{codigo}]\n{conteudo}"
            )

    contexto = "\n\n".join(referencias)

    if not contexto:
        return (
            "As fichas necessárias não estão disponíveis. "
            "Não posso confirmar a informação solicitada. "
            "Este é um protótipo educacional, não um canal oficial."
        )

    # ======================================
    # 4. AGENTE DE ORIENTAÇÃO
    # ======================================

    orientacao_run = await Runner.run(
        agente_orientacao,
        (
            f"Pergunta do cidadão:\n{pergunta}\n\n"
            f"Fichas autorizadas: {fichas_validas}\n\n"
            "Consulte as fichas autorizadas antes de responder. "
            "Não invente informações."
        )
    )

    resposta_orientacao = str(
        orientacao_run.final_output
    ).strip()

    print("\n=== DEBUG ORIENTAÇÃO ===")
    print("Resposta:", resposta_orientacao)

    if not resposta_orientacao:
        return (
            "Não foi possível gerar uma orientação. "
            "Consulte o órgão competente. "
            "Este é um protótipo educacional, não um canal oficial."
        )

    # ======================================
    # 5. AGENTE DE REVISÃO
    # ======================================

    revisao_run = await Runner.run(
        agente_revisao,
        (
            f"Pergunta original:\n{pergunta}\n\n"
            f"Resposta do agente de orientação:\n"
            f"{resposta_orientacao}\n\n"
            f"Fichas autorizadas:\n{contexto}\n\n"
            "Verifique se a resposta está fundamentada "
            "nas fichas e corrija eventuais inconsistências. "
            "Retorne a resposta final no campo resposta_corrigida."
        )
    )

    revisao = revisao_run.final_output

    print("\n=== DEBUG REVISÃO ===")
    print("Aprovado:", revisao.aprovado)
    print("Justificativa:", revisao.justificativa)
    print("Resposta corrigida:", revisao.resposta_corrigida)

    # ======================================
    # 6. VALIDAÇÃO DA RESPOSTA
    # ======================================

    resposta_final = (
        revisao.resposta_corrigida or ""
    ).strip()

    if not resposta_final:
        return (
            "Não foi possível validar a resposta. "
            "Consulte o órgão competente. "
            "Este é um protótipo educacional, não um canal oficial."
        )

    # A revisão pode reprovar a resposta original
    # e fornecer uma versão corrigida.
    # Por isso, não bloqueamos apenas por
    # revisao.aprovado ser False.

    motivo_saida = verificar_saida(
        resposta_final
    )

    if motivo_saida:
        print(
            "Resposta bloqueada pelo guardrail:",
            motivo_saida
        )

        return (
            "Não foi possível fornecer uma resposta segura. "
            "Consulte o órgão competente. "
            "Este é um protótipo educacional, não um canal oficial."
        )

    # ======================================
    # 7. RESPOSTA FINAL
    # ======================================

    # Não executa novamente o agente principal.
    # Retorna diretamente a resposta revisada.

    return resposta_final

def identificar_fichas_por_palavras(pergunta: str) -> list[str]:
    texto = pergunta.lower()

    palavras = {
        "FC-01": ["rg", "identidade"],
        "FC-02": ["cpf"],
        "FC-03": ["título de eleitor", "votar"],
        "FC-04": ["carteira de trabalho", "ctps"],
        "FC-05": ["certidão", "certidoes", "certidões"],
        "FC-06": ["cnh", "habilitação"],
        "FC-07": ["libras", "horário de atendimento"],
    }

    return [
        codigo
        for codigo, termos in palavras.items()
        if any(termo in texto for termo in termos)
    ]