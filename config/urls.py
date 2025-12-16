"""
URL configuration for OKR Performance System project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI Schema
schema_view = get_schema_view(
    openapi.Info(
        title="OKR Performance System API",
        default_version='v1',
        description="""
        # 团队OKR任务看板和绩效得分系统 API 文档
        
        这是一个综合性的团队管理平台API，用于跟踪任务进度、计算团队和个人绩效得分，并生成月度报告。
        
        ## 主要功能模块
        
        ### 用户管理 (Users)
        - 用户注册和认证
        - 团队成员管理
        - 工作小时记录
        
        ### 任务管理 (Tasks)
        - 任务创建和状态管理
        - 分值分配计算
        - 任务看板功能
        
        ### 评价系统 (Reviews)
        - 任务评价
        - 月度互评
        - 匿名评价支持
        
        ### 报告系统 (Reports)
        - 月度综合评价
        - 绩效分值计算
        - 管理员最终评价
        
        ## 认证方式
        
        API使用JWT (JSON Web Token) 进行认证。获取token后，在请求头中添加：
        ```
        Authorization: Bearer <your_token>
        ```
        
        ## 权限说明
        
        - **管理员 (admin)**: 拥有完整系统权限
        - **团队成员 (member)**: 可查看团队任务、提交评价、查看自己的报告
        
        ## 数据格式
        
        - 所有日期时间字段使用ISO 8601格式
        - 分值保留两位小数
        - UUID使用标准36字符格式
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(
            name="OKR Performance System Support",
            email="support@okr-system.com",
            url="https://www.okr-system.com/support"
        ),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        path('api/', include([
            path('users/', include('apps.users.urls')),
            path('tasks/', include('apps.tasks.urls')),
            path('reviews/', include('apps.reviews.urls')),
            path('reports/', include('apps.reports.urls')),
        ])),
    ],
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API Endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
    path('api/reports/', include('apps.reports.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
