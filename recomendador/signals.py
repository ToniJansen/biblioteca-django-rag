"""Signals do modulo recomendador.

- Regenera o embedding sempre que um livro e criado ou editado.
- Invalida o cache em memoria da matriz de embeddings sempre que o acervo muda
  (criacao/atualizacao/delecao de livro, criacao/delecao de LivroEmbedding).

Lazy import do embeddings.py para nao carregar o modelo durante migrations
ou comandos como `startapp` que disparam Django setup.
"""
import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


logger = logging.getLogger(__name__)


@receiver(post_save, sender='core.livro')
def regenerar_embedding(sender, instance, **kwargs):
    """Recalcula o embedding do livro recem-salvo.

    Falha silenciosamente se o modelo nao puder ser carregado (ex: sem rede
    na primeira execucao, sem disco para baixar). O CRUD do livro nao deve
    quebrar por causa do modulo de recomendacao.

    Em producao com volume maior, mover para celery/background task.
    """
    try:
        import numpy as np

        from .embeddings import build_text_for_embedding, gerar_embedding, get_nome_modelo
        from .models import LivroEmbedding

        texto = build_text_for_embedding(instance)
        vetor = gerar_embedding(texto).astype(np.float32)

        LivroEmbedding.objects.update_or_create(
            livro=instance,
            defaults={
                'texto_fonte': texto,
                'modelo_versao': get_nome_modelo(),
                'vetor': vetor.tobytes(),
                'dimensao': int(vetor.shape[0]),
            },
        )
    except Exception as e:
        logger.warning('Falhou ao gerar embedding para livro id=%s: %s', instance.pk, e)


def _invalidar_cache(*args, **kwargs):
    """Invalida o cache da matriz de embeddings usado pelo chat e pela recomendacao."""
    from .services import invalidar_cache_matriz
    invalidar_cache_matriz()


# Invalidacao do cache em toda mutacao relevante no acervo.
post_save.connect(_invalidar_cache, sender='core.livro')
post_delete.connect(_invalidar_cache, sender='core.livro')
post_save.connect(_invalidar_cache, sender='recomendador.LivroEmbedding')
post_delete.connect(_invalidar_cache, sender='recomendador.LivroEmbedding')
