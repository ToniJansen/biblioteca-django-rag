# ADR-001 — Escolha do modelo de embeddings para recomendação

**Status:** 🟢 **APROVADO PROVISORIAMENTE** (2026-04-21) — aguarda benchmark T2 independente do Givanildo para confirmação formal
**Data:** 2026-04-20 (draft) / 2026-04-21 (aprovação provisória) / _____________________ (aprovação final após T2)
**Decisor(es):** Antonio Jansen (arquitetura), Givanildo Gramacho (pesquisa)
**Aprovadores:** grupo inteiro (retro Sprint 1 em 10/05)

---

## Contexto

O módulo `recomendador/` do `biblioteca_mvp` precisa gerar vetores de embedding de obras do acervo (título + autor + tipo de obra) para calcular similaridade semântica e recomendar livros relacionados a um leitor.

Restrições técnicas:

- Acervo pequeno (~30–100 obras) — FAISS e índices pesados são overkill
- Rodar em **CPU** local (nenhum integrante tem GPU)
- Cache do modelo no repositório Git de cada integrante — tamanho <500 MB preferível
- **Português brasileiro** obrigatório (títulos acadêmicos em pt-br)
- Latência <200ms por encode (não travar o admin)

A stack está fixada em **Sentence-Transformers (HuggingFace)** por decisão da proposta (seção 4.2) — este ADR decide *qual* variante específica dentro dessa família.

---

## Decisão

**Modelo escolhido:** `paraphrase-multilingual-MiniLM-L12-v2`

Configurado em `biblioteca_mvp/biblioteca_mvp/settings.py`:

```python
RECOMENDADOR_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
```

Dimensão do embedding: **384** (caberá em `BinaryField` do SQLite sem problemas).

---

## Justificativa

### Alternativas consideradas

| Modelo | Descartado? | Razão |
|---|---|---|
| `all-MiniLM-L6-v2` | ✅ descartado | Treinado só em inglês. Títulos em pt-br produzem embeddings ruins. |
| `distiluse-base-multilingual-cased-v1` | ❌ mantido como fallback | 512 dim, ~480 MB, qualidade similar mas maior e mais lento sem ganho claro |
| `neuralmind/bert-base-portuguese-cased` (BERTimbau) | ❌ mantido como fallback | 768 dim, nativo pt-br, mas precisa pooling manual (não é sentence-transformer) e encode ~300 ms |
| **`paraphrase-multilingual-MiniLM-L12-v2`** | ✅ escolhido | Melhor custo-benefício: pt-br + 384 dim + ~100 ms + API padrão |

### Critérios de escolha (em ordem)

1. **Qualidade pt-br** — MiniLM multilingual cobre 50+ línguas incluindo pt-br; benchmark público (MTEB) mostra resultados sólidos
2. **Latência CPU** — MiniLM-L12 é a variante "enxuta" do MiniLM, 100ms em CPU moderna
3. **Simplicidade de uso** — `SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2').encode(texto)` funciona direto, sem pooling manual como BERT puro
4. **Tamanho** — 420 MB cabe no cache local sem inflar o clone do projeto (modelo é baixado na primeira execução em `~/.cache/huggingface`)

### O que o benchmark do Givanildo precisa validar (T2)

Para confirmar esta decisão, o benchmark deve mostrar:

- [x] ~~Latência de encode individual < 200 ms~~ — medido em CPU Mac: **33 ms/obra em batch de 30** (6× melhor que a meta) ✅
- [ ] Similaridade cosseno > 0.5 entre pares sabidamente próximos — *aguarda T2 Givanildo rodar*
- [ ] Similaridade cosseno < 0.3 entre pares sabidamente distantes — *aguarda T2 Givanildo rodar*
- [x] ~~Download do modelo funciona~~ — confirmado em 2026-04-20, ~420 MB em `~/.cache/huggingface/` ✅
- [x] **Bônus:** acurácia qualitativa — no smoke test em UI `/livro/detail/12/` (Deep Learning), as 5 recomendações foram: Hands-On ML, tese Deep Learning em fraudes, Pattern Recognition, IA Uma Abordagem Moderna, tese RNC em imagens médicas — 5/5 plausíveis ✅

**Evidência em produção:** o pipeline RAG do chat RAG (Fase 2) também usa o mesmo modelo para vetorizar perguntas do usuário em tempo real. Em 7 consultas de teste (incluindo `"tem livros sobre redes neurais em medicina?"`), o retrieval trouxe obras relevantes com precisão adequada.

Se o benchmark T2 do Givanildo confirmar os critérios 2 e 3 pendentes, o status deste ADR passa para **APROVADO DEFINITIVO**. Se falhar, reabrir com decisão revisada (provavelmente BERTimbau).

---

## Consequências

### Positivas

- API idêntica ao sentence-transformers padrão, onboarding trivial para qualquer integrante
- 384 dim é compacto: `30 obras × 384 floats × 4 bytes = 46 KB` no banco total
- Portável: Apache 2.0, sem lock-in
- Multilingual: se no futuro o acervo tiver obras em inglês/espanhol, funciona igual

### Negativas

- Download de 420 MB na primeira execução — documentar no README que pode demorar 2–5 min
- Modelo não é especializado em pt-br; possível perda marginal de qualidade vs BERTimbau
- Depende de torch (~800 MB a mais no venv) — não-negociável pois sentence-transformers requer

### Riscos residuais

- Se o acervo crescer para >10k obras, a busca em numpy deixa de escalar e precisa migrar pra FAISS ou pgvector (fora do escopo do MVP)
- Primeira carga do modelo em cada nova máquina requer rede e ~90 s — CI/CD futuro precisa fazer cache do diretório `~/.cache/huggingface`

---

## Referências

- Proposta seção 4.2: `biblioteca_mvp/proposta/proposta.md`
- Benchmark comparativo: `biblioteca_mvp/docs/benchmark_modelos.md`
- Card HuggingFace: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- MTEB leaderboard multilingual: https://huggingface.co/spaces/mteb/leaderboard
