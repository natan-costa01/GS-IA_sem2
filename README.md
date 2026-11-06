
# Citizen Assist AI

### Assistente Inteligente de Orientação ao Cidadão

Projeto acadêmico desenvolvido na **FIAP**, com foco na aplicação de Inteligência Artificial Generativa, sistemas multiagentes, validação de respostas e avaliação automatizada.

O **Citizen Assist AI** é um assistente virtual que orienta cidadãos sobre procedimentos relacionados a documentos e serviços públicos, utilizando uma base de conhecimento fictícia e controlada.

O sistema foi desenvolvido em Python, com interface Gradio, agentes especializados e integração com modelos de linguagem da OpenAI.

---

## 12. Equipe de desenvolvimento

Projeto desenvolvido por estudantes da **FIAP — Faculdade de Informática e Administração Paulista**.

| Integrante | RM |
|---|---|
| Leonardo Scotti Tobias | 573305 |
| Natan Silva da Costa | 573100 |
| Henrique de Souza Aragão | 570529 |

---

## 1. Objetivo do projeto

Desenvolver um assistente inteligente capaz de interpretar perguntas em linguagem natural e fornecer orientações claras, seguras e fundamentadas em documentos previamente disponibilizados.

### Objetivos específicos

- Implementar uma arquitetura multiagentes.
- Utilizar documentos como fonte de conhecimento.
- Identificar o assunto da solicitação do usuário.
- Consultar fichas informativas relacionadas à pergunta.
- Aplicar mecanismos de segurança (Guardrails).
- Validar as respostas antes de apresentá-las.
- Disponibilizar uma interface gráfica intuitiva.
- Avaliar o desempenho utilizando um Golden Dataset.
- Aplicar LLM-as-a-Judge para avaliação automatizada.

---

## 2. Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python | Linguagem principal |
| OpenAI API | Processamento de linguagem natural |
| GPT-4o-mini | Modelo utilizado pelos agentes |
| OpenAI Agents SDK | Orquestração dos agentes |
| Pydantic | Estruturação e validação dos dados |
| Gradio | Interface gráfica |
| Markdown | Base documental |
| Golden Dataset | Casos de teste |
| LLM-as-a-Judge | Avaliação das respostas |

---

## 3. Arquitetura multiagentes

O sistema utiliza agentes especializados para organizar o processamento das solicitações.

### Agente de triagem

Responsável por interpretar a pergunta, identificar o assunto e selecionar as fichas documentais relevantes.

### Agente de orientação

Responsável por elaborar a resposta utilizando as informações disponíveis na base de conhecimento.

### Agente de revisão

Responsável por verificar a qualidade da resposta, sua coerência e sua adequação às informações documentadas.

### Agente principal

Responsável pela coordenação do atendimento e pela integração dos componentes do sistema.

### Fluxo de funcionamento

```text
              USUÁRIO
                 |
                 v
          INTERFACE GRADIO
                 |
                 v
        VALIDAÇÃO DE ENTRADA
                 |
                 v
          AGENTE DE TRIAGEM
                 |
                 v
       IDENTIFICAÇÃO DAS FICHAS
                 |
                 v
             DATA LOADER
                 |
                 v
        AGENTE DE ORIENTAÇÃO
                 |
                 v
          AGENTE DE REVISÃO
                 |
                 v
         VALIDAÇÃO DE SAÍDA
                 |
                 v
          RESPOSTA AO USUÁRIO
```

---

## 4. Base de conhecimento

O sistema utiliza sete fichas documentais, identificadas de FC-01 a FC-07.

| Ficha | Assunto |
|---|---|
| FC-01 | Documento de identidade (RG) |
| FC-02 | Cadastro de Pessoa Física (CPF) |
| FC-03 | Título de eleitor |
| FC-04 | Serviços documentais |
| FC-05 | Serviços documentais |
| FC-06 | Serviços documentais |
| FC-07 | Regras gerais de atendimento |

As fichas estão armazenadas na pasta `Documents/` e são consultadas conforme o assunto identificado.

**Importante:** as informações utilizadas no projeto são fictícias e destinadas exclusivamente à demonstração acadêmica. O assistente não substitui canais oficiais de atendimento.

---

## 5. Guardrails e segurança

O projeto implementa mecanismos de proteção para aumentar a confiabilidade das interações.

Entre as verificações realizadas estão:

- Identificação de dados sensíveis.
- Proteção contra tentativas de prompt injection.
- Validação das entradas do usuário.
- Verificação das respostas geradas.
- Controle de solicitações fora do escopo.
- Redução de respostas sem fundamentação documental.

Esses mecanismos fazem parte do processamento do sistema e complementam a revisão realizada pelos agentes.

---

## 6. Interface Gradio

A interface foi desenvolvida para permitir que o usuário envie perguntas em linguagem natural e receba orientações de maneira simples.

### Exemplo de atendimento — Documento de identidade

![Interface de atendimento sobre RG](img/interface-rg.png)

### Exemplo de atendimento — Título de eleitor e acessibilidade

![Interface de atendimento sobre voto e Libras](img/interface-voto-libras.png)

A interface permite demonstrar a integração entre os agentes, a base documental e os mecanismos de validação.

---

## 7. Golden Dataset

Para avaliar o funcionamento do sistema, foi utilizado um **Golden Dataset composto por 26 casos de teste**.

Os casos permitem verificar diferentes aspectos do comportamento do assistente, incluindo:

