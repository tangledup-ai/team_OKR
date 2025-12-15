"""
Review views for OKR Performance System
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count, Q
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Review, ReviewType
from .serializers import (
    ReviewSerializer, TaskReviewCreateSerializer, MonthlyReviewCreateSerializer,
    TaskReviewSummarySerializer
)
from apps.tasks.models import Task


class ReviewViewSet(viewsets.ModelViewSet):
    """评价视图集"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取查询集"""
        queryset = Review.objects.all()
        
        # 过滤参数
        review_type = self.request.query_params.get('type')
        task_id = self.request.query_params.get('task')
        reviewee_id = self.request.query_params.get('reviewee')
        month = self.request.query_params.get('month')
        
        if review_type:
            queryset = queryset.filter(type=review_type)
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        if reviewee_id:
            queryset = queryset.filter(reviewee_id=reviewee_id)
        if month:
            queryset = queryset.filter(month=month)
        
        return queryset.select_related('reviewer', 'reviewee', 'task').order_by('-created_at')
    
    @swagger_auto_schema(
        method='post',
        operation_description="提交任务评价",
        request_body=TaskReviewCreateSerializer,
        responses={
            201: ReviewSerializer,
            400: "验证错误"
        }
    )
    @action(detail=False, methods=['post'], url_path='task-review')
    def submit_task_review(self, request):
        """提交任务评价"""
        serializer = TaskReviewCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            with transaction.atomic():
                review = serializer.save()
                
                # 重新计算任务的评分调整系数
                self._update_task_score_adjustment(review.task)
                
                return Response(
                    ReviewSerializer(review, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='post',
        operation_description="提交月度评价",
        request_body=MonthlyReviewCreateSerializer,
        responses={
            201: ReviewSerializer,
            400: "验证错误"
        }
    )
    @action(detail=False, methods=['post'], url_path='monthly-review')
    def submit_monthly_review(self, request):
        """提交月度评价"""
        serializer = MonthlyReviewCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            review = serializer.save()
            return Response(
                ReviewSerializer(review, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        method='get',
        operation_description="获取任务的所有评价",
        manual_parameters=[
            openapi.Parameter(
                'task_id',
                openapi.IN_PATH,
                description="任务ID",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            )
        ],
        responses={
            200: ReviewSerializer(many=True),
            404: "任务不存在"
        }
    )
    @action(detail=False, methods=['get'], url_path='task-reviews/(?P<task_id>[^/.]+)')
    def list_task_reviews(self, request, task_id=None):
        """获取任务的所有评价"""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {'error': '任务不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reviews = Review.objects.filter(
            type=ReviewType.TASK,
            task=task
        ).select_related('reviewer').order_by('-created_at')
        
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='monthly-reviews')
    def list_monthly_reviews(self, request):
        """获取月度评价列表"""
        month = request.query_params.get('month')
        reviewee_id = request.query_params.get('reviewee')
        
        queryset = Review.objects.filter(type=ReviewType.MONTHLY)
        
        if month:
            queryset = queryset.filter(month=month)
        if reviewee_id:
            queryset = queryset.filter(reviewee_id=reviewee_id)
        
        reviews = queryset.select_related('reviewer', 'reviewee').order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='task-summary/(?P<task_id>[^/.]+)')
    def get_task_review_summary(self, request, task_id=None):
        """获取任务评价汇总信息"""
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response(
                {'error': '任务不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 获取任务的所有评价
        reviews = Review.objects.filter(type=ReviewType.TASK, task=task)
        
        if not reviews.exists():
            return Response({
                'task_id': task.id,
                'task_title': task.title,
                'average_rating': 0,
                'review_count': 0,
                'admin_review_count': 0,
                'member_review_count': 0,
                'adjustment_factor': Decimal('0.700')
            })
        
        # 计算统计信息
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_count=Count('id')
        )
        
        # 分别统计管理员和普通成员的评价
        admin_reviews = reviews.filter(reviewer__role='admin')
        member_reviews = reviews.filter(reviewer__role='member')
        
        admin_count = admin_reviews.count()
        member_count = member_reviews.count()
        
        # 计算加权平均评分（管理员评分权重更高）
        weighted_average = self._calculate_weighted_average_rating(task)
        
        # 计算调整系数
        adjustment_factor = self._calculate_adjustment_factor(weighted_average)
        
        summary_data = {
            'task_id': task.id,
            'task_title': task.title,
            'average_rating': weighted_average,
            'review_count': stats['total_count'],
            'admin_review_count': admin_count,
            'member_review_count': member_count,
            'adjustment_factor': adjustment_factor
        }
        
        serializer = TaskReviewSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-reviews')
    def get_my_reviews(self, request):
        """获取当前用户的评价记录"""
        reviews = Review.objects.filter(
            reviewer=request.user
        ).select_related('reviewee', 'task').order_by('-created_at')
        
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='received-reviews')
    def get_received_reviews(self, request):
        """获取当前用户收到的评价"""
        reviews = Review.objects.filter(
            Q(reviewee=request.user) | Q(task__owner=request.user) | Q(task__collaborators=request.user)
        ).distinct().select_related('reviewer', 'task').order_by('-created_at')
        
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    def _calculate_weighted_average_rating(self, task):
        """计算任务的加权平均评分（管理员评分权重更高）"""
        admin_reviews = Review.objects.filter(
            type=ReviewType.TASK,
            task=task,
            reviewer__role='admin'
        )
        member_reviews = Review.objects.filter(
            type=ReviewType.TASK,
            task=task,
            reviewer__role='member'
        )
        
        admin_stats = admin_reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        member_stats = member_reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        
        admin_avg = admin_stats['avg_rating'] or 0
        member_avg = member_stats['avg_rating'] or 0
        admin_count = admin_stats['count'] or 0
        member_count = member_stats['count'] or 0
        
        if admin_count == 0 and member_count == 0:
            return Decimal('0.00')
        
        # 管理员评分权重为2，普通成员权重为1
        admin_weight = 2
        member_weight = 1
        
        total_weighted_score = (
            Decimal(str(admin_avg)) * admin_count * admin_weight +
            Decimal(str(member_avg)) * member_count * member_weight
        )
        total_weight = admin_count * admin_weight + member_count * member_weight
        
        if total_weight == 0:
            return Decimal('0.00')
        
        weighted_average = (total_weighted_score / total_weight).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return weighted_average
    
    def _calculate_adjustment_factor(self, weighted_average_rating):
        """计算任务评分调整系数"""
        if weighted_average_rating == 0:
            return Decimal('0.700')  # 没有评分时使用基础系数0.7
        
        # 调整系数 = (平均评分 / 10) * 0.3 + 0.7
        rating_factor = (weighted_average_rating / Decimal('10')) * Decimal('0.3')
        adjustment_factor = rating_factor + Decimal('0.7')
        
        return adjustment_factor.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    
    def _update_task_score_adjustment(self, task):
        """更新任务的分值调整"""
        # 重新计算加权平均评分
        weighted_average = self._calculate_weighted_average_rating(task)
        
        # 计算新的调整系数
        adjustment_factor = self._calculate_adjustment_factor(weighted_average)
        
        # 更新任务的分值分配（如果存在）
        if hasattr(task, 'score_distribution'):
            distribution = task.score_distribution
            
            # 重新计算调整后的分值
            base_total_score = Decimal(str(task.difficulty_score)) * distribution.penalty_coefficient
            adjusted_total_score = (base_total_score * adjustment_factor).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            # 更新分值分配
            distribution.total_score = adjusted_total_score
            distribution.save()
            
            # 重新分配个人分值
            self._redistribute_individual_scores(distribution, adjusted_total_score)
    
    def _redistribute_individual_scores(self, distribution, new_total_score):
        """重新分配个人分值"""
        allocations = distribution.allocations.all()
        
        for allocation in allocations:
            # 按比例重新计算个人分值
            new_score = (new_total_score * allocation.percentage / Decimal('100')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            allocation.adjusted_score = new_score
            allocation.save()
