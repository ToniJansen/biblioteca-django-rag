"""View do painel /metricas/.

Renderiza um dashboard simples com a tabela de papéis e views
da camada analítica proposta para o MVP. A tabela é desenhada
com plotly.graph_objects.Table e embarcada como HTML no template.
"""

import plotly.graph_objects as go
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# Catálogo das views da camada analítica (read models).
# Mantido em código para o MVP — quando as views SQL existirem
# de fato no banco, este catálogo pode ser lido de
# sqlite_master / information_schema.
VIEWS_ANALITICAS = [
    (
        'vw_analytics_emprestimos_obt',
        'SQL view (read model)',
        'Base analítica por empréstimo (OBT, 1 linha por empréstimo).',
    ),
    (
        'vw_analytics_acervo_por_tipo',
        'SQL view (read model)',
        'Composição e disponibilidade do acervo por tipo de obra.',
    ),
    (
        'vw_analytics_circulacao_mensal',
        'SQL view (read model)',
        'Empréstimos por mês, tipo de obra e status.',
    ),
    (
        'vw_analytics_leitores_resumo',
        'SQL view (read model)',
        'Engajamento e risco de atraso por leitor.',
    ),
    (
        'vw_analytics_ia_cobertura',
        'SQL view (read model)',
        'Cobertura de embeddings — obras com/sem vetor.',
    ),
    (
        'metricas',
        'Django view',
        'Página Django que renderiza o painel /metricas/.',
    ),
]


def _tabela_views_html() -> str:
    """Monta a tabela Plotly e devolve HTML pronto para incluir no template."""
    nomes = [v[0] for v in VIEWS_ANALITICAS]
    tipos = [v[1] for v in VIEWS_ANALITICAS]
    papeis = [v[2] for v in VIEWS_ANALITICAS]

    # Cores alternadas por linha — paleta sóbria, alinhada ao verde do nav.
    cor_par = '#f6fbf6'
    cor_impar = '#ffffff'
    cores_linha = [cor_par if i % 2 == 0 else cor_impar for i in range(len(nomes))]

    figura = go.Figure(
        data=[
            go.Table(
                columnwidth=[34, 22, 44],
                header=dict(
                    values=['<b>View</b>', '<b>Tipo</b>', '<b>Papel</b>'],
                    fill_color='#198754',  # bootstrap success
                    font=dict(color='white', size=13),
                    align='left',
                    height=34,
                ),
                cells=dict(
                    values=[nomes, tipos, papeis],
                    fill_color=[cores_linha],
                    align='left',
                    font=dict(color='#212529', size=12),
                    height=28,
                ),
            )
        ]
    )
    figura.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=60 + 32 * len(nomes),
    )
    return figura.to_html(include_plotlyjs='cdn', full_html=False)


@login_required
def painel(request):
    contexto = {
        'tabela_views_html': _tabela_views_html(),
        'total_views': len(VIEWS_ANALITICAS),
    }
    return render(request, 'metricas/painel.html', contexto)
