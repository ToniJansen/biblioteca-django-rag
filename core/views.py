from datetime import date

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_tables2 import SingleTableView

from .models import emprestimo, livro, pessoa
from .tables import emprestimo_table, livro_table, pessoa_table


def index(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None:
            login(request, user)
            return redirect('menu_alias')
    return render(request, 'core/index.html')


def logout_view(request):
    logout(request)
    return redirect('index_alias')


@login_required
def menu(request):
    todos_emprestimos = emprestimo.objects.filter(data_devolucao_real__isnull=True)
    atrasados = sum(1 for e in todos_emprestimos if e.atrasado)
    context = {
        'total_livros': livro.objects.count(),
        'total_leitores': pessoa.objects.filter(funcao='Leitor', ativo=True).count(),
        'emprestimos_ativos': todos_emprestimos.count(),
        'emprestimos_atrasados': atrasados,
        'bibliografias': livro.objects.filter(tipo_obra='BIBLIOGRAFIA').count(),
        'teses': livro.objects.filter(tipo_obra='TESE_DISSERTACAO').count(),
        'monografias': livro.objects.filter(tipo_obra='MONOGRAFIA').count(),
        'usuario': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'core/menu.html', context)


@login_required
def atrasados(request):
    todos = emprestimo.objects.filter(data_devolucao_real__isnull=True, data_devolucao_prevista__lt=date.today())
    return render(request, 'core/atrasados.html', {'emprestimos': todos})


@login_required
def exportar_livros_csv(request):
    """Exporta o acervo de livros para CSV (download direto pelo navegador).

    Demonstra integracao Django ORM + Pandas:
      banco SQL  ->  pessoa.objects.values()  ->  pd.DataFrame  ->  CSV  ->  download
    """
    import pandas as pd

    # 1) Pega dados do banco via ORM (queryset.values devolve dicionarios)
    qs = livro.objects.values('id', 'titulo', 'autor', 'tipo_obra',
                              'ano', 'isbn', 'exemplares_total',
                              'exemplares_disponiveis')

    # 2) Converte em DataFrame Pandas
    df = pd.DataFrame(list(qs))

    # 3) Configura HttpResponse para forcar download de CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=livros.csv'

    # 4) Escreve o CSV direto no corpo da resposta HTTP
    df.to_csv(path_or_buf=response, index=False)
    return response


@login_required
def importar_livros_csv(request):
    """Le um CSV do disco e imprime no terminal (versao didatica, sem gravar).

    Demonstra o caminho inverso: CSV -> DataFrame -> iterrows -> Python.
    A gravacao real (.objects.create) fica para uma proxima iteracao.
    """
    import pandas as pd
    from pathlib import Path

    arquivo = Path.home() / 'Downloads' / 'livros.csv'
    if not arquivo.exists():
        return HttpResponse(
            f"Arquivo nao encontrado em {arquivo}. "
            f"Exporte primeiro em /exportar_livros_csv/ e mova o arquivo para ~/Downloads/"
        )

    df = pd.read_csv(arquivo)

    for indice, linha in df.iterrows():
        print(indice, "Titulo:", linha.get('titulo'))
        print(indice, "Autor:", linha.get('autor'))
        print(indice, "Ano:", linha.get('ano'))
        print(indice, "Exemplares:", linha.get('exemplares_total'))
        print("---")

    return HttpResponse(f"Lidas {len(df)} linhas do CSV (saida no terminal do servidor).")


@login_required
def chat(request):
    """Chat conversacional sobre o acervo (RAG: MiniLM + Groq)."""
    context = {'pergunta': '', 'resposta': None, 'obras_citadas': [], 'erro': None}

    if request.method == 'POST':
        pergunta = (request.POST.get('pergunta') or '').strip()
        context['pergunta'] = pergunta

        if pergunta:
            try:
                from recomendador.chat.interface import responder_pergunta
                resp = responder_pergunta(pergunta)
                context['resposta'] = resp.texto
                if resp.obras_citadas:
                    context['obras_citadas'] = list(
                        livro.objects.filter(pk__in=resp.obras_citadas)
                    )
                    # preserva a ordem em que o LLM citou
                    ordem = {lid: i for i, lid in enumerate(resp.obras_citadas)}
                    context['obras_citadas'].sort(key=lambda o: ordem.get(o.pk, 999))
            except Exception as e:
                context['erro'] = str(e)

    return render(request, 'core/chat.html', context)


class pessoa_list(LoginRequiredMixin, ListView):
    model = pessoa


class pessoa_menu(LoginRequiredMixin, SingleTableView):
    model = pessoa
    table_class = pessoa_table
    template_name = 'core/pessoa_menu.html'
    table_pagination = {'per_page': 10}


class pessoa_create(LoginRequiredMixin, CreateView):
    model = pessoa
    fields = ['nome', 'email', 'celular', 'funcao', 'nascimento', 'ativo']
    success_url = reverse_lazy('pessoa_menu_alias')


class pessoa_update(LoginRequiredMixin, UpdateView):
    model = pessoa
    fields = ['nome', 'email', 'celular', 'funcao', 'nascimento', 'ativo']
    success_url = reverse_lazy('pessoa_menu_alias')


class pessoa_delete(LoginRequiredMixin, DeleteView):
    model = pessoa
    template_name_suffix = '_delete'
    success_url = reverse_lazy('pessoa_menu_alias')


class livro_detail(LoginRequiredMixin, DetailView):
    """Pagina de detalhe de uma obra com top-5 similares via embeddings."""
    model = livro
    template_name = 'core/livro_detail.html'
    context_object_name = 'obra'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # import local pra nao quebrar se o app recomendador nao estiver carregado em algum ambiente
        from recomendador.services import recomendar_livros
        ctx['similares'] = recomendar_livros(self.object.pk, top_k=5)
        # flag pra template: embedding existe?
        ctx['tem_embedding'] = hasattr(self.object, 'embedding')
        return ctx


class livro_list(LoginRequiredMixin, ListView):
    model = livro


class livro_menu(LoginRequiredMixin, SingleTableView):
    model = livro
    table_class = livro_table
    template_name = 'core/livro_menu.html'
    table_pagination = {'per_page': 10}


class livro_create(LoginRequiredMixin, CreateView):
    model = livro
    fields = ['titulo', 'autor', 'tipo_obra', 'ano', 'isbn', 'exemplares_total', 'exemplares_disponiveis']
    success_url = reverse_lazy('livro_menu_alias')


class livro_update(LoginRequiredMixin, UpdateView):
    model = livro
    fields = ['titulo', 'autor', 'tipo_obra', 'ano', 'isbn', 'exemplares_total', 'exemplares_disponiveis']
    success_url = reverse_lazy('livro_menu_alias')


class livro_delete(LoginRequiredMixin, DeleteView):
    model = livro
    template_name_suffix = '_delete'
    success_url = reverse_lazy('livro_menu_alias')


class emprestimo_list(LoginRequiredMixin, ListView):
    model = emprestimo


class emprestimo_menu(LoginRequiredMixin, SingleTableView):
    model = emprestimo
    table_class = emprestimo_table
    template_name = 'core/emprestimo_menu.html'
    table_pagination = {'per_page': 10}


class emprestimo_create(LoginRequiredMixin, CreateView):
    model = emprestimo
    fields = ['livro', 'leitor']
    success_url = reverse_lazy('emprestimo_menu_alias')


class emprestimo_update(LoginRequiredMixin, UpdateView):
    model = emprestimo
    fields = ['livro', 'leitor', 'data_devolucao_prevista', 'data_devolucao_real']
    success_url = reverse_lazy('emprestimo_menu_alias')


class emprestimo_delete(LoginRequiredMixin, DeleteView):
    model = emprestimo
    template_name_suffix = '_delete'
    success_url = reverse_lazy('emprestimo_menu_alias')
