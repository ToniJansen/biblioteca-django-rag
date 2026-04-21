"""Wrapper em torno do sentence-transformers com lazy-load e modo mock para testes.

Uso:
    from recomendador.embeddings import gerar_embedding, build_text_for_embedding
    vetor = gerar_embedding("Introducao a redes neurais | Joao da Silva | bibliografia")

O modelo so e baixado/carregado na primeira chamada. Em testes ou ambientes sem
rede, setar RECOMENDADOR_MOCK=True nas settings retorna vetores deterministicos
derivados de um hash do texto.
"""
from __future__ import annotations

import hashlib
import logging
from typing import List

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

_modelo = None


def _carregar_modelo():
    """Lazy-load do SentenceTransformer. Retorna None em modo mock."""
    global _modelo

    if getattr(settings, 'RECOMENDADOR_MOCK', False):
        return None

    if _modelo is None:
        from sentence_transformers import SentenceTransformer
        nome = getattr(settings, 'RECOMENDADOR_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
        logger.info('Carregando modelo de embeddings: %s', nome)
        _modelo = SentenceTransformer(nome)
    return _modelo


def _mock_embedding(texto: str, dim: int = 384) -> np.ndarray:
    """Vetor deterministico baseado em hash do texto. So usado com RECOMENDADOR_MOCK=True."""
    seed = int(hashlib.md5(texto.encode('utf-8')).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(dim).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-10)


def build_text_for_embedding(livro_obj) -> str:
    """Monta o texto que sera vetorizado para um livro.

    Concatena titulo + autor + tipo de obra legivel. Formato legivel para o
    modelo multilingual entender o contexto sem depender de sinopse (a maioria
    das obras do acervo nao tem sinopse).
    """
    tipo_legivel = {
        'BIBLIOGRAFIA': 'bibliografia',
        'TESE_DISSERTACAO': 'tese ou dissertacao',
        'MONOGRAFIA': 'monografia',
    }.get(livro_obj.tipo_obra, livro_obj.tipo_obra.lower())

    partes = [livro_obj.titulo, livro_obj.autor, tipo_legivel]
    return ' | '.join(p.strip() for p in partes if p and p.strip())


def gerar_embedding(texto: str) -> np.ndarray:
    """Gera vetor float32 normalizado para um texto."""
    modelo = _carregar_modelo()

    if modelo is None:
        return _mock_embedding(texto)

    vetor = modelo.encode(texto, normalize_embeddings=True)
    return vetor.astype(np.float32)


def gerar_embeddings_batch(textos: List[str]) -> np.ndarray:
    """Gera vetores para uma lista de textos em uma passada (mais rapido que encode individual)."""
    modelo = _carregar_modelo()

    if modelo is None:
        return np.stack([_mock_embedding(t) for t in textos])

    vetores = modelo.encode(textos, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    return vetores.astype(np.float32)


def get_nome_modelo() -> str:
    """Retorna o nome/versao do modelo atualmente configurado. Usado para versionar embeddings."""
    if getattr(settings, 'RECOMENDADOR_MOCK', False):
        return 'mock'
    return getattr(settings, 'RECOMENDADOR_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')


def preload_model() -> bool:
    """Forca o carregamento do modelo SentenceTransformer.

    Destina-se a ser chamado no startup da aplicacao (AppConfig.ready para
    runserver, gunicorn.conf.py on_starting para producao com preload_app=True)
    para evitar que cada worker faça lazy-load independente e gere picos de
    memoria (~450 MB por worker).

    Retorna True se o modelo foi carregado, False em modo mock ou se houve
    falha (logada, nao propagada).
    """
    try:
        modelo = _carregar_modelo()
        return modelo is not None
    except Exception as e:
        logger.warning('preload_model falhou: %s', e)
        return False
