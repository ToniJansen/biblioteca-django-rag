"""Analytics queries — read from the SQL views created in migration 0003.

Each function returns plain Python dicts/lists ready for JSON serialization
in the template (D3.js / Chart.js).
"""

from django.db import connection


def _dictfetchall(cursor):
    """Return all rows from a cursor as a list of dicts."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _dictfetchone(cursor):
    row = cursor.fetchone()
    if not row:
        return {}
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def get_acervo_por_tipo():
    """Tab Acervo: composition and availability by obra type."""
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM vw_analytics_acervo_por_tipo ORDER BY tipo_obra")
        return _dictfetchall(cur)


def get_acervo_totais():
    """Tab Acervo: aggregate KPIs."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                SUM(total_obras)               AS total_obras,
                SUM(exemplares_total)           AS exemplares_total,
                SUM(exemplares_disponiveis)     AS exemplares_disponiveis,
                SUM(exemplares_emprestados)     AS exemplares_emprestados,
                SUM(obras_esgotadas)            AS obras_esgotadas
            FROM vw_analytics_acervo_por_tipo
        """)
        row = _dictfetchall(cur)
        return row[0] if row else {}


def get_top_obras_emprestadas(limit=10):
    """Tab Acervo: most borrowed books."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT livro_id, titulo, autor, tipo_obra, COUNT(*) AS total
            FROM vw_analytics_emprestimos_obt
            GROUP BY livro_id, titulo, autor, tipo_obra
            ORDER BY total DESC
            LIMIT %s
        """, [limit])
        return _dictfetchall(cur)


def get_circulacao_kpis():
    """Tab Circulação: status breakdown KPIs."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*)                                                    AS total,
                SUM(CASE WHEN status = 'EMPRESTADO' THEN 1 ELSE 0 END)     AS ativos,
                SUM(CASE WHEN status = 'DEVOLVIDO'  THEN 1 ELSE 0 END)     AS devolvidos,
                SUM(CASE WHEN status = 'ATRASADO'   THEN 1 ELSE 0 END)     AS atrasados
            FROM vw_analytics_emprestimos_obt
        """)
        row = _dictfetchall(cur)
        return row[0] if row else {}


def get_circulacao_mensal():
    """Tab Circulação: monthly loan counts."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT ano_mes_saida, SUM(total_emprestimos) AS total
            FROM vw_analytics_circulacao_mensal
            GROUP BY ano_mes_saida
            ORDER BY ano_mes_saida
        """)
        return _dictfetchall(cur)


def get_circulacao_por_tipo_status():
    """Tab Circulação: loans grouped by obra type and status."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT tipo_obra, status, SUM(total_emprestimos) AS total
            FROM vw_analytics_circulacao_mensal
            GROUP BY tipo_obra, status
            ORDER BY tipo_obra, status
        """)
        return _dictfetchall(cur)


def get_emprestimos_atrasados():
    """Tab Circulação: overdue loans list."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT leitor_nome, titulo, data_devolucao_prevista, dias_atraso
            FROM vw_analytics_emprestimos_obt
            WHERE status = 'ATRASADO'
            ORDER BY dias_atraso DESC
        """)
        return _dictfetchall(cur)


def get_leitores_resumo(limit=15):
    """Tab Leitores: reader engagement summary."""
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM vw_analytics_leitores_resumo ORDER BY total_emprestimos DESC LIMIT %s", [limit])
        return _dictfetchall(cur)


def get_leitores_kpis():
    """Tab Leitores: aggregate KPIs."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(DISTINCT CASE WHEN leitor_ativo = 1 THEN leitor_id END) AS ativos,
                COUNT(DISTINCT CASE WHEN leitor_ativo = 0 THEN leitor_id END) AS inativos,
                ROUND(CAST(COUNT(*) AS REAL) / NULLIF(COUNT(DISTINCT leitor_id), 0), 1) AS media_emp
            FROM vw_analytics_emprestimos_obt
        """)
        row = _dictfetchall(cur)
        return row[0] if row else {}


def get_ia_cobertura():
    """Tab IA: embedding coverage."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                SUM(CASE WHEN tem_embedding = 1 THEN 1 ELSE 0 END) AS com_embedding,
                SUM(CASE WHEN tem_embedding = 0 THEN 1 ELSE 0 END) AS sem_embedding,
                COUNT(*) AS total
            FROM vw_analytics_ia_cobertura
        """)
        row = _dictfetchall(cur)
        return row[0] if row else {}


def get_obras_sem_embedding():
    """Tab IA: books missing embeddings."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT livro_id, titulo, autor, tipo_obra
            FROM vw_analytics_ia_cobertura
            WHERE tem_embedding = 0
            ORDER BY titulo
        """)
        return _dictfetchall(cur)


# ---------------------------------------------------------------------------
# Novas queries para o storytelling D3
# ---------------------------------------------------------------------------

def get_circulacao_ultimos_12m():
    """Retorna empréstimos por mês dos últimos 12 meses (para o gráfico de tendência)."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT ano_mes_saida AS mes, SUM(total_emprestimos) AS total
            FROM vw_analytics_circulacao_mensal
            WHERE ano_mes_saida >= strftime('%Y-%m', date('now', '-12 months'))
            GROUP BY ano_mes_saida
            ORDER BY ano_mes_saida
        """)
        return _dictfetchall(cur)


def get_ritmo_semanal():
    """Distribuição de empréstimos por dia da semana (0=Dom, 6=Sáb)."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                CAST(strftime('%w', data_saida) AS INTEGER) AS dia_semana,
                COUNT(*) AS total
            FROM core_emprestimo
            GROUP BY dia_semana
            ORDER BY dia_semana
        """)
        return _dictfetchall(cur)


def get_heatmap_mensal():
    """Retorna (mes_num, ano, total) para heatmap de sazonalidade."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                CAST(strftime('%m', data_saida) AS INTEGER) AS mes_num,
                CAST(strftime('%Y', data_saida) AS INTEGER) AS ano,
                COUNT(*) AS total
            FROM core_emprestimo
            GROUP BY ano, mes_num
            ORDER BY ano, mes_num
        """)
        return _dictfetchall(cur)


def get_status_gauge():
    """Retorna proporções do status de empréstimos como fracções 0-1."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status='EMPRESTADO' THEN 1 ELSE 0 END) AS ativos,
                SUM(CASE WHEN status='DEVOLVIDO'  THEN 1 ELSE 0 END) AS devolvidos,
                SUM(CASE WHEN status='ATRASADO'   THEN 1 ELSE 0 END) AS atrasados
            FROM vw_analytics_emprestimos_obt
        """)
        row = _dictfetchone(cur)
        total = row.get('total') or 1
        return {
            'total': total,
            'ativos': row.get('ativos', 0),
            'devolvidos': row.get('devolvidos', 0),
            'atrasados': row.get('atrasados', 0),
            'pct_atrasados': round((row.get('atrasados', 0) or 0) / total * 100, 1),
            'pct_devolvidos': round((row.get('devolvidos', 0) or 0) / total * 100, 1),
        }


def get_top_obras_d3(limit=8):
    """Top obras em formato pronto para horizontal bar D3."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT titulo, autor, tipo_obra, COUNT(*) AS total
            FROM vw_analytics_emprestimos_obt
            GROUP BY livro_id, titulo, autor, tipo_obra
            ORDER BY total DESC
            LIMIT %s
        """, [limit])
        return _dictfetchall(cur)


def get_perfil_leitores():
    """Distribuição de leitores por faixas de engajamento."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT
                CASE
                    WHEN total_emprestimos = 1 THEN 'Ocasional (1)'
                    WHEN total_emprestimos BETWEEN 2 AND 5 THEN 'Regular (2-5)'
                    WHEN total_emprestimos BETWEEN 6 AND 10 THEN 'Ativo (6-10)'
                    ELSE 'Super-leitor (10+)'
                END AS perfil,
                COUNT(*) AS qtd_leitores
            FROM vw_analytics_leitores_resumo
            GROUP BY perfil
            ORDER BY qtd_leitores DESC
        """)
        return _dictfetchall(cur)
