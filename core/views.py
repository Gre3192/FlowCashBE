from rest_framework import viewsets
from .models import Category, Transaction, Budget, TransactionEntry
from .serializers import (
    CategorySerializer,
    TransactionSerializer,
    TransactionDetailSerializer,
    BudgetSerializer,
    TransactionEntrySerializer,
)


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