"""
Report models for OKR Performance System
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import Department
import uuid


class MonthlyReport(models.Model):
    """月度报告模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    month = models.DateField(unique=True, verbose_name='月份')
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')

    class Meta:
        db_table = 'monthly_reports'
        verbose_name = '月度报告'
        verbose_name_plural = '月度报告'

    def __str__(self):
        return f"{self.month.strftime('%Y年%m月')}报告"


class DepartmentReport(models.Model):
    """部门报告模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    monthly_report = models.ForeignKey(
        MonthlyReport,
        on_delete=models.CASCADE,
        related_name='department_reports',
        verbose_name='月度报告'
    )
    department = models.CharField(
        max_length=20,
        choices=Department.choices,
        verbose_name='部门'
    )
    total_okr_score = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='部门OKR总分'
    )
    member_count = models.IntegerField(verbose_name='成员数量')
    avg_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='平均分'
    )
    completed_tasks = models.IntegerField(verbose_name='完成任务数')
    avg_difficulty = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='平均难度'
    )

    class Meta:
        db_table = 'department_reports'
        verbose_name = '部门报告'
        verbose_name_plural = '部门报告'

    def __str__(self):
        return f"{self.get_department_display()} - {self.monthly_report.month.strftime('%Y年%m月')}"


class WorkHours(models.Model):
    """工作小时记录"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='work_hours',
        verbose_name='用户'
    )
    month = models.DateField(verbose_name='月份')
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='工作小时'
    )
    recorded_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_work_hours',
        verbose_name='记录人'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'work_hours'
        verbose_name = '工作小时'
        verbose_name_plural = '工作小时'
        unique_together = [['user', 'month']]
        ordering = ['-month', 'user__name']

    def __str__(self):
        return f"{self.user.name} - {self.month.strftime('%Y年%m月')} - {self.hours}小时"


class PerformanceScore(models.Model):
    """绩效分值模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='performance_scores',
        verbose_name='用户'
    )
    month = models.DateField(verbose_name='月份')

    # 基础维度
    work_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='工作小时'
    )
    work_hours_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='工作小时分'
    )
    completion_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='完成任务比例'
    )
    completion_rate_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='完成任务比例分'
    )
    avg_difficulty_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='难度平均分'
    )
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='变现金额总和'
    )
    revenue_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='变现金额分'
    )
    department_avg_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='部门平均分'
    )

    # 任务评分
    task_rating_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='任务评分'
    )

    # 月度评价维度
    culture_understanding_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='企业文化理解分'
    )
    team_fit_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='团队契合度分'
    )
    monthly_growth_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='本月成长分'
    )
    biggest_contribution_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='本月最大贡献分'
    )
    peer_evaluation_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name='他人评价分'
    )
    admin_final_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='管理员最终评分'
    )

    # 最终分值
    final_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='最终分值'
    )
    rank = models.IntegerField(verbose_name='排名')
    calculated_at = models.DateTimeField(auto_now_add=True, verbose_name='计算时间')

    class Meta:
        db_table = 'performance_scores'
        verbose_name = '绩效分值'
        verbose_name_plural = '绩效分值'
        unique_together = [['user', 'month']]
        indexes = [
            models.Index(fields=['month', 'final_score']),
        ]

    def __str__(self):
        return f"{self.user.name} - {self.month.strftime('%Y年%m月')} - {self.final_score}分"


class MonthlyEvaluation(models.Model):
    """月度综合评价模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='monthly_evaluations',
        verbose_name='被评价人'
    )
    month = models.DateField(verbose_name='月份')

    # 自我评价维度
    culture_understanding_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='企业文化理解分值'
    )
    culture_understanding_text = models.TextField(verbose_name='企业文化理解文字')
    culture_understanding_option = models.CharField(
        max_length=100,
        verbose_name='企业文化理解选项'
    )

    team_fit_option = models.CharField(
        max_length=100,
        verbose_name='团队契合度选项'
    )
    team_fit_text = models.TextField(verbose_name='团队契合度文字')
    team_fit_ranking = models.JSONField(
        verbose_name='团队契合度-其他员工排名',
        help_text='存储用户对其他员工的排名列表'
    )

    monthly_growth_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='本月成长分值'
    )
    monthly_growth_text = models.TextField(verbose_name='本月成长文字')
    monthly_growth_option = models.CharField(
        max_length=100,
        verbose_name='本月成长选项'
    )

    biggest_contribution_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='本月最大贡献分值'
    )
    biggest_contribution_text = models.TextField(verbose_name='本月最大贡献文字')
    biggest_contribution_option = models.CharField(
        max_length=100,
        verbose_name='本月最大贡献选项'
    )

    # 管理员最终评价
    admin_final_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='管理员最终评分'
    )
    admin_final_comment = models.TextField(
        blank=True,
        verbose_name='管理员最终评价'
    )
    admin_evaluated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_evaluations',
        verbose_name='评价管理员'
    )
    admin_evaluated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='管理员评价时间'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'monthly_evaluations'
        verbose_name = '月度综合评价'
        verbose_name_plural = '月度综合评价'
        unique_together = [['user', 'month']]

    def __str__(self):
        return f"{self.user.name} - {self.month.strftime('%Y年%m月')}评价"


class PeerEvaluation(models.Model):
    """他人评价模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    monthly_evaluation = models.ForeignKey(
        MonthlyEvaluation,
        on_delete=models.CASCADE,
        related_name='peer_evaluations',
        verbose_name='月度评价'
    )
    evaluator = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='given_peer_evaluations',
        verbose_name='评价人'
    )
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='评分'
    )
    ranking = models.IntegerField(
        verbose_name='排名',
        help_text='评价人给被评价人的排名'
    )
    comment = models.TextField(verbose_name='评价文字')
    is_anonymous = models.BooleanField(default=False, verbose_name='是否匿名')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'peer_evaluations'
        verbose_name = '他人评价'
        verbose_name_plural = '他人评价'
        unique_together = [['monthly_evaluation', 'evaluator']]

    def __str__(self):
        return f"{self.evaluator.name} 评价 {self.monthly_evaluation.user.name}"


class AdminEvaluationHistory(models.Model):
    """管理员评价修改历史记录"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    monthly_evaluation = models.ForeignKey(
        MonthlyEvaluation,
        on_delete=models.CASCADE,
        related_name='admin_history',
        verbose_name='月度评价'
    )
    admin_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='admin_evaluation_history',
        verbose_name='管理员'
    )
    previous_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='修改前评分'
    )
    new_score = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='修改后评分'
    )
    previous_comment = models.TextField(
        blank=True,
        verbose_name='修改前评价'
    )
    new_comment = models.TextField(
        blank=True,
        verbose_name='修改后评价'
    )
    action_type = models.CharField(
        max_length=20,
        choices=[
            ('create', '创建'),
            ('update', '更新'),
            ('delete', '删除')
        ],
        verbose_name='操作类型'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')
    
    class Meta:
        db_table = 'admin_evaluation_history'
        verbose_name = '管理员评价历史'
        verbose_name_plural = '管理员评价历史'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.admin_user.name} {self.get_action_type_display()} {self.monthly_evaluation.user.name}的评价"
