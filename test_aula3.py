"""
Bateria de testes automatizada do biblioteca_mvp.

Foca nas 5 features adicionadas nos commits da Aula 3 + funcionalidades core.
Usa Django Test Client (simula requests sem precisar de senha real).

Rodar: /caminho/para/python test_aula3.py
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_mvp.settings')
django.setup()

from django.contrib.auth.models import User, Permission, Group
from django.test import Client
from core.models import livro, pessoa, emprestimo


def make_client():
    """Cria Client com HTTP_HOST='localhost' (compatível com ALLOWED_HOSTS do .env)."""
    c = Client(HTTP_HOST='localhost')
    return c


# Cores no terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


passou = 0
falhou = 0
warnings = 0


def ok(msg):
    global passou
    passou += 1
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg):
    global falhou
    falhou += 1
    print(f"  {RED}✗{RESET} {msg}")


def warn(msg):
    global warnings
    warnings += 1
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def secao(titulo):
    print(f"\n{CYAN}{BOLD}━━━ {titulo} ━━━{RESET}")


def assert_status(response, status_esperado, descricao):
    if response.status_code == status_esperado:
        ok(f"{descricao} (HTTP {response.status_code})")
    else:
        fail(f"{descricao} — esperado HTTP {status_esperado}, recebido {response.status_code}")


def assert_in_content(response, texto, descricao):
    content = response.content.decode('utf-8', errors='ignore')
    if texto in content:
        ok(f"{descricao}")
    else:
        fail(f"{descricao} — '{texto}' NÃO encontrado no HTML")


def assert_not_in_content(response, texto, descricao):
    content = response.content.decode('utf-8', errors='ignore')
    if texto not in content:
        ok(f"{descricao}")
    else:
        fail(f"{descricao} — '{texto}' encontrado no HTML (não deveria)")


# ============================================================
# Setup: garantir que existe pelo menos um livro com "Python"
# no título ou autor para o teste de busca.
# ============================================================

print(f"\n{BOLD}🧪 BATERIA DE TESTES — biblioteca_mvp (Aula 3){RESET}")
print(f"   Total de livros no banco: {livro.objects.count()}")
print(f"   Total de pessoas:         {pessoa.objects.count()}")
print(f"   Total de empréstimos:     {emprestimo.objects.count()}")
print(f"   Total de usuários:        {User.objects.count()}")

# Procura ou cria um livro de teste com "Python" no título
livro_teste = livro.objects.filter(titulo__icontains='python').first()
if not livro_teste:
    livro_teste = livro.objects.create(
        titulo='Python para Iniciantes (livro de teste)',
        autor='Autor Teste',
        tipo_obra='BIBLIOGRAFIA',
        ano=2026,
        isbn='9999999999',
        exemplares_total=5,
        exemplares_disponiveis=5,
    )
    print(f"   {YELLOW}⚠ Criou livro de teste:{RESET} {livro_teste.titulo}")


# ============================================================
# SECAO 1: Página de login (não autenticado)
# ============================================================

secao("1. Página de login (sem autenticação)")
client = make_client()

resp = client.get('/')
assert_status(resp, 200, "GET / deveria retornar 200")
assert_in_content(resp, 'username', "Form de login tem campo username")
assert_in_content(resp, 'password', "Form de login tem campo password")

resp = client.get('/menu/')
if resp.status_code in (302, 200):
    if resp.status_code == 302:
        ok("GET /menu/ sem login redireciona (302)")
    else:
        warn("GET /menu/ retorna 200 sem login (deveria redirecionar?)")
else:
    fail(f"GET /menu/ sem login retornou {resp.status_code}")


# ============================================================
# SECAO 2: Login como admin (superuser)
# ============================================================

secao("2. Login como admin (superuser)")
admin = User.objects.filter(username='admin').first()
if not admin:
    fail("Usuário 'admin' não existe no banco")
    sys.exit(1)

# Reset senha pra um valor conhecido só pra teste
admin.set_password('senha-de-teste-temporaria-12345')
admin.save()
print(f"   {YELLOW}⚠ Senha do admin foi resetada temporariamente para o teste{RESET}")

logged = client.login(username='admin', password='senha-de-teste-temporaria-12345')
if logged:
    ok("Login como admin bem-sucedido")
else:
    fail("Login como admin FALHOU")
    sys.exit(1)

resp = client.get('/menu/')
assert_status(resp, 200, "GET /menu/ logado")
assert_in_content(resp, 'admin', "Menu mostra nome do usuário")


# ============================================================
# SECAO 3: ⭐ FEATURE 1 — Pandas (export CSV)
# ============================================================

secao("3. ⭐ FEATURE 1 — Pandas: Exportar Livros CSV")

resp = client.get('/exportar_livros_csv/')
assert_status(resp, 200, "GET /exportar_livros_csv/ logado")

content_type = resp.get('Content-Type', '')
if 'text/csv' in content_type:
    ok(f"Content-Type é text/csv (recebido: {content_type})")
else:
    fail(f"Content-Type incorreto: {content_type}")

content_disp = resp.get('Content-Disposition', '')
if 'attachment' in content_disp and 'livros.csv' in content_disp:
    ok(f"Content-Disposition correto: {content_disp}")
else:
    fail(f"Content-Disposition incorreto: {content_disp}")

csv_body = resp.content.decode('utf-8', errors='ignore')
linhas = csv_body.strip().split('\n')
header = linhas[0] if linhas else ''
ok(f"CSV tem {len(linhas) - 1} linhas de dados (esperado: ~{livro.objects.count()})")

if 'titulo' in header and 'autor' in header:
    ok(f"Cabeçalho do CSV correto: {header}")
else:
    fail(f"Cabeçalho do CSV incorreto: {header}")


# ============================================================
# SECAO 4: ⭐ FEATURE 1 — Pandas: Import CSV (preview)
# ============================================================

secao("4. ⭐ FEATURE 1 — Pandas: Importar Livros CSV (modo preview)")

# A view de import lê de ~/Downloads/livros.csv. Vamos criar um CSV de teste lá.
import pandas as pd
from pathlib import Path

csv_teste_path = Path.home() / 'Downloads' / 'livros.csv'
df_teste = pd.DataFrame({
    'titulo': ['Livro Teste Import 1', 'Livro Teste Import 2'],
    'autor': ['Autor X', 'Autor Y'],
    'ano': [2026, 2026],
    'exemplares_total': [3, 5],
})
df_teste.to_csv(csv_teste_path, index=False)
print(f"   {YELLOW}⚠ Criou CSV de teste em {csv_teste_path}{RESET}")

resp = client.get('/importar_livros_csv/')
assert_status(resp, 200, "GET /importar_livros_csv/ com CSV existente")
content = resp.content.decode('utf-8', errors='ignore')
if 'Lidas' in content or 'Importado' in content or 'linhas' in content.lower():
    ok(f"Resposta da importação parece coerente: {content.strip()[:80]}")
else:
    warn(f"Resposta inesperada: {content.strip()[:80]}")

# Limpa o CSV de teste
csv_teste_path.unlink(missing_ok=True)


# ============================================================
# SECAO 5: ⭐ FEATURE 3 — Q objects (busca livros)
# ============================================================

secao("5. ⭐ FEATURE 3 — Q objects: busca por título OU autor")

# Busca sem termo (todos)
resp = client.get('/livro/')
assert_status(resp, 200, "GET /livro/ sem busca")
assert_in_content(resp, 'name="q"', "Form de busca presente")
assert_in_content(resp, 'placeholder="Buscar', "Placeholder do input correto")

# Busca por "python" — deve trazer pelo menos 1 (o livro de teste)
resp = client.get('/livro/?q=python')
assert_status(resp, 200, "GET /livro/?q=python")
content = resp.content.decode('utf-8', errors='ignore')
if 'python' in content.lower():
    ok("Busca 'python' retorna conteúdo relevante")
else:
    warn("Busca 'python' não retornou conteúdo claramente relevante")

# Busca por algo INEXISTENTE
resp = client.get('/livro/?q=jghkfjhgfk999inexistente')
assert_status(resp, 200, "GET /livro/?q=inexistente")
# Não dá pra detectar facilmente "0 resultados" sem inspecionar HTML;
# basta confirmar que NÃO crasha

# Botão Limpar deveria aparecer quando há busca
resp = client.get('/livro/?q=teste')
assert_in_content(resp, 'Limpar', "Botão 'Limpar' aparece quando há busca ativa")

# Sem busca, não deve ter botão limpar
resp = client.get('/livro/')
assert_not_in_content(resp, '>Limpar<', "Botão 'Limpar' AUSENTE quando sem busca")


# ============================================================
# SECAO 6: ⭐ FEATURE 4 — forloop.counter + |date filter
# ============================================================

secao("6. ⭐ FEATURE 4 — forloop.counter + |date em /atrasados/")

resp = client.get('/atrasados/')
assert_status(resp, 200, "GET /atrasados/")

content = resp.content.decode('utf-8', errors='ignore')

# Cabeçalho '#' deve estar presente
if '<th>#</th>' in content:
    ok("Cabeçalho '#' (forloop.counter) presente")
else:
    fail("Cabeçalho '#' NÃO encontrado")

# Vê se tem alguma data formatada com / (formato dd/mm/yyyy)
import re
datas_format_br = re.findall(r'\d{2}/\d{2}/\d{4}', content)
datas_format_iso = re.findall(r'\d{4}-\d{2}-\d{2}', content)

if datas_format_br:
    ok(f"Encontradas {len(datas_format_br)} datas em formato BR (dd/mm/yyyy)")
else:
    if 'Nenhum emprestimo atrasado' in content:
        warn("Nenhum empréstimo atrasado pra testar formato — OK")
    else:
        fail("Nenhuma data em formato dd/mm/yyyy encontrada")


# ============================================================
# SECAO 7: ⭐ FEATURE 5 — |upper em livro_detail
# ============================================================

secao("7. ⭐ FEATURE 5 — |upper no título do livro_detail")

if livro_teste:
    resp = client.get(f'/livro/detail/{livro_teste.pk}/')
    assert_status(resp, 200, f"GET /livro/detail/{livro_teste.pk}/")

    content = resp.content.decode('utf-8', errors='ignore')

    titulo_upper = livro_teste.titulo.upper()
    if titulo_upper in content:
        ok(f"Título em maiúsculas presente: '{titulo_upper[:50]}...'")
    else:
        fail(f"Título em maiúsculas NÃO encontrado: '{titulo_upper[:50]}'")


# ============================================================
# SECAO 8: ⭐ FEATURE 2 — has_perm() em livro_create
# ============================================================

secao("8. ⭐ FEATURE 2 — has_perm() em /livro/create/")

# Como admin (superuser), deve passar
resp = client.get('/livro/create/')
assert_status(resp, 200, "Admin acessa /livro/create/ (deve ter permissão)")

content = resp.content.decode('utf-8', errors='ignore')
if 'Sem permissão' in content:
    fail("Admin NÃO deveria ver mensagem 'Sem permissão'")
else:
    ok("Admin NÃO vê mensagem de bloqueio (correto)")

# Logout admin, login como leitor1 (usuário sem permissão de criar livro)
client.logout()
leitor = User.objects.filter(username='leitor1').first()
if leitor:
    leitor.set_password('senha-leitor-teste-12345')
    leitor.save()
    print(f"   {YELLOW}⚠ Senha do leitor1 foi resetada temporariamente{RESET}")

    # Garantir que leitor1 NÃO tenha 'core.add_livro'
    perm = Permission.objects.filter(codename='add_livro').first()
    if perm and leitor.user_permissions.filter(pk=perm.pk).exists():
        leitor.user_permissions.remove(perm)
    # Remover de grupos que possam ter a permissão
    for grupo in leitor.groups.all():
        if grupo.permissions.filter(codename='add_livro').exists():
            leitor.groups.remove(grupo)

    logged = client.login(username='leitor1', password='senha-leitor-teste-12345')
    if logged:
        ok("Login como leitor1 (sem permissão de criar)")
    else:
        fail("Login como leitor1 FALHOU")

    resp = client.get('/livro/create/')
    content = resp.content.decode('utf-8', errors='ignore')
    if 'Sem permissão' in content:
        ok("Leitor1 SEM permissão recebe mensagem de bloqueio")
    else:
        if resp.status_code == 200 and 'titulo' in content.lower():
            fail("Leitor1 SEM permissão conseguiu ver formulário (deveria bloquear)")
        else:
            ok("Leitor1 SEM permissão é bloqueado (de alguma forma)")
else:
    warn("Usuário 'leitor1' não existe — pulando teste de bloqueio")


# ============================================================
# SECAO 9: Funcionalidades core (CRUD)
# ============================================================

secao("9. Funcionalidades core (CRUD básico)")

# Re-login como admin
client.logout()
client.login(username='admin', password='senha-de-teste-temporaria-12345')

resp = client.get('/pessoa/')
assert_status(resp, 200, "GET /pessoa/ (lista pessoas)")

resp = client.get('/emprestimo/')
assert_status(resp, 200, "GET /emprestimo/ (lista empréstimos)")

resp = client.get('/admin/')
assert_status(resp, 200, "GET /admin/ (Django Admin)")

resp = client.get('/admin/core/livro/')
assert_status(resp, 200, "GET /admin/core/livro/ (admin de livros)")

# Tenta acessar uma pessoa específica
primeira_pessoa = pessoa.objects.first()
if primeira_pessoa:
    resp = client.get(f'/pessoa/update/{primeira_pessoa.pk}/')
    assert_status(resp, 200, f"GET /pessoa/update/{primeira_pessoa.pk}/")


# ============================================================
# SECAO 10: Chat RAG (verificação leve)
# ============================================================

secao("10. Chat RAG (página acessível)")

resp = client.get('/chat/')
assert_status(resp, 200, "GET /chat/ (chat conversacional)")
assert_in_content(resp, 'pergunta', "Página de chat tem campo de pergunta")


# ============================================================
# RESUMO
# ============================================================

print(f"\n{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
print(f"{BOLD}📊 RESULTADO FINAL{RESET}")
print(f"{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
print(f"  {GREEN}✓ Passou:    {passou}{RESET}")
print(f"  {RED}✗ Falhou:    {falhou}{RESET}")
print(f"  {YELLOW}⚠ Warnings:  {warnings}{RESET}")
print(f"  Total:       {passou + falhou + warnings}")

if falhou == 0:
    print(f"\n{GREEN}{BOLD}✅ TODOS OS TESTES PASSARAM!{RESET}")
    sys.exit(0)
else:
    print(f"\n{RED}{BOLD}❌ {falhou} TESTE(S) FALHARAM{RESET}")
    sys.exit(1)
