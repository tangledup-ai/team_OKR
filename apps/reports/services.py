"""
Performance calculation services for OKR Performance System
"""
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Avg, Count, Sum, Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from typing import Dict, List, Optional

from .models import (
    PerformanceScore, WorkHours, MonthlyEvaluation, 
    PeerEvaluation, DepartmentReport
)
from apps.tasks.models import Task, TaskStatus, ScoreAllocation
from apps.reviews.models import Review, ReviewType
from apps.users.models import Department

User = get_user_model()


class PerformanceCalculationService:
    """绩效分值计算服务"""
    
    # 权重配置（根据设计文档）
    WEIGHTS = {
        'work_hours': Decimal('0.10'),           # 工作小时 10%
        'completion_rate': Decimal('0.15'),      # 完成任务比例 15%
        'avg_difficulty': Decimal('0.10'),       # 难度平均分 10%
        'revenue': Decimal('0.10'),              # 变现金额 10%
        'department_avg': Decimal('0.05'),       # 部门平均分 5%
        'task_rating': Decimal('0.10'),          # 任务评分 10%
        'culture_understanding': Decimal('0.05'), # 企业文化理解 5%
        'team_fit': Decimal('0.03'),             # 团队契合度 3%
        'monthly_growth': Decimal('0.03'),       # 本月成长 3%
        'biggest_contribution': Decimal('0.04'), # 本月最大贡献 4%
        'peer_evaluation': Decimal('0.05'),      # 他人评价 5%
        'admin_final': Decimal('0.15'),          # 管理员最终评分 15%
    }
    
    # 标准化参数
    WORK_HOURS_FULL_SCORE = Decimal('300.00')  # 300小时满分
    POSTPONE_PENALTY = Decimal('0.800')         # 推迟任务惩罚系数
    
    @classmethod
    def calculate_user_performance(cls, user: User, month: date) -> PerformanceScore:
        """
        计算用户月度绩效分值
        
        Args:
            user: 用户对象
            month: 计算月份
            
        Returns:
            PerformanceScore: 绩效分值对象
        """
        # 获取或创建绩效分值记录
        performance_score, created = PerformanceScore.objects.get_or_create(
            user=user,
            month=month,
            defaults=cls._get_default_performance_data(user, month)
        )
        
        # 计算各维度分值
        cls._calculate_work_hours_score(performance_score, user, month)
        cls._calculate_completion_rate_score(performance_score, user, month)
        cls._calculate_difficulty_score(performance_score, user, month)
        cls._calculate_revenue_score(performance_score, user, month)
        cls._calculate_department_avg_score(performance_score, user, month)
        cls._calculate_task_rating_score(performance_score, user, month)
        cls._calculate_monthly_evaluation_scores(performance_score, user, month)
        cls._calculate_peer_evaluation_score(performance_score, user, month)
        cls._calculate_admin_final_score(performance_score, user, month)
        
        # 计算最终分值
        cls._calculate_final_score(performance_score)
        
        # 保存结果
        performance_score.save()
        
        return performance_score
    
    @classmethod
    def calculate_all_users_performance(cls, month: date) -> List[PerformanceScore]:
        """
        计算所有活跃用户的月度绩效分值
        
        Args:
            month: 计算月份
            
        Returns:
            List[PerformanceScore]: 所有用户的绩效分值列表
        """
        active_users = User.objects.filter(is_active=True)
        performance_scores = []
        
        for user in active_users:
            performance_score = cls.calculate_user_performance(user, month)
            performance_scores.append(performance_score)
        
        # 计算排名
        cls._calculate_rankings(month)
        
        return performance_scores
    
    @classmethod
    def _get_default_performance_data(cls, user: User, month: date) -> Dict:
        """获取默认绩效数据"""
        return {
            'work_hours': Decimal('0.00'),
            'work_hours_score': Decimal('0.00'),
            'completion_rate': Decimal('0.00'),
            'completion_rate_score': Decimal('0.00'),
            'avg_difficulty_score': Decimal('0.00'),
            'total_revenue': Decimal('0.00'),
            'revenue_score': Decimal('0.00'),
            'department_avg_score': Decimal('0.00'),
            'task_rating_score': Decimal('0.00'),
            'culture_understanding_score': Decimal('0.00'),
            'team_fit_score': Decimal('0.00'),
            'monthly_growth_score': Decimal('0.00'),
            'biggest_contribution_score': Decimal('0.00'),
            'peer_evaluation_score': Decimal('0.00'),
            'admin_final_score': Decimal('0.00'),
            'final_score': Decimal('0.00'),
            'rank': 0
        }
    
    @classmethod
    def _calculate_work_hours_score(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算工作小时分值"""
        work_hours_record = WorkHours.objects.filter(user=user, month=month).first()
        
        if work_hours_record:
            work_hours = work_hours_record.hours
        else:
            work_hours = Decimal('0.00')
        
        # 标准化工作小时：min(工作小时 / 300 × 10, 10)
        work_hours_score = cls._normalize_work_hours(work_hours)
        
        performance_score.work_hours = work_hours
        performance_score.work_hours_score = work_hours_score
    
    @classmethod
    def _normalize_work_hours(cls, hours: Decimal) -> Decimal:
        """
        标准化工作小时
        
        Args:
            hours: 工作小时数
            
        Returns:
            Decimal: 标准化分数 (0-10)
        """
        if hours <= 0:
            return Decimal('0.00')
        
        normalized = (hours / cls.WORK_HOURS_FULL_SCORE * Decimal('10.00'))
        return min(normalized, Decimal('10.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @classmethod
    def _calculate_completion_rate_score(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算完成任务比例分值"""
        # 获取该月份分配给用户的所有任务
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1)
        
        # 查询该月份的任务（基于任务创建时间或完成时间）
        user_tasks = Task.objects.filter(
            Q(owner=user) | Q(collaborators=user),
            Q(created_at__gte=month_start, created_at__lt=month_end) |
            Q(completed_at__gte=month_start, completed_at__lt=month_end)
        ).distinct()
        
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter(status=TaskStatus.COMPLETED).count()
        
        if total_tasks > 0:
            completion_rate = Decimal(str(completed_tasks)) / Decimal(str(total_tasks))
        else:
            completion_rate = Decimal('0.00')
        
        # 标准化完成任务比例：完成率 × 10
        completion_rate_score = cls._normalize_completion_rate(completion_rate)
        
        performance_score.completion_rate = completion_rate
        performance_score.completion_rate_score = completion_rate_score
    
    @classmethod
    def _normalize_completion_rate(cls, rate: Decimal) -> Decimal:
        """
        标准化完成任务比例
        
        Args:
            rate: 完成率 (0-1)
            
        Returns:
            Decimal: 标准化分数 (0-10)
        """
        return (rate * Decimal('10.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @classmethod
    def _calculate_difficulty_score(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算难度平均分"""
        # 获取该月份用户完成的任务
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1)
        
        completed_tasks = Task.objects.filter(
            Q(owner=user) | Q(collaborators=user),
            status=TaskStatus.COMPLETED,
            completed_at__gte=month_start,
            completed_at__lt=month_end
        ).distinct()
        
        if completed_tasks.exists():
            avg_difficulty = completed_tasks.aggregate(
                avg=Avg('difficulty_score')
            )['avg']
            avg_difficulty_score = Decimal(str(avg_difficulty)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            avg_difficulty_score = Decimal('0.00')
        
        performance_score.avg_difficulty_score = avg_difficulty_score
    
    @classmethod
    def _calculate_revenue_score(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算变现金额分值"""
        # 获取该月份用户完成的任务的变现金额总和
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1)
        
        completed_tasks = Task.objects.filter(
            Q(owner=user) | Q(collaborators=user),
            status=TaskStatus.COMPLETED,
            completed_at__gte=month_start,
            completed_at__lt=month_end
        ).distinct()
        
        total_revenue = completed_tasks.aggregate(
            total=Sum('revenue_amount')
        )['total'] or Decimal('0.00')
        
        # 标准化变现金额
        revenue_score = cls._normalize_revenue(total_revenue)
        
        performance_score.total_revenue = total_revenue
        performance_score.revenue_score = revenue_score
    
    @classmethod
    def _normalize_revenue(cls, revenue: Decimal) -> Decimal:
        """
        标准化变现金额
        
        Args:
            revenue: 变现金额
            
        Returns:
            Decimal: 标准化分数 (0-10)
        """
        if revenue <= 0:
            return Decimal('0.00')
        
        # 简化的标准化方法：使用对数缩放
        # 这里可以根据实际业务情况调整标准化方法
        # 暂时使用线性映射，假设10万为满分
        max_revenue = Decimal('100000.00')  # 10万
        normalized = (revenue / max_revenue * Decimal('10.00'))
        return min(normalized, Decimal('10.00')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @classmethod
    def _calculate_department_avg_score(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算部门平均分"""
        # 获取部门所有成员的OKR分值总和
        department_users = User.objects.filter(
            department=user.department,
            is_active=True
        )
        
        # 计算部门OKR总分（所有成员完成任务的累积分值）
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1)
        
        department_okr_score = Decimal('0.00')
        
        for dept_user in department_users:
            # 获取该用户该月份的分值分配
            user_allocations = ScoreAllocation.objects.filter(
                user=dept_user,
                distribution__calculated_at__gte=month_start,
                distribution__calculated_at__lt=month_end
            )
            user_total = user_allocations.aggregate(
                total=Sum('adjusted_score')
            )['total'] or Decimal('0.00')
            department_okr_score += user_total
        
        # 计算部门平均分
        member_count = department_users.count()
        if member_count > 0:
            department_avg_score = (department_okr_score / member_count).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        else:
            department_avg_score = Decimal('0.00')
        
        performance_score.department_avg_score = department_avg_score
    
    @classmethod
    def _calculate_task_rating_score(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算任务评分"""
        # 获取该月份用户完成的任务的评分
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1)
        
        # 获取用户完成的任务
        completed_tasks = Task.objects.filter(
            Q(owner=user) | Q(collaborators=user),
            status=TaskStatus.COMPLETED,
            completed_at__gte=month_start,
            completed_at__lt=month_end
        ).distinct()
        
        # 计算所有任务评分的平均值
        task_reviews = Review.objects.filter(
            type=ReviewType.TASK,
            task__in=completed_tasks
        )
        
        if task_reviews.exists():
            avg_rating = task_reviews.aggregate(avg=Avg('rating'))['avg']
            task_rating_score = Decimal(str(avg_rating)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            task_rating_score = Decimal('0.00')
        
        performance_score.task_rating_score = task_rating_score
    
    @classmethod
    def _calculate_monthly_evaluation_scores(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算月度评价各维度分值"""
        monthly_evaluation = MonthlyEvaluation.objects.filter(
            user=user,
            month=month
        ).first()
        
        if monthly_evaluation:
            # 直接使用1-10的分值
            performance_score.culture_understanding_score = Decimal(str(monthly_evaluation.culture_understanding_score))
            performance_score.monthly_growth_score = Decimal(str(monthly_evaluation.monthly_growth_score))
            performance_score.biggest_contribution_score = Decimal(str(monthly_evaluation.biggest_contribution_score))
            
            # 计算团队契合度分值（基于排名）
            team_fit_score = cls._calculate_team_fit_score(monthly_evaluation)
            performance_score.team_fit_score = team_fit_score
        else:
            # 如果没有月度评价，设为0
            performance_score.culture_understanding_score = Decimal('0.00')
            performance_score.team_fit_score = Decimal('0.00')
            performance_score.monthly_growth_score = Decimal('0.00')
            performance_score.biggest_contribution_score = Decimal('0.00')
    
    @classmethod
    def _calculate_team_fit_score(cls, monthly_evaluation: MonthlyEvaluation) -> Decimal:
        """
        计算团队契合度分值（基于用户对其他员工的排名）
        
        Args:
            monthly_evaluation: 月度评价对象
            
        Returns:
            Decimal: 团队契合度分值 (0-10)
        """
        # 这里可以根据团队契合度排名计算分值
        # 暂时使用简化方法：基于排名位置计算
        team_fit_ranking = monthly_evaluation.team_fit_ranking
        
        if not team_fit_ranking or not isinstance(team_fit_ranking, list):
            return Decimal('5.00')  # 默认中等分值
        
        # 简化计算：排名越靠前分值越高
        total_members = len(team_fit_ranking)
        if total_members == 0:
            return Decimal('5.00')
        
        # 假设用户对团队的理解程度反映在排名的合理性上
        # 这里使用固定分值，实际可以根据更复杂的算法计算
        return Decimal('7.00')  # 暂时使用固定分值
    
    @classmethod
    def _calculate_peer_evaluation_score(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算他人评价综合分数"""
        # 获取该用户该月份收到的他人评价
        peer_evaluations = PeerEvaluation.objects.filter(
            monthly_evaluation__user=user,
            monthly_evaluation__month=month
        )
        
        if peer_evaluations.exists():
            # 计算评分和排名的综合分数
            avg_score = peer_evaluations.aggregate(avg=Avg('score'))['avg']
            avg_ranking = peer_evaluations.aggregate(avg=Avg('ranking'))['avg']
            
            # 综合计算：评分占70%，排名占30%（排名越小越好，需要转换）
            score_component = Decimal(str(avg_score)) * Decimal('0.70')
            
            # 排名转换：假设总人数为10，排名1最好(10分)，排名10最差(1分)
            total_members = User.objects.filter(is_active=True).count()
            ranking_score = max(Decimal('1.00'), 
                              Decimal(str(total_members + 1 - avg_ranking)))
            ranking_component = ranking_score * Decimal('0.30')
            
            peer_evaluation_score = (score_component + ranking_component).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        else:
            peer_evaluation_score = Decimal('0.00')
        
        performance_score.peer_evaluation_score = peer_evaluation_score
    
    @classmethod
    def _calculate_admin_final_score(cls, performance_score: PerformanceScore, user: User, month: date):
        """计算管理员最终评分"""
        monthly_evaluation = MonthlyEvaluation.objects.filter(
            user=user,
            month=month
        ).first()
        
        if monthly_evaluation and monthly_evaluation.admin_final_score is not None:
            performance_score.admin_final_score = Decimal(str(monthly_evaluation.admin_final_score))
        else:
            performance_score.admin_final_score = Decimal('0.00')
    
    @classmethod
    def _calculate_final_score(cls, performance_score: PerformanceScore):
        """计算最终分值（加权平均）"""
        final_score = (
            performance_score.work_hours_score * cls.WEIGHTS['work_hours'] +
            performance_score.completion_rate_score * cls.WEIGHTS['completion_rate'] +
            performance_score.avg_difficulty_score * cls.WEIGHTS['avg_difficulty'] +
            performance_score.revenue_score * cls.WEIGHTS['revenue'] +
            performance_score.department_avg_score * cls.WEIGHTS['department_avg'] +
            performance_score.task_rating_score * cls.WEIGHTS['task_rating'] +
            performance_score.culture_understanding_score * cls.WEIGHTS['culture_understanding'] +
            performance_score.team_fit_score * cls.WEIGHTS['team_fit'] +
            performance_score.monthly_growth_score * cls.WEIGHTS['monthly_growth'] +
            performance_score.biggest_contribution_score * cls.WEIGHTS['biggest_contribution'] +
            performance_score.peer_evaluation_score * cls.WEIGHTS['peer_evaluation'] +
            performance_score.admin_final_score * cls.WEIGHTS['admin_final']
        )
        
        # 确保分值在0-100范围内，保留两位小数
        final_score = max(Decimal('0.00'), min(final_score, Decimal('100.00')))
        performance_score.final_score = final_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @classmethod
    def _calculate_rankings(cls, month: date):
        """计算该月份所有用户的排名"""
        # 获取该月份所有绩效分值记录，按分值降序排列
        performance_scores = PerformanceScore.objects.filter(
            month=month
        ).order_by('-final_score', 'user__name')  # 分值相同时按姓名排序保证稳定性
        
        # 更新排名
        for index, score in enumerate(performance_scores, 1):
            score.rank = index
            score.save(update_fields=['rank'])
    
    @classmethod
    def recalculate_department_reports(cls, month: date):
        """重新计算部门报告"""
        from .models import MonthlyReport
        
        # 获取或创建月度报告
        monthly_report, created = MonthlyReport.objects.get_or_create(
            month=month
        )
        
        # 删除现有的部门报告
        DepartmentReport.objects.filter(monthly_report=monthly_report).delete()
        
        # 为每个部门创建报告
        for department_code, department_name in Department.choices:
            cls._create_department_report(monthly_report, department_code, month)
    
    @classmethod
    def _create_department_report(cls, monthly_report, department: str, month: date):
        """创建部门报告"""
        # 获取部门成员
        department_users = User.objects.filter(
            department=department,
            is_active=True
        )
        
        if not department_users.exists():
            return
        
        # 计算部门统计数据
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month.replace(year=month.year + 1, month=1, day=1)
        else:
            month_end = month.replace(month=month.month + 1, day=1)
        
        # 部门OKR总分
        total_okr_score = Decimal('0.00')
        completed_tasks_count = 0
        total_difficulty = Decimal('0.00')
        difficulty_count = 0
        
        for user in department_users:
            # 用户分值分配总和
            user_allocations = ScoreAllocation.objects.filter(
                user=user,
                distribution__calculated_at__gte=month_start,
                distribution__calculated_at__lt=month_end
            )
            user_total = user_allocations.aggregate(
                total=Sum('adjusted_score')
            )['total'] or Decimal('0.00')
            total_okr_score += user_total
            
            # 用户完成的任务
            user_completed_tasks = Task.objects.filter(
                Q(owner=user) | Q(collaborators=user),
                status=TaskStatus.COMPLETED,
                completed_at__gte=month_start,
                completed_at__lt=month_end
            ).distinct()
            
            completed_tasks_count += user_completed_tasks.count()
            
            # 累计难度分值
            for task in user_completed_tasks:
                total_difficulty += Decimal(str(task.difficulty_score))
                difficulty_count += 1
        
        # 计算平均值
        member_count = department_users.count()
        avg_score = (total_okr_score / member_count).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        ) if member_count > 0 else Decimal('0.00')
        
        avg_difficulty = (total_difficulty / difficulty_count).quantize(
            Decimal('0.01'), r