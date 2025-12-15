"""
Task-related business logic services
"""
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db import transaction
from .models import Task, ScoreDistribution, ScoreAllocation


class TaskScoreService:
    """任务分值计算服务"""
    
    # 推迟任务惩罚系数
    POSTPONED_PENALTY_COEFFICIENT = Decimal('0.800')
    NORMAL_COEFFICIENT = Decimal('1.000')
    
    # 分值分配比例
    OWNER_PERCENTAGE = Decimal('50.00')
    COLLABORATOR_PERCENTAGE = Decimal('50.00')
    SINGLE_OWNER_PERCENTAGE = Decimal('100.00')

    @classmethod
    @transaction.atomic
    def calculate_task_score_distribution(cls, task):
        """
        计算任务分值分配
        
        Args:
            task: Task实例
            
        Returns:
            ScoreDistribution实例
            
        Raises:
            ValueError: 如果任务未完成
        """
        if not task.is_completed():
            raise ValueError("只有已完成的任务才能计算分值分配")
        
        # 删除已存在的分值分配（如果有）
        ScoreDistribution.objects.filter(task=task).delete()
        
        # 计算惩罚系数（如果任务曾经被推迟过）
        penalty_coefficient = (
            cls.POSTPONED_PENALTY_COEFFICIENT 
            if task.was_ever_postponed() 
            else cls.NORMAL_COEFFICIENT
        )
        
        # 计算总分值（应用惩罚系数）
        base_score = Decimal(str(task.difficulty_score))
        total_score = cls._round_to_two_decimals(base_score * penalty_coefficient)
        
        # 创建分值分配记录
        distribution = ScoreDistribution.objects.create(
            task=task,
            total_score=total_score,
            penalty_coefficient=penalty_coefficient
        )
        
        # 计算个人分值分配
        cls._create_score_allocations(distribution, task, total_score)
        
        # 更新累积分值
        cls._update_cumulative_scores(distribution)
        
        return distribution

    @classmethod
    def _create_score_allocations(cls, distribution, task, total_score):
        """创建个人分值分配明细"""
        collaborators = list(task.collaborators.all())
        
        if not collaborators:
            # 单人任务：负责人获得100%分值
            ScoreAllocation.objects.create(
                distribution=distribution,
                user=task.owner,
                base_score=total_score,
                adjusted_score=total_score,
                percentage=cls.SINGLE_OWNER_PERCENTAGE
            )
        else:
            # 多人任务：负责人50%，协作者平分50%
            owner_score = cls._round_to_two_decimals(
                total_score * cls.OWNER_PERCENTAGE / 100
            )
            
            # 协作者总分值 = 总分值 - 负责人分值（确保分值守恒）
            collaborator_total = total_score - owner_score
            collaborator_score = cls._round_to_two_decimals(
                collaborator_total / len(collaborators)
            )
            
            # 创建负责人分值分配
            ScoreAllocation.objects.create(
                distribution=distribution,
                user=task.owner,
                base_score=owner_score,
                adjusted_score=owner_score,
                percentage=cls.OWNER_PERCENTAGE
            )
            
            # 创建协作者分值分配
            collaborator_percentage = cls._round_to_two_decimals(
                cls.COLLABORATOR_PERCENTAGE / len(collaborators)
            )
            
            for collaborator in collaborators:
                ScoreAllocation.objects.create(
                    distribution=distribution,
                    user=collaborator,
                    base_score=collaborator_score,
                    adjusted_score=collaborator_score,
                    percentage=collaborator_percentage
                )

    @classmethod
    def _update_cumulative_scores(cls, distribution):
        """更新所有参与者的累积分值"""
        # 这里可以实现累积分值更新逻辑
        # 目前先预留接口，后续可以扩展到用户模型或单独的累积分值模型
        pass

    @classmethod
    def _round_to_two_decimals(cls, value):
        """将数值四舍五入到两位小数"""
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    def get_user_monthly_score(cls, user, year, month):
        """获取用户某月的累积分值"""
        allocations = ScoreAllocation.objects.filter(
            user=user,
            distribution__calculated_at__year=year,
            distribution__calculated_at__month=month
        ).select_related('distribution__task')
        
        total_score = sum(allocation.adjusted_score for allocation in allocations)
        return cls._round_to_two_decimals(total_score)

    @classmethod
    def get_user_task_count(cls, user, year, month):
        """获取用户某月完成的任务数量"""
        return ScoreAllocation.objects.filter(
            user=user,
            distribution__calculated_at__year=year,
            distribution__calculated_at__month=month
        ).count()

    @classmethod
    def recalculate_task_score(cls, task):
        """重新计算任务分值分配"""
        return cls.calculate_task_score_distribution(task)