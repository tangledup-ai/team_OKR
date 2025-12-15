"""
Review serializers for OKR Performance System
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Review, ReviewType
from apps.tasks.models import Task

User = get_user_model()


class ReviewerSerializer(serializers.ModelSerializer):
    """评价人序列化器（用于显示评价人信息）"""
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'department']


class ReviewSerializer(serializers.ModelSerializer):
    """评价序列化器"""
    reviewer = ReviewerSerializer(read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'type', 'task', 'reviewee', 'reviewer', 'reviewer_name',
            'rating', 'comment', 'is_anonymous', 'month', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer', 'created_at']
    
    def get_reviewer_name(self, obj):
        """获取评价人姓名，如果是匿名评价则返回'匿名'"""
        if obj.is_anonymous:
            # 检查当前用户是否为管理员
            request = self.context.get('request')
            if request and request.user.is_authenticated and request.user.role == 'admin':
                return obj.reviewer.name
            return '匿名'
        return obj.reviewer.name
    
    def validate_rating(self, value):
        """验证评分范围"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("评分必须在1到10之间")
        return value
    
    def validate(self, data):
        """验证评价数据"""
        # 验证任务评价的逻辑
        if data.get('type') == ReviewType.TASK:
            if not data.get('task'):
                raise serializers.ValidationError("任务评价必须指定任务")
            
            task = data['task']
            if not task.is_completed():
                raise serializers.ValidationError("只能对已完成的任务进行评价")
            
            # 检查是否已经评价过该任务
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                existing_review = Review.objects.filter(
                    type=ReviewType.TASK,
                    task=task,
                    reviewer=request.user
                ).first()
                
                if existing_review and not self.instance:
                    raise serializers.ValidationError("您已经对该任务进行过评价")
        
        # 验证月度评价的逻辑
        elif data.get('type') == ReviewType.MONTHLY:
            if not data.get('reviewee'):
                raise serializers.ValidationError("月度评价必须指定被评价人")
            if not data.get('month'):
                raise serializers.ValidationError("月度评价必须指定月份")
        
        return data


class TaskReviewCreateSerializer(serializers.ModelSerializer):
    """任务评价创建序列化器"""
    class Meta:
        model = Review
        fields = ['task', 'rating', 'comment', 'is_anonymous']
    
    def validate_rating(self, value):
        """验证评分范围"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("评分必须在1到10之间")
        return value
    
    def validate_task(self, value):
        """验证任务状态"""
        if not value.is_completed():
            raise serializers.ValidationError("只能对已完成的任务进行评价")
        return value
    
    def validate(self, data):
        """验证是否已经评价过该任务"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            existing_review = Review.objects.filter(
                type=ReviewType.TASK,
                task=data['task'],
                reviewer=request.user
            ).first()
            
            if existing_review:
                raise serializers.ValidationError("您已经对该任务进行过评价")
        
        return data
    
    def create(self, validated_data):
        """创建任务评价"""
        validated_data['type'] = ReviewType.TASK
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)


class MonthlyReviewCreateSerializer(serializers.ModelSerializer):
    """月度评价创建序列化器"""
    class Meta:
        model = Review
        fields = ['reviewee', 'rating', 'comment', 'is_anonymous', 'month']
    
    def validate_rating(self, value):
        """验证评分范围"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("评分必须在1到10之间")
        return value
    
    def validate_reviewee(self, value):
        """验证被评价人不能是自己"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and value == request.user:
            raise serializers.ValidationError("不能评价自己")
        return value
    
    def validate(self, data):
        """验证是否已经评价过该用户的该月度"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            existing_review = Review.objects.filter(
                type=ReviewType.MONTHLY,
                reviewee=data['reviewee'],
                reviewer=request.user,
                month=data['month']
            ).first()
            
            if existing_review:
                raise serializers.ValidationError("您已经对该用户的该月度进行过评价")
        
        return data
    
    def create(self, validated_data):
        """创建月度评价"""
        validated_data['type'] = ReviewType.MONTHLY
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)


class TaskReviewSummarySerializer(serializers.Serializer):
    """任务评价汇总序列化器"""
    task_id = serializers.UUIDField()
    task_title = serializers.CharField()
    average_rating = serializers.DecimalField(max_digits=4, decimal_places=2)
    review_count = serializers.IntegerField()
    admin_review_count = serializers.IntegerField()
    member_review_count = serializers.IntegerField()
    adjustment_factor = serializers.DecimalField(max_digits=4, decimal_places=3)