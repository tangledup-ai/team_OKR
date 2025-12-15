from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'tasks'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'score-distributions', views.ScoreDistributionViewSet, basename='score-distribution')
router.register(r'score-allocations', views.ScoreAllocationViewSet, basename='score-allocation')

urlpatterns = [
    path('', include(router.urls)),
]