- Fidelidade às informações documentadas.
- Completude das orientações.
- Segurança das respostas.
- Clareza da comunicação.

O conjunto foi utilizado para executar uma avaliação sistemática do sistema.

---

## 8. Avaliação com LLM-as-a-Judge

O projeto utiliza uma abordagem de avaliação automatizada denominada **LLM-as-a-Judge**.

Nesse processo, um modelo de linguagem atua como avaliador das respostas produzidas pelo sistema, atribuindo notas segundo critérios previamente definidos.

### Resultados finais

Após os ajustes e a nova execução do avaliador, foram obtidos os seguintes resultados:

| Indicador | Resultado |
|---|---:|
| Total de casos | 26 |
| Casos avaliados | 26 |
| Casos aprovados | 26 |
| Casos reprovados | 0 |
| Erros de execução | 0 |
| **Taxa de aprovação** | **100,00%** |
| Média de fidelidade | 5,00/5 |
| Média de completude | 4,88/5 |
| Média de segurança | 5,00/5 |
| Média de clareza | 5,00/5 |
| **Média geral** | **4,97/5** |

### Comparação entre as avaliações

| Indicador | Avaliação anterior | Avaliação final |
|---|---:|---:|
| Casos avaliados | 26 | 26 |
| Aprovados | 23 | 26 |
| Reprovados | 3 | 0 |
| Taxa de aprovação | 88,46% | 100,00% |
| Média geral | 4,71/5 | 4,97/5 |

### Análise dos resultados

A avaliação final apresentou aprovação de todos os 26 casos, representando um aumento de **11,54 pontos percentuais** em relação à avaliação anterior.

Os critérios de fidelidade, segurança e clareza alcançaram nota máxima.

A completude apresentou média de 4,88/5, indicando que ainda existe uma pequena margem para aperfeiçoar o nível de detalhamento de determinadas respostas.

A média geral de 4,97/5 demonstra desempenho elevado no conjunto de testes utilizado.

É importante destacar que os resultados correspondem ao Golden Dataset avaliado e não representam garantia de desempenho perfeito em todas as situações possíveis.

---

## 9. Como executar o projeto

### Pré-requisitos

- Python instalado.
- Dependências do projeto instaladas.
- Chave de API da OpenAI configurada.
- Ambiente virtual Python recomendado.

### Clonar o repositório

```bash
git clone https://github.com/natan-costa01/GS-IA_sem2.git
cd GS-IA_sem2
```

### Criar o ambiente virtual

```powershell
python -m venv .venv
```

### Ativar o ambiente virtual no PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### Instalar as dependências

Caso o projeto possua um arquivo `requirements.txt`:

```powershell
pip install -r requirements.txt
```

### Configurar a chave da OpenAI

No PowerShell:

```powershell
$env:OPENAI_API_KEY="SUA_CHAVE_AQUI"
```

Não publique sua chave de API no GitHub.

### Executar a interface

Execute o arquivo Python responsável pela inicialização da interface Gradio, conforme a estrutura do repositório.

---

## 10. Executando a avaliação

Para executar novamente o LLM-as-a-Judge, localize o arquivo `evaluate.py` no projeto.

No PowerShell, a partir da raiz do repositório:

```powershell
$arquivo = Get-ChildItem -Path . -Filter "evaluate.py" -Recurse -File |
Where-Object { $_.FullName -notmatch '\\.venv\\' } |
Select-Object -First 1

if ($arquivo) {
    & ".\.venv\Scripts\python.exe" $arquivo.FullName
} else {
    Write-Host "evaluate.py não encontrado."
}
```

O script executa a avaliação conforme as configurações implementadas no arquivo.

**Resultado registrado na última execução: 26 casos aprovados, 0 reprovados e média geral de 4,97/5.**

A execução utiliza a API e pode gerar custos de processamento.

---

## 11. Organização do projeto

Os principais componentes estão organizados por responsabilidade:

| Componente | Responsabilidade |
|---|---|
| `LLM/agents.py` | Implementação e coordenação dos agentes |
| `LLM/prompt.py` | Instruções e prompts dos agentes |
| `LLM/guardrails.py` | Validações e mecanismos de segurança |
| `Data/data_loader.py` | Carregamento das fichas documentais |
| `Documents/` | Base de conhecimento |
| `img/` | Imagens da interface |
| `evaluate.py` | Script de avaliação, localizado em uma subpasta do projeto |

---


## 13. Considerações finais

O desenvolvimento do Citizen Assist AI permitiu aplicar conceitos de Inteligência Artificial Generativa, arquiteturas multiagentes, validação de entradas e saídas, utilização de bases documentais e avaliação sistemática de modelos de linguagem.

A utilização do Golden Dataset e do LLM-as-a-Judge permitiu mensurar o comportamento do sistema e comparar os resultados antes e depois dos ajustes realizados.

Na avaliação final, o projeto obteve **100% de aprovação nos 26 casos testados**, com média geral de **4,97/5**.

O projeto demonstra uma aplicação acadêmica de agentes de IA para orientação documental, mantendo a preocupação com segurança, clareza e fidelidade às fontes.

---

## 14. Repositório

**GitHub:** https://github.com/natan-costa01/GS-IA_sem2

**Projeto:** Citizen Assist AI

**Instituição:** FIAP

**Área:** Inteligência Artificial Generativa e Sistemas Multiagentes
