"""
Seed de dados do Biblioteca MVP. Execute com:
    python manage.py shell < seed.py

Cria/atualiza: superusuario admin/admin123, grupos (Visualizador, Editor),
usuarios de teste (biblio1, leitor1), 4 pessoas, ~30 obras (22 bibliografias,
5 teses/dissertacoes, 3 monografias) e 3 emprestimos (1 ativo, 1 devolvido,
1 atrasado).

As 30 obras foram escolhidas para dar massa suficiente ao modulo de
recomendacao semantica (acervo minimo para validar top-5).
"""
import django
django.setup()

from datetime import date, timedelta
from django.contrib.auth.models import Group, Permission, User
from core.models import pessoa, livro, emprestimo


if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    print('superuser admin/admin123 criado')

perms_view = Permission.objects.filter(codename__startswith='view_', content_type__app_label='core')
perms_edit = Permission.objects.filter(content_type__app_label='core').exclude(codename__startswith='delete_')

grupo_vis, _ = Group.objects.get_or_create(name='Visualizador')
grupo_vis.permissions.set(perms_view)

grupo_edit, _ = Group.objects.get_or_create(name='Editor')
grupo_edit.permissions.set(perms_edit)
print('grupos Visualizador/Editor configurados')

if not User.objects.filter(username='biblio1').exists():
    u = User.objects.create_user('biblio1', 'biblio@test.com', 'biblio123', first_name='Ana', last_name='Biblioteca')
    u.groups.add(grupo_edit)

if not User.objects.filter(username='leitor1').exists():
    u = User.objects.create_user('leitor1', 'leitor@test.com', 'leitor123', first_name='Bruno', last_name='Leitor')
    u.groups.add(grupo_vis)

if not pessoa.objects.exists():
    pessoa.objects.create(nome='Ana Biblioteca', email='ana@biblio.com', funcao='Bibliotecario', celular='62999990001')
    pessoa.objects.create(nome='Bruno Leitor', email='bruno@test.com', funcao='Leitor', celular='62999990002')
    pessoa.objects.create(nome='Carla Silva', email='carla@test.com', funcao='Leitor', celular='62999990003')
    pessoa.objects.create(nome='Diego Santos', email='diego@test.com', funcao='Leitor', celular='62999990004')
    print(f'pessoas criadas: {pessoa.objects.count()}')


# ---------------------------------------------------------------------------
# BIBLIOGRAFIAS (22 obras — acervo didatico de CS/engenharia/gestao/humanidades)
# ---------------------------------------------------------------------------
bibliografias = [
    # Programacao e engenharia de software
    dict(titulo='Django for Beginners', autor='William S. Vincent', isbn='9781735467207', ano=2022, exemplares_total=3),
    dict(titulo='Two Scoops of Django', autor='Audrey & Daniel Roy Greenfeld', isbn='9780692915721', ano=2021, exemplares_total=2),
    dict(titulo='Python Fluente', autor='Luciano Ramalho', isbn='9788575227534', ano=2023, exemplares_total=4),
    dict(titulo='Clean Code', autor='Robert C. Martin', isbn='9780132350884', ano=2008, exemplares_total=2),
    dict(titulo='The Pragmatic Programmer', autor='Hunt & Thomas', isbn='9780135957059', ano=2019, exemplares_total=1),
    dict(titulo='Design Patterns', autor='Gamma Helm Johnson Vlissides', isbn='9780201633610', ano=1994, exemplares_total=2),
    dict(titulo='Refactoring', autor='Martin Fowler', isbn='9780134757599', ano=2018, exemplares_total=1),
    # Banco de dados
    dict(titulo='Sistemas de Banco de Dados', autor='Elmasri Navathe', isbn='9788579362859', ano=2011, exemplares_total=3),
    dict(titulo='SQL Fundamentos', autor='Jennifer Widom', isbn='9781234567890', ano=2020, exemplares_total=2),
    # IA / ML
    dict(titulo='Deep Learning', autor='Ian Goodfellow Yoshua Bengio', isbn='9780262035613', ano=2016, exemplares_total=2),
    dict(titulo='Hands-On Machine Learning', autor='Aurelien Geron', isbn='9781492032649', ano=2019, exemplares_total=3),
    dict(titulo='Inteligencia Artificial: Uma Abordagem Moderna', autor='Russell Norvig', isbn='9788535237016', ano=2013, exemplares_total=1),
    dict(titulo='Pattern Recognition and Machine Learning', autor='Christopher Bishop', isbn='9780387310732', ano=2006, exemplares_total=1),
    # Algoritmos e matematica
    dict(titulo='Algoritmos: Teoria e Pratica', autor='Cormen Leiserson Rivest Stein', isbn='9788535236996', ano=2012, exemplares_total=2),
    dict(titulo='Teoria dos Grafos', autor='Bondy Murty', isbn='9781846289699', ano=2008, exemplares_total=1),
    # Redes e sistemas
    dict(titulo='Redes de Computadores', autor='Andrew S. Tanenbaum', isbn='9788576059240', ano=2011, exemplares_total=2),
    dict(titulo='Sistemas Operacionais Modernos', autor='Andrew S. Tanenbaum', isbn='9788543005676', ano=2016, exemplares_total=1),
    # Metodologia cientifica e gestao
    dict(titulo='Metodologia Cientifica', autor='Antonio Carlos Gil', isbn='9788522449972', ano=2008, exemplares_total=3),
    dict(titulo='Como Elaborar Projetos de Pesquisa', autor='Antonio Carlos Gil', isbn='9788522478651', ano=2017, exemplares_total=2),
    dict(titulo='Administracao da Producao', autor='Nigel Slack', isbn='9788522464722', ano=2009, exemplares_total=1),
    # Humanidades
    dict(titulo='Etica a Nicomaco', autor='Aristoteles', isbn='9788580631777', ano=2014, exemplares_total=1),
    dict(titulo='Casa Grande e Senzala', autor='Gilberto Freyre', isbn='9788525421302', ano=2006, exemplares_total=1),
]

