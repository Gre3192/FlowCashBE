from rest_framework import serializers

from .models import (
    Category,
    Transaction,
    TransactionBudget,
    TransactionMovement,
    
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "name",
            "type",
            "note",
            "category",
            "category_name",
        ]


class TransactionBudgetSerializer(serializers.ModelSerializer):
    transaction_id = serializers.PrimaryKeyRelatedField(
        source="transaction",
        queryset=Transaction.objects.all(),
    )

    class Meta:
        model = TransactionBudget
        fields = [
            "id",
            "transaction_id",
            "year",
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


class TransactionBudgetYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionBudget
        fields = [
            "id",
            "year",
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


class TransactionMovementSerializer(serializers.ModelSerializer):
    transaction_id = serializers.PrimaryKeyRelatedField(
        source="transaction",
        queryset=Transaction.objects.all(),
    )

    transaction_name = serializers.CharField(
        source="transaction.name",
        read_only=True,
    )

    transaction_type = serializers.CharField(
        source="transaction.type",
        read_only=True,
    )

    category_id = serializers.UUIDField(
        source="transaction.category.id",
        read_only=True,
    )

    category_name = serializers.CharField(
        source="transaction.category.name",
        read_only=True,
    )

    class Meta:
        model = TransactionMovement
        fields = [
            "id",
            "transaction_id",
            "transaction_name",
            "transaction_type",
            "category_id",
            "category_name",
            "name",
            "amount",
            "movement_date",
            "note",
        ]


class TransactionDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    budgets = TransactionBudgetSerializer(
        many=True,
        read_only=True,
    )

    movements = TransactionMovementSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "name",
            "type",
            "note",
            "category",
            "category_name",
            "budgets",
            "movements",
        ]