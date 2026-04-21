"""Configuracao do Gunicorn para o biblioteca_mvp.

Pre-carrega o modelo SentenceTransformer uma unica vez no master antes de
forkar os workers. Isso evita que cada worker carregue o modelo de ~450 MB em
memoria de forma independente, reduzindo o uso total de RAM proporcionalmente
ao numero de workers.

Uso:
    gunicorn biblioteca_mvp.wsgi:application --config gunicorn.conf.py

Ajuste workers/bind conforme ambiente. Preload_app=True e essencial para que o
modelo carregado aqui seja herdado pelos workers via copy-on-write.
"""
import os

# Rede e workers
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
timeout = int(os.getenv('GUNICORN_TIMEOUT', '60'))

# Fundamental para que o modelo pre-carregado em on_starting seja herdado
# pelos workers. Com preload_app=False, cada worker faz seu proprio carregamento.
preload_app = True


def on_starting(server):
    """Executado uma unica vez no master, antes do fork dos workers."""
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_mvp.settings')
    django.setup()

    try:
        from recomendador.embeddings import preload_model
        ok = preload_model()
        server.log.info(
            'recomendador.preload_model: %s',
            'modelo carregado' if ok else 'mock ou falha (ver logs)',
        )
    except Exception as e:
        server.log.error('Falha ao pre-carregar modelo de embeddings: %s', e)
