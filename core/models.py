from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import models, transaction


FUNCAO_CHOICES = [
    ('Leitor', 'Leitor'),
    ('Bibliotecario', 'Bibliotecario'),
]


class pessoa(models.Model):
    nome = models.CharField(max_length=50, verbose_name='Nome')
    email = models.CharField(max_length=50, verbose_name='eMail')
    celular = models.CharField(max_length=20, null=True, blank=True, verbose_name='Celular')
    funcao = models.CharField(max_length=30, choices=FUNCAO_CHOICES, verbose_name='Funcao')
    nascimento = models.DateField(null=True, blank=True, verbose_name='Nascimento')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    def __str__(self):
        return f'{self.nome} ({self.funcao})'

    class Meta:
        ordering = ['nome']
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'


TIPO_OBRA_CHOICES = [
    ('BIBLIOGRAFIA', 'Bibliografia'),
    ('TESE_DISSERTACAO', 'Tese/Dissertacao'),
    ('MONOGRAFIA', 'Monografia'),
]


class livro(models.Model):
    titulo = models.CharField(max_length=200, verbose_name='Titulo')
    autor = models.CharField(max_length=100, verbose_name='Autor')
    tipo_obra = models.CharField(
        max_length=20,
        choices=TIPO_OBRA_CHOICES,
        default='BIBLIOGRAFIA',
        verbose_name='Tipo de Obra',
    )
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='ISBN')
    ano = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ano')
    exemplares_total = models.PositiveIntegerField(default=1, verbose_name='Total')
    exemplares_disponiveis = models.PositiveIntegerField(default=1, verbose_name='Disponiveis')

    def clean(self):
        super().clean()
        if self.exemplares_disponiveis > self.exemplares_total:
            raise ValidationError('Exemplares disponiveis nao pode ser maior que total.')
        if self.tipo_obra == 'BIBLIOGRAFIA' and not self.isbn:
            raise ValidationError('ISBN e obrigatorio para Bibliografia.')

    def __str__(self):
        return f'{self.titulo} - {self.autor}'

    class Meta:
        ordering = ['titulo']
        verbose_name = 'Obra'
        verbose_name_plural = 'Obras'


PRAZO_EMPRESTIMO_DIAS = 14


class emprestimo(models.Model):
    livro = models.ForeignKey(
        livro,
        on_delete=models.PROTECT,
        related_name='emprestimos',
        verbose_name='Obra',
    )
    leitor = models.ForeignKey(
        pessoa,
        on_delete=models.PROTECT,
        related_name='emprestimos',
        limit_choices_to={'funcao': 'Leitor'},
        verbose_name='Leitor',
    )
    data_saida = models.DateField(auto_now_add=True, verbose_name='Saida')
    data_devolucao_prevista = models.DateField(null=True, blank=True, verbose_name='Devolucao prevista')
    data_devolucao_real = models.DateField(null=True, blank=True, verbose_name='Devolucao real')

    def save(self, *args, **kwargs):
        """Cria/atualiza o emprestimo de forma atomica.

        A transacao garante que o decremento (ou incremento) do estoque do livro
        e o save do proprio emprestimo aconteçam como uma unica operacao. Se
        qualquer etapa falhar, nenhuma alteracao persiste e o contador de
        exemplares disponiveis mantem-se consistente.
        """
        eh_novo = self.pk is None

        with transaction.atomic():
            if eh_novo:
                if self.livro.exemplares_disponiveis <= 0:
                    raise ValidationError(f'Obra "{self.livro.titulo}" nao tem exemplares disponiveis.')
                if not self.leitor.ativo:
                    raise ValidationError(f'Leitor "{self.leitor.nome}" esta inativo.')
                self.livro.exemplares_disponiveis -= 1
                self.livro.save()
                if not self.data_devolucao_prevista:
                    self.data_devolucao_prevista = date.today() + timedelta(days=PRAZO_EMPRESTIMO_DIAS)
            else:
                anterior = emprestimo.objects.get(pk=self.pk)
                acabou_de_devolver = anterior.data_devolucao_real is None and self.data_devolucao_real is not None
                if acabou_de_devolver:
                    self.livro.exemplares_disponiveis += 1
                    self.livro.save()

            super().save(*args, **kwargs)

    @property
    def status(self):
        if self.data_devolucao_real is not None:
            return 'DEVOLVIDO'
        if self.data_devolucao_prevista and self.data_devolucao_prevista < date.today():
            return 'ATRASADO'
        return 'EMPRESTADO'

    @property
    def atrasado(self):
        return self.status == 'ATRASADO'

    def __str__(self):
        return f'{self.livro.titulo} -> {self.leitor.nome}'

    class Meta:
        ordering = ['-data_saida']
        verbose_name = 'Emprestimo'
        verbose_name_plural = 'Emprestimos'
