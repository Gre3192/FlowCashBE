from rest_framework import serializers
from .models import Category, Transaction, Budget, TransactionEntry


class CategorySerializer(serializers.ModelSerializer):
    has_transactions = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "has_transactions"]

    def get_has_transactions(self, obj):
        return obj.transactions.exists()


class BudgetSerializer(serializers.ModelSerializer):
    transaction_id = serializers.PrimaryKeyRelatedField(
        source="transaction",
        queryset=Transaction.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Budget
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


class TransactionEntrySerializer(serializers.ModelSerializer):
    transaction_id = serializers.PrimaryKeyRelatedField(
        source="transaction",
        queryset=Transaction.objects.all(),
        write_only=True,
    )

    class Meta:
        model = TransactionEntry
        fields = [
            "id",
            "transaction_id",
            "amount",
            "entry_date",
            "note",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        write_only=True,
    )
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "name",
            "type",
            "category_id",
            "category",
        ]


class TransactionDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    budget = BudgetSerializer(source="budgets", many=True, read_only=True)
    entries = TransactionEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "name",
            "type",
            "category",
            "budget",
            "entries",
        ]