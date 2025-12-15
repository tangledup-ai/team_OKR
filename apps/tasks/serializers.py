"""
Serializers for Task model
"""
from rest_framework import serializers
from .models import Task, TaskStatus, ScoreDistribution, ScoreAllocation
from apps.users.serializers import UserSerializer


class TaskSerializer(serializers.ModelSerializer):
    """任务序列化器"""
    owner = UserSerializer(read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'difficulty_score', 'revenue_amount',
            'status', 'owner', 'collaborators', 'created_by', 'created_at',
            'started_at', 'completed_at', 'postponed_at', 'postpone_reason'
        ]
        read_only_fields = [
            'id', 'created_at', 'started_at', 'completed_at', 'postponed_at'
        ]


class TaskCreateSerializer(serializers.ModelSerializer):
    """任务创建序列化器"""
    owner_id = serializers.UUIDField(write_only=True)
    collaborator_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'difficulty_score', 'revenue_amount',
            'owner_id', 'collaborator_ids'
        ]
    
    def validate_difficulty_score(self, value):
        """验证难度分值范围"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError('难度分值必须在1到10之间')
        return value
    
    def validate_revenue_amount(self, value):
        """验证变现金额非负"""
        if value < 0:
            raise serializers.ValidationError('变现金额不能为负数')
        return value
    
    def validate_owner_id(self, value):
        """验证负责人存在"""
        from apps.users.models import User
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('指定的负责人不存在')
        return value
    
    def validate_collaborator_ids(self, value):
        """验证协作者存在"""
        if not value:
            return value
        
        from apps.users.models import User
        existing_ids = set(User.objects.filter(id__in=value).values_list('id', flat=True))
        provided_ids = set(value)
        
        if existing_ids != provided_ids:
            missing_ids = provided_ids - existing_ids
            raise serializers.ValidationError(f'以下协作者不存在: {list(missing_ids)}')
        
        return value
    
    def create(self, validated_data):
        """创建任务"""
        owner_id = validated_data.pop('owner_id')
        collaborator_ids = validated_data.pop('collaborator_ids', [])
        
        # Set owner and created_by
        from apps.users.models import User
        owner = User.objects.get(id=owner_id)
        validated_data['owner'] = owner
        validated_data['created_by'] = self.context['request'].user
        
        # Create task
        task = Task.objects.create(**validated_data)
        
        # Add collaborators
        if collaborator_ids:
            collaborators = User.objects.filter(id__in=collaborator_ids)
            task.collaborators.set(collaborators)
        
        return task


class TaskUpdateSerializer(serializers.ModelSerializer):
    """任务更新序列化器"""
    collaborator_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'difficulty_score', 'revenue_amount',
            'collaborator_ids'
        ]
    
    def validate_difficulty_score(self, value):
        """验证难度分值范围"""
        if not (1 <= value <= 10):
            raise serializers.ValidationError('难度分值必须在1到10之间')
        return value
    
    def validate_revenue_amount(self, value):
        """验证变现金额非负"""
        if value < 0:
            raise serializers.ValidationError('变现金额不能为负数')
        return value
    
    def validate_collaborator_ids(self, value):
        """验证协作者存在"""
        if not value:
            return value
        
        from apps.users.models import User
        existing_ids = set(User.objects.filter(id__in=value).values_list('id', flat=True))
        provided_ids = set(value)
        
        if existing_ids != provided_ids:
            missing_ids = provided_ids - existing_ids
            raise serializers.ValidationError(f'以下协作者不存在: {list(missing_ids)}')
        
        return value
    
    def update(self, instance, validated_data):
        """更新任务"""
        collaborator_ids = validated_data.pop('collaborator_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update collaborators if provided
        if collaborator_ids is not None:
            if collaborator_ids:
                from apps.users.models import User
                collaborators = User.objects.filter(id__in=collaborator_ids)
                instance.collaborators.set(collaborators)
            else:
                instance.collaborators.clear()
        
        return instance


class TaskStatusUpdateSerializer(serializers.Serializer):
    """任务状态更新序列化器"""
    status = serializers.ChoiceField(choices=TaskStatus.choices)
    postpone_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """验证状态转换数据"""
        status = data.get('status')
        postpone_reason = data.get('postpone_reason', '')
        
        # 如果状态是推迟，必须提供推迟原因
        if status == TaskStatus.POSTPONED and not postpone_reason.strip():
            raise serializers.ValidationError({
                'postpone_reason': '将任务状态设置为推迟时必须提供推迟原因'
            })
        
        return data


class TaskListSerializer(serializers.ModelSerializer):
    """任务列表序列化器（简化版）"""
    owner_name = serializers.CharField(source='owner.name', read_only=True)
    collaborator_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'difficulty_score', 'revenue_amount', 'status',
            'owner_name', 'collaborator_count', 'created_at'
        ]
    
    def get_collaborator_count(self, obj):
        """获取协作者数量"""
        return obj.collaborators.count()


class ScoreAllocationSerializer(serializers.ModelSerializer):
    """分值分配明细序列化器"""
    user = UserSerializer(read_only=True)
    task_title = serializers.CharField(source='distribution.task.title', read_only=True)
    
    class Meta:
        model = ScoreAllocation
        fields = [
            'id', 'user', 'task_title', 'base_score', 'adjusted_score', 'percentage'
        ]


class ScoreDistributionSerializer(serializers.ModelSerializer):
    """分值分配序列化器"""
    task = TaskSerializer(read_only=True)
    allocations = ScoreAllocationSerializer(many=True, read_only=True)
    
    class Meta:
        model = ScoreDistribution
        fields = [
            'id', 'task', 'total_score', 'penalty_coefficient', 
            'calculated_at', 'allocations'
        ]


class ScoreDistributionSummarySerializer(serializers.ModelSerializer):
    """分值分配摘要序列化器（不包含详细分配信息）"""
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_id = serializers.UUIDField(source='task.id', read_only=True)
    allocation_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ScoreDistribution
        fields = [
            'id', 'task_id', 'task_title', 'total_score', 
            'penalty_coefficient', 'calculated_at', 'allocation_count'
        ]
    
    def get_allocation_count(self, obj):
        """获取分配明细数量"""
        return obj.allocations.count()