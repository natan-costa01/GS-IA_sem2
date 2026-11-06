
import sys
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv


# ==========================================
# CONFIGURAÇÃO
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
LIVE_DIR = Path(__file__).resolve().parent
CSS_PATH = LIVE_DIR / "style.css"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from LLM.agents import executar_agentes


APP_NAME = "Citizen Assist AI"

AVISO = (
    "Este é um protótipo educacional, não um canal "
    "oficial. Confirme as informações no órgão competente."
)

MENSAGEM_INICIAL = (
    "Olá! Sou o **Citizen Assist AI**, seu assistente "
    "virtual de orientação ao cidadão.\n\n"
    "Posso ajudar com informações sobre **RG, CPF, "
    "título de eleitor, carteira de trabalho, "
    "certidões, CNH e atendimento presencial**.\n\n"
    "Como posso ajudar você hoje?\n\n"
    "**Privacidade:** não compartilhe CPF, endereço, "
    "telefone, senhas ou outros dados pessoais."
)


# ==========================================
# HISTÓRICO
# ==========================================

def novo_historico():
    return [
        {
            "role": "assistant",
            "content": MENSAGEM_INICIAL
        }
    ]


# ==========================================
# FUNÇÕES DO CHAT
# ==========================================

def preparar_mensagem(mensagem, historico):
    historico = list(historico or novo_historico())
    pergunta = (mensagem or "").strip()

    if not pergunta:
        return "", historico, ""

    historico.append({
        "role": "user",
        "content": pergunta
    })

    return "", historico, pergunta


async def processar_resposta(historico, pergunta):
    historico = list(historico or novo_historico())

    if not pergunta:
        return historico

    try:
        resposta = await executar_agentes(pergunta)
        resposta = str(resposta or "").strip()

        if not resposta:
            resposta = (
                "Não foi possível gerar uma resposta. "
                "Por favor, reformule sua pergunta.\n\n"
                + AVISO
            )

    except Exception as erro:
        import traceback

        print("\n========== ERRO CITIZEN ASSIST AI ==========")
        traceback.print_exc()
        print("============================================\n")

        resposta = (
            "Ocorreu um problema ao processar sua pergunta. "
            "Tente novamente.\n\n" + AVISO
        )

    historico.append({
        "role": "assistant",
        "content": resposta
    })

    return historico


def limpar_conversa():
    return novo_historico(), "", ""


# ==========================================
# ELEMENTOS VISUAIS
# ==========================================

SIDEBAR_HTML = """
<div class="brand">
    <div class="eyebrow">ASSISTENTE DIGITAL</div>

    <h1>Citizen<br>Assist AI</h1>

    <p>
        Inteligência artificial para
        orientação ao cidadão.
    </p>

    <span class="brand-badge">
        PROTÓTIPO EDUCACIONAL
    </span>
</div>

<div class="section-heading">
    SERVIÇOS DISPONÍVEIS
</div>

<div class="services">
    <div>RG e CPF</div>
    <div>Título de eleitor</div>
    <div>Certidões e trabalho</div>
    <div>CNH</div>
    <div>Atendimento e acessibilidade</div>
</div>

<div class="section-heading">
    PERGUNTAS SUGERIDAS
</div>
"""

CHAT_HEADER_HTML = """
<div class="chat-heading">
    <div>
        <h2>Chat de atendimento</h2>
        <p>
            Orientações baseadas nas fichas
            documentais do projeto.
        </p>
    </div>

    <span class="chat-indicator">
        ASSISTENTE VIRTUAL
    </span>
</div>
"""

PRIVACY_HTML = """
<div class="privacy-line">
    Não compartilhe dados pessoais.
    Este assistente é um protótipo educacional,
    não realiza agendamentos e não substitui
    os canais oficiais de atendimento.
</div>
"""

SIDEBAR_FOOTER = """
<div class="sidebar-note">
    Citizen Assist AI<br>
    Projeto acadêmico de Inteligência Artificial.<br>
    Informações sujeitas à confirmação
    nos órgãos competentes.
</div>
"""


# ==========================================
# INTERFACE
# ==========================================

