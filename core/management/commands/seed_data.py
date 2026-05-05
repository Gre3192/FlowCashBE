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
                "note": "Abbonamento ricorrente per servizi Amazon e Prime Video.",
                "budget": {
                    2026: [4.99] * 12,
                },
                "movements": [
                    {
                        "name": "Pagamento Amazon Prime",
                        "amount": "4.99",
                        "movement_date": date(2026, 1, 5),
                        "note": "Addebito automatico mensile di gennaio.",
                    },
                    {
                        "name": "Pagamento Amazon Prime",
                        "amount": "4.99",
                        "movement_date": date(2026, 2, 5),
                        "note": "Addebito automatico mensile di febbraio.",
                    },
                    {
                        "name": "Pagamento Amazon Prime",
                        "amount": "4.99",
                        "movement_date": date(2026, 4, 5),
                        "note": "Addebito automatico mensile di aprile.",
                    },
                ],
            },
            {
                "name": "Netflix",
                "type": "Expense",
                "category": "Abbonamenti",
                "note": "Abbonamento streaming mensile.",
                "budget": {
                    2026: [12.99] * 12,
                },
                "movements": [
                    {
                        "name": "Netflix gennaio",
                        "amount": "12.99",
                        "movement_date": date(2026, 1, 10),
                        "note": "Pagamento abbonamento Netflix di gennaio.",
                    },
                    {
                        "name": "Netflix aprile",
                        "amount": "12.99",
                        "movement_date": date(2026, 4, 10),
                        "note": "Pagamento abbonamento Netflix di aprile.",
                    },
                ],
            },
            {
                "name": "Affitto",
                "type": "Expense",
                "category": "Casa",
                "note": "Canone mensile dell’abitazione.",
                "budget": {
                    2026: [650.00] * 12,
                },
                "movements": [
                    {
                        "name": "Affitto gennaio",
                        "amount": "650.00",
                        "movement_date": date(2026, 1, 1),
                        "note": "Pagamento affitto relativo al mese di gennaio.",
                    },
                    {
                        "name": "Affitto aprile",
                        "amount": "650.00",
                        "movement_date": date(2026, 4, 1),
                        "note": "Pagamento affitto relativo al mese di aprile.",
                    },
                ],
            },
            {
                "name": "Benzina",
                "type": "Expense",
                "category": "Trasporti",
                "note": "Spese carburante e rifornimenti auto.",
                "budget": {
                    2026: [120.00] * 12,
                },
                "movements": [
                    {
                        "name": "Rifornimento",
                        "amount": "55.00",
                        "movement_date": date(2026, 1, 8),
                        "note": "Rifornimento carburante inizio gennaio.",
                    },
                    {
                        "name": "Rifornimento",
                        "amount": "62.50",
                        "movement_date": date(2026, 1, 22),
                        "note": "Secondo rifornimento del mese.",
                    },
                    {
                        "name": "Rifornimento",
                        "amount": "48.00",
                        "movement_date": date(2026, 4, 6),
                        "note": "Rifornimento carburante prima settimana di aprile.",
                    },
                    {
                        "name": "Parcheggio",
                        "amount": "8.00",
                        "movement_date": date(2026, 4, 13),
                        "note": "Parcheggio in centro.",
                    },
                ],
            },
            {
                "name": "Stipendio",
                "type": "Income",
                "category": "Stipendio",
                "note": "Entrata mensile principale da lavoro.",
                "budget": {
                    2026: [1800.00] * 12,
                },
                "movements": [
                    {
                        "name": "Stipendio gennaio",
                        "amount": "1800.00",
                        "movement_date": date(2026, 1, 27),
                        "note": "Accredito stipendio relativo a gennaio.",
                    },
                    {
                        "name": "Stipendio aprile",
                        "amount": "1800.00",
                        "movement_date": date(2026, 4, 27),
                        "note": "Accredito stipendio relativo ad aprile.",
                    },
                ],
            },
            {
                "name": "Svago",
                "type": "Expense",
                "category": "Svago",
                "note": "Spese personali, uscite e tempo libero.",
                "budget": {
                    2026: [100.00] * 12,
                },
                "movements": [
                    {
                        "name": "Sigarette",
                        "amount": "6.00",
                        "movement_date": date(2026, 4, 5),
                        "note": "Acquisto sigarette.",
                    },
                    {
                        "name": "Panino",
                        "amount": "8.00",
                        "movement_date": date(2026, 4, 5),
                        "note": "Pranzo veloce fuori casa.",
                    },
                    {
                        "name": "Barbiere",
                        "amount": "26.00",
                        "movement_date": date(2026, 4, 5),
                        "note": "Taglio capelli.",
                    },
                    {
                        "name": "Cinema",
                        "amount": "15.00",
                        "movement_date": date(2026, 4, 12),
                        "note": "Biglietto cinema.",
                    },
                    {
                        "name": "Birra",
                        "amount": "10.00",
                        "movement_date": date(2026, 4, 12),
                        "note": "Uscita serale con amici.",
                    },
                ],
            },
            {
                "name": "Supermercato",
                "type": "Expense",
                "category": "Spesa",
                "note": "Spese alimentari e prodotti per la casa.",
                "budget": {
                    2026: [250.00] * 12,
                },
                "movements": [
                    {
                        "name": "Spesa settimanale",
                        "amount": "72.35",
                        "movement_date": date(2026, 4, 3),
                        "note": "Spesa alimentare prima settimana di aprile.",
                    },
                    {
                        "name": "Detersivi",
                        "amount": "18.90",
                        "movement_date": date(2026, 4, 9),
                        "note": "Prodotti per pulizia casa.",
                    },
                    {
                        "name": "Spesa settimanale",
                        "amount": "64.20",
                        "movement_date": date(2026, 4, 17),
                        "note": "Spesa alimentare metà mese.",
                    },
                ],
            },
        ]

        for item in seed_items:
            transaction_obj = Transaction.objects.create(
                name=item["name"],
                type=item["type"],
                note=item["note"],
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