# Benchmark de modelos Sentence-Transformers para o acervo

> **Status:** 🟡 rascunho pré-preenchido por Antonio (arquitetura) com base na pesquisa inicial. **Givanildo precisa reproduzir os números localmente (ticket T2)** — os valores abaixo são estimativas de literatura/HuggingFace, não medidas reais.
>
> **Dono final:** Givanildo Gramacho
> **Prazo:** 03/05/2026 (fim da Semana 1 da Sprint 1)
> **Como reproduzir:** ver `scripts/bench_modelos.py` (a criar) ou rodar o script de exemplo no final deste doc.

---

## Contexto

O projeto precisa de um modelo de Sentence-Transformer para gerar embeddings de obras do acervo (título + autor + tipo). Requisitos não-negociáveis:

- **Suporte a português brasileiro** (títulos e autores em pt-br misturados com termos em inglês)
- **Rodar em CPU** — nenhum integrante tem GPU para desenvolvimento
- **Latência de encode <200ms por obra** — pra não travar o admin quando o bibliotecário cadastra um livro
- **Tamanho <500 MB em disco** — pra não inflar o clone do repo e caber no cache local

## Candidatos avaliados

| Modelo | Dim | Tamanho | Latência CPU* | pt-br | Licença |
|---|---|---|---|---|---|
| **`paraphrase-multilingual-MiniLM-L12-v2`** ⭐ | 384 | ~420 MB | ~100 ms | ✅ sim | Apache 2.0 |
| `distiluse-base-multilingual-cased-v1` | 512 | ~480 MB | ~180 ms | ✅ sim | Apache 2.0 |
| `neuralmind/bert-base-portuguese-cased` (BERTimbau) | 768 | ~400 MB | ~300 ms | ✅ nativo pt-br | MIT |
| `all-MiniLM-L6-v2` (descartado) | 384 | ~90 MB | ~30 ms | ❌ só inglês | Apache 2.0 |

*Latência estimada em CPU Intel i5 moderna, encode individual. Valores a confirmar via T2.

## Metodologia proposta (T2 — Givanildo)

1. Ativar venv compartilhada: `source framework/BigData-T2-env/bin/activate`
2. Criar `biblioteca_mvp/scripts/bench_modelos.py` que:
   - Carrega cada um dos 3 modelos candidatos
   - Faz encode individual de cada uma das 30 obras (medindo tempo)
   - Faz encode em batch de todas (medindo tempo total)
   - Mede distância cosseno entre pares sabidamente próximos (ex: "Deep Learning" vs "Pattern Recognition and Machine Learning") e pares sabidamente distantes (ex: "Deep Learning" vs "Casa Grande e Senzala")
   - Salva resultado em `docs/benchmark_resultado.csv`
3. Preencher a tabela acima com números reais
4. Escolher campeão com justificativa em ADR-001

## Critérios de escolha (ordem de prioridade)

1. Qualidade semântica para pt-br — o benchmark de pares próximos/distantes precisa mostrar separação clara
2. Latência em CPU — modelo que demore >2s por encode é descartado
3. Tamanho total — entre modelos equivalentes, preferir o menor
4. Simplicidade de uso — preferir `SentenceTransformer(...)` direto sem pooling manual

## Recomendação preliminar

**`paraphrase-multilingual-MiniLM-L12-v2`** é a primeira escolha porque:

- É o mesmo MiniLM do modelo só-inglês que o time conhece, mas treinado multilingual (50+ línguas, inclui pt-br)
- 384 dimensões é suficiente para 30–100 obras (cabe tranquilo em SQLite BinaryField)
- API compatível com sentence-transformers padrão, sem pooling manual
- Benchmark público do HuggingFace mostra boa qualidade para pt-br em MTEB

Se o benchmark real do Givanildo mostrar qualidade ruim, o fallback é BERTimbau (mais pesado mas nativo pt-br).

## Exemplo de script de benchmark

```python
# biblioteca_mvp/scripts/bench_modelos.py
import time
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

CANDIDATOS = [
    'paraphrase-multilingual-MiniLM-L12-v2',
    'distiluse-base-multilingual-cased-v1',
    'neuralmind/bert-base-portuguese-cased',  # atencao: nao e sentence-transformer nativo, precisa pooling
]

TEXTOS = [
    'Deep Learning | Ian Goodfellow | bibliografia',
    'Pattern Recognition and Machine Learning | Bishop | bibliografia',
    'Python Fluente | Luciano Ramalho | bibliografia',
    'Casa Grande e Senzala | Gilberto Freyre | bibliografia',
]

for nome in CANDIDATOS:
    print(f'\n=== {nome} ===')
    t0 = time.perf_counter()
    modelo = SentenceTransformer(nome)
    print(f'load: {time.perf_counter() - t0:.2f}s')

    t0 = time.perf_counter()
    vetores = modelo.encode(TEXTOS, normalize_embeddings=True)
    print(f'encode 4 textos: {(time.perf_counter() - t0)*1000:.1f}ms')

    sim = cosine_similarity(vetores)
    print(f'sim(DL, PRML) [esperado alto]: {sim[0,1]:.3f}')
    print(f'sim(DL, Casa Grande) [esperado baixo]: {sim[0,3]:.3f}')
```

Uso: `python scripts/bench_modelos.py 2>&1 | tee docs/benchmark_log.txt`
