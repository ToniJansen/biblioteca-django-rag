# Sistema de Gestão de Biblioteca com Recomendações

**Proposta de Trabalho da Disciplina**

Disciplina: INF0330 — Framework de Desenvolvimento Web para Consumo de Modelos Treinados de Inteligência Artificial
Professor: Ronaldo M. da Costa
Instituição: Universidade Federal de Goiás (UFG)
Data: Abril de 2026

---

## 1. Componentes do Grupo

- Antonio Jansen
- Givanildo Gramacho
- Jucelino Santos
- Ronny Marcelo
- Vanderson Darriba

---

## 2. Contextualização

A disciplina INF0330 tem como foco o desenvolvimento de aplicações web utilizando frameworks modernos, com ênfase na integração e consumo de modelos treinados de Inteligência Artificial em cenários reais de uso. O trabalho proposto neste documento busca atender diretamente essa ementa, combinando um sistema web tradicional (CRUD com autenticação, gestão de entidades e regras de negócio) com uma camada inteligente de recomendação baseada em modelo de linguagem treinado.

---

## 3. Definição do Trabalho

### 3.1 Problema

Bibliotecas acadêmicas lidam diariamente com grandes acervos de livros, teses, dissertações e monografias. Os leitores (alunos, pesquisadores e docentes) enfrentam duas dificuldades recorrentes:

1. A gestão operacional do acervo é trabalhosa sem um sistema digital adequado (cadastros, empréstimos, devoluções, controle de atrasos).
2. A descoberta de novas obras relevantes dentro do acervo é limitada, uma vez que os mecanismos tradicionais de busca dependem de correspondência exata por título ou autor, deixando de explorar relações semânticas entre os conteúdos.

### 3.2 Solução Proposta

Desenvolver um sistema web de gestão de biblioteca que cubra o ciclo completo de operação do acervo e que, adicionalmente, ofereça recomendações de leituras baseadas em similaridade semântica. O sistema utilizará um modelo treinado de representação textual para gerar sugestões personalizadas ao leitor, a partir do livro consultado e do seu histórico de empréstimos.

### 3.3 Objetivos

**Objetivo geral.** Construir uma aplicação web funcional e segura, desenvolvida com o framework Django, que integre um módulo de recomendação baseado em modelo treinado de inteligência artificial.

**Objetivos específicos.**

- Modelar e implementar o CRUD das entidades da biblioteca (pessoas, obras, empréstimos).
- Implementar regras de negócio de empréstimo, devolução, controle de disponibilidade e atrasos.
- Prover autenticação e autorização por perfis de usuário (bibliotecário, leitor e administrador).
- Consumir um modelo treinado para gerar recomendações de obras por similaridade semântica.
- Disponibilizar um painel de indicadores (dashboard) com métricas operacionais do acervo.

---

## 4. Escopo do Sistema

### 4.1 Módulo CRUD (base operacional)

**Entidades.** Pessoa (bibliotecário e leitor), Livro (bibliografia, tese/dissertação, monografia) e Empréstimo.

**Funcionalidades.**

- Cadastro, edição, consulta e remoção das três entidades.
- Autenticação com login e grupos de permissão (Editor, Visualizador, Superusuário).
- Regras de negócio no empréstimo: validação de disponibilidade do exemplar, validação de leitor ativo, cálculo automático da data de devolução prevista (14 dias) e atualização do acervo ao registrar devolução.
- Cálculo de status dinâmico do empréstimo (Emprestado, Devolvido, Atrasado).
- Relatório de empréstimos atrasados.
- Dashboard com contadores e indicadores básicos.

### 4.2 Módulo de Inteligência Artificial

O módulo de inteligência artificial é composto por duas camadas que consomem modelos treinados distintos, cada um adequado à sua função. A Fase 1 foi implementada ao longo da Sprint 1 e a Fase 2 está planejada para a Sprint 2.

#### 4.2.1 Fase 1 — Recomendação por similaridade semântica (HuggingFace)

A recomendação de obras foi implementada consumindo o modelo pré-treinado **`paraphrase-multilingual-MiniLM-L12-v2`**, disponibilizado publicamente pelo HuggingFace Hub por meio da biblioteca `sentence-transformers`. O modelo é baixado uma única vez (aproximadamente quatrocentos e vinte megabytes) e executado localmente em CPU, sem necessidade de GPU nem de chamadas a serviços externos.

O pipeline funciona em quatro passos:

