from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Category, Transaction, Budget, TransactionEntry
from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    TransactionDetailSerializer,
    BudgetSerializer,
    TransactionEntrySerializer,
)

from decimal import Decimal
from calendar import monthrange




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
    return f"{Decimal(value):.2f}"


@extend_schema(
    tags=["FlowCash"],
    parameters=[
        OpenApiParameter(
            name="year",
            description="Anno di riferimento, esempio 2026",
            required=True,
            type=int,
        ),
        OpenApiParameter(
            name="month",
            description="Mese di riferimento da 1 a 12",
            required=True,
            type=int,
        ),
    ],
    responses={200: dict},
)

@api_view(["GET"])
def monthly_overview(request):
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
            {
                "detail": "year e month devono essere numeri interi."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if month < 1 or month > 12:
        return Response(
            {
                "detail": "month deve essere compreso tra 1 e 12."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    month_field = MONTH_FIELD_MAP[month]

    first_day = f"{year}-{month:02d}-01"
    last_day_number = monthrange(year, month)[1]
    last_day = f"{year}-{month:02d}-{last_day_number}"

    categories = Category.objects.prefetch_related("transactions").order_by("name")

    transactions = (
        Transaction.objects
        .select_related("category")
        .filter(category__in=categories)
        .order_by("category__name", "name")
    )

    transaction_ids = [transaction.id for transaction in transactions]

    budgets = Budget.objects.filter(
        transaction_id__in=transaction_ids,
        year=year,
    )

    entries = TransactionEntry.objects.filter(
        transaction_id__in=transaction_ids,
        entry_date__range=[first_day, last_day],
    ).order_by("entry_date")

    if not budgets.exists() and not entries.exists():
        return Response({})

    budgets_by_transaction_id = {
        budget.transaction_id: budget
        for budget in budgets
    }

    entries_by_transaction_id = {}

    for entry in entries:
        entries_by_transaction_id.setdefault(entry.transaction_id, []).append(entry)

    transactions_by_category_id = {}

    for transaction in transactions:
        transactions_by_category_id.setdefault(transaction.category_id, []).append(transaction)

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

        for transaction in category_transactions:
            budget = budgets_by_transaction_id.get(transaction.id)
            transaction_entries = entries_by_transaction_id.get(transaction.id, [])

            month_value = Decimal("0.00")

            if budget:
                month_value = getattr(budget, month_field) or Decimal("0.00")

            entries_total = sum(
                (entry.amount for entry in transaction_entries),
                Decimal("0.00"),
            )

            category_budget_total += month_value
            category_entries_total += entries_total

            if transaction.type == "Income":
                income_budget_total += month_value
                income_entries_total += entries_total

            if transaction.type == "Expense":
                expense_budget_total += month_value
                expense_entries_total += entries_total

            transactions_response.append(
                {
                    "id": transaction.id,
                    "name": transaction.name,
                    "type": transaction.type,
                    "budget": {
                        "id": budget.id if budget else None,
                        "year": budget.year if budget else year,
                        "month_value": decimal_to_string(month_value),
                    },
                    "entries": [
                        {
                            "id": entry.id,
                            "amount": decimal_to_string(entry.amount),
                            "entry_date": entry.entry_date,
                            "note": entry.note,
                        }
                        for entry in transaction_entries
                    ],
                    "entries_total": decimal_to_string(entries_total),
                }
            )

        categories_response.append(
            {
                "id": category.id,
                "name": category.name,
                "transactions": transactions_response,
                "category_budget_total": decimal_to_string(category_budget_total),
                "category_entries_total": decimal_to_string(category_entries_total),
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
            "balance_budget": decimal_to_string(income_budget_total - expense_budget_total),
            "balance_entries": decimal_to_string(income_entries_total - expense_entries_total),
        },
        "categories": categories_response,
    }

    return Response(response)


