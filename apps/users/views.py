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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserDetailSerializer,
    LoginSerializer
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
    
    @action(detail=True, methods=['get'])
    @swagger_auto_schema(
        operation_description="获取当前登录用户信息",
        responses={200: UserDetailSerializer}
    )
    def me(self, request):
        """获取当前登录用户信息"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
