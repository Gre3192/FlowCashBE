from decimal import Decimal
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Category, Transaction, Budget, TransactionEntry


class Command(BaseCommand):
    help = "Popola il database con dati di test per FlowCash"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seed database started..."))

        with transaction.atomic():
            self.create_seed_data()

        self.stdout.write(self.style.SUCCESS("Seed completato con successo."))

    def create_seed_data(self):
        categories_data = [
            "Abbonamenti",
            "Casa",
            "Trasporti",
            "Stipendio",
            "Svago",
            "Spesa",
        ]

        categories = {}

        for category_name in categories_data:
            category, _ = Category.objects.get_or_create(
                name=category_name
            )
            categories[category_name] = category

        transactions_data = [
            {
                "name": "Amazon Prime",
                "type": "Expense",
                "category": categories["Abbonamenti"],
                "budget": {
                    2026: [4.99] * 12,
                    2027: [4.99] * 12,
                },
                "entries": [
                    {
                        "amount": "4.99",
                        "entry_date": date(2026, 1, 5),
                        "note": "Pagamento Amazon Prime gennaio",
                    },
                    {
                        "amount": "4.99",
                        "entry_date": date(2026, 2, 5),
                        "note": "Pagamento Amazon Prime febbraio",
                    },
                ],
            },
            {
                "name": "Netflix",
                "type": "Expense",
                "category": categories["Abbonamenti"],
                "budget": {
                    2026: [12.99] * 12,
                },
                "entries": [
                    {
                        "amount": "12.99",
                        "entry_date": date(2026, 1, 10),
                        "note": "Abbonamento Netflix",
                    }
                ],
            },
            {
                "name": "Affitto",
                "type": "Expense",
                "category": categories["Casa"],
                "budget": {
                    2026: [650.00] * 12,
                },
                "entries": [
                    {
                        "amount": "650.00",
                        "entry_date": date(2026, 1, 1),
                        "note": "Affitto gennaio",
                    }
                ],
            },
            {
                "name": "Benzina",
                "type": "Expense",
                "category": categories["Trasporti"],
                "budget": {
                    2026: [120.00] * 12,
                },
                "entries": [
                    {
                        "amount": "55.00",
                        "entry_date": date(2026, 1, 8),
                        "note": "Rifornimento",
                    },
                    {
                        "amount": "62.50",
                        "entry_date": date(2026, 1, 22),
                        "note": "Rifornimento",
                    },
                ],
            },
            {
                "name": "Stipendio",
                "type": "Income",
                "category": categories["Stipendio"],
                "budget": {
                    2026: [1800.00] * 12,
                },
                "entries": [
                    {
                        "amount": "1800.00",
                        "entry_date": date(2026, 1, 27),
                        "note": "Stipendio gennaio",
                    }
                ],
            },
        ]

        month_fields = [
            "gen_val",
            "feb_val",
            "mar_val",
            "apr_val",
            "mag_val",
            "giu_val",
            "lug_val",
            "ago_val",
            "set_val",
            "ott_val",
            "nov_val",
            "dic_val",
        ]

        for item in transactions_data:
            transaction_obj, _ = Transaction.objects.get_or_create(
                name=item["name"],
                type=item["type"],
                category=item["category"],
            )

            for year, values in item["budget"].items():
                budget_values = {
                    month_fields[index]: Decimal(str(value))
                    for index, value in enumerate(values)
                }

                Budget.objects.update_or_create(
                    transaction=transaction_obj,
                    year=year,
                    defaults=budget_values,
                )

            for entry in item["entries"]:
                TransactionEntry.objects.get_or_create(
                    transaction=transaction_obj,
                    amount=Decimal(entry["amount"]),
                    entry_date=entry["entry_date"],
                    note=entry["note"],
                )