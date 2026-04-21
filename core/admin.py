from django.contrib import admin
from .models import pessoa, livro, emprestimo


@admin.register(pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'funcao', 'ativo')
    list_filter = ('funcao', 'ativo')
    search_fields = ('nome', 'email')


@admin.register(livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'tipo_obra', 'ano', 'isbn', 'exemplares_disponiveis', 'exemplares_total')
    list_filter = ('tipo_obra',)
    search_fields = ('titulo', 'autor', 'isbn')


@admin.register(emprestimo)
class EmprestimoAdmin(admin.ModelAdmin):
    list_display = ('livro', 'leitor', 'data_saida', 'data_devolucao_prevista', 'data_devolucao_real', 'status')
    list_filter = ('data_devolucao_real',)
    search_fields = ('livro__titulo', 'leitor__nome')
