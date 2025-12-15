from django.contrib import admin
from .models import (
    MonthlyReport, DepartmentReport, WorkHours,
    PerformanceScore, MonthlyEvaluation, PeerEvaluation, AdminEvaluationHistory
)


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = ('month', 'generated_at')
    ordering = ('-month',)


@admin.register(DepartmentReport)
class DepartmentReportAdmin(admin.ModelAdmin):
    list_display = ('monthly_report', 'department', 'total_okr_score', 'member_count', 'avg_score')
    list_filter = ('department',)
    ordering = ('-monthly_report__month',)


@admin.register(WorkHours)
class WorkHoursAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'hours', 'recorded_by', 'created_at')
    list_filter = ('month',)
    search_fields = ('user__name',)
    ordering = ('-month', 'user__name')


@admin.register(PerformanceScore)
class PerformanceScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'final_score', 'rank', 'calculated_at')
    list_filter = ('month',)
    search_fields = ('user__name',)
    ordering = ('-month', 'rank')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'month', 'final_score', 'rank')
        }),
        ('基础维度', {
            'fields': (
                'work_hours', 'work_hours_score',
                'completion_rate', 'completion_rate_score',
                'avg_difficulty_score', 'total_revenue', 'revenue_score',
                'department_avg_score'
            )
        }),
        ('评价维度', {
            'fields': (
                'task_rating_score', 'culture_understanding_score',
                'team_fit_score', 'monthly_growth_score',
                'biggest_contribution_score', 'peer_evaluation_score',
                'admin_final_score'
            )
        }),
    )
    
    readonly_fields = ('calculated_at',)


@admin.register(MonthlyEvaluation)
class MonthlyEvaluationAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'culture_understanding_score', 'admin_final_score', 'created_at')
    list_filter = ('month',)
    search_fields = ('user__name',)
    ordering = ('-month', 'user__name')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'month')
        }),
        ('企业文化理解', {
            'fields': ('culture_understanding_score', 'culture_understanding_text', 'culture_understanding_option')
        }),
        ('团队契合度', {
            'fields': ('team_fit_option', 'team_fit_text', 'team_fit_ranking')
        }),
        ('本月成长', {
            'fields': ('monthly_growth_score', 'monthly_growth_text', 'monthly_growth_option')
        }),
        ('本月最大贡献', {
            'fields': ('biggest_contribution_score', 'biggest_contribution_text', 'biggest_contribution_option')
        }),
        ('管理员评价', {
            'fields': ('admin_final_score', 'admin_final_comment', 'admin_evaluated_by', 'admin_evaluated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'admin_evaluated_at')


@admin.register(PeerEvaluation)
class PeerEvaluationAdmin(admin.ModelAdmin):
    list_display = ('evaluator', 'get_evaluatee', 'score', 'ranking', 'is_anonymous', 'created_at')
    list_filter = ('is_anonymous', 'score')
    search_fields = ('evaluator__name', 'monthly_evaluation__user__name')
    ordering = ('-created_at',)
    
    def get_evaluatee(self, obj):
        return obj.monthly_evaluation.user.name
    get_evaluatee.short_description = '被评价人'


@admin.register(AdminEvaluationHistory)
class AdminEvaluationHistoryAdmin(admin.ModelAdmin):
    list_display = ('admin_user', 'get_evaluatee', 'action_type', 'previous_score', 'new_score', 'created_at')
    list_filter = ('action_type', 'created_at', 'admin_user')
    search_fields = ('admin_user__name', 'monthly_evaluation__user__name')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    
    def get_evaluatee(self, obj):
        """获取被评价人"""
        return obj.monthly_evaluation.user.name
    get_evaluatee.short_description = '被评价人'
    
    def has_add_permission(self, request):
        """禁止手动添加历史记录"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """禁止修改历史记录"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """禁止删除历史记录"""
        return False
