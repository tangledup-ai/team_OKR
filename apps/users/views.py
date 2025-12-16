"""
Views for user management and authentication
"""
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Sum, Avg, Count
from django.db import IntegrityError
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User
from apps.reports.models import WorkHours
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserDetailSerializer,
    LoginSerializer,
    WorkHoursSerializer,
    WorkHoursCreateSerializer,
    WorkHoursUpdateSerializer,
    MonthlyWorkHoursStatsSerializer
)


class IsAdminUser(permissions.BasePermission):
    """
    自定义权限：只允许管理员访问
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                hasattr(request.user, 'role') and request.user.role == 'admin')


class LoginView(APIView):
    """用户登录视图"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="用户登录",
        operation_description="""
        用户通过邮箱和密码进行登录认证。
        
        成功登录后返回JWT访问令牌和刷新令牌，以及用户基本信息。
        访问令牌用于后续API调用的认证。
        """,
        tags=['用户认证'],
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="登录成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='刷新令牌'),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='访问令牌'),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, description='用户ID'),
                                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='邮箱'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description='姓名'),
                                'department': openapi.Schema(type=openapi.TYPE_STRING, description='部门', enum=['hardware', 'software', 'marketing']),
                                'role': openapi.Schema(type=openapi.TYPE_STRING, description='角色', enum=['admin', 'member'])
                            }
                        )
                    }
                ),
                examples={
                    "application/json": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@example.com",
                            "name": "张三",
                            "department": "software",
                            "role": "member"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="请求参数错误",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'password': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                )
            ),
            401: openapi.Response(
                description="认证失败",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='邮箱或密码错误')
                    }
                )
            )
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Authenticate user (using email as username)
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.name,
                    'department': user.department,
                    'role': user.role,
                }
            })
        else:
            return Response(
                {'error': '邮箱或密码错误'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class RegisterView(APIView):
    """用户注册视图（仅管理员可用）"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="注册新团队成员",
        operation_description="""
        管理员创建新的团队成员账户。
        
        需要提供成员的基本信息包括姓名、邮箱、密码和所属部门。
        系统会自动生成唯一的用户ID。
        
        **权限要求**: 仅管理员可访问
        """,
        tags=['用户管理'],
        request_body=UserCreateSerializer,
        responses={
            201: openapi.Response(
                description="用户创建成功",
                schema=UserSerializer
            ),
            400: openapi.Response(
                description="请求参数错误",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'password': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)),
                        'department': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                )
            ),
            403: openapi.Response(
                description="权限不足",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example='您没有执行该操作的权限。')
                    }
                )
            )
        }
    )
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Return user data
        response_serializer = UserSerializer(user)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    用户管理ViewSet
    
    list: 获取所有团队成员列表
    retrieve: 获取单个成员详情
    update: 更新成员信息（管理员）
    partial_update: 部分更新成员信息（管理员）
    destroy: 删除成员（管理员）
    """
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """
        根据操作设置不同的权限
        - list, retrieve: 所有认证用户
        - update, partial_update, destroy: 仅管理员
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    @swagger_auto_schema(
        operation_summary="获取团队成员列表",
        operation_description="获取所有团队成员的基本信息列表",
        tags=['用户管理'],
        responses={
            200: openapi.Response(
                description="成功获取团队成员列表",
                schema=UserSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="获取成员详情",
        operation_description="获取指定成员的详细信息，包括最后登录时间等",
        tags=['用户管理'],
        responses={
            200: openapi.Response(
                description="成功获取成员详情",
                schema=UserDetailSerializer
            ),
            404: openapi.Response(
                description="成员不存在",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example='未找到。')
                    }
                )
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="更新成员信息",
        operation_description="""
        管理员更新团队成员的信息。
        
        可更新的字段包括姓名、部门、角色和激活状态。
        
        **权限要求**: 仅管理员可访问
        """,
        tags=['用户管理'],
        request_body=UserUpdateSerializer,
        responses={
            200: openapi.Response(
                description="成员信息更新成功",
                schema=UserSerializer
            ),
            400: openapi.Response(description="请求参数错误"),
            403: openapi.Response(description="权限不足"),
            404: openapi.Response(description="成员不存在")
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="部分更新成员信息",
        operation_description="""
        管理员部分更新团队成员的信息。
        
        只需要提供需要更新的字段。
        
        **权限要求**: 仅管理员可访问
        """,
        tags=['用户管理'],
        request_body=UserUpdateSerializer,
        responses={
            200: openapi.Response(
                description="成员信息更新成功",
                schema=UserSerializer
            ),
            400: openapi.Response(description="请求参数错误"),
            403: openapi.Response(description="权限不足"),
            404: openapi.Response(description="成员不存在")
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='by-department/(?P<department>[^/.]+)')
    @swagger_auto_schema(
        operation_summary="按部门查询成员",
        operation_description="""
        根据部门筛选团队成员。
        
        支持的部门类型:
        - hardware: 硬件部门
        - software: 软件部门  
        - marketing: 市场部门
        """,
        tags=['用户管理'],
        manual_parameters=[
            openapi.Parameter(
                'department',
                openapi.IN_PATH,
                description="部门代码",
                type=openapi.TYPE_STRING,
                enum=['hardware', 'software', 'marketing'],
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="成功获取部门成员列表",
                schema=UserSerializer(many=True)
            ),
            400: openapi.Response(description="无效的部门参数")
        }
    )
    def by_department(self, request, department=None):
        """按部门查询成员"""
        users = self.queryset.filter(department=department)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_summary="获取当前用户信息",
        operation_description="""
        获取当前登录用户的详细信息。
        
        返回包含用户ID、邮箱、姓名、部门、角色等完整信息。
        """,
        tags=['用户管理'],
        responses={
            200: openapi.Response(
                description="成功获取当前用户信息",
                schema=UserDetailSerializer
            ),
            401: openapi.Response(description="未认证")
        }
    )
    def me(self, request):
        """获取当前登录用户信息"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)


class WorkHoursViewSet(viewsets.ModelViewSet):
    """
    工作小时记录ViewSet
    
    list: 获取工作小时记录列表
    retrieve: 获取单个工作小时记录详情
    create: 创建工作小时记录（管理员）
    update: 更新工作小时记录（管理员）
    partial_update: 部分更新工作小时记录（管理员）
    destroy: 删除工作小时记录（管理员）
    """
    queryset = WorkHours.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'create':
            return WorkHoursCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WorkHoursUpdateSerializer
        return WorkHoursSerializer
    
    def get_permissions(self):
        """
        根据操作设置不同的权限
        - list, retrieve: 所有认证用户
        - create, update, partial_update, destroy: 仅管理员
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """根据查询参数过滤数据"""
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return WorkHours.objects.none()
            
        queryset = WorkHours.objects.select_related('user', 'recorded_by')
        
        # 按用户过滤
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 按月份过滤
        month = self.request.query_params.get('month')
        if month:
            try:
                month_date = datetime.strptime(month, '%Y-%m').date()
                queryset = queryset.filter(month=month_date)
            except ValueError:
                pass
        
        # 按部门过滤
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(user__department=department)
        
        return queryset.order_by('-month', 'user__name')
    
    @swagger_auto_schema(
        operation_summary="获取工作小时记录列表",
        operation_description="""
        获取工作小时记录列表，支持多种过滤条件。
        
        普通用户只能查看自己的记录，管理员可以查看所有记录。
        """,
        tags=['工作小时管理'],
        manual_parameters=[
            openapi.Parameter(
                'user_id', 
                openapi.IN_QUERY, 
                description="用户ID（UUID格式）", 
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            ),
            openapi.Parameter(
                'month', 
                openapi.IN_QUERY, 
                description="月份 (YYYY-MM格式)", 
                type=openapi.TYPE_STRING,
                example="2024-01"
            ),
            openapi.Parameter(
                'department', 
                openapi.IN_QUERY, 
                description="部门", 
                type=openapi.TYPE_STRING,
                enum=['hardware', 'software', 'marketing']
            ),
        ],
        responses={
            200: openapi.Response(
                description="成功获取工作小时记录列表",
                schema=WorkHoursSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_summary="创建工作小时记录",
        operation_description="""
        管理员为团队成员创建工作小时记录。
        
        每个用户每月只能有一条工作小时记录。
        
        **权限要求**: 仅管理员可访问
        """,
        tags=['工作小时管理'],
        request_body=WorkHoursCreateSerializer,
        responses={
            201: openapi.Response(
                description="工作小时记录创建成功",
                schema=WorkHoursSerializer
            ),
            400: openapi.Response(
                description="请求参数错误或记录已存在",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, example='该用户在此月份的工作小时记录已存在，请使用更新操作')
                    }
                )
            ),
            403: openapi.Response(description="权限不足")
        }
    )
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {'error': '该用户在此月份的工作小时记录已存在，请使用更新操作'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @swagger_auto_schema(
        operation_description="更新工作小时记录（管理员）",
        request_body=WorkHoursUpdateSerializer,
        responses={200: WorkHoursSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="部分更新工作小时记录（管理员）",
        request_body=WorkHoursUpdateSerializer,
        responses={200: WorkHoursSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='monthly-stats')
    @swagger_auto_schema(
        operation_description="获取月度工作小时统计",
        manual_parameters=[
            openapi.Parameter('month', openapi.IN_QUERY, description="月份 (YYYY-MM)", type=openapi.TYPE_STRING, required=True),
        ],
        responses={200: MonthlyWorkHoursStatsSerializer}
    )
    def monthly_stats(self, request):
        """获取月度工作小时统计"""
        month = request.query_params.get('month')
        if not month:
            return Response(
                {'error': '请提供月份参数 (YYYY-MM)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            month_date = datetime.strptime(month, '%Y-%m').date()
        except ValueError:
            return Response(
                {'error': '月份格式错误，请使用 YYYY-MM 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取该月份的工作小时记录
        work_hours = WorkHours.objects.filter(month=month_date).select_related('user')
        
        # 计算总体统计
        total_stats = work_hours.aggregate(
            total_hours=Sum('hours'),
            average_hours=Avg('hours'),
            member_count=Count('user', distinct=True)
        )
        
        # 计算部门统计
        from .models import Department
        department_stats = {}
        for dept_code, dept_name in Department.choices:
            dept_hours = work_hours.filter(user__department=dept_code).aggregate(
                total_hours=Sum('hours'),
                average_hours=Avg('hours'),
                member_count=Count('user', distinct=True)
            )
            department_stats[dept_name] = {
                'total_hours': dept_hours['total_hours'] or 0,
                'average_hours': dept_hours['average_hours'] or 0,
                'member_count': dept_hours['member_count'] or 0
            }
        
        data = {
            'month': month_date,
            'total_hours': total_stats['total_hours'] or 0,
            'average_hours': total_stats['average_hours'] or 0,
            'member_count': total_stats['member_count'] or 0,
            'department_stats': department_stats
        }
        
        serializer = MonthlyWorkHoursStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    @swagger_auto_schema(
        operation_description="获取指定用户的工作小时记录",
        responses={200: WorkHoursSerializer(many=True)}
    )
    def user_work_hours(self, request, user_id=None):
        """获取指定用户的工作小时记录"""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        work_hours = WorkHours.objects.filter(user=user).order_by('-month')
        serializer = WorkHoursSerializer(work_hours, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='batch-create')
    @swagger_auto_schema(
        operation_description="批量创建工作小时记录（管理员）",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'month': openapi.Schema(type=openapi.TYPE_STRING, description='月份 (YYYY-MM)'),
                'records': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'user_id': openapi.Schema(type=openapi.TYPE_STRING, description='用户ID'),
                            'hours': openapi.Schema(type=openapi.TYPE_NUMBER, description='工作小时')
                        }
                    )
                )
            }
        ),
        responses={
            201: "批量创建成功",
            400: "请求参数错误",
            403: "权限不足"
        }
    )
    def batch_create(self, request):
        """批量创建工作小时记录（管理员）"""
        month = request.data.get('month')
        records = request.data.get('records', [])
        
        if not month:
            return Response(
                {'error': '请提供月份参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not records:
            return Response(
                {'error': '请提供工作小时记录'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            month_date = datetime.strptime(month, '%Y-%m').date()
        except ValueError:
            return Response(
                {'error': '月份格式错误，请使用 YYYY-MM 格式'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_records = []
        errors = []
        
        for i, record in enumerate(records):
            user_id = record.get('user_id')
            hours = record.get('hours')
            
            if not user_id or hours is None:
                errors.append(f'记录 {i+1}: 缺少用户ID或工作小时')
                continue
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                errors.append(f'记录 {i+1}: 用户不存在')
                continue
            
            # 检查是否已存在记录
            if WorkHours.objects.filter(user=user, month=month_date).exists():
                errors.append(f'记录 {i+1}: 用户 {user.name} 在 {month} 的记录已存在')
                continue
            
            try:
                work_hour = WorkHours.objects.create(
                    user=user,
                    month=month_date,
                    hours=hours,
                    recorded_by=request.user
                )
                created_records.append(work_hour)
            except Exception as e:
                errors.append(f'记录 {i+1}: 创建失败 - {str(e)}')
        
        response_data = {
            'created_count': len(created_records),
            'error_count': len(errors),
            'created_records': WorkHoursSerializer(created_records, many=True).data
        }
        
        if errors:
            response_data['errors'] = errors
        
        return Response(response_data, status=status.HTTP_201_CREATED)
