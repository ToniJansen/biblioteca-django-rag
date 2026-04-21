import os
import sys

from django.apps import AppConfig


class RecomendadorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recomendador'

    def ready(self):
        from . import signals  # noqa: F401 — conecta post_save/post_delete

        # Pre-carrega o modelo SentenceTransformer quando rodando em runserver,
        # pulando comandos administrativos (migrate, makemigrations, shell,
        # test, collectstatic, etc.) que nao precisam do modelo. Em producao
        # com gunicorn, usar preload_app=True e chamar preload_model() no
        # gunicorn.conf.py (ver on_starting hook).
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'false':
            try:
                from .embeddings import preload_model
                preload_model()
            except Exception:
                # nao quebra o startup do runserver se modelo nao puder ser carregado
                pass
