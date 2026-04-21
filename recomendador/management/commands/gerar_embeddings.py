"""Management command: gera embeddings para todas as obras do acervo.

Uso:
    python manage.py gerar_embeddings              # gera apenas para livros sem embedding
    python manage.py gerar_embeddings --force      # regenera tudo (ex: trocou de modelo)
    python manage.py gerar_embeddings --mock       # modo mock (CI / sem rede)

Primeira execucao baixa o modelo do HuggingFace (~420 MB) e cacheia em ~/.cache/huggingface.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from core.models import livro
from recomendador.embeddings import (
    build_text_for_embedding,
    gerar_embeddings_batch,
    get_nome_modelo,
)
from recomendador.models import LivroEmbedding


class Command(BaseCommand):
    help = 'Gera embeddings para todas as obras do acervo (ou apenas as pendentes).'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Regenera todos os embeddings, mesmo os existentes.')
        parser.add_argument('--mock', action='store_true', help='Usa embeddings mock deterministicos (sem baixar modelo).')

    def handle(self, *args, **options):
        if options['mock']:
            settings.RECOMENDADOR_MOCK = True
            self.stdout.write(self.style.WARNING('Modo MOCK ativado — embeddings deterministicos sem modelo real.'))

        if options['force']:
            queryset = livro.objects.all()
            self.stdout.write(f'Regenerando {queryset.count()} embeddings (--force).')
        else:
            queryset = livro.objects.exclude(
                pk__in=LivroEmbedding.objects.values_list('livro_id', flat=True),
            )
            self.stdout.write(f'Gerando embeddings pendentes: {queryset.count()} obras.')

        if not queryset.exists():
            self.stdout.write(self.style.SUCCESS('Nada a fazer.'))
            return

        obras = list(queryset)
        textos = [build_text_for_embedding(o) for o in obras]

        self.stdout.write(f'Modelo: {get_nome_modelo()}')
        self.stdout.write('Gerando vetores...')
        vetores = gerar_embeddings_batch(textos)

        versao = get_nome_modelo()
        criados, atualizados = 0, 0

        import numpy as np

        for obra, texto, vetor in zip(obras, textos, vetores):
            vetor = vetor.astype(np.float32)
            _, created = LivroEmbedding.objects.update_or_create(
                livro=obra,
                defaults={
                    'texto_fonte': texto,
                    'modelo_versao': versao,
                    'vetor': vetor.tobytes(),
                    'dimensao': int(vetor.shape[0]),
                },
            )
            if created:
                criados += 1
            else:
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Pronto. {criados} criado(s), {atualizados} atualizado(s). Dimensao: {vetores.shape[1]}.'
        ))
