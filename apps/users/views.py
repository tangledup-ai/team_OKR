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
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class LoginView(APIView):
    """用户登录视图"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="用户登录",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="登录成功",
                examples={
                    "application/json": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
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
            400: "请求参数错误",
            401: "邮箱或密码错误"
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
        operation_description="管理员注册新团队成员",
        request_body=UserCreateSerializer,
        responses={
            201: UserSerializer,
            400: "请求参数错误",
            403: "权限不足"
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
        operation_description="获取所有团队成员列表",
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="获取单个成员详情",
        responses={200: UserDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="更新成员信息（管理员）",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="部分更新成员信息（管理员）",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='by-department/(?P<department>[^/.]+)')
    @swagger_auto_schema(
        operation_description="按部门查询成员",
        responses={200: UserSerializer(many=True)}
    )
    def by_department(self, request, department=None):
        """按部门查询成员"""
        users = self.queryset.filter(department=department)
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @swagger_auto_schema(
        operation_description="获取当前登录用户信息",
        responses={200: UserDetailSerializer}
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
        operation_description="获取工作小时记录列表",
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description="用户ID", type=openapi.TYPE_STRING),
            openapi.Parameter('month', openapi.IN_QUERY, description="月份 (YYYY-MM)", type=openapi.TYPE_STRING),
            openapi.Parameter('department', openapi.IN_QUERY, description="部门", type=openapi.TYPE_STRING),
        ],
        responses={200: WorkHoursSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="创建工作小时记录（管理员）",
        request_body=WorkHoursCreateSerializer,
        responses={
            201: WorkHoursSerializer,
            400: "请求参数错误",
            403: "权限不足"
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
