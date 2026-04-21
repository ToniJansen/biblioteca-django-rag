from django.apps import AppConfig


class RecomendadorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recomendador'

    def ready(self):
        from . import signals  # noqa: F401 — conecta o post_save do livro
