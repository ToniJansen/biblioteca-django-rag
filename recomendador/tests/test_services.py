"""Testes unitarios do modulo de recomendacao.

Usa RECOMENDADOR_MOCK=True nas settings para gerar vetores deterministicos sem
baixar o modelo real. Isto permite rodar o pytest em CI sem rede e sem GPU.
"""
from datetime import date

import numpy as np
from django.test import TestCase, override_settings

from core.models import emprestimo, livro, pessoa
from recomendador.embeddings import build_text_for_embedding, gerar_embedding
from recomendador.models import LivroEmbedding
from recomendador.services import recomendar_livros, recomendar_para_leitor


@override_settings(RECOMENDADOR_MOCK=True)
class ServicesRecomendacaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.leitor = pessoa.objects.create(
            nome='Teste Leitor', email='teste@t.com', funcao='Leitor', ativo=True,
        )
        cls.livros = []
        for i, (titulo, autor, tipo) in enumerate([
            ('Introducao a Redes Neurais', 'Ian Goodfellow', 'BIBLIOGRAFIA'),
            ('Deep Learning com PyTorch', 'Eli Stevens', 'BIBLIOGRAFIA'),
            ('Banco de Dados Relacional', 'Elmasri Navathe', 'BIBLIOGRAFIA'),
            ('Teoria dos Grafos', 'Bondy Murty', 'BIBLIOGRAFIA'),
            ('Arquitetura de Software', 'Martin Fowler', 'BIBLIOGRAFIA'),
        ]):
            l = livro.objects.create(
                titulo=titulo, autor=autor, tipo_obra=tipo,
                isbn=f'978-TEST-{i:04d}',
                exemplares_total=1, exemplares_disponiveis=1,
            )
            cls.livros.append(l)
        # gera embeddings mockados
        for l in cls.livros:
            texto = build_text_for_embedding(l)
            vetor = gerar_embedding(texto)
            emb = LivroEmbedding(livro=l, texto_fonte=texto, modelo_versao='mock')
            emb.set_vetor(vetor)
            emb.save()

    def test_build_text_for_embedding_inclui_tipo_legivel(self):
        l = self.livros[0]
        texto = build_text_for_embedding(l)
        self.assertIn(l.titulo, texto)
        self.assertIn(l.autor, texto)
        self.assertIn('bibliografia', texto)

    def test_gerar_embedding_retorna_vetor_float32(self):
        vetor = gerar_embedding('texto de teste')
        self.assertEqual(vetor.dtype, np.float32)
        self.assertTrue(vetor.shape[0] > 0)

    def test_gerar_embedding_deterministico_em_mock(self):
        v1 = gerar_embedding('mesmo texto')
        v2 = gerar_embedding('mesmo texto')
        np.testing.assert_array_equal(v1, v2)

    def test_recomendar_livros_retorna_top_k(self):
        resultado = recomendar_livros(self.livros[0].pk, top_k=3)
        self.assertEqual(len(resultado), 3)

    def test_recomendar_livros_exclui_o_proprio_livro(self):
        resultado = recomendar_livros(self.livros[0].pk, top_k=5)
        ids = [l.pk for l in resultado]
        self.assertNotIn(self.livros[0].pk, ids)

    def test_recomendar_livros_retorna_ids_distintos(self):
        resultado = recomendar_livros(self.livros[0].pk, top_k=4)
        ids = [l.pk for l in resultado]
        self.assertEqual(len(ids), len(set(ids)))

    def test_recomendar_livros_vazio_quando_sem_embedding(self):
        l = livro.objects.create(
            titulo='Sem embedding', autor='X', tipo_obra='MONOGRAFIA',
            exemplares_total=1, exemplares_disponiveis=1,
        )
        LivroEmbedding.objects.filter(livro=l).delete()
        self.assertEqual(recomendar_livros(l.pk), [])

    def test_recomendar_para_leitor_usa_historico(self):
        e = emprestimo.objects.create(livro=self.livros[0], leitor=self.leitor)
        e.data_devolucao_real = date.today()
        e.save()
        resultado = recomendar_para_leitor(self.leitor.pk, top_k=3)
        self.assertEqual(len(resultado), 3)
        ids = [l.pk for l in resultado]
        self.assertNotIn(self.livros[0].pk, ids)  # exclui o que ja leu

    def test_recomendar_para_leitor_sem_historico(self):
        leitor_novo = pessoa.objects.create(
            nome='Novo', email='novo@t.com', funcao='Leitor', ativo=True,
        )
        self.assertEqual(recomendar_para_leitor(leitor_novo.pk), [])
