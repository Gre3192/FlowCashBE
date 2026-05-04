from django.contrib import admin

from .models import (
    Category,
    Transaction,
    TransactionBudget,
    TransactionMovement,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "category"]
    list_filter = ["type", "category"]
    search_fields = ["name", "category__name"]


@admin.register(TransactionBudget)
class TransactionBudgetAdmin(admin.ModelAdmin):
    list_display = ["id", "transaction", "year"]
    list_filter = ["year"]
    search_fields = ["transaction__name"]


@admin.register(TransactionMovement)
class TransactionMovementAdmin(admin.ModelAdmin):
    list_display = ["id", "transaction", "name", "amount", "movement_date"]
    list_filter = ["movement_date", "transaction__type", "transaction__category"]
    search_fields = ["name", "note", "transaction__name"]