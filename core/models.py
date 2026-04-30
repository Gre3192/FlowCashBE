import uuid
from django.db import models


class Category(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "categories"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "Income", "Income"
        EXPENSE = "Expense", "Expense"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    name = models.CharField(max_length=120)
    type = models.CharField(max_length=20, choices=TransactionType.choices)

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="transactions",
        db_column="category_id",
    )

    class Meta:
        db_table = "transactions"


class Budget(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="budgets",
        db_column="transaction_id",
    )

    year = models.IntegerField()

    gen_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    feb_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mar_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    apr_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mag_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    giu_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    lug_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ago_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    set_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ott_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nov_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dic_val = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "budget"
        constraints = [
            models.UniqueConstraint(
                fields=["transaction", "year"],
                name="unique_budget_transaction_year",
            )
        ]


class TransactionEntry(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="entries",
        db_column="transaction_id",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    entry_date = models.DateField()
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "transaction_entries"