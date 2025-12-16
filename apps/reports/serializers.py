"""
Report serializers for OKR Performance System
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import (
    MonthlyEvaluation, PeerEvaluation, MonthlyReport, 
    DepartmentReport, WorkHours, PerformanceScore, AdminEvaluationHistory
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """用户基础信息序列化器"""
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'department']


class MonthlyEvaluationSerializer(serializers.ModelSerializer):
    """月度综合评价序列化器"""
    user = UserBasicSerializer(read_only=True)
    peer_evaluations = serializers.SerializerMethodField()
    
    class Meta:
        model = MonthlyEvaluation
        fields = [
            'id', 'user', 'month',
            'culture_understanding_score', 'culture_understanding_text', 'culture_understanding_option',
            'team_fit_option', 'team_fit_text', 'team_fit_ranking',
            'monthly_growth_score', 'monthly_growth_text', 'monthly_growth_option',
            'biggest_contribution_score', 'biggest_contribution_text', 'biggest_contribution_option',
            'admin_final_score', 'admin_final_comment', 'admin_evaluated_by', 'admin_evaluated_at',
            'peer_evaluations', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'admin_evaluated_by', 'admin_evaluated_at', 'created_at', 'updated_at']
    
    def get_peer_evaluations(self, obj):
        """获取他人评价列表"""
        peer_evaluations = obj.peer_evaluations.all()
        return PeerEvaluationSerializer(peer_evaluations, many=True, context=self.context).data


class SelfEvaluationCreateSerializer(serializers.ModelSerializer):
    """自我评价创建序列化器"""
    class Meta:
        model = MonthlyEvaluation
        fields = [
            'month',
            'culture_understanding_score', 'culture_understanding_text', 'culture_understanding_option',
            'team_fit_option', 'team_fit_text', 'team_fit_ranking',
            'monthly_growth_score', 'monthly_growth_text', 'monthly_growth_option',
            'biggest_contribution_score', 'biggest_contribution_text', 'biggest_contribution_option'
        ]
    
    def validate_culture_understanding_score(self, value):
        """验证企业文化理解分值"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("企业文化理解分值必须在1到10之间")
        return value
    
    def validate_monthly_growth_score(self, value):
        """验证本月成长分值"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("本月成长分值必须在1到10之间")
        return value
    
    def validate_biggest_contribution_score(self, value):
        """验证本月最大贡献分值"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("本月最大贡献分值必须在1到10之间")
        return value
    
    def validate_team_fit_ranking(self, value):
        """验证团队契合度排名"""
        if not isinstance(value, list):
            raise serializers.ValidationError("团队契合度排名必须是列表格式")
        
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("用户未认证")
        
        # 获取除当前用户外的所有团队成员
        other_users = User.objects.filter(is_active=True).exclude(id=request.user.id)
        other_user_ids = [str(user.id) for user in other_users]
        
        # 验证排名列表包含所有其他成员且无重复
        if len(value) != len(other_user_ids):
            raise serializers.ValidationError(f"排名列表必须包含除自己外的所有{len(other_user_ids)}名团队成员")
        
        # 验证所有ID都是有效的用户ID
        for user_id in value:
            if str(user_id) not in other_user_ids:
                raise serializers.ValidationError(f"无效的用户ID: {user_id}")
        
        # 验证无重复
        if len(set(value)) != len(value):
            raise serializers.ValidationError("排名列表中不能有重复的用户")
        
        return value
    
    def validate(self, data):
        """验证整体数据"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("用户未认证")
        
        # 检查是否已经提交过该月度的自我评价
        existing_evaluation = MonthlyEvaluation.objects.filter(
            user=request.user,
            month=data['month']
        ).first()
        
        if existing_evaluation and not self.instance:
            raise serializers.ValidationError("您已经提交过该月度的自我评价")
        
        return data
    
    def create(self, validated_data):
        """创建自我评价"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PeerEvaluationSerializer(serializers.ModelSerializer):
    """他人评价序列化器"""
    evaluator = UserBasicSerializer(read_only=True)
    evaluator_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PeerEvaluation
        fields = [
            'id', 'monthly_evaluation', 'evaluator', 'evaluator_name',
            'score', 'ranking', 'comment', 'is_anonymous', 'created_at'
        ]
        read_only_fields = ['id', 'evaluator', 'created_at']
    
    def get_evaluator_name(self, obj):
        """获取评价人姓名，如果是匿名评价则返回'匿名'"""
        if obj.is_anonymous:
            # 检查当前用户是否为管理员
            request = self.context.get('request')
            if request and request.user.is_authenticated and request.user.role == 'admin':
                return obj.evaluator.name
            return '匿名'
        return obj.evaluator.name


