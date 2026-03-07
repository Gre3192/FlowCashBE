from rest_framework.routers import DefaultRouter
from .views import BudgetYearViewSet, CategoryViewSet, BudgetElementViewSet

router = DefaultRouter()
router.register(r"budget-years", BudgetYearViewSet, basename="budget-year")
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"elements", BudgetElementViewSet, basename="element")

urlpatterns = router.urls