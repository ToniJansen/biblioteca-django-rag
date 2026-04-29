"""Create the 5 analytics SQL views (read-only layer over transactional models).

These are SQLite views — no physical tables are created.
"""

from django.db import migrations


SQL_CREATE = """
-- ============================================================
-- 1. OBT (One Big Table) — grain: 1 row per emprestimo
-- ============================================================
CREATE VIEW IF NOT EXISTS vw_analytics_emprestimos_obt AS
SELECT
    e.id                        AS emprestimo_id,
    e.data_saida,
    e.data_devolucao_prevista,
    e.data_devolucao_real,
    strftime('%%Y-%%m', e.data_saida) AS ano_mes_saida,
    CASE
        WHEN e.data_devolucao_real IS NOT NULL            THEN 'DEVOLVIDO'
        WHEN e.data_devolucao_prevista < date('now')      THEN 'ATRASADO'
        ELSE 'EMPRESTADO'
    END                         AS status,
    CASE
        WHEN e.data_devolucao_real IS NULL
         AND e.data_devolucao_prevista < date('now')
        THEN CAST(julianday('now') - julianday(e.data_devolucao_prevista) AS INTEGER)
        ELSE 0
    END                         AS dias_atraso,
    l.id                        AS livro_id,
    l.titulo,
    l.autor,
    l.tipo_obra,
    l.isbn,
    l.ano,
    l.exemplares_total,
    l.exemplares_disponiveis,
    p.id                        AS leitor_id,
    p.nome                      AS leitor_nome,
    p.email                     AS leitor_email,
    p.funcao                    AS leitor_funcao,
    p.ativo                     AS leitor_ativo
FROM core_emprestimo e
JOIN core_livro   l ON l.id = e.livro_id
JOIN core_pessoa  p ON p.id = e.leitor_id;

-- ============================================================
-- 2. Acervo por tipo
-- ============================================================
CREATE VIEW IF NOT EXISTS vw_analytics_acervo_por_tipo AS
SELECT
    l.tipo_obra,
    COUNT(*)                                                        AS total_obras,
    SUM(l.exemplares_total)                                         AS exemplares_total,
    SUM(l.exemplares_disponiveis)                                   AS exemplares_disponiveis,
    SUM(l.exemplares_total) - SUM(l.exemplares_disponiveis)         AS exemplares_emprestados,
    SUM(CASE WHEN l.exemplares_disponiveis = 0 THEN 1 ELSE 0 END)  AS obras_esgotadas
FROM core_livro l
GROUP BY l.tipo_obra;

-- ============================================================
-- 3. Circulacao mensal
-- ============================================================
CREATE VIEW IF NOT EXISTS vw_analytics_circulacao_mensal AS
SELECT
    ano_mes_saida,
    tipo_obra,
    status,
    COUNT(*) AS total_emprestimos
FROM vw_analytics_emprestimos_obt
GROUP BY ano_mes_saida, tipo_obra, status;

-- ============================================================
-- 4. Resumo de leitores
-- ============================================================
CREATE VIEW IF NOT EXISTS vw_analytics_leitores_resumo AS
SELECT
    leitor_id,
    leitor_nome,
    leitor_email,
    leitor_ativo,
    COUNT(*)                                                      AS total_emprestimos,
    SUM(CASE WHEN status = 'EMPRESTADO' THEN 1 ELSE 0 END)       AS emprestimos_ativos,
    SUM(CASE WHEN status = 'ATRASADO'   THEN 1 ELSE 0 END)       AS emprestimos_atrasados,
    SUM(CASE WHEN status = 'DEVOLVIDO'  THEN 1 ELSE 0 END)       AS emprestimos_devolvidos,
    ROUND(
        CAST(SUM(CASE WHEN status = 'ATRASADO' THEN 1 ELSE 0 END) AS REAL)
        / NULLIF(COUNT(*), 0) * 100, 1
    )                                                             AS pct_atraso,
    MAX(dias_atraso)                                              AS max_dias_atraso
FROM vw_analytics_emprestimos_obt
GROUP BY leitor_id, leitor_nome, leitor_email, leitor_ativo;

-- ============================================================
-- 5. Cobertura de IA (embeddings)
-- ============================================================
CREATE VIEW IF NOT EXISTS vw_analytics_ia_cobertura AS
SELECT
    l.id           AS livro_id,
    l.titulo,
    l.autor,
    l.tipo_obra,
    CASE
        WHEN le.livro_id IS NOT NULL THEN 1
        ELSE 0
    END            AS tem_embedding,
    le.modelo_versao,
    le.dimensao,
    le.atualizado_em
FROM core_livro l
LEFT JOIN recomendador_livroembedding le ON le.livro_id = l.id;
"""

SQL_DROP = """
DROP VIEW IF EXISTS vw_analytics_ia_cobertura;
DROP VIEW IF EXISTS vw_analytics_leitores_resumo;
DROP VIEW IF EXISTS vw_analytics_circulacao_mensal;
DROP VIEW IF EXISTS vw_analytics_acervo_por_tipo;
DROP VIEW IF EXISTS vw_analytics_emprestimos_obt;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_livro_options_livro_ano_livro_tipo_obra_and_more'),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_CREATE, reverse_sql=SQL_DROP),
    ]
