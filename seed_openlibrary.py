import os
import sys

# Ajusta o caminho para carregar o Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_mvp.settings')

import django
django.setup()

import requests
import random
from datetime import date, timedelta
from faker import Faker
from core.models import pessoa, livro, emprestimo

fake = Faker('pt_BR')

def get_openlibrary_books(limit=1000):
    url = f"https://openlibrary.org/search.json?q=programming+science+history+fiction&limit={limit}"
    print(f"Buscando {limit} livros na OpenLibrary...")
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('docs', [])
    print("Falha ao buscar livros.")
    return []

def seed():
    print("Iniciando seed avançado...")
    
    # 1. Gerar Leitores
    print("Gerando 200 leitores...")
    leitores = []
    for _ in range(200):
        nome = fake.name()
        email = fake.unique.email()
        celular = fake.msisdn()[:11]
        p = pessoa.objects.create(
            nome=nome,
            email=email,
            celular=celular,
            funcao='Leitor',
            nascimento=fake.date_of_birth(minimum_age=16, maximum_age=80),
            ativo=True
        )
        leitores.append(p)
        
    # 2. Gerar Livros
    docs = get_openlibrary_books(limit=1000)
    livros_criados = []
    
    for doc in docs:
        titulo = doc.get('title', 'Sem Título')[:200]
        autor = doc.get('author_name', ['Desconhecido'])[0][:100]
        ano = doc.get('first_publish_year', 2000)
        isbn = None
        if doc.get('isbn'):
            isbn = doc.get('isbn')[0][:20]
            
        try:
            l, created = livro.objects.get_or_create(
                isbn=isbn if isbn else f"FAKE-{random.randint(100000, 999999)}",
                defaults={
                    'titulo': titulo,
                    'autor': autor,
                    'tipo_obra': 'BIBLIOGRAFIA',
                    'ano': ano,
                    'exemplares_total': random.randint(1, 5),
                }
            )
            # Garante que exemplares estao atualizados caso ja existisse
            l.exemplares_disponiveis = l.exemplares_total
            l.save()
            livros_criados.append(l)
        except Exception as e:
            # Pula em caso de erro (ex: ISBN duplicado do faker)
            continue
            
    print(f"{len(livros_criados)} livros cadastrados/atualizados.")

    # 3. Gerar Emprestimos Retroativos
    print("Gerando 1500 empréstimos...")
    
    todos_leitores = list(pessoa.objects.filter(funcao='Leitor'))
    todos_livros = list(livro.objects.all())
    
    emprestimos_criados = 0
    hoje = date.today()
    
    for _ in range(1500):
        leitor = random.choice(todos_leitores)
        obra = random.choice(todos_livros)
        
        if obra.exemplares_disponiveis > 0:
            dias_atras = random.randint(0, 730)
            data_saida = hoje - timedelta(days=dias_atras)
            data_prevista = data_saida + timedelta(days=14)
            
            status = random.choices(['devolvido', 'atrasado', 'andamento'], weights=[0.8, 0.1, 0.1])[0]
            
            data_real = None
            if status == 'devolvido':
                dias_devolucao = random.randint(5, 20)
                data_real = data_saida + timedelta(days=dias_devolucao)
                if data_real > hoje:
                    data_real = hoje
                    
            elif status == 'atrasado':
                if data_prevista >= hoje:
                    data_saida = hoje - timedelta(days=random.randint(15, 60))
                    data_prevista = data_saida + timedelta(days=14)
            
            elif status == 'andamento':
                data_saida = hoje - timedelta(days=random.randint(0, 10))
                data_prevista = data_saida + timedelta(days=14)
                
            try:
                # Criar sem data real primeiro para descontar o estoque
                e = emprestimo(
                    livro=obra,
                    leitor=leitor,
                    data_devolucao_prevista=data_prevista
                )
                e.save()
                
                # Ajusta data saida
                emprestimo.objects.filter(pk=e.pk).update(data_saida=data_saida)
                
                # Devolve o livro se for o caso (aciona a logica do model save)
                if data_real:
                    e.data_devolucao_real = data_real
                    e.save()
                    
                emprestimos_criados += 1
            except Exception as e:
                pass

    print(f"{emprestimos_criados} empréstimos criados.")
    print("Seed avançado concluído com sucesso!")

if __name__ == '__main__':
    seed()
