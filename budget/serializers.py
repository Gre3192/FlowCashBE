from rest_framework import serializers
from .models import BudgetYear, Category, BudgetElement


class BudgetElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetElement
        fields = [
            "id",
            "name",
            "values",
            "order",
            "category",
            "created_at",
            "updated_at",
        ]

    def validate_values(self, value):
        if len(value) != 12:
            raise serializers.ValidationError("values deve contenere 12 elementi")
        return value


class CategorySerializer(serializers.ModelSerializer):
    elements = BudgetElementSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "title",
            "type",
            "order",
            "budget_year",
            "elements",
            "created_at",
            "updated_at",
        ]


class BudgetYearSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = BudgetYear
        fields = [
            "id",
            "year",
            "prev_end_wallet",
            "current_surplus_money_added",
            "current_saved_money",
            "saved_money",
            "categories",
            "created_at",
            "updated_at",
        ]

    def validate_current_surplus_money_added(self, value):
        if len(value) != 12:
            raise serializers.ValidationError("current_surplus_money_added deve contenere 12 elementi")
        return value

    def validate_current_saved_money(self, value):
        if len(value) != 12:
            raise serializers.ValidationError("current_saved_money deve contenere 12 elementi")
        return value


class BudgetYearAggregateSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = BudgetYear
        fields = [
            "id",
            "year",
            "prevEndWallet",
            "currentSurplusMoneyAdded",
            "currentSavedMoney",
            "savedMoney",
            "categories",
        ]

    def get_categories(self, obj):
        return [
            {
                "id": str(category.id),
                "title": category.title,
                "type": category.type,
                "elements": [
                    {
                        "id": str(element.id),
                        "name": element.name,
                        "values": element.values,
                    }
                    for element in category.elements.all()
                ],
            }
            for category in obj.categories.all()
        ]

    def to_representation(self, instance):
        return {
            "id": str(instance.id),
            "year": instance.year,
            "prevEndWallet": instance.prev_end_wallet,
            "currentSurplusMoneyAdded": instance.current_surplus_money_added,
            "currentSavedMoney": instance.current_saved_money,
            "savedMoney": instance.saved_money,
            "categories": self.get_categories(instance),
        }