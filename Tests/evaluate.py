
"""
Citizen Assist AI - Avaliação Automatizada

Executa o Golden Dataset e avalia as respostas
utilizando o LLM-as-a-Judge.

Modelo: GPT-4o-mini
Framework: OpenAI Agents SDK
"""

import os
import sys
import json
import asyncio
import argparse

from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv


# ==========================================
# CONFIGURAÇÃO DO PROJETO
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from LLM.agents import executar_agentes
from LLM.judge import avaliar_resposta


DATASET_PATH = (
    BASE_DIR / "Golden-Dataset" / "golden_dataset.json"
)

RESULTADOS_DIR = BASE_DIR / "Tests" / "results"


# ==========================================
# CARREGAMENTO DO GOLDEN DATASET
# ==========================================

def carregar_dataset():

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Golden Dataset não encontrado: {DATASET_PATH}"
        )

    with open(DATASET_PATH, "r", encoding="utf-8") as arquivo:
        dataset = json.load(arquivo)

    if not isinstance(dataset, list):
        raise ValueError(
            "O Golden Dataset deve conter uma lista JSON."
        )

    return dataset


# ==========================================
# SALVAMENTO DOS RESULTADOS
# ==========================================

def salvar_resultados(dados):

    RESULTADOS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho = RESULTADOS_DIR / "run.json"

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=4
        )

    return caminho


# ==========================================
# CÁLCULO DAS MÉTRICAS
# ==========================================

def calcular_metricas(resultados):

    avaliacoes = [
        caso["avaliacao"]
        for caso in resultados
        if "avaliacao" in caso
    ]

    total = len(resultados)
    avaliados = len(avaliacoes)

    aprovados = sum(
        1 for avaliacao in avaliacoes
        if avaliacao["aprovado"]
    )

    reprovados = avaliados - aprovados

    erros = sum(
        1 for caso in resultados
        if "erro" in caso
    )

    def media_criterio(nome):

        if not avaliacoes:
            return None

        return round(
            sum(
                avaliacao[nome]
                for avaliacao in avaliacoes
            ) / avaliados,
            2
        )

    return {
        "total_casos": total,
        "casos_avaliados": avaliados,
        "aprovados": aprovados,
        "reprovados": reprovados,
        "erros": erros,
        "taxa_aprovacao": (
            round(aprovados / total * 100, 2)
            if total else 0
        ),
        "media_fidelidade": media_criterio(
            "fidelidade"
        ),
        "media_completude": media_criterio(
            "completude"
        ),
        "media_seguranca": media_criterio(
            "seguranca"
        ),
        "media_clareza": media_criterio(
            "clareza"
        ),
        "media_geral": media_criterio(
            "media"
        )
    }


# ==========================================
# EXECUÇÃO DA AVALIAÇÃO
# ==========================================

async def executar_avaliacao(
    limite=None,
    usar_juiz=True
):

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY não configurada no .env"
        )

    dataset = carregar_dataset()

    if limite is not None:
        if limite < 1:
            raise ValueError(
                "O limite deve ser maior que zero."
            )
        dataset = dataset[:limite]

    resultados = []

    print("\n===================================")
    print(" CITIZEN ASSIST AI")
    print(" AVALIAÇÃO AUTOMATIZADA")
    print("===================================")

    print(f"\nTotal de casos: {len(dataset)}")
    print(f"LLM-as-a-Judge: {'SIM' if usar_juiz else 'NÃO'}")

    for indice, caso in enumerate(dataset, start=1):

        print("\n-----------------------------------")
        print(
            f"TESTE {indice}/{len(dataset)} "
            f"| ID: {caso['id']}"
        )
        print("-----------------------------------")

        print(f"Categoria: {caso['tipo']}")
        print(f"Pergunta: {caso['pergunta']}")

        registro = {
            "id": caso["id"],
            "tipo": caso["tipo"],
            "pergunta": caso["pergunta"],
            "resposta_esperada": caso["resposta_esperada"],
            "fontes_esperadas": caso.get("fonte", [])
        }

        try:

            # Executa os agentes principais.
            resposta = await executar_agentes(
                caso["pergunta"]
            )

            registro["resposta_obtida"] = resposta

            print("\nResposta gerada:")
            print(resposta)

            # Executa o LLM-as-a-Judge.
            if usar_juiz:

                avaliacao = await avaliar_resposta(
                    caso,
                    resposta
                )

                registro["avaliacao"] = avaliacao

                status = (
                    "APROVADO"
                    if avaliacao["aprovado"]
                    else "REPROVADO"
                )

                print(f"\nResultado: {status}")
                print(f"Média: {avaliacao['media']}/5")

                print(
                    "Fidelidade:",
                    avaliacao["fidelidade"]
                )
                print(
                    "Completude:",
                    avaliacao["completude"]
                )
                print(
                    "Segurança:",
                    avaliacao["seguranca"]
                )
                print(
                    "Clareza:",
                    avaliacao["clareza"]
                )

                print(
                    "Justificativa:",
                    avaliacao["justificativa"]
                )

        except Exception as erro:

            registro["erro"] = (
                f"{type(erro).__name__}: {erro}"
            )

            print("\nERRO:")
            print(registro["erro"])

        resultados.append(registro)

        # Salva progresso a cada teste.
        dados_parciais = {
            "projeto": "Citizen Assist AI",
            "modelo": "gpt-4o-mini",
            "modo": "live",
            "judge_ativado": usar_juiz,
            "data_execucao": datetime.now(
                timezone.utc
            ).isoformat(),
            "metricas": calcular_metricas(resultados),
            "resultados": resultados
        }

        salvar_resultados(dados_parciais)

    # ======================================
    # RESULTADO FINAL
    # ======================================

    metricas = calcular_metricas(resultados)

    print("\n===================================")
    print(" RESULTADO FINAL")
    print("===================================")

    print(f"Total: {metricas['total_casos']}")
    print(f"Avaliados: {metricas['casos_avaliados']}")
    print(f"Aprovados: {metricas['aprovados']}")
    print(f"Reprovados: {metricas['reprovados']}")
    print(f"Erros: {metricas['erros']}")

    print(
        "Taxa de aprovação:",
        f"{metricas['taxa_aprovacao']}%"
    )

    print(
        "Média de fidelidade:",
        metricas["media_fidelidade"]
    )

    print(
        "Média de completude:",
        metricas["media_completude"]
    )

    print(
        "Média de segurança:",
        metricas["media_seguranca"]
    )

    print(
        "Média de clareza:",
        metricas["media_clareza"]
    )

    print(
        "Média geral:",
        metricas["media_geral"]
    )

    print(
        "\nResultados salvos em:",
        RESULTADOS_DIR / "run.json"
    )


# ==========================================
# EXECUÇÃO PELO TERMINAL
# ==========================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Avaliação do Citizen Assist AI"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita a quantidade de testes."
    )

    parser.add_argument(
        "--sem-juiz",
        action="store_true",
        help="Executa sem o LLM-as-a-Judge."
    )

    argumentos = parser.parse_args()

    asyncio.run(
        executar_avaliacao(
            limite=argumentos.limit,
            usar_juiz=not argumentos.sem_juiz
        )
    )
