from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reports'

router = DefaultRouter()
router.register(r'monthly-evaluations', views.MonthlyEvaluationViewSet, basename='monthly-evaluations')
router.register(r'work-hours', views.WorkHoursViewSet, basename='work-hours')

urlpatterns = [
    path('', include(router.urls)),
]
