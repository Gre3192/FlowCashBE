import uuid
from django.db import models


class Category(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "Income", "Income"
        EXPENSE = "Expense", "Expense"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    name = models.CharField(max_length=120)

    type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="transactions",
        db_column="category_id",
    )

    class Meta:
        db_table = "transactions"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["type"]),
            models.Index(fields=["category"]),
            models.Index(fields=["category", "type"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.type}"


class Budget(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

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
        ordering = ["transaction", "year"]
        constraints = [
            models.UniqueConstraint(
                fields=["transaction", "year"],
                name="unique_budget_transaction_year",
            )
        ]
        indexes = [
            models.Index(fields=["transaction"]),
            models.Index(fields=["year"]),
            models.Index(fields=["transaction", "year"]),
        ]

    def __str__(self):
        return f"{self.transaction.name} - {self.year}"


class TransactionEntry(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

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
        ordering = ["-entry_date"]
        indexes = [
            models.Index(fields=["transaction"]),
            models.Index(fields=["entry_date"]),
            models.Index(fields=["transaction", "entry_date"]),
        ]

    def __str__(self):
        return f"{self.transaction.name} - {self.amount} - {self.entry_date}"