with gr.Blocks(
    title=APP_NAME,
    css_paths=str(CSS_PATH),
    fill_height=True
) as demo:

    pergunta_pendente = gr.State("")

    with gr.Row(
        elem_id="workspace",
        equal_height=False
    ):

        # ==================================
        # BARRA LATERAL
        # ==================================

        with gr.Column(
            scale=1,
            min_width=255,
            elem_id="sidebar"
        ):

            gr.HTML(SIDEBAR_HTML)

            sugestao_rg = gr.Button(
                "Quanto custa a segunda via do RG?",
                elem_classes=["suggestion-btn"]
            )

            sugestao_cpf = gr.Button(
                "Como faço para me inscrever no CPF?",
                elem_classes=["suggestion-btn"]
            )

            sugestao_titulo = gr.Button(
                "O voto é obrigatório aos 17 anos?",
                elem_classes=["suggestion-btn"]
            )

            sugestao_cnh = gr.Button(
                "Quando posso renovar minha CNH?",
                elem_classes=["suggestion-btn"]
            )

            sugestao_libras = gr.Button(
                "Como solicitar intérprete de Libras?",
                elem_classes=["suggestion-btn"]
            )

            gr.HTML(SIDEBAR_FOOTER)

        # ==================================
        # CHAT
        # ==================================

        with gr.Column(
            scale=4,
            min_width=320,
            elem_id="chat-panel"
        ):

            gr.HTML(CHAT_HEADER_HTML)

            chatbot = gr.Chatbot(
                value=novo_historico(),
                elem_id="citizen-chatbot",
                height=400,
                min_height=150,
                show_label=False,
                render_markdown=True,
                buttons=["copy"],
                autoscroll=True
            )

            with gr.Row(elem_id="composer"):

                mensagem = gr.Textbox(
                    placeholder=(
                        "Digite sua pergunta sobre "
                        "documentos e serviços..."
                    ),
                    show_label=False,
                    lines=2,
                    max_lines=5,
                    container=False,
                    scale=8,
                    elem_id="message-input"
                )

                with gr.Column(
                    scale=1,
                    min_width=110,
                    elem_id="action-buttons"
                ):

                    enviar = gr.Button(
                        "Enviar",
                        variant="primary",
                        elem_id="send-btn"
                    )

                    limpar = gr.Button(
                        "Limpar",
                        variant="secondary",
                        elem_id="clear-btn"
                    )

            gr.HTML(PRIVACY_HTML)

    # ======================================
    # ENVIO DE MENSAGENS
    # ======================================

    def configurar_envio(evento):

        return evento(
            fn=preparar_mensagem,
            inputs=[mensagem, chatbot],
            outputs=[
                mensagem,
                chatbot,
                pergunta_pendente
            ],
            queue=False
        ).then(
            fn=processar_resposta,
            inputs=[
                chatbot,
                pergunta_pendente
            ],
            outputs=chatbot
        )

    configurar_envio(enviar.click)
    configurar_envio(mensagem.submit)

    # ======================================
    # PERGUNTAS SUGERIDAS
    # ======================================

    sugestao_rg.click(
        fn=lambda: "Quanto custa a segunda via do RG?",
        outputs=mensagem,
        queue=False
    )

    sugestao_cpf.click(
        fn=lambda: "Como faço para me inscrever no CPF?",
        outputs=mensagem,
        queue=False
    )

    sugestao_titulo.click(
        fn=lambda: "Votar é obrigatório para quem tem 17 anos?",
        outputs=mensagem,
        queue=False
    )

    sugestao_cnh.click(
        fn=lambda: (
            "Com quanto tempo de antecedência "
            "posso renovar minha CNH?"
        ),
        outputs=mensagem,
        queue=False
    )

    sugestao_libras.click(
        fn=lambda: (
            "Preciso de intérprete de Libras. "
            "Como faço?"
        ),
        outputs=mensagem,
        queue=False
    )

    limpar.click(
        fn=limpar_conversa,
        outputs=[
            chatbot,
            mensagem,
            pergunta_pendente
        ],
        queue=False
    )


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":

    print("=" * 50)
    print("CITIZEN ASSIST AI")
    print("Interface Gradio")
    print("=" * 50)

    demo.queue(default_concurrency_limit=2)

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=False
    )
