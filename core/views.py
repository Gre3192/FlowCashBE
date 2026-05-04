from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import (
    Category,
    Transaction,
    TransactionBudget,
    TransactionMovement,
)

from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    TransactionDetailSerializer,
    TransactionBudgetSerializer,
    TransactionMovementSerializer,
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


def get_month_range(year, month):
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    return first_day, last_day


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = (
        Transaction.objects
        .select_related("category")
        .prefetch_related("budgets", "movements")
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


class TransactionBudgetViewSet(viewsets.ModelViewSet):
    queryset = TransactionBudget.objects.select_related("transaction").all()
    serializer_class = TransactionBudgetSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        transaction_id = self.request.query_params.get("transaction_id")
        year = self.request.query_params.get("year")

        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)

        if year:
            queryset = queryset.filter(year=year)

        return queryset


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="transaction_id",
            type=str,
            required=False,
            location=OpenApiParameter.QUERY,
            description="UUID della transaction.",
        ),
        OpenApiParameter(
            name="year",
            type=int,
            required=False,
            location=OpenApiParameter.QUERY,
            description="Anno. Esempio: 2026",
        ),
        OpenApiParameter(
            name="month",
            type=int,
            required=False,
            location=OpenApiParameter.QUERY,
            description="Mese da 1 a 12.",
        ),
        OpenApiParameter(
            name="day",
            type=int,
            required=False,
            location=OpenApiParameter.QUERY,
            description="Giorno del mese.",
        ),
    ]
)
class TransactionMovementViewSet(viewsets.ModelViewSet):
    queryset = TransactionMovement.objects.select_related(
        "transaction",
        "transaction__category",
    ).all()

    serializer_class = TransactionMovementSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        transaction_id = self.request.query_params.get("transaction_id")
        year = self.request.query_params.get("year")
        month = self.request.query_params.get("month")
        day = self.request.query_params.get("day")

        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)

        if year and month and day:
            try:
                movement_date = date(
                    int(year),
                    int(month),
                    int(day),
                )

                queryset = queryset.filter(movement_date=movement_date)

            except ValueError:
                return queryset.none()

        elif year and month:
            try:
                year = int(year)
                month = int(month)

                if 1 <= month <= 12:
                    first_day, last_day = get_month_range(year, month)

                    queryset = queryset.filter(
                        movement_date__range=[first_day, last_day]
                    )
                else:
                    return queryset.none()

            except ValueError:
                return queryset.none()

        return queryset


