"""Logica de recomendacao: dado um livro ou leitor, retorna obras similares do acervo.

Funcoes publicas:
    recomendar_livros(livro_id, top_k)           -> por similaridade com uma obra
    recomendar_para_leitor(leitor_id, top_k)     -> por historico do leitor (media)

Como funciona: carrega todas as embeddings numa matriz numpy, calcula similaridade
cosseno (vetores ja vem normalizados pelo embeddings.py), retorna top-k. Para
acervo de ate ~1000 obras isso roda em <5ms.
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np
from django.db.models import QuerySet

from core.models import emprestimo, livro
from .models import LivroEmbedding


def _carregar_matriz(queryset: Optional[QuerySet] = None) -> tuple:
    """Carrega todas as embeddings em memoria.

    Retorna (matriz_numpy [N, D], lista_de_livro_ids na mesma ordem).
    Se nao houver embeddings ou apenas 0 itens, retorna tupla vazia.
    """
    qs = queryset if queryset is not None else LivroEmbedding.objects.all()
    registros = list(qs.only('livro_id', 'vetor', 'dimensao'))

    if not registros:
        return np.empty((0, 0), dtype=np.float32), []

    ids = [r.livro_id for r in registros]
    matriz = np.stack([r.as_numpy for r in registros])
    return matriz, ids


def _top_k_similaridade(vetor_alvo: np.ndarray, matriz: np.ndarray, ids: List[int],
                        top_k: int, ids_excluir: List[int] = None) -> List[int]:
    """Retorna os top_k ids de livros mais similares, excluindo ids_excluir."""
    if matriz.size == 0:
        return []

    # vetores ja vem normalizados de embeddings.py -> produto interno = similaridade cosseno
    # errstate silencia warnings cosmeticos do BLAS em operacoes com subnormais
    with np.errstate(divide='ignore', over='ignore', invalid='ignore'):
        scores = matriz @ vetor_alvo.reshape(-1)

    excluir = set(ids_excluir or [])
    if excluir:
        for i, livro_id in enumerate(ids):
            if livro_id in excluir:
                scores[i] = -np.inf

    # argpartition e mais rapido que argsort quando top_k << N, mas ambos funcionam
    indices = np.argsort(scores)[::-1][:top_k]
    return [ids[i] for i in indices if scores[i] > -np.inf]


def recomendar_livros(livro_id: int, top_k: int = 5) -> List:
    """Dado um livro, retorna top_k livros similares (excluindo o proprio).

    Retorna lista vazia se o livro nao tem embedding ou se o acervo tem <2 obras.
    """
    try:
        alvo = LivroEmbedding.objects.get(livro_id=livro_id)
    except LivroEmbedding.DoesNotExist:
        return []

    matriz, ids = _carregar_matriz()
    if len(ids) <= 1:
        return []

    ids_recomendados = _top_k_similaridade(
        vetor_alvo=alvo.as_numpy,
        matriz=matriz,
        ids=ids,
        top_k=top_k,
        ids_excluir=[livro_id],
    )

    # preserva a ordem da recomendacao ao trazer do banco
    ordem = {lid: i for i, lid in enumerate(ids_recomendados)}
    obras = list(livro.objects.filter(pk__in=ids_recomendados))
    obras.sort(key=lambda l: ordem.get(l.pk, 999))
    return obras


def recomendar_para_leitor(leitor_id: int, top_k: int = 5) -> List:
    """Recomenda com base na media dos embeddings do historico do leitor.

    Exclui livros ja emprestados pelo leitor. Retorna vazio se o leitor
    nunca emprestou nada ou se nenhum dos livros emprestados tem embedding.
    """
    ids_lidos = list(
        emprestimo.objects.filter(leitor_id=leitor_id)
        .values_list('livro_id', flat=True).distinct()
    )
    if not ids_lidos:
        return []

    registros = list(LivroEmbedding.objects.filter(livro_id__in=ids_lidos))
    if not registros:
        return []

    vetores = np.stack([r.as_numpy for r in registros])
    vetor_medio = vetores.mean(axis=0)
    # renormaliza apos a media
    vetor_medio = vetor_medio / (np.linalg.norm(vetor_medio) + 1e-10)

    matriz, ids = _carregar_matriz()
    ids_recomendados = _top_k_similaridade(
        vetor_alvo=vetor_medio,
        matriz=matriz,
        ids=ids,
        top_k=top_k,
        ids_excluir=ids_lidos,
    )

    ordem = {lid: i for i, lid in enumerate(ids_recomendados)}
    obras = list(livro.objects.filter(pk__in=ids_recomendados))
    obras.sort(key=lambda l: ordem.get(l.pk, 999))
    return obras
