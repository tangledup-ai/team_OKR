"""
Task views for OKR Performance System
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Task, TaskStatus, ScoreDistribution, ScoreAllocation
from .serializers import (
    TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer, TaskListSerializer,
    TaskStatusUpdateSerializer, ScoreDistributionSerializer, ScoreDistributionSummarySerializer,
    ScoreAllocationSerializer
)
from .services import TaskScoreService


class TaskViewSet(viewsets.ModelViewSet):
    """任务管理ViewSet"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'owner', 'difficulty_score']
    
    def get_queryset(self):
        """获取当前用户可见的任务"""
        user = self.request.user
        # 用户可以看到自己作为负责人或协作者的任务
        return Task.objects.filter(
            Q(owner=user) | Q(collaborators=user)
        ).distinct().select_related('owner', 'created_by').prefetch_related('collaborators')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        elif self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    @swagger_auto_schema(
        operation_description="创建新任务",
        request_body=TaskCreateSerializer,
        responses={
            201: TaskSerializer,
            400: "验证错误"
        }
    )
    def create(self, request, *args, **kwargs):
        """创建任务"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        
        # 返回完整的任务信息
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="获取任务列表",
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="按状态过滤任务",
                type=openapi.TYPE_STRING,
                enum=[choice[0] for choice in TaskStatus.choices]
            ),
            openapi.Parameter(
                'owner',
                openapi.IN_QUERY,
                description="按负责人过滤任务",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            ),
            openapi.Parameter(
                'difficulty_score',
                openapi.IN_QUERY,
                description="按难度分值过滤任务",
                type=openapi.TYPE_INTEGER
            ),
        ],
        responses={200: TaskListSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """获取任务列表（支持按状态过滤）"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="获取任务详情",
        responses={
            200: TaskSerializer,
            404: "任务不存在"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取任务详情"""
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="更新任务",
        request_body=TaskUpdateSerializer,
        responses={
            200: TaskSerializer,
            400: "验证错误",
            403: "权限不足",
            404: "任务不存在"
        }
    )
    def update(self, request, *args, **kwargs):
        """更新任务"""
        task = self.get_object()
        
        # 检查权限：只有负责人或协作者可以修改任务
        user = request.user
        if not (task.owner == user or user in task.collaborators.all()):
            return Response(
                {'detail': '只有任务负责人或协作者可以修改任务'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(task, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        
        # 返回完整的任务信息
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data)
    
    @swagger_auto_schema(
        operation_description="部分更新任务",
        request_body=TaskUpdateSerializer,
        responses={
            200: TaskSerializer,
            400: "验证错误",
            403: "权限不足",
            404: "任务不存在"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """部分更新任务"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="按状态分组获取任务",
        responses={200: openapi.Response(
            description="按状态分组的任务",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'todo': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'in_progress': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'completed': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    'postponed': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                }
            )
        )}
    )
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """按状态分组获取任务"""
        queryset = self.get_queryset()
        
        # 按状态分组
        grouped_tasks = {
            'todo': [],
            'in_progress': [],
            'completed': [],
            'postponed': []
        }
        
        for task in queryset:
            status_key = task.status
            if status_key in grouped_tasks:
                grouped_tasks[status_key].append(TaskListSerializer(task).data)
        
        return Response(grouped_tasks)
    
    @swagger_auto_schema(
        operation_description="获取用户的任务统计",
        responses={200: openapi.Response(
            description="任务统计信息",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'total_tasks': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'owned_tasks': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'collaborated_tasks': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'completed_tasks': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'in_progress_tasks': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'todo_tasks': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'postponed_tasks': openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            )
        )}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取用户的任务统计"""
        user = request.user
        queryset = self.get_queryset()
        
        # 计算统计数据
        stats = {
            'total_tasks': queryset.count(),
            'owned_tasks': queryset.filter(owner=user).count(),
            'collaborated_tasks': queryset.filter(collaborators=user).exclude(owner=user).count(),
            'completed_tasks': queryset.filter(status=TaskStatus.COMPLETED).count(),
            'in_progress_tasks': queryset.filter(status=TaskStatus.IN_PROGRESS).count(),
            'todo_tasks': queryset.filter(status=TaskStatus.TODO).count(),
            'postponed_tasks': queryset.filter(status=TaskStatus.POSTPONED).count(),
        }
        
        return Response(stats)
    
    @swagger_auto_schema(
        operation_description="更新任务状态",
        request_body=TaskStatusUpdateSerializer,
        responses={
            200: TaskSerializer,
            400: "验证错误",
            403: "权限不足",
            404: "任务不存在"
        }
    )
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """更新任务状态"""
        task = self.get_object()
        user = request.user
        
        # 检查权限：只有负责人或协作者可以修改任务状态
        if not (task.owner == user or user in task.collaborators.all()):
            return Response(
                {'detail': '只有任务负责人或协作者可以修改任务状态'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TaskStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        postpone_reason = serializer.validated_data.get('postpone_reason', '')
        
        # 记录状态转换时间戳
        now = timezone.now()
        
        if new_status == TaskStatus.IN_PROGRESS and task.status != TaskStatus.IN_PROGRESS:
            task.started_at = now
        elif new_status == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
            task.completed_at = now
        elif new_status == TaskStatus.POSTPONED and task.status != TaskStatus.POSTPONED:
            task.postponed_at = now
            task.postpone_reason = postpone_reason
        
        # 更新状态
        task.status = new_status
        
        # 如果不是推迟状态，清空推迟原因
        if new_status != TaskStatus.POSTPONED:
            task.postpone_reason = ''
        
        task.save()
        
        # 如果任务状态变为完成，自动计算分值分配
        if new_status == TaskStatus.COMPLETED:
            try:
                TaskScoreService.calculate_task_score_distribution(task)
            except Exception as e:
                # 记录错误但不影响状态更新
                pass
        
        # 返回更新后的任务信息
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data)

    @swagger_auto_schema(
        operation_description="计算任务分值分配",
        responses={
            200: ScoreDistributionSerializer,
            400: "任务未完成或其他错误",
            403: "权限不足",
            404: "任务不存在"
        }
    )
    @action(detail=True, methods=['post'])
    def calculate_score(self, request, pk=None):
        """计算任务分值分配"""
        task = self.get_object()
        user = request.user
        
        # 检查权限：只有负责人或协作者可以计算分值
        if not (task.owner == user or user in task.collaborators.all()):
            return Response(
                {'detail': '只有任务负责人或协作者可以计算分值分配'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            distribution = TaskScoreService.calculate_task_score_distribution(task)
            serializer = ScoreDistributionSerializer(distribution)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="获取任务分值分配",
        responses={
            200: ScoreDistributionSerializer,
            404: "任务不存在或未计算分值分配"
        }
    )
    @action(detail=True, methods=['get'])
    def score_distribution(self, request, pk=None):
        """获取任务分值分配"""
        task = self.get_object()
        
        try:
            distribution = task.score_distribution
            serializer = ScoreDistributionSerializer(distribution)
            return Response(serializer.data)
        except ScoreDistribution.DoesNotExist:
            return Response(
                {'detail': '该任务尚未计算分值分配'},
                status=status.HTTP_404_NOT_FOUND
            )


class ScoreDistributionViewSet(viewsets.ReadOnlyModelViewSet):
    """分值分配ViewSet（只读）"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['penalty_coefficient']
    
    def get_queryset(self):
        """获取当前用户相关的分值分配"""
        user = self.request.user
        # 用户可以看到自己参与的任务的分值分配
        return ScoreDistribution.objects.filter(
            Q(task__owner=user) | Q(task__collaborators=user)
        ).distinct().select_related('task').prefetch_related('allocations__user')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return ScoreDistributionSummarySerializer
        return ScoreDistributionSerializer
    
    @swagger_auto_schema(
        operation_description="获取分值分配列表",
        responses={200: ScoreDistributionSummarySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """获取分值分配列表"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="获取分值分配详情",
        responses={
            200: ScoreDistributionSerializer,
            404: "分值分配不存在"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取分值分配详情"""
        return super().retrieve(request, *args, **kwargs)


class ScoreAllocationViewSet(viewsets.ReadOnlyModelViewSet):
    """分值分配明细ViewSet（只读）"""
    permission_classes = [IsAuthenticated]
    serializer_class = ScoreAllocationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user']
    
    def get_queryset(self):
        """获取当前用户的分值分配明细"""
        user = self.request.user
        return ScoreAllocation.objects.filter(user=user).select_related(
            'distribution__task', 'user'
        ).order_by('-distribution__calculated_at')
    
    @swagger_auto_schema(
        operation_description="获取用户分值分配明细列表",
        responses={200: ScoreAllocationSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """获取用户分值分配明细列表"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="获取用户月度分值统计",
        manual_parameters=[
            openapi.Parameter(
                'year',
                openapi.IN_QUERY,
                description="年份",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'month',
                openapi.IN_QUERY,
                description="月份",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ],
        responses={200: openapi.Response(
            description="月度分值统计",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'year': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'month': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'total_score': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'task_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'allocations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                }
            )
        )}
    )
    @action(detail=False, methods=['get'])
    def monthly_stats(self, request):
        """获取用户月度分值统计"""
        user = request.user
        now = timezone.now()
        
        # 获取查询参数
        year = int(request.query_params.get('year', now.year))
        month = int(request.query_params.get('month', now.month))
        
        # 获取该月的分值分配
        allocations = ScoreAllocation.objects.filter(
            user=user,
            distribution__calculated_at__year=year,
            distribution__calculated_at__month=month
        ).select_related('distribution__task')
        
        # 计算统计数据
        total_score = TaskScoreService.get_user_monthly_score(user, year, month)
        task_count = TaskScoreService.get_user_task_count(user, year, month)
        
        # 序列化分配明细
        allocation_data = ScoreAllocationSerializer(allocations, many=True).data
        
        return Response({
            'year': year,
            'month': month,
            'total_score': str(total_score),
            'task_count': task_count,
            'allocations': allocation_data
        })
