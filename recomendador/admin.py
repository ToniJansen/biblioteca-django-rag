from django.contrib import admin
from .models import LivroEmbedding


@admin.register(LivroEmbedding)
class LivroEmbeddingAdmin(admin.ModelAdmin):
    list_display = ('livro', 'modelo_versao', 'dimensao', 'atualizado_em')
    list_filter = ('modelo_versao',)
    search_fields = ('livro__titulo', 'texto_fonte')
    readonly_fields = ('texto_fonte', 'modelo_versao', 'dimensao', 'atualizado_em')
    exclude = ('vetor',)  # esconde o blob
