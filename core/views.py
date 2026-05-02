import json
from datetime import date

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
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
    from . import analytics as an

    todos_emprestimos = emprestimo.objects.filter(data_devolucao_real__isnull=True)
    atrasados = sum(1 for e in todos_emprestimos if e.atrasado)
    total_livros = livro.objects.count()
    total_leitores = pessoa.objects.filter(funcao='Leitor', ativo=True).count()

    acervo_totais = an.get_acervo_totais()
    acervo_por_tipo = an.get_acervo_por_tipo()
    status_gauge = an.get_status_gauge()
    circ_mensal_12m = an.get_circulacao_ultimos_12m()
    ia_cobertura = an.get_ia_cobertura()
    top_obras = an.get_top_obras_d3(limit=4)

    exemplares_total = acervo_totais.get('exemplares_total', 0) or 0
    exemplares_disponiveis = acervo_totais.get('exemplares_disponiveis', 0) or 0
    disponibilidade_pct = round(exemplares_disponiveis / exemplares_total * 100, 1) if exemplares_total else 0
    atraso_pct = round((status_gauge.get('atrasados', 0) or 0) / (status_gauge.get('total', 0) or 1) * 100, 1)
    ia_total = ia_cobertura.get('total', 0) or 0
    ia_pct = round((ia_cobertura.get('com_embedding', 0) or 0) / ia_total * 100, 1) if ia_total else 0

    tipo_labels = {
        'BIBLIOGRAFIA': 'Bibliografia',
        'TESE_DISSERTACAO': 'Teses e Dissertacoes',
        'MONOGRAFIA': 'Monografias',
    }
    acervo_tipo_cards = []
    for item in acervo_por_tipo:
        total_tipo = item.get('total_obras', 0) or 0
        acervo_tipo_cards.append({
            'label': tipo_labels.get(item.get('tipo_obra'), item.get('tipo_obra')),
            'total': total_tipo,
            'disponiveis': item.get('exemplares_disponiveis', 0) or 0,
            'esgotadas': item.get('obras_esgotadas', 0) or 0,
            'pct': round(total_tipo / total_livros * 100, 1) if total_livros else 0,
        })

    context = {
        'total_livros': total_livros,
        'total_leitores': total_leitores,
        'emprestimos_ativos': todos_emprestimos.count(),
        'emprestimos_atrasados': atrasados,
        'bibliografias': livro.objects.filter(tipo_obra='BIBLIOGRAFIA').count(),
        'teses': livro.objects.filter(tipo_obra='TESE_DISSERTACAO').count(),
        'monografias': livro.objects.filter(tipo_obra='MONOGRAFIA').count(),
        'usuario': request.user.get_full_name() or request.user.username,
        'acervo_totais': acervo_totais,
        'acervo_tipo_cards': acervo_tipo_cards,
        'status_gauge': status_gauge,
        'disponibilidade_pct': disponibilidade_pct,
        'atraso_pct': atraso_pct,
        'ia_pct': ia_pct,
        'top_obras': top_obras,
        'circ_mensal_12m': circ_mensal_12m,
        'circ_mensal_12m_json': json.dumps(circ_mensal_12m),
        'status_gauge_json': json.dumps(status_gauge),
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

    def get_queryset(self):
        # Busca por titulo OU autor usando Q objects (Aula 3).
        # Demonstra:
        #   - Q(...) | Q(...)  → operador OR no ORM
        #   - __icontains      → lookup case-insensitive
        qs = super().get_queryset()
        q = (self.request.GET.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(titulo__icontains=q) | Q(autor__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        return ctx


class livro_create(LoginRequiredMixin, CreateView):
    model = livro
    fields = ['titulo', 'autor', 'tipo_obra', 'ano', 'isbn', 'exemplares_total', 'exemplares_disponiveis']
    success_url = reverse_lazy('livro_menu_alias')

    def dispatch(self, request, *args, **kwargs):
        # Aula 3: verificação granular de permissão (alem do LoginRequiredMixin).
        # Permissão padrão Django: <app>.<acao>_<modelo>
        if not request.user.has_perm('core.add_livro'):
            return HttpResponse(
                "Sem permissão para adicionar livros. "
                "Solicite ao administrador a permissão 'core | livro | Can add livro'."
            )
        return super().dispatch(request, *args, **kwargs)


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


@login_required
def metricas(request):
    """Painel analitico alimentado pelas 5 views SQL de analytics."""
    from . import analytics as an

    # KPIs gerais
    acervo_totais = an.get_acervo_totais()
    acervo_por_tipo = an.get_acervo_por_tipo()
    status_gauge = an.get_status_gauge()

    # Circulacao
    circ_mensal_12m = an.get_circulacao_ultimos_12m()
    heatmap = an.get_heatmap_mensal()
    ritmo_semanal = an.get_ritmo_semanal()
    atrasados_lista = an.get_emprestimos_atrasados()

    # Acervo
    top_obras = an.get_top_obras_d3(limit=8)

    # Leitores
    leitores_kpis = an.get_leitores_kpis()
    perfil_leitores = an.get_perfil_leitores()
    leitores_resumo = an.get_leitores_resumo(limit=8)

    # IA
    ia_cobertura = an.get_ia_cobertura()
    obras_sem_emb = an.get_obras_sem_embedding()[:6]
    ia_total = ia_cobertura.get('total', 0) or 0
    ia_com = ia_cobertura.get('com_embedding', 0) or 0
    ia_pct = round(ia_com / ia_total * 100, 1) if ia_total else 0

    exemplares_total = acervo_totais.get('exemplares_total', 0) or 0
    exemplares_disponiveis = acervo_totais.get('exemplares_disponiveis', 0) or 0
    disponibilidade_pct = round(exemplares_disponiveis / exemplares_total * 100, 1) if exemplares_total else 0

    pico_circulacao = max(circ_mensal_12m, key=lambda item: item.get('total', 0), default={})
    ultimo_mes = circ_mensal_12m[-1] if circ_mensal_12m else {}
    ritmo_labels = ['Domingo', 'Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado']
    pico_ritmo = max(ritmo_semanal, key=lambda item: item.get('total', 0), default={})
    pico_dia_idx = pico_ritmo.get('dia_semana')
    pico_dia_nome = ritmo_labels[pico_dia_idx] if isinstance(pico_dia_idx, int) and 0 <= pico_dia_idx < len(ritmo_labels) else 'Sem dados'
    perfil_dominante = max(perfil_leitores, key=lambda item: item.get('qtd_leitores', 0), default={})
    leitor_destaque = leitores_resumo[0] if leitores_resumo else {}
    tipo_labels = {
        'BIBLIOGRAFIA': 'Bibliografia',
        'TESE_DISSERTACAO': 'Tese/Dissertacao',
        'MONOGRAFIA': 'Monografia',
    }
    tipo_dominante = max(acervo_por_tipo, key=lambda item: item.get('total_obras', 0), default={})
    tipo_dominante_nome = tipo_labels.get(tipo_dominante.get('tipo_obra'), tipo_dominante.get('tipo_obra', 'n/d'))
    obras_esgotadas = acervo_totais.get('obras_esgotadas', 0) or 0
    atrasados_total = status_gauge.get('atrasados', 0) or 0
    ativos_total = status_gauge.get('ativos', 0) or 0

    storytelling = {
        'acervo': (
            f"O acervo reune {acervo_totais.get('total_obras', 0) or 0} obras e mantém "
            f"{disponibilidade_pct}% dos exemplares livres para nova circulacao."
        ),
        'circulacao': (
            f"O pico recente de emprestimos aconteceu em {pico_circulacao.get('mes', 'n/d')} "
            f"com {pico_circulacao.get('total', 0) or 0} movimentacoes; {pico_dia_nome} "
            f"e o dia com maior ritmo operacional."
        ),
        'leitores': (
            f"O perfil mais frequente e {perfil_dominante.get('perfil', 'n/d')}, enquanto "
            f"{leitor_destaque.get('leitor_nome', 'o acervo')} concentra "
            f"{leitor_destaque.get('total_emprestimos', 0) or 0} emprestimos."
        ),
        'ia': (
            f"A camada de IA cobre {ia_pct}% do catalogo; "
            f"{ia_cobertura.get('sem_embedding', 0) or 0} obras ainda aguardam embedding."
        ),
    }
    story_titles = {
        'acervo': (
            f"{tipo_dominante_nome} concentra o acervo"
            if tipo_dominante.get('total_obras')
            else "O acervo ainda precisa de dados para leitura"
        ),
        'circulacao': (
            f"{atrasados_total} emprestimos atrasados exigem acompanhamento"
            if atrasados_total
            else "A circulacao esta sem atrasos relevantes"
        ),
        'leitores': (
            f"{perfil_dominante.get('perfil', 'Leitores')} e o perfil mais comum"
            if perfil_dominante
            else "A base de leitores ainda precisa de historico"
        ),
        'ia': (
            f"IA cobre {ia_pct}% do catalogo"
            if ia_total
            else "A cobertura de IA ainda nao foi medida"
        ),
    }
    story_notes = {
        'acervo': (
            f"{tipo_dominante_nome} soma {tipo_dominante.get('total_obras', 0) or 0} obras; "
            f"{obras_esgotadas} obras estao sem saldo disponivel."
        ),
        'circulacao': (
            f"Ha {ativos_total} emprestimos ativos e {atrasados_total} atrasados. "
            f"O pico mensal observado foi {pico_circulacao.get('mes', 'n/d')}."
        ),
        'leitores': (
            f"{leitor_destaque.get('leitor_nome', 'Nenhum leitor')} lidera o volume registrado, "
            f"com {leitor_destaque.get('total_emprestimos', 0) or 0} emprestimos."
        ),
        'ia': (
            f"{ia_cobertura.get('com_embedding', 0) or 0} obras ja alimentam recomendacao e RAG; "
            f"{ia_cobertura.get('sem_embedding', 0) or 0} seguem pendentes."
        ),
    }

    story_cards = [
        {
            'kicker': 'Acervo',
            'value': acervo_totais.get('total_obras', 0) or 0,
            'label': 'obras catalogadas',
            'support': f'{disponibilidade_pct}% dos exemplares estao disponiveis',
        },
        {
            'kicker': 'Circulacao',
            'value': status_gauge.get('total', 0) or 0,
            'label': 'emprestimos acumulados',
            'support': f"Pico em {pico_circulacao.get('mes', 'n/d')}",
        },
        {
            'kicker': 'Leitores',
            'value': leitores_kpis.get('ativos', 0) or 0,
            'label': 'leitores ativos',
            'support': f"Perfil dominante: {perfil_dominante.get('perfil', 'n/d')}",
        },
        {
            'kicker': 'IA',
            'value': f'{ia_pct}%',
            'label': 'cobertura de embeddings',
            'support': f"{ia_cobertura.get('sem_embedding', 0) or 0} obras pendentes",
        },
    ]

    context = {
        # KPIs diretos
        'acervo_totais': acervo_totais,
        'status_gauge': status_gauge,
        'leitores_kpis': leitores_kpis,
        'ia_pct': ia_pct,
        'ia_cobertura': ia_cobertura,
        'disponibilidade_pct': disponibilidade_pct,
        'storytelling': storytelling,
        'story_titles': story_titles,
        'story_notes': story_notes,
        'story_cards': story_cards,
        'top_obras': top_obras[:5],
        'obras_sem_emb': obras_sem_emb,
        'ultimo_mes_total': ultimo_mes.get('total', 0) or 0,
        'pico_mes': pico_circulacao.get('mes', 'n/d'),
        'pico_mes_total': pico_circulacao.get('total', 0) or 0,
        'pico_dia_nome': pico_dia_nome,
        'perfil_dominante': perfil_dominante.get('perfil', 'n/d'),
        'acervo_por_tipo': acervo_por_tipo,
        'circ_mensal_12m': circ_mensal_12m,
        'ritmo_semanal': ritmo_semanal,
        'perfil_leitores': perfil_leitores,
        # D3 datasets (JSON)
        'acervo_por_tipo_json': json.dumps(acervo_por_tipo),
        'circ_mensal_12m_json': json.dumps(circ_mensal_12m),
        'heatmap_json': json.dumps(heatmap),
        'ritmo_semanal_json': json.dumps(ritmo_semanal),
        'top_obras_json': json.dumps(top_obras),
        'perfil_leitores_json': json.dumps(perfil_leitores),
        'status_gauge_json': json.dumps(status_gauge),
        # Tabelas compactas
        'atrasados_lista': atrasados_lista[:5],
        'leitores_resumo': leitores_resumo,
    }
    return render(request, 'core/metricas.html', context)
