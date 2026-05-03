from calendar import monthrange
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.models import emprestimo


class Command(BaseCommand):
    help = (
        "Redistribui datas dos emprestimos existentes para demonstrar a "
        "circulacao ao longo do tempo no dashboard analitico."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--months',
            type=int,
            default=12,
            help='Quantidade de meses para distribuir os emprestimos devolvidos/atrasados.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria alterado sem gravar no banco.',
        )

    def handle(self, *args, **options):
        months = max(1, options['months'])
        today = date.today()
        loans = list(emprestimo.objects.select_related('livro', 'leitor').order_by('id'))

        if not loans:
            self.stdout.write(self.style.WARNING('Nenhum emprestimo encontrado.'))
            return

        def month_anchor(index):
            total_month = today.year * 12 + today.month - 1 - (months - 1 - index)
            year = total_month // 12
            month = total_month % 12 + 1
            return year, month

        def spread_date(sequence, month_index):
            year, month = month_anchor(month_index)
            last_day = monthrange(year, month)[1]
            day = min(1 + (sequence * 7) % 26, last_day)
            return date(year, month, day)

        updated = []
        status_counts = {'DEVOLVIDO': 0, 'ATRASADO': 0, 'EMPRESTADO': 0}
        historical_index = 0

        for index, loan in enumerate(loans):
            current_status = loan.status
            status_counts[current_status] = status_counts.get(current_status, 0) + 1

            if current_status == 'EMPRESTADO':
                data_saida = today - timedelta(days=index % 10)
                loan.data_saida = data_saida
                loan.data_devolucao_prevista = data_saida + timedelta(days=14)
                loan.data_devolucao_real = None
            else:
                month_index = historical_index % months
                data_saida = spread_date(historical_index, month_index)
                historical_index += 1

                if current_status == 'ATRASADO':
                    max_saida = today - timedelta(days=20)
                    if data_saida > max_saida:
                        data_saida = max_saida - timedelta(days=index % 18)
                    loan.data_saida = data_saida
                    loan.data_devolucao_prevista = data_saida + timedelta(days=14)
                    loan.data_devolucao_real = None
                else:
                    loan.data_saida = data_saida
                    loan.data_devolucao_prevista = data_saida + timedelta(days=14)
                    loan.data_devolucao_real = data_saida + timedelta(days=3 + (index % 10))

            updated.append(loan)

        self.stdout.write(
            'Emprestimos encontrados: {total} | devolvidos={devolvidos}, '
            'atrasados={atrasados}, ativos={ativos}'.format(
                total=len(loans),
                devolvidos=status_counts.get('DEVOLVIDO', 0),
                atrasados=status_counts.get('ATRASADO', 0),
                ativos=status_counts.get('EMPRESTADO', 0),
            )
        )

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry-run: nenhuma data foi gravada.'))
            return

        emprestimo.objects.bulk_update(
            updated,
            ['data_saida', 'data_devolucao_prevista', 'data_devolucao_real'],
            batch_size=500,
        )
        self.stdout.write(self.style.SUCCESS(f'Datas redistribuidas em {months} meses.'))
