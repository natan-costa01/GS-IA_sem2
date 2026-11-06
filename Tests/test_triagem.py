
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from agents import Runner
from LLM.agents import agente_triagem


async def main():
    pergunta = "Quanto custa a segunda via do RG?"

    resultado = await Runner.run(
        agente_triagem,
        pergunta
    )

    triagem = resultado.final_output

    print("\n=== RESULTADO DA TRIAGEM ===")
    print("Assunto:", triagem.assunto)
    print("Fichas:", triagem.fichas)
    print("Dentro do escopo:", triagem.dentro_escopo)


if __name__ == "__main__":
    asyncio.run(main())
