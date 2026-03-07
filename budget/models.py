import uuid
from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models


def default_12_decimals():
    return [Decimal("0.00")] * 12


class BudgetYear(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.PositiveIntegerField(unique=True)
    prev_end_wallet = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_surplus_money_added = ArrayField(
        base_field=models.DecimalField(max_digits=12, decimal_places=2),
        size=12,
        default=default_12_decimals,
    )
    current_saved_money = ArrayField(
        base_field=models.DecimalField(max_digits=12, decimal_places=2),
        size=12,
        default=default_12_decimals,
    )
    saved_money = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year"]

    def __str__(self):
        return f"Budget {self.year}"

    def clean(self):
        if len(self.current_surplus_money_added) != 12:
            raise ValidationError("current_surplus_money_added deve contenere 12 elementi")
        if len(self.current_saved_money) != 12:
            raise ValidationError("current_saved_money deve contenere 12 elementi")


class Category(models.Model):
    TYPE_CHOICES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget_year = models.ForeignKey(
        BudgetYear,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.type})"


class BudgetElement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="elements",
    )
    name = models.CharField(max_length=255)
    values = ArrayField(
        base_field=models.DecimalField(max_digits=12, decimal_places=2),
        size=12,
        default=default_12_decimals,
    )
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.name

    def clean(self):
        if len(self.values) != 12:
            raise ValidationError("values deve contenere 12 elementi")