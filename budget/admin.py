from django.contrib import admin
from .models import BudgetYear, Category, BudgetElement


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0


class BudgetElementInline(admin.TabularInline):
    model = BudgetElement
    extra = 0


@admin.register(BudgetYear)
class BudgetYearAdmin(admin.ModelAdmin):
    list_display = ("year", "prev_end_wallet", "saved_money", "created_at")
    search_fields = ("year",)
    inlines = [CategoryInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "budget_year", "order", "created_at")
    list_filter = ("type", "budget_year__year")
    search_fields = ("title",)
    inlines = [BudgetElementInline]


@admin.register(BudgetElement)
class BudgetElementAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "order", "created_at")
    list_filter = ("category__budget_year__year", "category__type")
    search_fields = ("name",)