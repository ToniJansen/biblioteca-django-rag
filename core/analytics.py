"""Analytics queries — read from the SQL views created in migration 0003.

Each function returns plain Python dicts/lists ready for JSON serialization
in the template (Chart.js).
"""

from django.db import connection


def _dictfetchall(cursor):
    """Return all rows from a cursor as a list of dicts."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


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


def get_leitores_resumo():
    """Tab Leitores: reader engagement summary."""
    with connection.cursor() as cur:
        cur.execute("SELECT * FROM vw_analytics_leitores_resumo ORDER BY total_emprestimos DESC")
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