for b in bibliografias:
    livro.objects.get_or_create(
        isbn=b['isbn'],
        defaults={**b, 'tipo_obra': 'BIBLIOGRAFIA', 'exemplares_disponiveis': b['exemplares_total']},
    )


# ---------------------------------------------------------------------------
# TESES E DISSERTACOES (5 obras)
# ---------------------------------------------------------------------------
teses = [
    dict(titulo='Deep Learning aplicado a deteccao de fraudes bancarias',
         autor='Eduardo Silva Monteiro', ano=2024),
    dict(titulo='Redes neurais convolucionais para diagnostico de imagens medicas',
         autor='Patricia Lopes de Araujo', ano=2023),
    dict(titulo='Analise preditiva de evasao escolar usando aprendizado supervisionado',
         autor='Fernando Nogueira Carvalho', ano=2025),
    dict(titulo='Processamento de linguagem natural em portugues brasileiro: estudo de caso em transformers',
         autor='Mariana Rocha de Almeida', ano=2024),
    dict(titulo='Otimizacao de consultas SQL distribuidas em clusters NoSQL',
         autor='Ricardo Teixeira Pereira', ano=2022),
]
for t in teses:
    # sem ISBN; usa titulo como identificador unico via get_or_create com titulo
    if not livro.objects.filter(titulo=t['titulo']).exists():
        livro.objects.create(**t, tipo_obra='TESE_DISSERTACAO', exemplares_total=1, exemplares_disponiveis=1)


# ---------------------------------------------------------------------------
# MONOGRAFIAS (3 obras)
# ---------------------------------------------------------------------------
monografias = [
    dict(titulo='Sistema web em Django para gestao academica', autor='Aluno Exemplo da Silva', ano=2025),
    dict(titulo='Aplicacao mobile de controle financeiro pessoal em Flutter', autor='Juliana Campos Ferreira', ano=2024),
    dict(titulo='Algoritmo de recomendacao de filmes baseado em conteudo', autor='Pedro Henrique Souza', ano=2023),
]
for m in monografias:
    if not livro.objects.filter(titulo=m['titulo']).exists():
        livro.objects.create(**m, tipo_obra='MONOGRAFIA', exemplares_total=1, exemplares_disponiveis=1)


print(f'obras totais: {livro.objects.count()}')
print(f'  - Bibliografias: {livro.objects.filter(tipo_obra="BIBLIOGRAFIA").count()}')
print(f'  - Teses/Dissertacoes: {livro.objects.filter(tipo_obra="TESE_DISSERTACAO").count()}')
print(f'  - Monografias: {livro.objects.filter(tipo_obra="MONOGRAFIA").count()}')


# ---------------------------------------------------------------------------
# EMPRESTIMOS
# ---------------------------------------------------------------------------
if not emprestimo.objects.exists():
    leitor_b = pessoa.objects.get(email='bruno@test.com')
    leitor_c = pessoa.objects.get(email='carla@test.com')
    leitor_d = pessoa.objects.get(email='diego@test.com')
    livro_dj = livro.objects.get(isbn='9781735467207')
    livro_py = livro.objects.get(isbn='9788575227534')
    livro_cc = livro.objects.get(isbn='9780132350884')

    e1 = emprestimo.objects.create(livro=livro_dj, leitor=leitor_b)
    print(f'emprestimo ativo: {e1}')

    e2 = emprestimo.objects.create(livro=livro_py, leitor=leitor_c)
    e2.data_devolucao_real = date.today()
    e2.save()
    print(f'emprestimo devolvido: {e2}')

    e3 = emprestimo.objects.create(livro=livro_cc, leitor=leitor_d)
    e3.data_saida = date.today() - timedelta(days=30)
    e3.data_devolucao_prevista = date.today() - timedelta(days=16)
    e3.save()
    print(f'emprestimo atrasado: {e3}')

print('seed concluido')
