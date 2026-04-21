"""Template tags para renderizacao consistente de badges.

Centraliza o mapeamento entre valores de dominio (tipo_obra, status de
emprestimo) e as classes Bootstrap usadas para colorir cada badge, de modo
que a manutencao fique em um unico lugar.

Uso nos templates:
    {% load badges %}
    {% badge_tipo_obra obra.tipo_obra %}
    {% badge_tipo_obra obra.tipo_obra 'Tese / Dissert.' %}  {# rotulo curto #}
    {% badge_status emprestimo.status %}
    {% badge_exemplares obra.exemplares_disponiveis %}
"""
from django import template
from django.utils.html import format_html

register = template.Library()


_CORES_TIPO_OBRA = {
    'BIBLIOGRAFIA': 'bg-primary',
    'TESE_DISSERTACAO': 'bg-warning text-dark',
    'MONOGRAFIA': 'bg-info text-dark',
}

_ROTULOS_TIPO_OBRA_LONGO = {
    'BIBLIOGRAFIA': 'Bibliografia',
    'TESE_DISSERTACAO': 'Tese / Dissertacao',
    'MONOGRAFIA': 'Monografia',
}

_ROTULOS_TIPO_OBRA_CURTO = {
    'BIBLIOGRAFIA': 'Bibliografia',
    'TESE_DISSERTACAO': 'Tese / Dissert.',
    'MONOGRAFIA': 'Monografia',
}

_CORES_STATUS = {
    'EMPRESTADO': 'bg-primary',
    'DEVOLVIDO': 'bg-success',
    'ATRASADO': 'bg-danger',
}


@register.simple_tag
def badge_tipo_obra(tipo_obra, curto=False):
    """Renderiza o badge Bootstrap para o tipo de obra."""
    cor = _CORES_TIPO_OBRA.get(tipo_obra, 'bg-secondary')
    rotulos = _ROTULOS_TIPO_OBRA_CURTO if curto else _ROTULOS_TIPO_OBRA_LONGO
    rotulo = rotulos.get(tipo_obra, tipo_obra)
    return format_html('<span class="badge {}">{}</span>', cor, rotulo)


@register.simple_tag
def badge_status(status):
    """Renderiza o badge Bootstrap para o status do emprestimo."""
    cor = _CORES_STATUS.get(status, 'bg-secondary')
    return format_html('<span class="badge {}">{}</span>', cor, status)


@register.simple_tag
def badge_exemplares(exemplares_disponiveis):
    """Renderiza um badge indicando disponibilidade de exemplares."""
    if exemplares_disponiveis and exemplares_disponiveis > 0:
        return format_html(
            '<span class="badge bg-success">{} disp.</span>',
            exemplares_disponiveis,
        )
    return format_html('<span class="badge bg-secondary">esgotado</span>')
