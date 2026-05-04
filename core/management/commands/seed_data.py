from decimal import Decimal
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from core.models import (
    Category,
    Transaction,
    TransactionBudget,
    TransactionMovement,
)


class Command(BaseCommand):
    help = "Popola il database con dati di test per FlowCash"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seed database started..."))

        with db_transaction.atomic():
            self.create_seed_data()

        self.stdout.write(self.style.SUCCESS("Seed completato con successo."))

    def create_seed_data(self):
        TransactionMovement.objects.all().delete()
        TransactionBudget.objects.all().delete()
        Transaction.objects.all().delete()
        Category.objects.all().delete()

        categories = {}

        for category_name in [
            "Abbonamenti",
            "Casa",
            "Trasporti",
            "Stipendio",
            "Svago",
            "Spesa",
        ]:
            category = Category.objects.create(name=category_name)
            categories[category_name] = category

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

        seed_items = [
            {
                "name": "Amazon Prime",
                "type": "Expense",
                "category": "Abbonamenti",
                "budget": {
                    2026: [4.99] * 12,
                },
                "movements": [
                    {
                        "name": "Pagamento Amazon Prime",
                        "amount": "4.99",
                        "movement_date": date(2026, 1, 5),
                        "note": "Pagamento mensile",
                    },
                    {
                        "name": "Pagamento Amazon Prime",
                        "amount": "4.99",
                        "movement_date": date(2026, 2, 5),
                        "note": "Pagamento mensile",
                    },
                ],
            },
            {
                "name": "Netflix",
                "type": "Expense",
                "category": "Abbonamenti",
                "budget": {
                    2026: [12.99] * 12,
                },
                "movements": [
                    {
                        "name": "Netflix gennaio",
                        "amount": "12.99",
                        "movement_date": date(2026, 1, 10),
                        "note": "",
                    }
                ],
            },
            {
                "name": "Affitto",
                "type": "Expense",
                "category": "Casa",
                "budget": {
                    2026: [650.00] * 12,
                },
                "movements": [
                    {
                        "name": "Affitto gennaio",
                        "amount": "650.00",
                        "movement_date": date(2026, 1, 1),
                        "note": "",
                    }
                ],
            },
            {
                "name": "Benzina",
                "type": "Expense",
                "category": "Trasporti",
                "budget": {
                    2026: [120.00] * 12,
                },
                "movements": [
                    {
                        "name": "Rifornimento",
                        "amount": "55.00",
                        "movement_date": date(2026, 1, 8),
                        "note": "",
                    },
                    {
                        "name": "Rifornimento",
                        "amount": "62.50",
                        "movement_date": date(2026, 1, 22),
                        "note": "",
                    },
                ],
            },
            {
                "name": "Stipendio",
                "type": "Income",
                "category": "Stipendio",
                "budget": {
                    2026: [1800.00] * 12,
                },
                "movements": [
                    {
                        "name": "Stipendio gennaio",
                        "amount": "1800.00",
                        "movement_date": date(2026, 1, 27),
                        "note": "",
                    }
                ],
            },
            {
                "name": "Svago",
                "type": "Expense",
                "category": "Svago",
                "budget": {
                    2026: [100.00] * 12,
                },
                "movements": [
                    {
                        "name": "Sigarette",
                        "amount": "6.00",
                        "movement_date": date(2026, 4, 5),
                        "note": "",
                    },
                    {
                        "name": "Panino",
                        "amount": "8.00",
                        "movement_date": date(2026, 4, 5),
                        "note": "",
                    },
                    {
                        "name": "Barbiere",
                        "amount": "26.00",
                        "movement_date": date(2026, 4, 5),
                        "note": "",
                    },
                    {
                        "name": "Cinema",
                        "amount": "15.00",
                        "movement_date": date(2026, 4, 12),
                        "note": "",
                    },
                ],
            },
        ]

        for item in seed_items:
            transaction_obj = Transaction.objects.create(
                name=item["name"],
                type=item["type"],
                category=categories[item["category"]],
            )

            for year, values in item["budget"].items():
                budget_values = {
                    month_fields[index]: Decimal(str(value))
                    for index, value in enumerate(values)
                }

                TransactionBudget.objects.create(
                    transaction=transaction_obj,
                    year=year,
                    **budget_values,
                )

            for movement in item["movements"]:
                TransactionMovement.objects.create(
                    transaction=transaction_obj,
                    name=movement["name"],
                    amount=Decimal(str(movement["amount"])),
                    movement_date=movement["movement_date"],
                    note=movement.get("note"),
                )