class MonthlyOverviewAPIView(APIView):
    """
    GET    /api/flowcash/monthly-overview/?year=2026&month=4
    POST   /api/flowcash/monthly-overview/
    PATCH  /api/flowcash/monthly-overview/
    DELETE /api/flowcash/monthly-overview/

    Restituisce sempre tutte le categorie.
    Se per year/month non ci sono movimenti/budget, le categorie restano presenti.
    """

    @extend_schema(
        tags=["flowcash"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=int,
                required=True,
                location=OpenApiParameter.QUERY,
                description="Anno di riferimento. Esempio: 2026",
            ),
            OpenApiParameter(
                name="month",
                type=int,
                required=True,
                location=OpenApiParameter.QUERY,
                description="Mese di riferimento da 1 a 12. Esempio: 4",
            ),
        ],
        responses={200: dict, 400: dict},
    )
    def get(self, request):
        year_param = request.query_params.get("year")
        month_param = request.query_params.get("month")

        if not year_param or not month_param:
            return Response(
                {
                    "detail": "Parametri obbligatori: year e month. Esempio: ?year=2026&month=4"
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
        first_day, last_day = get_month_range(year, month)

        categories = Category.objects.order_by("name")

        transactions = (
            Transaction.objects
            .select_related("category")
            .order_by("category__name", "name")
        )

        transaction_ids = list(transactions.values_list("id", flat=True))

        budgets = TransactionBudget.objects.filter(
            transaction_id__in=transaction_ids,
            year=year,
        )

        budgets_by_transaction_id = {
            budget.transaction_id: budget
            for budget in budgets
        }

        movement_totals = (
            TransactionMovement.objects
            .filter(
                transaction_id__in=transaction_ids,
                movement_date__range=[first_day, last_day],
            )
            .values("transaction_id")
            .annotate(total=Sum("amount"))
        )

        movement_totals_by_transaction_id = {
            item["transaction_id"]: item["total"] or Decimal("0.00")
            for item in movement_totals
        }

        valid_transaction_ids = (
            set(budgets_by_transaction_id.keys())
            | set(movement_totals_by_transaction_id.keys())
        )

        transactions_by_category_id = defaultdict(list)

        for transaction_obj in transactions:
            transactions_by_category_id[transaction_obj.category_id].append(
                transaction_obj
            )

        income_budget_total = Decimal("0.00")
        expense_budget_total = Decimal("0.00")
        income_movements_total = Decimal("0.00")
        expense_movements_total = Decimal("0.00")

        categories_response = []

        for category in categories:
            category_transactions = transactions_by_category_id.get(category.id, [])

            category_budget_total = Decimal("0.00")
            category_movements_total = Decimal("0.00")
            transactions_response = []

            for transaction_obj in category_transactions:
                if transaction_obj.id not in valid_transaction_ids:
                    continue

                budget = budgets_by_transaction_id.get(transaction_obj.id)

                target = Decimal("0.00")

                if budget:
                    target = getattr(budget, month_field) or Decimal("0.00")

                current = movement_totals_by_transaction_id.get(
                    transaction_obj.id,
                    Decimal("0.00"),
                )

                remaining = max(target - current, Decimal("0.00"))

                progress = (
                    current / target * Decimal("100.00")
                    if target > 0
                    else Decimal("0.00")
                )

                category_budget_total += target
                category_movements_total += current

                if transaction_obj.type == "Income":
                    income_budget_total += target
                    income_movements_total += current

                if transaction_obj.type == "Expense":
                    expense_budget_total += target
                    expense_movements_total += current

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
                            "month_value": decimal_to_string(target),
                        },
                        "entries_total": decimal_to_string(current),
                        "movements_total": decimal_to_string(current),
                    }
                )

            category_progress = (
                category_movements_total / category_budget_total * Decimal("100.00")
                if category_budget_total > 0
                else Decimal("0.00")
            )

            categories_response.append(
                {
                    "id": str(category.id),
                    "name": category.name,
                    "has_transactions": len(category_transactions) > 0,
                    "budget_total": decimal_to_string(category_budget_total),
                    "entries_total": decimal_to_string(category_movements_total),
                    "movements_total": decimal_to_string(category_movements_total),
                    "progress": float(category_progress),
                    "transactions": transactions_response,
                }
            )

        return Response(
            {
                "year": year,
                "month": month,
                "month_field": month_field,
                "summary": {
                    "income_budget_total": decimal_to_string(income_budget_total),
                    "expense_budget_total": decimal_to_string(expense_budget_total),
                    "income_entries_total": decimal_to_string(income_movements_total),
                    "expense_entries_total": decimal_to_string(expense_movements_total),
                    "income_movements_total": decimal_to_string(income_movements_total),
                    "expense_movements_total": decimal_to_string(expense_movements_total),
                    "balance_budget": decimal_to_string(
                        income_budget_total - expense_budget_total
                    ),
                    "balance_entries": decimal_to_string(
                        income_movements_total - expense_movements_total
                    ),
                    "balance_movements": decimal_to_string(
                        income_movements_total - expense_movements_total
                    ),
                },
                "categories": categories_response,
            }
        )

    @extend_schema(
        tags=["flowcash"],
        request=dict,
        responses={201: dict, 200: dict, 400: dict},
    )
    @db_transaction.atomic
    def post(self, request):
        data = request.data
        action = data.get("action", "create_transaction")

        if action == "create_category":
            name = data.get("name")

            if not name:
                return Response(
                    {"detail": "name obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            category, created = Category.objects.get_or_create(name=name)

            return Response(
                {
                    "detail": (
                        "Category creata correttamente."
                        if created
                        else "Category già esistente."
                    ),
                    "category": {
                        "id": str(category.id),
                        "name": category.name,
                    },
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )

        if action == "create_transaction":
            year = data.get("year")
            month = data.get("month")
            category_name = data.get("category_name")
            category_id = data.get("category_id")
            transaction_name = data.get("transaction_name")
            transaction_type = data.get("type")
            budget_value = data.get("budget_value", "0.00")

            if not year or not month or not transaction_name or not transaction_type:
                return Response(
                    {
                        "detail": "Campi obbligatori: year, month, transaction_name, type."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not category_name and not category_id:
                return Response(
                    {"detail": "Devi passare category_name oppure category_id."},
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

            if category_id:
                category = get_object_or_404(Category, id=category_id)
            else:
                category, _ = Category.objects.get_or_create(name=category_name)

            transaction_obj = Transaction.objects.create(
                name=transaction_name,
                type=transaction_type,
                category=category,
            )

            month_field = MONTH_FIELD_MAP[month]

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

            budget = TransactionBudget.objects.create(
                transaction=transaction_obj,
                year=year,
                **budget_defaults,
            )

            return Response(
                {
                    "detail": "Transaction creata correttamente.",
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
                },
                status=status.HTTP_201_CREATED,
            )

        if action == "create_movement":
            transaction_id = data.get("transaction_id")
            name = data.get("name")
            amount = data.get("amount")
            movement_date = data.get("movement_date")
            note = data.get("note")

            if not transaction_id or not name or not amount or not movement_date:
                return Response(
                    {
                        "detail": "Campi obbligatori: transaction_id, name, amount, movement_date."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            transaction_obj = get_object_or_404(Transaction, id=transaction_id)

            movement = TransactionMovement.objects.create(
                transaction=transaction_obj,
                name=name,
                amount=Decimal(str(amount)),
                movement_date=movement_date,
                note=note,
            )

            return Response(
                {
                    "detail": "Movement creato correttamente.",
                    "movement": {
                        "id": str(movement.id),
                        "transaction_id": str(movement.transaction_id),
                        "name": movement.name,
                        "amount": decimal_to_string(movement.amount),
                        "movement_date": movement.movement_date,
                        "note": movement.note,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"detail": f"Azione non supportata: {action}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["flowcash"],
        request=dict,
        responses={200: dict, 400: dict},
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

            budget, _ = TransactionBudget.objects.get_or_create(
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
                        "transaction_id": str(budget.transaction_id),
                        "year": budget.year,
                        "month": month,
                        "month_field": month_field,
                        "month_value": decimal_to_string(getattr(budget, month_field)),
                    },
                }
            )

        if action == "update_movement":
            movement_id = data.get("movement_id")

            if not movement_id:
                return Response(
                    {"detail": "movement_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            movement = get_object_or_404(TransactionMovement, id=movement_id)

            if "name" in data:
                movement.name = data["name"]

            if "amount" in data:
                movement.amount = Decimal(str(data["amount"]))

            if "movement_date" in data:
                movement.movement_date = data["movement_date"]

            if "note" in data:
                movement.note = data["note"]

            if "transaction_id" in data:
                transaction_obj = get_object_or_404(
                    Transaction,
                    id=data["transaction_id"],
                )
                movement.transaction = transaction_obj

            movement.save()

            return Response(
                {
                    "detail": "Movement aggiornato correttamente.",
                    "movement": {
                        "id": str(movement.id),
                        "transaction_id": str(movement.transaction_id),
                        "name": movement.name,
                        "amount": decimal_to_string(movement.amount),
                        "movement_date": movement.movement_date,
                        "note": movement.note,
                    },
                }
            )

        return Response(
            {"detail": f"Azione non supportata: {action}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["flowcash"],
        request=dict,
        responses={200: dict, 400: dict},
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

            budget = get_object_or_404(TransactionBudget, id=budget_id)
            budget.delete()

            return Response({"detail": "Budget eliminato correttamente."})

        if action == "delete_movement":
            movement_id = data.get("movement_id")

            if not movement_id:
                return Response(
                    {"detail": "movement_id obbligatorio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            movement = get_object_or_404(TransactionMovement, id=movement_id)
            movement.delete()

            return Response({"detail": "Movement eliminato correttamente."})

        return Response(
            {"detail": f"Azione non supportata: {action}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class TransactionMovementsByMonthAPIView(APIView):
    """
    GET /api/transactions/{transaction_id}/movements/monthly/?year=2026&month=4
    """

    @extend_schema(
        tags=["transactions"],
        parameters=[
            OpenApiParameter(
                name="year",
                type=int,
                required=True,
                location=OpenApiParameter.QUERY,
                description="Anno di riferimento. Esempio: 2026",
            ),
            OpenApiParameter(
                name="month",
                type=int,
                required=True,
                location=OpenApiParameter.QUERY,
                description="Mese di riferimento da 1 a 12. Esempio: 4",
            ),
        ],
        responses={200: dict, 400: dict},
    )
    def get(self, request, transaction_id):
        year_param = request.query_params.get("year")
        month_param = request.query_params.get("month")

        if not year_param or not month_param:
            return Response(
                {"detail": "Parametri obbligatori: year e month."},
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

        transaction_obj = get_object_or_404(Transaction, id=transaction_id)

        first_day, last_day = get_month_range(year, month)

        movements = (
            TransactionMovement.objects
            .filter(
                transaction=transaction_obj,
                movement_date__range=[first_day, last_day],
            )
            .order_by("movement_date", "name")
        )

        movements_by_day_dict = defaultdict(list)

        for movement in movements:
            movements_by_day_dict[movement.movement_date].append(movement)

        movements_by_day = []
        total = Decimal("0.00")

        for movement_date, day_movements in movements_by_day_dict.items():
            day_total = sum(
                (movement.amount for movement in day_movements),
                Decimal("0.00"),
            )

            total += day_total

            movements_by_day.append(
                {
                    "date": movement_date,
                    "total": decimal_to_string(day_total),
                    "movements": [
                        {
                            "id": str(movement.id),
                            "name": movement.name,
                            "amount": decimal_to_string(movement.amount),
                            "movement_date": movement.movement_date,
                            "note": movement.note,
                        }
                        for movement in day_movements
                    ],
                }
            )

        return Response(
            {
                "transaction": {
                    "id": str(transaction_obj.id),
                    "name": transaction_obj.name,
                    "type": transaction_obj.type,
                    "category": {
                        "id": str(transaction_obj.category.id),
                        "name": transaction_obj.category.name,
                    },
                },
                "year": year,
                "month": month,
                "total": decimal_to_string(total),
                "movements_by_day": movements_by_day,
            }
        )