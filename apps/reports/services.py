"""
Performance score calculation services for OKR Performance System
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db.models import Avg, Sum, Count, Q
from django.db import transaction
from django.utils import timezone

from .models import PerformanceScore, WorkHours, MonthlyEvaluation, PeerEvaluation
from apps.tasks.models import Task, TaskStatus, ScoreAllocation
from apps.reviews.models import Review, ReviewType
from apps.users.models import User, Department


class PerformanceScoreService:
    """绩效分值计算服务"""
    
    # 权重配置（总和为100%）
    WEIGHTS = {
        'work_hours': Decimal('0.10'),           # 工作小时 10%
        'completion_rate': Decimal('0.15'),      # 完成任务比例 15%
        'avg_difficulty': Decimal('0.10'),       # 难度平均分 10%
        'revenue': Decimal('0.10'),              # 变现金额 10%
        'department_avg': Decimal('0.05'),       # 部门平均分 5%
        'task_rating': Decimal('0.10'),          # 任务评分 10%
        'culture_understanding': Decimal('0.05'), # 企业文化理解 5%
        'team_fit': Decimal('0.05'),             # 团队契合度 5%
        'monthly_growth': Decimal('0.05'),       # 本月成长 5%
        'biggest_contribution': Decimal('0.05'), # 本月最大贡献 5%
        'peer_evaluation': Decimal('0.05'),      # 他人评价 5%
        'admin_final': Decimal('0.15'),          # 管理员最终评分 15%
    }
    
    # 标准化参数
    WORK_HOURS_FULL_SCORE = Decimal('300.00')  # 300小时满分
    MAX_SCORE = Decimal('10.00')                # 标准化后最大分值
    MIN_SCORE = Decimal('0.00')                 # 标准化后最小分值
    FINAL_SCORE_MAX = Decimal('100.00')         # 最终分值最大值
    FINAL_SCORE_MIN = Decimal('0.00')           # 最终分值最小值

    @classmethod
    @transaction.atomic
    def calculate_user_performance_score(cls, user, month):
        """
        计算用户月度绩效分值
        
        Args:
            user: User实例
            month: date对象，表示月份
            
        Returns:
            PerformanceScore实例
        """
        # 删除已存在的绩效分值记录
        PerformanceScore.objects.filter(user=user, month=month).delete()
        
        # 1. 计算基础维度
        work_hours, work_hours_score = cls._calculate_work_hours_score(user, month)
        completion_rate, completion_rate_score = cls._calculate_completion_rate_score(user, month)
        avg_difficulty_score = cls._calculate_avg_difficulty_score(user, month)
        total_revenue, revenue_score = cls._calculate_revenue_score(user, month)
        department_avg_score = cls._calculate_department_avg_score(user.department, month)
        
        # 2. 计算任务评分
        task_rating_score = cls._calculate_task_rating_score(user, month)
        
        # 3. 计算月度评价维度
        culture_understanding_score = cls._calculate_culture_understanding_score(user, month)
        team_fit_score = cls._calculate_team_fit_score(user, month)
        monthly_growth_score = cls._calculate_monthly_growth_score(user, month)
        biggest_contribution_score = cls._calculate_biggest_contribution_score(user, month)
        peer_evaluation_score = cls._calculate_peer_evaluation_score(user, month)
        admin_final_score = cls._get_admin_final_score(user, month)
        
        # 4. 计算加权平均最终分值
        final_score = cls._calculate_weighted_final_score(
            work_hours_score, completion_rate_score, avg_difficulty_score,
            revenue_score, department_avg_score, task_rating_score,
            culture_understanding_score, team_fit_score, monthly_growth_score,
            biggest_contribution_score, peer_evaluation_score, admin_final_score
        )
        
        # 5. 创建绩效分值记录
        performance_score = PerformanceScore.objects.create(
            user=user,
            month=month,
            work_hours=work_hours,
            work_hours_score=work_hours_score,
            completion_rate=completion_rate,
            completion_rate_score=completion_rate_score,
            avg_difficulty_score=avg_difficulty_score,
            total_revenue=total_revenue,
            revenue_score=revenue_score,
            department_avg_score=department_avg_score,
            task_rating_score=task_rating_score,
            culture_understanding_score=culture_understanding_score,
            team_fit_score=team_fit_score,
            monthly_growth_score=monthly_growth_score,
            biggest_contribution_score=biggest_contribution_score,
            peer_evaluation_score=peer_evaluation_score,
            admin_final_score=admin_final_score,
            final_score=final_score,
            rank=0  # 排名将在批量计算后更新
        )
        
        return performance_score

    @classmethod
    def _calculate_work_hours_score(cls, user, month):
        """计算工作小时标准化分数"""
        try:
            work_hours_record = WorkHours.objects.get(user=user, month=month)
            hours = work_hours_record.hours
        except WorkHours.DoesNotExist:
            hours = Decimal('0.00')
        
        # 标准化：min(工作小时 / 300 × 10, 10)
        normalized_score = min(
            (hours / cls.WORK_HOURS_FULL_SCORE) * cls.MAX_SCORE,
            cls.MAX_SCORE
        )
        
        return hours, cls._round_to_two_decimals(normalized_score)

    @classmethod
    def _calculate_completion_rate_score(cls, user, month):
        """计算完成任务比例标准化分数"""
        # 获取用户分配的所有任务（不限制创建时间）
        assigned_tasks = Task.objects.filter(
            Q(owner=user) | Q(collaborators=user)
        ).distinct()
        
        total_tasks = assigned_tasks.count()
        if total_tasks == 0:
            return Decimal('0.00'), Decimal('0.00')
        
        # 获取已完成的任务数
        completed_tasks = assigned_tasks.filter(status=TaskStatus.COMPLETED).count()
        
        # 计算完成率
        completion_rate = Decimal(str(completed_tasks)) / Decimal(str(total_tasks))
        
        # 标准化：完成率 × 10
        normalized_score = completion_rate * cls.MAX_SCORE
        
        return (
            cls._round_to_two_decimals(completion_rate * 100),  # 转换为百分比
            cls._round_to_two_decimals(normalized_score)
        )

    @classmethod
    def _calculate_avg_difficulty_score(cls, user, month):
        """计算难度平均分"""
        # 获取用户在该月完成的任务
        completed_tasks = Task.objects.filter(
            Q(owner=user) | Q(collaborators=user),
            status=TaskStatus.COMPLETED,
            completed_at__year=month.year,
            completed_at__month=month.month
        ).distinct()
        
        if not completed_tasks.exists():
            return Decimal('0.00')
        
        # 计算平均难度分值
        avg_difficulty = completed_tasks.aggregate(
            avg_difficulty=Avg('difficulty_score')
        )['avg_difficulty']
        
        return cls._round_to_two_decimals(Decimal(str(avg_difficulty or 0)))

    @classmethod
    def _calculate_revenue_score(cls, user, month):
        """计算变现金额标准化分数"""
        # 获取用户在该月完成的任务的变现金额总和
        completed_tasks = Task.objects.filter(
            Q(owner=user) | Q(collaborators=user),
            status=TaskStatus.COMPLETED,
            completed_at__year=month.year,
            completed_at__month=month.month
        ).distinct()
        
        total_revenue = completed_tasks.aggregate(
            total_revenue=Sum('revenue_amount')
        )['total_revenue'] or Decimal('0.00')
        
        # 变现金额标准化：这里使用简单的对数标准化
        # 可以根据实际业务需求调整标准化方法
        if total_revenue <= 0:
            normalized_score = Decimal('0.00')
        else:
            # 使用分段标准化：0-10000为0-5分，10000以上为5-10分
            if total_revenue <= 10000:
                normalized_score = (total_revenue / Decimal('10000')) * Decimal('5.00')
            else:
                # 超过10000的部分使用对数标准化
                import math
                log_factor = Decimal(str(math.log10(float(total_revenue / 10000))))
                normalized_score = Decimal('5.00') + min(log_factor * Decimal('2.50'), Decimal('5.00'))
            
            normalized_score = min(normalized_score, cls.MAX_SCORE)
        
        return total_revenue, cls._round_to_two_decimals(normalized_score)

    @classmethod
    def _calculate_department_avg_score(cls, department, month):
        """计算部门平均分"""
        # 获取部门所有成员在该月的累积分值
        department_users = User.objects.filter(department=department, is_active=True)
        
        if not department_users.exists():
            return Decimal('0.00')
        
        # 计算部门OKR总分值（所有成员的任务分值总和）
        total_department_score = Decimal('0.00')
        
        for user in department_users:
            # 获取用户在该月的任务分值
            user_allocations = ScoreAllocation.objects.filter(
                user=user,
                distribution__task__completed_at__year=month.year,
                distribution__task__completed_at__month=month.month
            )
            user_score = sum(allocation.adjusted_score for allocation in user_allocations)
            total_department_score += user_score
        
        # 部门平均分 = 部门OKR总分 / 部门成员数
        member_count = department_users.count()
        department_avg = total_department_score / Decimal(str(member_count))
        
        return cls._round_to_two_decimals(department_avg)

    @classmethod
    def _calculate_task_rating_score(cls, user, month):
        """计算任务评分标准化分数"""
        # 获取用户在该月完成的任务
        completed_tasks = Task.objects.filter(
            Q(owner=user) | Q(collaborators=user),
            status=TaskStatus.COMPLETED,
            completed_at__year=month.year,
            completed_at__month=month.month
        ).distinct()
        
        if not completed_tasks.exists():
            return Decimal('0.00')
        
        # 计算所有评分的总加权平均
        total_weighted_score = Decimal('0.00')
        total_weight = 0
        
        for task in completed_tasks:
            task_reviews = Review.objects.filter(
                type=ReviewType.TASK,
                task=task
            )
            
            if task_reviews.exists():
                # 计算每个任务的加权评分（管理员评分权重更高）
                admin_reviews = task_reviews.filter(reviewer__role='admin')
                member_reviews = task_reviews.filter(reviewer__role='member')
                
                admin_count = admin_reviews.count()
                member_count = member_reviews.count()
                
                # 累加所有评分的加权值
                for review in admin_reviews:
                    total_weighted_score += Decimal(str(review.rating)) * 2  # 管理员权重为2
                    total_weight += 2
                
                for review in member_reviews:
                    total_weighted_score += Decimal(str(review.rating)) * 1  # 普通成员权重为1
                    total_weight += 1
        
        if total_weight == 0:
            return Decimal('0.00')
        
        # 计算总体加权平均评分
        avg_task_rating = total_weighted_score / Decimal(str(total_weight))
        
        return cls._round_to_two_decimals(avg_task_rating)

    @classmethod
    def _calculate_culture_understanding_score(cls, user, month):
        """计算企业文化理解分数"""
        try:
            evaluation = MonthlyEvaluation.objects.get(user=user, month=month)
            return cls._round_to_two_decimals(Decimal(str(evaluation.culture_understanding_score)))
        except MonthlyEvaluation.DoesNotExist:
            return Decimal('0.00')

    @classmethod
    def _calculate_team_fit_score(cls, user, month):
        """计算团队契合度分数"""
        try:
            evaluation = MonthlyEvaluation.objects.get(user=user, month=month)
            # 团队契合度基于排名计算，这里简化为固定分值
            # 实际实现中可以根据排名位置计算分数
            return Decimal('5.00')  # 暂时使用固定值，后续可以根据排名算法优化
        except MonthlyEvaluation.DoesNotExist:
            return Decimal('0.00')

    @classmethod
    def _calculate_monthly_growth_score(cls, user, month):
        """计算本月成长分数"""
        try:
            evaluation = MonthlyEvaluation.objects.get(user=user, month=month)
            return cls._round_to_two_decimals(Decimal(str(evaluation.monthly_growth_score)))
        except MonthlyEvaluation.DoesNotExist:
            return Decimal('0.00')

    @classmethod
    def _calculate_biggest_contribution_score(cls, user, month):
        """计算本月最大贡献分数"""
        try:
            evaluation = MonthlyEvaluation.objects.get(user=user, month=month)
            return cls._round_to_two_decimals(Decimal(str(evaluation.biggest_contribution_score)))
        except MonthlyEvaluation.DoesNotExist:
            return Decimal('0.00')

    @classmethod
    def _calculate_peer_evaluation_score(cls, user, month):
        """计算他人评价综合分数"""
        try:
            evaluation = MonthlyEvaluation.objects.get(user=user, month=month)
            peer_evaluations = evaluation.peer_evaluations.all()
            
            if not peer_evaluations.exists():
                return Decimal('0.00')
            
            # 计算评分和排名的综合分数
            total_score = Decimal('0.00')
            total_ranking_score = Decimal('0.00')
            count = peer_evaluations.count()
            
            # 获取总用户数用于排名标准化
            total_users = User.objects.filter(is_active=True).count()
            
            for peer_eval in peer_evaluations:
                # 评分直接使用
                total_score += Decimal(str(peer_eval.score))
                
                # 排名转换为分数：排名越高分数越高
                # 排名分数 = (总人数 - 排名 + 1) / 总人数 * 10
                ranking_score = (
                    (Decimal(str(total_users)) - Decimal(str(peer_eval.ranking)) + 1) /
                    Decimal(str(total_users)) * cls.MAX_SCORE
                )
                total_ranking_score += ranking_score
            
            # 评分和排名各占50%权重
            avg_score = total_score / Decimal(str(count))
            avg_ranking_score = total_ranking_score / Decimal(str(count))
            
            final_peer_score = (avg_score + avg_ranking_score) / 2
            
            return cls._round_to_two_decimals(final_peer_score)
            
        except MonthlyEvaluation.DoesNotExist:
            return Decimal('0.00')

    @classmethod
    def _get_admin_final_score(cls, user, month):
        """获取管理员最终评分"""
        try:
            evaluation = MonthlyEvaluation.objects.get(user=user, month=month)
            if evaluation.admin_final_score is not None:
                return cls._round_to_two_decimals(Decimal(str(evaluation.admin_final_score)))
            return Decimal('0.00')
        except MonthlyEvaluation.DoesNotExist:
            return Decimal('0.00')

    @classmethod
    def _calculate_weighted_final_score(cls, work_hours_score, completion_rate_score,
                                      avg_difficulty_score, revenue_score, department_avg_score,
                                      task_rating_score, culture_understanding_score,
                                      team_fit_score, monthly_growth_score,
                                      biggest_contribution_score, peer_evaluation_score,
                                      admin_final_score):
        """计算加权平均最终分值"""
        
        # 计算加权总分
        weighted_sum = (
            work_hours_score * cls.WEIGHTS['work_hours'] +
            completion_rate_score * cls.WEIGHTS['completion_rate'] +
            avg_difficulty_score * cls.WEIGHTS['avg_difficulty'] +
            revenue_score * cls.WEIGHTS['revenue'] +
            department_avg_score * cls.WEIGHTS['department_avg'] +
            task_rating_score * cls.WEIGHTS['task_rating'] +
            culture_understanding_score * cls.WEIGHTS['culture_understanding'] +
            team_fit_score * cls.WEIGHTS['team_fit'] +
            monthly_growth_score * cls.WEIGHTS['monthly_growth'] +
            biggest_contribution_score * cls.WEIGHTS['biggest_contribution'] +
            peer_evaluation_score * cls.WEIGHTS['peer_evaluation'] +
            admin_final_score * cls.WEIGHTS['admin_final']
        )
        
        # 转换为0-100分制
        final_score = weighted_sum * 10
        
        # 确保分值在0-100范围内
        final_score = max(cls.FINAL_SCORE_MIN, min(final_score, cls.FINAL_SCORE_MAX))
        
        return cls._round_to_two_decimals(final_score)

    @classmethod
    def calculate_monthly_rankings(cls, month):
        """计算月度排名"""
        # 获取该月所有绩效分值记录
        performance_scores = PerformanceScore.objects.filter(month=month).order_by('-final_score', 'user__name')
        
        # 更新排名
        for rank, score in enumerate(performance_scores, 1):
            score.rank = rank
            score.save(update_fields=['rank'])
        
        return performance_scores

    @classmethod
    def batch_calculate_monthly_scores(cls, month):
        """批量计算月度绩效分值"""
        active_users = User.objects.filter(is_active=True)
        
        performance_scores = []
        for user in active_users:
            score = cls.calculate_user_performance_score(user, month)
            performance_scores.append(score)
        
        # 计算排名并返回更新后的记录
        updated_scores = cls.calculate_monthly_rankings(month)
        
        return updated_scores

    @classmethod
    def recalculate_user_score(cls, user, month):
        """重新计算用户绩效分值"""
        score = cls.calculate_user_performance_score(user, month)
        
        # 重新计算该月所有用户的排名
        cls.calculate_monthly_rankings(month)
        
        return score

    @classmethod
    def _round_to_two_decimals(cls, value):
        """将数值四舍五入到两位小数"""
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    def get_user_performance_summary(cls, user, month):
        """获取用户绩效分值汇总信息"""
        try:
            performance_score = PerformanceScore.objects.get(user=user, month=month)
            
            return {
                'user': user,
                'month': month,
                'final_score': performance_score.final_score,
                'rank': performance_score.rank,
                'dimensions': {
                    'work_hours': {
                        'raw_value': performance_score.work_hours,
                        'score': performance_score.work_hours_score,
                        'weight': cls.WEIGHTS['work_hours'] * 100
                    },
                    'completion_rate': {
                        'raw_value': performance_score.completion_rate,
                        'score': performance_score.completion_rate_score,
                        'weight': cls.WEIGHTS['completion_rate'] * 100
                    },
                    'avg_difficulty': {
                        'raw_value': performance_score.avg_difficulty_score,
                        'score': performance_score.avg_difficulty_score,
                        'weight': cls.WEIGHTS['avg_difficulty'] * 100
                    },
                    'revenue': {
                        'raw_value': performance_score.total_revenue,
                        'score': performance_score.revenue_score,
                        'weight': cls.WEIGHTS['revenue'] * 100
                    },
                    'department_avg': {
                        'raw_value': performance_score.department_avg_score,
                        'score': performance_score.department_avg_score,
                        'weight': cls.WEIGHTS['department_avg'] * 100
                    },
                    'task_rating': {
                        'raw_value': performance_score.task_rating_score,
                        'score': performance_score.task_rating_score,
                        'weight': cls.WEIGHTS['task_rating'] * 100
                    },
                    'culture_understanding': {
                        'raw_value': performance_score.culture_understanding_score,
                        'score': performance_score.culture_understanding_score,
                        'weight': cls.WEIGHTS['culture_understanding'] * 100
                    },
                    'team_fit': {
                        'raw_value': performance_score.team_fit_score,
                        'score': performance_score.team_fit_score,
                        'weight': cls.WEIGHTS['team_fit'] * 100
                    },
                    'monthly_growth': {
                        'raw_value': performance_score.monthly_growth_score,
                        'score': performance_score.monthly_growth_score,
                        'weight': cls.WEIGHTS['monthly_growth'] * 100
                    },
                    'biggest_contribution': {
                        'raw_value': performance_score.biggest_contribution_score,
                        'score': performance_score.biggest_contribution_score,
                        'weight': cls.WEIGHTS['biggest_contribution'] * 100
                    },
                    'peer_evaluation': {
                        'raw_value': performance_score.peer_evaluation_score,
                        'score': performance_score.peer_evaluation_score,
                        'weight': cls.WEIGHTS['peer_evaluation'] * 100
                    },
                    'admin_final': {
                        'raw_value': performance_score.admin_final_score,
                        'score': performance_score.admin_final_score,
                        'weight': cls.WEIGHTS['admin_final'] * 100
                    }
                },
                'calculated_at': performance_score.calculated_at
            }
            
        except PerformanceScore.DoesNotExist:
            return None

    @classmethod
    def get_department_performance_summary(cls, department, month):
        """获取部门绩效汇总信息"""
        department_users = User.objects.filter(department=department, is_active=True)
        performance_scores = PerformanceScore.objects.filter(
            user__in=department_users,
            month=month
        ).order_by('-final_score')
        
        if not performance_scores.exists():
            return None
        
        # 计算部门统计
        total_score = sum(score.final_score for score in performance_scores)
        avg_score = total_score / performance_scores.count()
        
        # 获取部门OKR总分
        department_okr_score = cls._calculate_department_okr_total(department, month)
        
        return {
            'department': department,
            'month': month,
            'member_count': performance_scores.count(),
            'avg_score': cls._round_to_two_decimals(avg_score),
            'total_okr_score': department_okr_score,
            'top_performer': performance_scores.first(),
            'performance_scores': performance_scores
        }

    @classmethod
    def _calculate_department_okr_total(cls, department, month):
        """计算部门OKR总分"""
        department_users = User.objects.filter(department=department, is_active=True)
        
        total_score = Decimal('0.00')
        for user in department_users:
            user_allocations = ScoreAllocation.objects.filter(
                user=user,
                distribution__task__completed_at__year=month.year,
                distribution__task__completed_at__month=month.month
            )
            user_score = sum(allocation.adjusted_score for allocation in user_allocations)
            total_score += user_score
        
        return cls._round_to_two_decimals(total_score)