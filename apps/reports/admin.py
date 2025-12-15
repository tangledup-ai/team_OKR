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
    """
    工作小时记录管理界面
    支持按用户、月份、部门过滤，支持批量录入
    """
    
    # 列表页面显示字段
    list_display = (
        'get_user_info',
        'get_month_display', 
        'hours',
        'get_department_display',
        'get_recorded_by_info',
        'created_at'
    )
    
    # 列表页面过滤器
    list_filter = (
        'month',
        'user__department',
        'recorded_by',
        'created_at'
    )
    
    # 搜索字段
    search_fields = ('user__name', 'user__email')
    
    # 排序
    ordering = ('-month', 'user__name')
    
    # 每页显示数量
    list_per_page = 50
    
    # 可编辑字段（在列表页面直接编辑）
    list_editable = ('hours',)
    
    # 详情页面字段分组
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'month', 'hours'),
            'description': '工作小时记录的基本信息'
        }),
        ('记录信息', {
            'fields': ('recorded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': '记录创建和修改信息'
        }),
    )
    
    # 只读字段
    readonly_fields = ('recorded_by', 'created_at', 'updated_at')
    
    # 自动填充字段
    autocomplete_fields = ['user']
    
    # 自定义显示方法
    def get_user_info(self, obj):
        """显示用户信息，包含姓名和邮箱"""
        from django.utils.html import format_html
        return format_html(
            '<strong>{}</strong><br><small style="color: #6C757D;">{}</small>',
            obj.user.name,
            obj.user.email
        )
    get_user_info.short_description = '用户'
    get_user_info.admin_order_field = 'user__name'
    
    def get_month_display(self, obj):
        """显示月份，格式化显示"""
        from django.utils.html import format_html
        return format_html(
            '<span style="font-weight: bold; color: #007BFF;">{}</span>',
            obj.month.strftime('%Y年%m月')
        )
    get_month_display.short_description = '月份'
    get_month_display.admin_order_field = 'month'
    
    def get_department_display(self, obj):
        """显示部门信息，带颜色标识"""
        from django.utils.html import format_html
        colors = {
            'hardware': '#FF6B6B',  # 红色
            'software': '#4ECDC4',  # 青色  
            'marketing': '#45B7D1'  # 蓝色
        }
        color = colors.get(obj.user.department, '#6C757D')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.user.get_department_display()
        )
    get_department_display.short_description = '部门'
    get_department_display.admin_order_field = 'user__department'
    
    def get_recorded_by_info(self, obj):
        """显示记录人信息"""
        from django.utils.html import format_html
        if obj.recorded_by:
            return format_html(
                '<small>{}</small>',
                obj.recorded_by.name
            )
        return '-'
    get_recorded_by_info.short_description = '记录人'
    get_recorded_by_info.admin_order_field = 'recorded_by__name'
    
    # 自定义操作
    actions = ['export_work_hours', 'calculate_monthly_stats']
    
    def export_work_hours(self, request, queryset):
        """导出工作小时记录"""
        count = queryset.count()
        self.message_user(
            request, 
            f'已选择 {count} 条工作小时记录进行导出。（导出功能待实现）',
            level='info'
        )
    export_work_hours.short_description = "导出选中的工作小时记录"
    
    def calculate_monthly_stats(self, request, queryset):
        """计算月度统计"""
        from django.db.models import Sum, Avg, Count
        
        stats = queryset.aggregate(
            total_hours=Sum('hours'),
            avg_hours=Avg('hours'),
            record_count=Count('id')
        )
        
        self.message_user(
            request,
            f'统计结果：总工时 {stats["total_hours"]:.2f} 小时，'
            f'平均工时 {stats["avg_hours"]:.2f} 小时，'
            f'记录数量 {stats["record_count"]} 条',
            level='success'
        )
    calculate_monthly_stats.short_description = "计算选中记录的统计信息"
    
    def save_model(self, request, obj, form, change):
        """保存时自动设置记录人"""
        if not change:  # 新建记录
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
    
    # 权限控制
    def has_add_permission(self, request):
        """只有管理员可以添加工作小时记录"""
        return request.user.is_superuser or (
            hasattr(request.user, 'role') and request.user.role == 'admin'
        )
    
    def has_change_permission(self, request, obj=None):
        """只有管理员可以修改工作小时记录"""
        return request.user.is_superuser or (
            hasattr(request.user, 'role') and request.user.role == 'admin'
        )
    
    def has_delete_permission(self, request, obj=None):
        """只有管理员可以删除工作小时记录"""
        return request.user.is_superuser or (
            hasattr(request.user, 'role') and request.user.role == 'admin'
        )
    
    def get_queryset(self, request):
        """优化查询，预加载相关对象"""
        return super().get_queryset(request).select_related('user', 'recorded_by')


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
