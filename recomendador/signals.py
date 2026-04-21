"""Signal que regenera o embedding sempre que um livro e criado ou editado.

Lazy import do embeddings.py para nao carregar o modelo durante migrations
ou comandos como `startapp` que disparam Django setup.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


import logging

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
