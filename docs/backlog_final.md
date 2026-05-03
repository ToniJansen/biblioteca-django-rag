# Backlog Final — Sprints Finais

> **Projeto:** Biblioteca Django RAG — INF0330 (UFG)
> **Entrega final:** 06/06/2026
> **Gerado em:** 02/05/2026

---

## Contexto

A aplicação já atende os requisitos da proposta.
O backlog abaixo contém **somente o necessário** para fechar gaps documentais e compor o documento final.

---

## Backlog por membro

### 🧠 Givanildo — Embeddings (3 itens)

| # | Artefato | O que fazer | Destino |
|---|----------|-------------|---------|
| G1 | **Benchmark T2 + ADR-001** | Rodar o benchmark na própria máquina, registrar latência (p50, p95) e specs. Com base nos resultados, aprovar o ADR-001 com data e justificativa. | `docs/benchmark_modelos.md` + `docs/adr/001-modelo-embeddings.md` |
| G2 | **Avaliação qualitativa** | Coordenar a avaliação (cada membro avalia 10 recomendações). Tabular resultados. | `docs/avaliacao_qualitativa.md` |
| G3 | **Seção do documento final** | 1-2 páginas: o que é embedding, por que MiniLM, resultados do benchmark e avaliação. | Documento final |

---

### 🛡️ Vanderson — Segurança (3 itens)

| # | Artefato | O que fazer | Destino |
|---|----------|-------------|---------|
| V1 | **Parecer LGPD** | Revisar e fechar `conformidade.md` com parecer próprio. Marcar status APROVADO. | `docs/conformidade.md` |
| V2 | **Evidências adversariais** | Executar os 7 testes adversariais no chat, capturar prints das respostas e documentar quais camadas (L1-L5) atuaram. | `docs/seguranca_chat.md` (atualização) |
| V3 | **Seção do documento final** | 1-2 páginas: as 5 camadas de defesa, evidências dos testes, conformidade LGPD. | Documento final |

---

### 📊 Ronny — Dashboard e Métricas (3 itens)

| # | Artefato | O que fazer | Destino |
|---|----------|-------------|---------|
| R1 | **Atualizar métricas** | Atualizar `metricas_sprint1.md` com dados reais atuais e capturas de tela do dashboard. | `docs/metricas_sprint1.md` |
| R2 | **Revisar doc RAG** | Conferir se `recommendation_and_rag_logic.md` ainda reflete o código atual. Anotar divergências. | `docs/recommendation_and_rag_logic.md` |
| R3 | **Seção do documento final** | 1-2 páginas: as 5 views analíticas, os indicadores do dashboard, capturas de tela. | Documento final |

---

### 🏛️ Antonio — RAG e Arquitetura (2 itens)

| # | Artefato | O que fazer | Destino |
|---|----------|-------------|---------|
| A1 | **ADR-002** | Documentar a decisão Groq/Llama 3.3: alternativas, trade-offs, justificativa. | `docs/adr/002-groq-llm.md` |
| A2 | **Seção do documento final** | 1-2 páginas: pipeline RAG, decisão Groq, estratégia híbrida de retrieval. | Documento final |

---

### ⚙️ Jucelino — Backend e Recomendação (2 itens)

| # | Artefato | O que fazer | Destino |
|---|----------|-------------|---------|
| J1 | **Seção do documento final** | 1-2 páginas: modelo de dados, regras de negócio do empréstimo, fluxo de recomendação, estratégia de testes. | Documento final |
| J2 | **Integração do documento** | Revisar e integrar as seções dos demais membros num documento coeso. Tag `v1.0`. | Documento final + repo |

---

## Cronograma

| Período | O que | Quem |
|---------|-------|------|
| 11/05 → 25/05 | Produzir artefatos | Cada um na sua área |
| 26/05 → 01/06 | Entregar seção do documento final | Todos |
| 02/06 → 05/06 | Jucelino integra documento + ensaio da apresentação | Jucelino + todos |
| **06/06** | **Apresentação final** | Todos |

---

## Resumo

| Membro | Itens |
|--------|-------|
| Givanildo | 3 (benchmark/ADR-001 + avaliação + seção) |
| Vanderson | 3 (parecer LGPD + evidências adversariais + seção) |
| Ronny | 3 (métricas + revisão doc RAG + seção) |
| Antonio | 2 (ADR-002 + seção) |
| Jucelino | 2 (seção + integração) |
| **Total** | **13 itens** |

---

## Referências rápidas

| Área | Arquivos-chave |
|------|---------------|
| Embeddings | `recomendador/embeddings.py`, `recomendador/services.py`, `docs/benchmark_modelos.md` |
| Segurança | `recomendador/chat/rag.py`, `docs/seguranca_chat.md`, `docs/conformidade.md` |
| Backend | `core/models.py`, `recomendador/signals.py`, `recomendador/tests/test_services.py` |
| Dashboard | `core/analytics.py`, `core/views.py`, `docs/metricas_sprint1.md` |
| RAG | `recomendador/chat/rag.py`, `docs/recommendation_and_rag_logic.md` |