1. **Geração de embeddings.** Para cada obra cadastrada, o texto formado pela concatenação de título, autor e tipo de obra é convertido em um vetor de trezentos e oitenta e quatro dimensões. O cálculo é disparado automaticamente por um *signal* do Django sempre que uma obra é criada ou editada.
2. **Armazenamento.** O vetor é persistido em um campo binário (`BinaryField`) no próprio banco SQLite, vinculado à chave primária da obra por meio do modelo `LivroEmbedding` (relação `OneToOne` com `Livro`).
3. **Busca por similaridade.** Ao acessar a página de detalhe de uma obra, o sistema carrega todos os vetores do acervo em memória (numpy), calcula a similaridade cosseno entre o vetor-alvo e os demais e retorna as cinco obras mais próximas. Para acervos de até alguns milhares de obras, o cálculo roda em menos de um milissegundo.
4. **Personalização.** Para leitores com histórico de empréstimos, é calculada a média dos vetores das obras já tomadas emprestado; o resultado é então utilizado como vetor-alvo, gerando recomendações baseadas no padrão de leitura individual.

Essa fase concretiza o requisito da disciplina de "consumir modelo treinado de inteligência artificial", com ênfase em execução local, gratuita e offline.

#### 4.2.2 Fase 2 — Assistente conversacional (Groq)

A extensão conversacional será implementada consumindo a API da plataforma **Groq**, que hospeda modelos abertos das famílias Llama, DeepSeek, Gemma e Mixtral, expondo uma interface REST compatível com o padrão OpenAI. O modelo escolhido como primeiro candidato é o **`llama-3.3-70b-versatile`**, em virtude de sua qualidade em português brasileiro e da latência extremamente baixa da arquitetura LPU customizada da Groq (da ordem de centenas de tokens por segundo).

A implementação segue o padrão **RAG (*Retrieval Augmented Generation*)**, combinando as duas camadas de IA:

1. O usuário digita uma pergunta em linguagem natural (por exemplo: *"Quais livros vocês têm sobre redes neurais aplicadas a saúde?"*).
2. A pergunta é vetorizada pelo mesmo modelo MiniLM da Fase 1.
3. **Estratégia de recuperação híbrida.** Para acervos de até duzentas obras (escopo deste MVP), o contexto enviado ao LLM é o **acervo inteiro**, ordenado por similaridade semântica com a pergunta. Isso permite que o modelo responda com precisão não apenas consultas temáticas ("livros sobre redes neurais") como também consultas de metadados — busca por autor, ISBN, ano de publicação, tipo de obra ou contagens ("quantas teses de 2024 temos?"). Acima desse limite, o sistema recua para busca por *top-k* mais similares, evitando custo desnecessário de *tokens* e latência.
4. Um *prompt* é montado com a pergunta do usuário e os metadados das obras (título, autor, tipo, ano, ISBN, exemplares disponíveis) como contexto estruturado.
5. A API da Groq é chamada; o modelo gera a resposta em português, citando as obras relevantes do acervo apresentado.
6. A interface exibe a resposta textual ao lado da lista de obras consideradas, com *links* diretos para suas páginas de detalhe.

**Justificativa da escolha da plataforma Groq.** O serviço oferece um *tier* gratuito suficiente para demonstração acadêmica; a API compatível com OpenAI facilita a troca futura de provedor; a disponibilidade de modelos abertos (Llama e Gemma) mantém o projeto alinhado ao princípio do curso de *consumir* modelos treinados sem *lock-in* proprietário; e a latência baixa é crítica para a experiência conversacional fluida.

**Alternativas avaliadas.** HuggingFace Inference API (*tier* gratuito mais limitado), Google Gemini (boa qualidade mas proprietário), Ollama local (totalmente *offline* mas lento em CPU) e OpenAI/Anthropic (pagos). A decisão final pela Groq será formalizada em ADR-002 no início da Sprint 2.

**Segurança e guardrails do chat.** A experiência conversacional exige cuidado específico com ataques dirigidos a modelos de linguagem — em especial a injeção de *prompts* e a indução a temas fora do escopo do sistema. A implementação adota **defesa em camadas** (*defense-in-depth*) com cinco linhas de proteção: (i) sanitização da pergunta de entrada (limite de mil caracteres, remoção de caracteres de controle e registro em *log* de padrões reconhecidamente adversariais); (ii) *system prompt* endurecido com nove regras inegociáveis cobrindo escopo estrito, antialucinação, bloqueio de troca de persona, fixação do idioma, recusa padronizada de temas sensíveis (diagnósticos médicos, pareceres jurídicos, aconselhamento financeiro, opiniões políticas) e confidencialidade do próprio *prompt*; (iii) encapsulamento da pergunta do usuário dentro de delimitadores explícitos, tratada como dado e não como instrução; (iv) parâmetros conservadores de inferência (temperatura 0.2) para reduzir improvisação; e (v) detecção programática da frase canônica de recusa no *output*, que ajusta a confiança da resposta e inibe o retorno de citações aleatórias quando o modelo declina responder. O conjunto foi submetido a sete casos de teste adversariais (pergunta legítima, tema fora do escopo, injeção clássica de instruções, *jailbreak* de persona com tema sensível, tentativa de troca de idioma, pedido educado de revelação do *prompt* do sistema e pergunta de saúde induzindo diagnóstico), tendo produzido o comportamento esperado em todos os sete. A documentação técnica completa dos *vetores de ataque*, *mitigação* aplicada e reprodução dos testes está registrada no documento interno `docs/seguranca_chat.md`.

