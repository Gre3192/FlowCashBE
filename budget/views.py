from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BudgetYear, Category, BudgetElement
from .serializers import (
    BudgetYearSerializer,
    CategorySerializer,
    BudgetElementSerializer,
    BudgetYearAggregateSerializer,
)


@extend_schema(tags=["Budget Years"])
class BudgetYearViewSet(viewsets.ModelViewSet):
    queryset = BudgetYear.objects.prefetch_related(
        Prefetch("categories", queryset=Category.objects.prefetch_related("elements"))
    ).all()
    serializer_class = BudgetYearSerializer
    filterset_fields = ["year"]
    search_fields = ["year"]
    ordering_fields = ["year", "created_at"]

    @action(detail=True, methods=["get"], url_path="aggregate")
    def aggregate(self, request, pk=None):
        budget_year = self.get_object()
        serializer = BudgetYearAggregateSerializer(budget_year)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path=r"by-year/(?P<year>\d+)")
    def by_year(self, request, year=None):
        budget_year = self.get_queryset().filter(year=year).first()
        if not budget_year:
            return Response({"detail": "Budget non trovato"}, status=404)

        serializer = BudgetYearAggregateSerializer(budget_year)
        return Response(serializer.data)


@extend_schema(tags=["Categories"])
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.select_related("budget_year").prefetch_related("elements").all()
    serializer_class = CategorySerializer
    filterset_fields = ["budget_year", "type"]
    search_fields = ["title"]
    ordering_fields = ["order", "created_at"]


@extend_schema(tags=["Elements"])
class BudgetElementViewSet(viewsets.ModelViewSet):
    queryset = BudgetElement.objects.select_related("category", "category__budget_year").all()
    serializer_class = BudgetElementSerializer
    filterset_fields = ["category", "category__budget_year"]
    search_fields = ["name"]
    ordering_fields = ["order", "created_at"]