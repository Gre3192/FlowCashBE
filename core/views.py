from decimal import Decimal
from calendar import monthrange

from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Category, Transaction, Budget, TransactionEntry
from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    TransactionDetailSerializer,
    BudgetSerializer,
    TransactionEntrySerializer,
)


MONTH_FIELD_MAP = {
    1: "gen_val",
    2: "feb_val",
    3: "mar_val",
    4: "apr_val",
    5: "mag_val",
    6: "giu_val",
    7: "lug_val",
    8: "ago_val",
    9: "set_val",
    10: "ott_val",
    11: "nov_val",
    12: "dic_val",
}


def decimal_to_string(value):
    return f"{Decimal(value or 0):.2f}"


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = (
        Transaction.objects
        .select_related("category")
        .prefetch_related("budgets", "entries")
        .all()
    )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TransactionDetailSerializer

        return TransactionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        category_id = self.request.query_params.get("category_id")
        transaction_type = self.request.query_params.get("type")

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if transaction_type:
            queryset = queryset.filter(type=transaction_type)

        return queryset


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.select_related("transaction").all()
    serializer_class = BudgetSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        transaction_id = self.request.query_params.get("transaction_id")
        year = self.request.query_params.get("year")

        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)

        if year:
            queryset = queryset.filter(year=year)

        return queryset


class TransactionEntryViewSet(viewsets.ModelViewSet):
    queryset = TransactionEntry.objects.select_related("transaction").all()
    serializer_class = TransactionEntrySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        transaction_id = self.request.query_params.get("transaction_id")
        entry_date = self.request.query_params.get("entry_date")

        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)

        if entry_date:
            queryset = queryset.filter(entry_date=entry_date)

        return queryset