#### 4.2.3 Diferença entre as duas camadas

Os dois modelos cumprem funções complementares, e a combinação é deliberada: o modelo encoder da HuggingFace realiza a busca semântica no acervo (rápida, local, sempre disponível); o modelo generativo da Groq apenas sintetiza a resposta final ao usuário (na nuvem, somente quando há pergunta explícita). Essa divisão minimiza custo, latência e dependência de rede, preservando a qualidade da resposta conversacional.

| Aspecto | Fase 1 — MiniLM (HuggingFace) | Fase 2 — Llama 3.3 (Groq) |
|---|---|---|
| Tipo de modelo | Encoder (embeddings) | Decoder (generativo) |
| Tarefa | Similaridade semântica | Síntese de texto em linguagem natural |
| Execução | Local, em CPU | Nuvem, LPU customizada |
| Custo | Gratuito, offline | Gratuito com limite de requisições |
| Tempo típico de resposta | Aproximadamente cem milissegundos | Um a dois segundos |
| Uso de rede | Somente no primeiro *download* do modelo | A cada pergunta do usuário |
| Dependência externa | Nenhuma após o *download* | Serviço da Groq precisa estar disponível |

### 4.3 Fora do Escopo

- Aplicação móvel nativa.
- Integração com sistemas de pagamento ou cobrança automática de multas.
- Digitalização do conteúdo integral das obras (somente metadados e sinopses).
- Publicação em ambiente de produção com infraestrutura de nuvem gerenciada.

---

## 5. Stack Tecnológica

- **Linguagem:** Python 3.x
- **Framework web:** Django 4.2
- **Banco de dados:** SQLite (desenvolvimento)
- **Interface:** Bootstrap 5 via django-bootstrap-v5 e django-tables2
- **Autenticação:** sistema nativo do Django com grupos e permissões
- **Camada de IA:** biblioteca Sentence-Transformers (HuggingFace); avaliação de modelos abertos (Llama, DeepSeek) para extensão conversacional
- **Controle de versão:** Git e GitHub
- **Ambiente de apresentação:** servidor de desenvolvimento local

---

## 6. Cronograma

O trabalho está organizado em quatro sprints, totalizando aproximadamente sete semanas de execução, com entrega final prevista para 06 de junho de 2026.

| Sprint | Período | Entregas |
|---|---|---|
| Sprint 0 | 21/04 a 26/04 | Documento de proposta submetido |
| Sprint 1 | 27/04 a 10/05 | Prova de conceito do módulo de recomendação; definição final do modelo |
| Sprint 2 | 11/05 a 24/05 | Integração do módulo de recomendação ao CRUD; interface de sugestões |
| Sprint 3 | 25/05 a 06/06 | Testes, dashboard de métricas, revisão de segurança, documentação final e apresentação |

Revisões semanais em grupo serão realizadas para acompanhamento de backlog, alinhamento técnico e ajustes de escopo, se necessário.

---

## 7. Divisão de Responsabilidades

Todos os integrantes participam das decisões arquiteturais, das revisões de código e das retrospectivas de sprint. Os papéis abaixo indicam a liderança de cada frente, e não exclusividade.

| Integrante | Frente Principal |
|---|---|
| Antonio Jansen | Arquitetura do sistema, coordenação, redação e integração da camada de IA |
| Jucelino Santos | Backend, modelagem de dados, integração do motor de recomendação |
| Givanildo Gramacho | Pesquisa, prova de conceito e avaliação dos modelos de IA |
| Vanderson Darriba | Segurança, autenticação, conformidade e boas práticas |
| Ronny Marcelo | Métricas, análise quantitativa e painel de indicadores |

---

## 8. Resultados Esperados

Ao final da disciplina, o grupo entregará:

- Uma aplicação web funcional para gestão de biblioteca, com autenticação, CRUD completo e regras de negócio implementadas.
- Um módulo de recomendação por similaridade semântica integrado ao sistema, consumindo um modelo treinado de linguagem.
- Documentação técnica do sistema, instruções de execução e relatório de avaliação da solução.
- Apresentação demonstrando o funcionamento end-to-end da aplicação.
