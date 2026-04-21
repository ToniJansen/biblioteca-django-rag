import django_tables2 as tables
from django.utils.html import format_html
from django_tables2.utils import A

from .models import pessoa, livro, emprestimo


class pessoa_table(tables.Table):
    nome = tables.LinkColumn('pessoa_update_alias', args=[A('pk')])
    email = tables.LinkColumn('pessoa_update_alias', args=[A('pk')])
    funcao = tables.LinkColumn('pessoa_update_alias', args=[A('pk')])
    ativo = tables.Column()
    id = tables.LinkColumn('pessoa_delete_alias', args=[A('pk')], verbose_name='Excluir')

    class Meta:
        model = pessoa
        attrs = {'class': 'table thead-light table-striped table-hover'}
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('nome', 'email', 'funcao', 'ativo')


class livro_table(tables.Table):
    titulo = tables.LinkColumn('livro_detail_alias', args=[A('pk')])
    autor = tables.LinkColumn('livro_detail_alias', args=[A('pk')])
    tipo_obra = tables.Column(verbose_name='Tipo')
    ano = tables.Column()
    isbn = tables.Column()
    exemplares_disponiveis = tables.Column(verbose_name='Disponiveis')
    exemplares_total = tables.Column(verbose_name='Total')
    editar = tables.LinkColumn('livro_update_alias', args=[A('pk')], text='Editar', orderable=False, empty_values=(), verbose_name='Editar')
    id = tables.LinkColumn('livro_delete_alias', args=[A('pk')], verbose_name='Excluir')

    def render_editar(self, record):
        from django.utils.html import format_html
        return format_html('<a href="/livro/update/{}/" class="btn btn-sm btn-outline-secondary">Editar</a>', record.pk)

    def render_tipo_obra(self, record):
        cores = {
            'BIBLIOGRAFIA': 'bg-primary',
            'TESE_DISSERTACAO': 'bg-warning text-dark',
            'MONOGRAFIA': 'bg-info text-dark',
        }
        rotulos = {
            'BIBLIOGRAFIA': 'Bibliografia',
            'TESE_DISSERTACAO': 'Tese/Dissert.',
            'MONOGRAFIA': 'Monografia',
        }
        return format_html('<span class="badge {}">{}</span>', cores.get(record.tipo_obra, 'bg-secondary'), rotulos.get(record.tipo_obra, record.tipo_obra))

    def render_isbn(self, value):
        return value or '-'

    def render_ano(self, value):
        return value or '-'

    class Meta:
        model = livro
        attrs = {'class': 'table thead-light table-striped table-hover'}
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('titulo', 'autor', 'tipo_obra', 'ano', 'isbn', 'exemplares_disponiveis', 'exemplares_total')


class emprestimo_table(tables.Table):
    livro = tables.LinkColumn('emprestimo_update_alias', args=[A('pk')])
    leitor = tables.LinkColumn('emprestimo_update_alias', args=[A('pk')])
    data_saida = tables.Column(verbose_name='Saida')
    data_devolucao_prevista = tables.Column(verbose_name='Prevista')
    data_devolucao_real = tables.Column(verbose_name='Devolvido em')
    status = tables.Column(empty_values=(), verbose_name='Status', orderable=False)
    id = tables.LinkColumn('emprestimo_delete_alias', args=[A('pk')], verbose_name='Excluir')

    def render_status(self, record):
        badge = {'EMPRESTADO': 'bg-primary', 'DEVOLVIDO': 'bg-success', 'ATRASADO': 'bg-danger'}.get(record.status, 'bg-secondary')
        return format_html('<span class="badge {}">{}</span>', badge, record.status)

    class Meta:
        model = emprestimo
        attrs = {'class': 'table thead-light table-striped table-hover'}
        template_name = 'django_tables2/bootstrap4.html'
        fields = ('livro', 'leitor', 'data_saida', 'data_devolucao_prevista', 'data_devolucao_real')