class PeerEvaluationCreateSerializer(serializers.ModelSerializer):
    """他人评价创建序列化器"""
    evaluee_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = PeerEvaluation
        fields = ['evaluee_id', 'score', 'ranking', 'comment', 'is_anonymous']
    
    def validate_score(self, value):
        """验证评分范围"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError("评分必须在1到10之间")
        return value
    
    def validate_ranking(self, value):
        """验证排名"""
        if value < 1:
            raise serializers.ValidationError("排名必须大于0")
        return value
    
    def validate_evaluee_id(self, value):
        """验证被评价人"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("用户未认证")
        
        # 不能评价自己
        if str(value) == str(request.user.id):
            raise serializers.ValidationError("不能评价自己")
        
        # 验证被评价人存在
        try:
            evaluee = User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("被评价人不存在")
        
        return value
    
    def validate(self, data):
        """验证整体数据"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("用户未认证")
        
        # 获取月份参数
        month = self.context.get('month')
        if not month:
            raise serializers.ValidationError("必须指定评价月份")
        
        # 获取或创建被评价人的月度评价记录
        evaluee = User.objects.get(id=data['evaluee_id'])
        monthly_evaluation, created = MonthlyEvaluation.objects.get_or_create(
            user=evaluee,
            month=month,
            defaults={
                'culture_understanding_score': 5,
                'culture_understanding_text': '',
                'culture_understanding_option': '',
                'team_fit_option': '',
                'team_fit_text': '',
                'team_fit_ranking': [],
                'monthly_growth_score': 5,
                'monthly_growth_text': '',
                'monthly_growth_option': '',
                'biggest_contribution_score': 5,
                'biggest_contribution_text': '',
                'biggest_contribution_option': ''
            }
        )
        
        # 检查是否已经评价过该用户的该月度
        existing_evaluation = PeerEvaluation.objects.filter(
            monthly_evaluation=monthly_evaluation,
            evaluator=request.user
        ).first()
        
        if existing_evaluation and not self.instance:
            raise serializers.ValidationError("您已经对该用户的该月度进行过评价")
        
        data['monthly_evaluation'] = monthly_evaluation
        return data
    
    def create(self, validated_data):
        """创建他人评价"""
        validated_data['evaluator'] = self.context['request'].user
        # 移除evaluee_id，因为我们已经设置了monthly_evaluation
        validated_data.pop('evaluee_id', None)
        return super().create(validated_data)


class AdminFinalEvaluationSerializer(serializers.ModelSerializer):
    """管理员最终评价序列化器"""
    class Meta:
        model = MonthlyEvaluation
        fields = ['admin_final_score', 'admin_final_comment']
    
    def validate_admin_final_score(self, value):
        """验证管理员最终评分"""
        if value is not None and not (1 <= value <= 10):
            raise serializers.ValidationError("管理员最终评分必须在1到10之间")
        return value
    
    def validate(self, data):
        """验证管理员权限"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("用户未认证")
        
        if not (request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'admin'):
            raise serializers.ValidationError("只有管理员才能提交最终评价")
        
        return data
    
    def update(self, instance, validated_data):
        """更新管理员最终评价"""
        from django.utils import timezone
        
        # 记录修改前的值
        previous_score = instance.admin_final_score
        previous_comment = instance.admin_final_comment
        
        # 获取新的值
        new_score = validated_data.get('admin_final_score')
        new_comment = validated_data.get('admin_final_comment', '')
        
        # 设置管理员信息
        validated_data['admin_evaluated_by'] = self.context['request'].user
        validated_data['admin_evaluated_at'] = timezone.now()
        
        # 更新实例
        updated_instance = super().update(instance, validated_data)
        
        # 创建历史记录
        action_type = 'create' if previous_score is None else 'update'
        AdminEvaluationHistory.objects.create(
            monthly_evaluation=updated_instance,
            admin_user=self.context['request'].user,
            previous_score=previous_score,
            new_score=new_score,
            previous_comment=previous_comment,
            new_comment=new_comment,
            action_type=action_type
        )
        
        return updated_instance


class MonthlyEvaluationSummarySerializer(serializers.Serializer):
    """月度评价汇总序列化器"""
    user = UserBasicSerializer()
    month = serializers.DateField()
    self_evaluation_completed = serializers.BooleanField()
    peer_evaluation_count = serializers.IntegerField()
    admin_evaluation_completed = serializers.BooleanField()
    average_peer_score = serializers.DecimalField(max_digits=4, decimal_places=2, allow_null=True)
    average_peer_ranking = serializers.DecimalField(max_digits=4, decimal_places=2, allow_null=True)


class WorkHoursSerializer(serializers.ModelSerializer):
    """工作小时序列化器"""
    user = UserBasicSerializer(read_only=True)
    recorded_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = WorkHours
        fields = ['id', 'user', 'month', 'hours', 'recorded_by', 'created_at']
        read_only_fields = ['id', 'recorded_by', 'created_at']
        ref_name = 'ReportsWorkHours'


class WorkHoursCreateSerializer(serializers.ModelSerializer):
    """工作小时创建序列化器"""
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = WorkHours
        fields = ['user_id', 'month', 'hours']
        ref_name = 'ReportsWorkHoursCreate'
    
    def validate_hours(self, value):
        """验证工作小时"""
        if value < 0:
            raise serializers.ValidationError("工作小时不能为负数")
        if value > 744:  # 31天 * 24小时
            raise serializers.ValidationError("工作小时不能超过744小时（31天*24小时）")
        return value
    
    def validate_user_id(self, value):
        """验证用户存在"""
        try:
            User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("用户不存在")
        return value
    
    def validate(self, data):
        """验证管理员权限和重复记录"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("用户未认证")
        
        if not (request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'admin'):
            raise serializers.ValidationError("只有管理员才能录入工作小时")
        
        # 检查是否已经存在该用户该月份的记录
        existing_record = WorkHours.objects.filter(
            user_id=data['user_id'],
            month=data['month']
        ).first()
        
        if existing_record and not self.instance:
            raise serializers.ValidationError("该用户该月份的工作小时已经存在")
        
        return data
    
    def create(self, validated_data):
        """创建工作小时记录"""
        user_id = validated_data.pop('user_id')
        validated_data['user_id'] = user_id
        validated_data['recorded_by'] = self.context['request'].user
        return super().create(validated_data)


class AdminEvaluationHistorySerializer(serializers.ModelSerializer):
    """管理员评价历史序列化器"""
    admin_user = UserBasicSerializer(read_only=True)
    evaluatee = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminEvaluationHistory
        fields = [
            'id', 'admin_user', 'evaluatee', 'previous_score', 'new_score',
            'previous_comment', 'new_comment', 'action_type', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_evaluatee(self, obj):
        """获取被评价人信息"""
        return UserBasicSerializer(obj.monthly_evaluation.user).data