class MonthlyOverviewAPIView(APIView):
    """
    GET /api/flowcash/monthly-overview/?year=2026&month=1

    Restituisce sempre tutte le categorie.
    Se year/month non hanno budget o entries associate,
    le categorie vengono comunque restituite con transactions: [].
    """

    def get(self, request):
        year_param = request.query_params.get("year")
        month_param = request.query_params.get("month")

        if not year_param or not month_param:
            return Response(
                {
                    "detail": "Parametri obbligatori: year e month. Esempio: ?year=2026&month=1"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            year = int(year_param)
            month = int(month_param)
        except ValueError:
            return Response(
                {"detail": "year e month devono essere numeri interi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if month < 1 or month > 12:
            return Response(
                {"detail": "month deve essere compreso tra 1 e 12."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        month_field = MONTH_FIELD_MAP[month]

        first_day = f"{year}-{month:02d}-01"
        last_day_number = monthrange(year, month)[1]
        last_day = f"{year}-{month:02d}-{last_day_number}"

        categories = Category.objects.order_by("name")

        transactions = (
            Transaction.objects
            .select_related("category")
            .order_by("category__name", "name")
        )

        transaction_ids = list(transactions.values_list("id", flat=True))

        budgets = Budget.objects.filter(
            transaction_id__in=transaction_ids,
            year=year,
        )

        entries = (
            TransactionEntry.objects
            .filter(
                transaction_id__in=transaction_ids,
                entry_date__range=[first_day, last_day],
            )
            .order_by("entry_date")
        )

        budgets_by_transaction_id = {
            budget.transaction_id: budget
            for budget in budgets
        }

        entries_by_transaction_id = {}

        for entry in entries:
            entries_by_transaction_id.setdefault(
                entry.transaction_id,
                []
            ).append(entry)

        valid_transaction_ids = (
            set(budgets_by_transaction_id.keys())
            | set(entries_by_transaction_id.keys())
        )

        transactions_by_category_id = {}

        for transaction_obj in transactions:
            transactions_by_category_id.setdefault(
                transaction_obj.category_id,
                []
            ).append(transaction_obj)

        income_budget_total = Decimal("0.00")
        expense_budget_total = Decimal("0.00")
        income_entries_total = Decimal("0.00")
        expense_entries_total = Decimal("0.00")

        categories_response = []

        for category in categories:
            category_transactions = transactions_by_category_id.get(category.id, [])

            category_budget_total = Decimal("0.00")
            category_entries_total = Decimal("0.00")

            transactions_response = []

            for transaction_obj in category_transactions:
                if transaction_obj.id not in valid_transaction_ids:
                    continue

                budget = budgets_by_transaction_id.get(transaction_obj.id)
                transaction_entries = entries_by_transaction_id.get(
                    transaction_obj.id,
                    [],
                )

                month_value = Decimal("0.00")

                if budget:
                    month_value = getattr(budget, month_field) or Decimal("0.00")

                entries_total = sum(
                    (entry.amount for entry in transaction_entries),
                    Decimal("0.00"),
                )

                current = entries_total
                target = month_value
                remaining = max(target - current, Decimal("0.00"))

                progress = (
                    current / target * Decimal("100.00")
                    if target > 0
                    else Decimal("0.00")
                )

                category_budget_total += target
                category_entries_total += current

                if transaction_obj.type == "Income":
                    income_budget_total += target
                    income_entries_total += current

                if transaction_obj.type == "Expense":
                    expense_budget_total += target
                    expense_entries_total += current

                transactions_response.append(
                    {
                        "id": str(transaction_obj.id),
                        "name": transaction_obj.name,
                        "description": transaction_obj.name,
                        "type": transaction_obj.type,
                        "current": decimal_to_string(current),
                        "target": decimal_to_string(target),
                        "remaining": decimal_to_string(remaining),
                        "progress": float(progress),
                        "budget": {
                            "id": str(budget.id) if budget else None,
                            "year": budget.year if budget else year,
                            "month_value": decimal_to_string(month_value),
                        },
                        "entries": [
                            {
                                "id": str(entry.id),
                                "amount": decimal_to_string(entry.amount),
                                "entry_date": entry.entry_date,
                                "note": entry.note,
                            }
                            for entry in transaction_entries
                        ],
                        "entries_total": decimal_to_string(entries_total),
                    }
                )

            category_progress = (
                category_entries_total / category_budget_total * Decimal("100.00")
                if category_budget_total > 0
                else Decimal("0.00")
            )

            categories_response.append(
                {
                    "id": str(category.id),
                    "name": category.name,
                    "has_transactions": len(category_transactions) > 0,
                    "budget_total": decimal_to_string(category_budget_total),
                    "entries_total": decimal_to_string(category_entries_total),
                    "progress": float(category_progress),
                    "transactions": transactions_response,
                }
            )

        response = {
            "year": year,
            "month": month,
            "month_field": month_field,
            "summary": {
                "income_budget_total": decimal_to_string(income_budget_total),
                "expense_budget_total": decimal_to_string(expense_budget_total),
                "income_entries_total": decimal_to_string(income_entries_total),
                "expense_entries_total": decimal_to_string(expense_entries_total),
                "balance_budget": decimal_to_string(
                    income_budget_total - expense_budget_total
                ),
                "balance_entries": decimal_to_string(
                    income_entries_total - expense_entries_total
                ),
            },
            "categories": categories_response,
        }

        return Response(response)

    @db_transaction.atomic
    def post(self, request):
        data = request.data

        year = data.get("year")
        month = data.get("month")
        category_name = data.get("category_name")
        transaction_name = data.get("transaction_name")
        transaction_type = data.get("type")
        budget_value = data.get("budget_value", "0.00")
        entry_amount = data.get("entry_amount")
        entry_date = data.get("entry_date")
        note = data.get("note")

        if not year or not month or not category_name or not transaction_name or not transaction_type:
            return Response(
                {
                    "detail": "Campi obbligatori: year, month, category_name, transaction_name, type."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            year = int(year)
            month = int(month)
        except ValueError:
            return Response(
                {"detail": "year e month devono essere numeri interi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if month < 1 or month > 12:
            return Response(
                {"detail": "month deve essere compreso tra 1 e 12."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if transaction_type not in ["Income", "Expense"]:
            return Response(
                {"detail": "type deve essere Income oppure Expense."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        month_field = MONTH_FIELD_MAP[month]

        category, _ = Category.objects.get_or_create(
            name=category_name
        )

        transaction_obj = Transaction.objects.create(
            name=transaction_name,
            type=transaction_type,
            category=category,
        )

        budget_defaults = {
            "gen_val": Decimal("0.00"),
            "feb_val": Decimal("0.00"),
            "mar_val": Decimal("0.00"),
            "apr_val": Decimal("0.00"),
            "mag_val": Decimal("0.00"),
            "giu_val": Decimal("0.00"),
            "lug_val": Decimal("0.00"),
            "ago_val": Decimal("0.00"),
            "set_val": Decimal("0.00"),
            "ott_val": Decimal("0.00"),
            "nov_val": Decimal("0.00"),
            "dic_val": Decimal("0.00"),
        }

        budget_defaults[month_field] = Decimal(str(budget_value or "0.00"))

        budget = Budget.objects.create(
            transaction=transaction_obj,
            year=year,
            **budget_defaults,
        )

        entry = None

        if entry_amount and entry_date:
            entry = TransactionEntry.objects.create(
                transaction=transaction_obj,
                amount=Decimal(str(entry_amount)),
                entry_date=entry_date,
                note=note,
            )

        return Response(
            {
                "detail": "Elemento creato correttamente.",
                "category": {
                    "id": str(category.id),
                    "name": category.name,
                },
                "transaction": {
                    "id": str(transaction_obj.id),
                    "name": transaction_obj.name,
                    "type": transaction_obj.type,
                },
                "budget": {
                    "id": str(budget.id),
                    "year": budget.year,
                    "month": month,
                    "month_field": month_field,
                    "month_value": decimal_to_string(getattr(budget, month_field)),
                },
                "entry": {
                    "id": str(entry.id),
                    "amount": decimal_to_string(entry.amount),
                    "entry_date": entry.entry_date,
                    "note": entry.note,
                } if entry else None,
            },
            status=status.HTTP_201_CREATED,
        )

    @db_transaction.atomic
    def patch(self, request):
        data = request.data
        action = data.get("action")

        if not action:
            return Response(
                {"detail": "Campo obbligatorio: action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == "update_category":
            category_id = data.get("category_id")

            if not category_id:
                return Response(
                    {"detail": "category_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            category = get_object_or_404(Category, id=category_id)

            if "name" in data:
                category.name = data["name"]

            category.save()

            return Response(
                {
                    "detail": "Category aggiornata correttamente.",
                    "category": {
                        "id": str(category.id),
                        "name": category.name,
                    },
                }
            )

        if action == "update_transaction":
            transaction_id = data.get("transaction_id")

            if not transaction_id:
                return Response(
                    {"detail": "transaction_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            transaction_obj = get_object_or_404(Transaction, id=transaction_id)

            if "name" in data:
                transaction_obj.name = data["name"]

            if "type" in data:
                if data["type"] not in ["Income", "Expense"]:
                    return Response(
                        {"detail": "type deve essere Income oppure Expense."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                transaction_obj.type = data["type"]

            if "category_id" in data:
                category = get_object_or_404(Category, id=data["category_id"])
                transaction_obj.category = category

            transaction_obj.save()

            return Response(
                {
                    "detail": "Transaction aggiornata correttamente.",
                    "transaction": {
                        "id": str(transaction_obj.id),
                        "name": transaction_obj.name,
                        "type": transaction_obj.type,
                        "category_id": str(transaction_obj.category_id),
                    },
                }
            )

        if action == "update_budget_month":
            transaction_id = data.get("transaction_id")
            year = data.get("year")
            month = data.get("month")
            value = data.get("value", "0.00")

            if not transaction_id or not year or not month:
                return Response(
                    {"detail": "transaction_id, year e month sono obbligatori."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                year = int(year)
                month = int(month)
            except ValueError:
                return Response(
                    {"detail": "year e month devono essere numeri interi."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if month < 1 or month > 12:
                return Response(
                    {"detail": "month deve essere compreso tra 1 e 12."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            transaction_obj = get_object_or_404(Transaction, id=transaction_id)
            month_field = MONTH_FIELD_MAP[month]

            budget, _ = Budget.objects.get_or_create(
                transaction=transaction_obj,
                year=year,
            )

            setattr(budget, month_field, Decimal(str(value or "0.00")))
            budget.save()

            return Response(
                {
                    "detail": "Budget mensile aggiornato correttamente.",
                    "budget": {
                        "id": str(budget.id),
                        "year": budget.year,
                        "month": month,
                        "month_field": month_field,
                        "month_value": decimal_to_string(getattr(budget, month_field)),
                    },
                }
            )

        if action == "update_entry":
            entry_id = data.get("entry_id")

            if not entry_id:
                return Response(
                    {"detail": "entry_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            entry = get_object_or_404(TransactionEntry, id=entry_id)

            if "amount" in data:
                entry.amount = Decimal(str(data["amount"]))

            if "entry_date" in data:
                entry.entry_date = data["entry_date"]

            if "note" in data:
                entry.note = data["note"]

            entry.save()

            return Response(
                {
                    "detail": "Entry aggiornata correttamente.",
                    "entry": {
                        "id": str(entry.id),
                        "amount": decimal_to_string(entry.amount),
                        "entry_date": entry.entry_date,
                        "note": entry.note,
                    },
                }
            )

        return Response(
            {"detail": f"Azione non supportata: {action}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @db_transaction.atomic
    def delete(self, request):
        data = request.data
        action = data.get("action")

        if not action:
            return Response(
                {"detail": "Campo obbligatorio: action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == "delete_category":
            category_id = data.get("category_id")

            if not category_id:
                return Response(
                    {"detail": "category_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            category = get_object_or_404(Category, id=category_id)
            category.delete()

            return Response({"detail": "Category eliminata correttamente."})

        if action == "delete_transaction":
            transaction_id = data.get("transaction_id")

            if not transaction_id:
                return Response(
                    {"detail": "transaction_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            transaction_obj = get_object_or_404(Transaction, id=transaction_id)
            transaction_obj.delete()

            return Response({"detail": "Transaction eliminata correttamente."})

        if action == "delete_budget":
            budget_id = data.get("budget_id")

            if not budget_id:
                return Response(
                    {"detail": "budget_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            budget = get_object_or_404(Budget, id=budget_id)
            budget.delete()

            return Response({"detail": "Budget eliminato correttamente."})

        if action == "delete_entry":
            entry_id = data.get("entry_id")

            if not entry_id:
                return Response(
                    {"detail": "entry_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            entry = get_object_or_404(TransactionEntry, id=entry_id)
            entry.delete()

            return Response({"detail": "Entry eliminata correttamente."})

        return Response(
            {"detail": f"Azione non supportata: {action}"},
            status=status.HTTP_400_BAD_REQUEST,
        )