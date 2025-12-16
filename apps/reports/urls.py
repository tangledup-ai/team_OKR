from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reports'

router = DefaultRouter()
router.register(r'monthly-evaluations', views.MonthlyEvaluationViewSet, basename='monthly-evaluations')
router.register(r'work-hours', views.WorkHoursViewSet, basename='work-hours')
router.register(r'performance-scores', views.PerformanceScoreViewSet, basename='performance-scores')
router.register(r'monthly-reports', views.MonthlyReportViewSet, basename='monthly-reports')

urlpatterns = [
    path('department-stats/', views.MonthlyReportViewSet.as_view({'get': 'department_stats'}), name='department-stats'),
    path('rankings/', views.MonthlyReportViewSet.as_view({'get': 'rankings'}), name='rankings'),
    path('', include(router.urls)),
]
