from django.contrib import admin
from .models import Category, Transaction, Budget, TransactionEntry


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "category"]
    list_filter = ["type", "category"]
    search_fields = ["name"]


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ["id", "transaction", "year"]
    list_filter = ["year"]
    search_fields = ["transaction__name"]


@admin.register(TransactionEntry)
class TransactionEntryAdmin(admin.ModelAdmin):
    list_display = ["id", "transaction", "amount", "entry_date"]
    list_filter = ["entry_date"]
    search_fields = ["transaction__name", "note"]