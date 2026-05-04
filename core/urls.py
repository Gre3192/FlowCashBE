from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    TransactionViewSet,
    TransactionBudgetViewSet,
    TransactionMovementViewSet,
    MonthlyOverviewAPIView,
    TransactionMovementsByMonthAPIView,
)

router = DefaultRouter()

router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(
    r"transaction-budgets",
    TransactionBudgetViewSet,
    basename="transaction-budget",
)
router.register(
    r"transaction-movements",
    TransactionMovementViewSet,
    basename="transaction-movement",
)

urlpatterns = [
    path(
        "flowcash/monthly-overview/",
        MonthlyOverviewAPIView.as_view(),
        name="monthly-overview",
    ),
    path(
        "transactions/<uuid:transaction_id>/movements/monthly/",
        TransactionMovementsByMonthAPIView.as_view(),
        name="transaction-movements-monthly",
    ),
]

urlpatterns += router.urls