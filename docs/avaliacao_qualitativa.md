# Avaliação qualitativa da recomendação semântica

> **Status:** 🟡 template pré-preenchido com estrutura e exemplos mockados. **Givanildo preenche com dados reais (ticket T9)** depois que `gerar_embeddings` estiver rodando.
>
> **Dono final:** Givanildo Gramacho
> **Prazo:** 10/05/2026 (fim da Sprint 1)
> **Critério de aprovação:** ≥60% das sugestões marcadas como "plausível" pelos 5 avaliadores.

---

## Metodologia

1. Rodar `python manage.py gerar_embeddings` pra popular a tabela `LivroEmbedding`
2. Para cada uma das 10 obras selecionadas abaixo, executar `recomendar_livros(livro_id, k=5)`
3. Cada um dos 5 avaliadores (Antonio, Givanildo, Jucelino, Ronny, Vanderson) marca cada uma das 50 sugestões (10 obras × 5 sugestões) como:
   - ✅ **plausível** — faz sentido como recomendação
   - ❌ **não plausível** — fora de contexto
   - ❓ **neutro** — não sei avaliar
4. Consolidar: total de (plausível) ÷ total de (plausível + não plausível + neutro) × 100%
5. Se ≥60% → aprovado. Se <60% → revisar modelo (trocar por BERTimbau) e refazer.

---

## Obras selecionadas para avaliação

Mix de 10 obras cobrindo todos os 3 tipos e áreas temáticas diversas:

| # | Obra-alvo | Tipo | Área |
|---|---|---|---|
| 1 | Django for Beginners | Bibliografia | Programação web |
| 2 | Python Fluente | Bibliografia | Linguagem Python |
| 3 | Deep Learning (Goodfellow) | Bibliografia | IA / ML |
| 4 | Sistemas de Banco de Dados (Elmasri) | Bibliografia | Banco de dados |
| 5 | Clean Code | Bibliografia | Eng. software |
| 6 | Casa Grande e Senzala | Bibliografia | Humanidades |
| 7 | Deep Learning aplicado a deteccao de fraudes bancarias | Tese/Dissert. | IA aplicada |
| 8 | Processamento de linguagem natural em portugues brasileiro | Tese/Dissert. | NLP |
| 9 | Sistema web em Django para gestao academica | Monografia | Web + TCC |
| 10 | Algoritmo de recomendacao de filmes baseado em conteudo | Monografia | ML + TCC |

---

## Planilha de avaliação (a preencher)

### Obra 1 — Django for Beginners

| Sugestão retornada | Antonio | Givanildo | Jucelino | Ronny | Vanderson | Consenso |
|---|---|---|---|---|---|---|
| ? | | | | | | |
| ? | | | | | | |
| ? | | | | | | |
| ? | | | | | | |
| ? | | | | | | |

*(Repetir para as outras 9 obras.)*

---

## Exemplo mockado (o que esperamos ver se o modelo for bom)

### Obra 1 — Django for Beginners (mock do resultado esperado)

| Sugestão retornada | Antonio | Consenso |
|---|---|---|
| Two Scoops of Django | ✅ | ✅ (mesma tecnologia) |
| Python Fluente | ✅ | ✅ (Django é em Python) |
| Sistema web em Django para gestao academica | ✅ | ✅ (monografia sobre Django) |
| Clean Code | ❓ | ❓ (geral demais) |
| Refactoring | ❓ | ❓ (geral demais) |

Resultado esperado: 3/5 = 60% plausível → aprovado no limite.

### Obra 3 — Deep Learning (Goodfellow) (mock)

| Sugestão retornada | Antonio | Consenso |
|---|---|---|
| Pattern Recognition and Machine Learning | ✅ | ✅ |
| Hands-On Machine Learning | ✅ | ✅ |
| Inteligencia Artificial: Uma Abordagem Moderna | ✅ | ✅ |
| Deep Learning aplicado a deteccao de fraudes bancarias | ✅ | ✅ |
| Redes neurais convolucionais para diagnostico de imagens medicas | ✅ | ✅ |

Resultado esperado: 5/5 = 100%. Um modelo bom de embeddings deve acertar esse cluster de IA.

---

## Consolidação final (a preencher após avaliação real)

| Métrica | Valor |
|---|---|
| Total de sugestões avaliadas | 10 × 5 = 50 |
| Total marcadas "plausível" | ? |
| Total marcadas "não plausível" | ? |
| Total marcadas "neutro" | ? |
| **% plausível** | ? |
| **Decisão** | ✅ aprovado / ❌ trocar modelo / 🔁 expandir seed antes de reavaliar |

---

## Observações qualitativas

*(A preencher após avaliação — padrões percebidos, falsos positivos recorrentes, sugestões de melhoria como adicionar sinopse ou gênero no texto embeddado.)*
