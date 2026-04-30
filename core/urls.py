from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    TransactionViewSet,
    BudgetViewSet,
    TransactionEntryViewSet,
    monthly_overview,
)

router = DefaultRouter()

router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"budget", BudgetViewSet, basename="budget")
router.register(r"transaction-entries", TransactionEntryViewSet, basename="transaction-entry")

urlpatterns = [
    path("flowcash/monthly-overview/", monthly_overview, name="monthly-overview"),
]

urlpatterns += router.urls