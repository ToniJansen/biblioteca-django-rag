import numpy as np
from django.db import models

from core.models import livro


class LivroEmbedding(models.Model):
    """Representacao vetorial de um livro, usada para busca por similaridade semantica."""

    livro = models.OneToOneField(
        livro,
        on_delete=models.CASCADE,
        related_name='embedding',
        primary_key=True,
        verbose_name='Obra',
    )
    vetor = models.BinaryField(verbose_name='Vetor (float32)')
    texto_fonte = models.TextField(verbose_name='Texto usado no embedding')
    modelo_versao = models.CharField(max_length=128, verbose_name='Modelo')
    dimensao = models.PositiveIntegerField(verbose_name='Dimensao do vetor')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    @property
    def as_numpy(self) -> np.ndarray:
        return np.frombuffer(bytes(self.vetor), dtype=np.float32)

    def set_vetor(self, array: np.ndarray) -> None:
        self.vetor = array.astype(np.float32).tobytes()
        self.dimensao = array.shape[0]

    def __str__(self):
        return f'Embedding de {self.livro.titulo} ({self.dimensao}d)'

    class Meta:
        verbose_name = 'Embedding de Obra'
        verbose_name_plural = 'Embeddings'
