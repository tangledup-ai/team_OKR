"""
Task models for OKR Performance System
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
import uuid


class TaskStatus(models.TextChoices):
    TODO = 'todo', '未完成'
    IN_PROGRESS = 'in_progress', '进行中'
    COMPLETED = 'completed', '完成'
    POSTPONED = 'postponed', '推迟'


class Task(models.Model):
    """任务模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name='任务标题')
    description = models.TextField(verbose_name='任务描述')
    difficulty_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='难度分值'
    )
    revenue_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='变现金额'
    )
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
        verbose_name='状态'
    )
    owner = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='owned_tasks',
        verbose_name='负责人'
    )
    collaborators = models.ManyToManyField(
        'users.User',
        related_name='collaborated_tasks',
        blank=True,
        verbose_name='协作者'
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    postponed_at = models.DateTimeField(null=True, blank=True, verbose_name='推迟时间')
    postpone_reason = models.TextField(blank=True, verbose_name='推迟原因')

    class Meta:
        db_table = 'tasks'
        verbose_name = '任务'
        verbose_name_plural = '任务'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['owner']),
            models.Index(fields=['completed_at']),
        ]

    def __str__(self):
        return self.title

    def get_all_participants(self):
        """获取任务的所有参与者（负责人+协作者）"""
        participants = [self.owner]
        participants.extend(self.collaborators.all())
        return participants

    def is_completed(self):
        """检查任务是否已完成"""
        return self.status == TaskStatus.COMPLETED

    def is_postponed(self):
        """检查任务是否被推迟"""
        return self.status == TaskStatus.POSTPONED

    def was_ever_postponed(self):
        """检查任务是否曾经被推迟过"""
        return self.postponed_at is not None


class ScoreDistribution(models.Model):
    """分值分配模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(
        Task,
        on_delete=models.CASCADE,
        related_name='score_distribution',
        verbose_name='任务'
    )
    total_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='总分值'
    )
    penalty_coefficient = models.DecimalField(
        max_digits=4,
        decimal_places=3,
        default=Decimal('1.000'),
        verbose_name='惩罚系数'
    )
    calculated_at = models.DateTimeField(auto_now_add=True, verbose_name='计算时间')
    
    class Meta:
        db_table = 'score_distributions'
        verbose_name = '分值分配'
        verbose_name_plural = '分值分配'

    def __str__(self):
        return f"{self.task.title} - 总分值: {self.total_score}"

    @classmethod
    def calculate_and_create(cls, task):
        """计算并创建任务分值分配"""
        if not task.is_completed():
            raise ValueError("只有已完成的任务才能计算分值分配")
        
        # 删除已存在的分值分配（如果有）
        cls.objects.filter(task=task).delete()
        
        # 计算惩罚系数（如果任务曾经被推迟过）
        penalty_coefficient = Decimal('0.800') if task.was_ever_postponed() else Decimal('1.000')
        
        # 计算总分值（应用惩罚系数）
        base_score = Decimal(str(task.difficulty_score))
        total_score = (base_score * penalty_coefficient).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # 创建分值分配记录
        distribution = cls.objects.create(
            task=task,
            total_score=total_score,
            penalty_coefficient=penalty_coefficient
        )
        
        # 计算个人分值分配
        participants = task.get_all_participants()
        collaborators = list(task.collaborators.all())
        
        if not collaborators:
            # 单人任务：负责人获得100%分值
            ScoreAllocation.objects.create(
                distribution=distribution,
                user=task.owner,
                base_score=total_score,
                adjusted_score=total_score,
                percentage=Decimal('100.00')
            )
        else:
            # 多人任务：负责人50%，协作者平分50%
            owner_score = (total_score * Decimal('0.50')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            collaborator_total = total_score - owner_score
            collaborator_score = (collaborator_total / len(collaborators)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # 创建负责人分值分配
            ScoreAllocation.objects.create(
                distribution=distribution,
                user=task.owner,
                base_score=owner_score,
                adjusted_score=owner_score,
                percentage=Decimal('50.00')
            )
            
            # 创建协作者分值分配
            collaborator_percentage = (Decimal('50.00') / len(collaborators)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            for collaborator in collaborators:
                ScoreAllocation.objects.create(
                    distribution=distribution,
                    user=collaborator,
                    base_score=collaborator_score,
                    adjusted_score=collaborator_score,
                    percentage=collaborator_percentage
                )
        
        # 更新用户累积分值
        distribution.update_cumulative_scores()
        
        return distribution
    
    def update_cumulative_scores(self):
        """更新所有参与者的累积分值"""
        from apps.users.models import User
        
        for allocation in self.allocations.all():
            user = allocation.user
            # 这里可以添加累积分值字段到User模型，或者创建单独的累积分值模型
            # 暂时先计算当前月份的累积分值
            current_month_allocations = ScoreAllocation.objects.filter(
                user=user,
                distribution__calculated_at__year=timezone.now().year,
                distribution__calculated_at__month=timezone.now().month
            )
            cumulative_score = sum(alloc.adjusted_score for alloc in current_month_allocations)
            
            # 这里可以保存到用户的累积分值字段或单独的模型中
            # 目前先在内存中计算，后续可以扩展


class ScoreAllocation(models.Model):
    """个人分值分配明细"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    distribution = models.ForeignKey(
        ScoreDistribution,
        on_delete=models.CASCADE,
        related_name='allocations',
        verbose_name='分值分配'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name='用户'
    )
    base_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='基础分值'
    )
    adjusted_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='调整后分值'
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='分配比例'
    )
    
    class Meta:
        db_table = 'score_allocations'
        verbose_name = '分值分配明细'
        verbose_name_plural = '分值分配明细'
        unique_together = [['distribution', 'user']]

    def __str__(self):
        return f"{self.user.name} - {self.distribution.task.title}: {self.adjusted_score}分"
