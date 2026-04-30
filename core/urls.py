from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet,
    TransactionViewSet,
    BudgetViewSet,
    TransactionEntryViewSet,
)

router = DefaultRouter()

router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"budget", BudgetViewSet, basename="budget")
router.register(r"transaction-entries", TransactionEntryViewSet, basename="transaction-entry")

urlpatterns = router.urls