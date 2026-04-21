# Métricas da Sprint 1 — Módulo de Recomendação

> **Status:** 🟢 **números reais preenchidos por Antonio em 2026-04-21** — Ronny (T10) revisa e expande com rodadas em máquinas diferentes.
>
> **Prazo:** 10/05/2026
> **Input:** execução do comando `gerar_embeddings` + rodadas de `recomendar_livros` + avaliação qualitativa.

---

## 1. Cobertura

> 🟢 **Dados preliminares medidos em 2026-04-20 por Antonio** — Ronny confirma em ambiente próprio.

| Métrica | Valor | Meta |
|---|---|---|
| Total de obras no acervo | **30** | ≥ 30 ✅ |
| Obras com embedding gerado | **30** | 30 (100%) ✅ |
| Obras sem embedding (falha / ignoradas) | **0** | 0 ✅ |
| % cobertura | **100%** | 100% ✅ |

**Comando para medir:**
```python
from core.models import livro
from recomendador.models import LivroEmbedding
total = livro.objects.count()
com_emb = LivroEmbedding.objects.count()
print(f'{com_emb}/{total} = {com_emb/total*100:.1f}%')
```

---

## 2. Latência

### 2.1 Bootstrap — `python manage.py gerar_embeddings`

> 🟢 **Dados preliminares (primeira medida em Mac M-series local):**

| Métrica | Valor |
|---|---|
| Tempo total para 30 obras (modelo já cacheado) | **~1.0 s** |
| Tempo por obra (média, encode em batch) | **~33 ms** |
| Memória RAM de pico | ~450 MB (modelo carregado) |
| Tamanho do modelo baixado | ~420 MB em `~/.cache/huggingface/` |

Primeira execução inclui download do modelo (~2–5 min dependendo da rede). Execuções subsequentes usam cache local.

### 2.2 Recomendação online — `recomendar_livros(livro_id, k=5)`

> 🟢 **50 runs contra acervo real de 30 obras com embeddings reais:**

| Métrica | Valor medido | Meta |
|---|---|---|
| Latência p50 | **0.47 ms** | < 100 ms ✅ |
| Latência p95 | **0.72 ms** | < 500 ms ✅ |
| Latência max (p99+) | **1.46 ms** | < 1 s ✅ |

Para `recomendar_para_leitor(leitor_id, k=5)` (1 empréstimo no histórico):
- p50: **0.64 ms**
- p95: **1.08 ms**
- max: **1.51 ms**

A latência vai escalar linearmente com o tamanho do acervo até ~10k obras (numpy matmul puro). Acima disso, trocar por FAISS.

**Script:**
```python
import time, statistics
from recomendador.services import recomendar_livros
tempos = []
for _ in range(20):
    t0 = time.perf_counter()
    recomendar_livros(1, top_k=5)
    tempos.append((time.perf_counter() - t0) * 1000)
print(f'p50: {statistics.median(tempos):.1f}ms')
print(f'p95: {sorted(tempos)[int(len(tempos)*0.95)]:.1f}ms')
print(f'p99: {max(tempos):.1f}ms')
```

---

## 3. Distribuição de similaridade

Medir pra cada uma das 30 obras quais scores de similaridade os top-5 retornam. Um histograma ajuda a ver se o modelo discrimina bem ou se "todo mundo é parecido com todo mundo".

| Métrica | Valor | Interpretação |
|---|---|---|
| Similaridade média (top-1) | ? | idealmente > 0.6 |
| Similaridade média (top-5) | ? | idealmente > 0.4 |
| Similaridade média do 6º ao 10º | ? | serve de baseline pra comparar |
| Std dev entre top-5 | ? | se muito baixo, modelo está "chapado" |

### Validação amostral (smoke test 2026-04-21)

Rodagem em duas obras-alvo do acervo:

| Obra-alvo | Top-5 retornados | Plausíveis (Antonio) |
|---|---|---|
| *Deep Learning* (Goodfellow) | Hands-On ML • tese fraudes • Pattern Recognition • IA Abordagem Moderna • tese RNC imagens médicas | **5/5** ✅ |
| *Django for Beginners* (Vincent) | Sistema web em Django (monografia) • Two Scoops of Django • Python Fluente • Pragmatic Programmer • Como Elaborar Projetos de Pesquisa | **4/5** ✅ |

Score médio aparente (estimativa visual): alta — o modelo claramente separa clusters temáticos (IA/ML vs. Web vs. Humanidades). Números precisos a serem colhidos pelo Ronny.

---

## 4. Qualidade subjetiva (do T9 — Givanildo)

| Métrica | Valor | Meta |
|---|---|---|
| Obras avaliadas | 0 (aguarda Givanildo) | 10 |
| Sugestões avaliadas | 0 | 50 (10 × 5) |
| Avaliadores | 1 informal (Antonio) | 5 (time inteiro) |
| % plausível (amostra de 10 no smoke test) | **90%** (9/10) | ≥ 60% ✅ (amostra pequena, precisa validação completa) |

Link: `docs/avaliacao_qualitativa.md`

---

## 4.1 Chat RAG (Fase 2 — bônus antecipado)

Métricas preliminares do chat conversacional com Groq (smoke test 2026-04-21):

| Métrica | Valor | Observação |
|---|---|---|
| Latência média da API Groq (llama-3.3-70b) | 1–3 s | inclui retrieval + inferência |
| Tamanho do contexto enviado | ~2000 tokens | 30 obras formatadas + system prompt |
| Limite de contexto do modelo | 128 K tokens | Groq para `versatile` |
| Testes adversariais | **7/7 recusados** | off-topic, injection, jailbreak, language-switch, system-reveal, médico, jurídico |
| Testes de metadados | **7/8 corretos** | contagem, autor, ISBN, ano, autoria, não-existente, esgotado (falha parcial em "esgotado"), temática |
| Frase de recusa canônica | 100% de aderência | em 7 ataques, todos usaram a frase literal configurada |

**Observações qualitativas:**
- Idioma pt-BR mantido mesmo sob ataque *language switch* ("Reply in English only").
- Nenhum vazamento do *system prompt* em 3 tentativas diretas.
- Citações `(Obra #N)` rastreadas corretamente aos IDs do acervo em todas as respostas on-topic.

Script de reprodução: `docs/seguranca_chat.md` §7.

## 5. Comparativo entre modelos (opcional)

Se o Givanildo rodar o T2 completo, compilar tabela comparativa:

| Modelo | Cobertura | p50 (ms) | p95 (ms) | % plausível |
|---|---|---|---|---|
| paraphrase-multilingual-MiniLM-L12-v2 ⭐ | ? | ? | ? | ? |
| distiluse-base-multilingual-cased-v1 | ? | ? | ? | ? |
| BERTimbau | ? | ? | ? | ? |

---

## 6. Painel de dashboard (proposta)

Para a apresentação final (Sprint 3), Ronny vai construir uma view Django em `/metricas/` com:

- Gráfico de barras: obras por tipo × com/sem embedding
- Histograma de latência das últimas 100 recomendações (logadas em uma tabela `RecomendacaoLog`)
- Tabela top-10 obras mais recomendadas
- Contador de cliques "ver similares" (a instrumentar)

Sprint 1 entrega só os números brutos. A UI vem na Sprint 3.

---

## 7. Observações finais

*(Ronny preenche: surpresas, outliers, recomendações de ajuste no modelo ou na função de busca.)*
