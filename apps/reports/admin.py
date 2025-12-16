from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Avg, Count
from apps.users.models import Department
from .models import (
    MonthlyReport, DepartmentReport, WorkHours,
    PerformanceScore, MonthlyEvaluation, PeerEvaluation, AdminEvaluationHistory
)


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    """
    月度报告管理界面
    支持查看和导出月度报告
    """
    
    list_display = (
        'get_month_display',
        'get_department_count',
        'get_total_members',
        'generated_at',
        'get_export_actions'
    )
    ordering = ('-month',)
    readonly_fields = ('generated_at',)
    
    fieldsets = (
        ('报告信息', {
            'fields': ('month', 'generated_at'),
            'description': '月度报告基本信息'
        }),
    )
    
    def get_month_display(self, obj):
        """显示月份，格式化显示"""
        return format_html(
            '<span style="font-weight: bold; color: #007BFF; font-size: 16px;">{}</span>',
            obj.month.strftime('%Y年%m月')
        )
    get_month_display.short_description = '报告月份'
    get_month_display.admin_order_field = 'month'
    
    def get_department_count(self, obj):
        """显示部门数量"""
        count = obj.department_reports.count()
        return format_html(
            '<span style="color: #28A745; font-weight: bold;">{} 个部门</span>',
            count
        )
    get_department_count.short_description = '部门数量'
    
    def get_total_members(self, obj):
        """显示总成员数"""
        from django.db.models import Sum
        total = obj.department_reports.aggregate(total=Sum('member_count'))['total'] or 0
        return format_html(
            '<span style="color: #007BFF; font-weight: bold;">{} 人</span>',
            total
        )
    get_total_members.short_description = '总成员数'
    
    def get_export_actions(self, obj):
        """显示导出操作链接"""
        return format_html(
            '<a href="#" onclick="alert(\'导出功能待实现\')" style="color: #17A2B8;">📊 导出Excel</a> | '
            '<a href="#" onclick="alert(\'导出功能待实现\')" style="color: #DC3545;">📄 导出PDF</a>'
        )
    get_export_actions.short_description = '导出操作'
    
    # 自定义操作
    actions = ['export_reports', 'regenerate_reports']
    
    def export_reports(self, request, queryset):
        """导出选中的月度报告"""
        count = queryset.count()
        self.message_user(
            request,
            f'已选择 {count} 个月度报告进行导出。（导出功能待实现）',
            level='info'
        )
    export_reports.short_description = "导出选中的月度报告"
    
    def regenerate_reports(self, request, queryset):
        """重新生成选中的月度报告"""
        count = queryset.count()
        self.message_user(
            request,
            f'已选择 {count} 个月度报告进行重新生成。（重新生成功能待实现）',
            level='warning'
        )
    regenerate_reports.short_description = "重新生成选中的月度报告"
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).prefetch_related('department_reports')


class DepartmentReportInline(admin.TabularInline):
    """部门报告内联显示"""
    model = DepartmentReport
    extra = 0
    readonly_fields = ('department', 'total_okr_score', 'member_count', 'avg_score', 'completed_tasks', 'avg_difficulty')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DepartmentReport)
class DepartmentReportAdmin(admin.ModelAdmin):
    """
    部门报告管理界面
    显示各部门的详细绩效数据
    """
    
    list_display = (
        'get_report_month',
        'get_department_display',
        'get_okr_score_display',
        'member_count',
        'get_avg_score_display',
        'completed_tasks',
        'get_avg_difficulty_display'
    )
    list_filter = (
        'department',
        'monthly_report__month'
    )
    ordering = ('-monthly_report__month', 'department')
    readonly_fields = (
        'monthly_report', 'department', 'total_okr_score',
        'member_count', 'avg_score', 'completed_tasks', 'avg_difficulty'
    )
    
    fieldsets = (
        ('基本信息', {
            'fields': ('monthly_report', 'department'),
            'description': '部门报告基本信息'
        }),
        ('绩效数据', {
            'fields': ('total_okr_score', 'avg_score', 'member_count'),
            'description': '部门绩效相关数据'
        }),
        ('任务数据', {
            'fields': ('completed_tasks', 'avg_difficulty'),
            'description': '部门任务完成情况'
        }),
    )
    
    def get_report_month(self, obj):
        """显示报告月份"""
        return obj.monthly_report.month.strftime('%Y年%m月')
    get_report_month.short_description = '报告月份'
    get_report_month.admin_order_field = 'monthly_report__month'
    
    def get_department_display(self, obj):
        """显示部门信息，带颜色标识"""
        colors = {
            'hardware': '#FF6B6B',
            'software': '#4ECDC4',
            'marketing': '#45B7D1'
        }
        color = colors.get(obj.department, '#6C757D')
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 14px;">{}</span>',
            color,
            obj.get_department_display()
        )
    get_department_display.short_description = '部门'
    get_department_display.admin_order_field = 'department'
    
    def get_okr_score_display(self, obj):
        """显示OKR总分"""
        return format_html(
            '<span style="color: #28A745; font-weight: bold; font-size: 16px;">{:.2f}</span>',
            obj.total_okr_score
        )
    get_okr_score_display.short_description = 'OKR总分'
    get_okr_score_display.admin_order_field = 'total_okr_score'
    
    def get_avg_score_display(self, obj):
        """显示平均分"""
        if obj.avg_score >= 80:
            color = '#28A745'  # 绿色
        elif obj.avg_score >= 60:
            color = '#FFC107'  # 黄色
        else:
            color = '#DC3545'  # 红色
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            obj.avg_score
        )
    get_avg_score_display.short_description = '平均分'
    get_avg_score_display.admin_order_field = 'avg_score'
    
    def get_avg_difficulty_display(self, obj):
        """显示平均难度"""
        if obj.avg_difficulty >= 7:
            color = '#DC3545'  # 红色 - 高难度
        elif obj.avg_difficulty >= 4:
            color = '#FFC107'  # 黄色 - 中等难度
        else:
            color = '#28A745'  # 绿色 - 低难度
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color,
            obj.avg_difficulty
        )
    get_avg_difficulty_display.short_description = '平均难度'
    get_avg_difficulty_display.admin_order_field = 'avg_difficulty'
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加，只能通过系统生成
    
    def has_change_permission(self, request, obj=None):
        return False  # 不允许修改，保证数据完整性
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('monthly_report')


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
    """
    绩效分值管理界面
    支持查看排名和分值详情
    """
    
    list_display = (
        'get_rank_display',
        'get_user_info',
        'get_final_score_display',
        'get_month_display',
        'get_score_breakdown',
        'calculated_at'
    )
    list_filter = (
        'month',
        'user__department',
        'rank'
    )
    search_fields = ('user__name', 'user__email')
    ordering = ('-month', 'rank')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'month', 'final_score', 'rank'),
            'description': '绩效评分基本信息'
        }),
        ('基础维度得分', {
            'fields': (
                ('work_hours', 'work_hours_score'),
                ('completion_rate', 'completion_rate_score'),
                ('avg_difficulty_score', 'total_revenue', 'revenue_score'),
                'department_avg_score'
            ),
            'description': '工作量和任务完成相关维度'
        }),
        ('评价维度得分', {
            'fields': (
                'task_rating_score',
                ('culture_understanding_score', 'team_fit_score'),
                ('monthly_growth_score', 'biggest_contribution_score'),
                ('peer_evaluation_score', 'admin_final_score')
            ),
            'description': '评价和反馈相关维度'
        }),
        ('计算信息', {
            'fields': ('calculated_at',),
            'classes': ('collapse',),
            'description': '分值计算时间信息'
        }),
    )
    
    readonly_fields = ('calculated_at',)
    
    def get_rank_display(self, obj):
        """显示排名，带奖牌图标"""
        if obj.rank == 1:
            return format_html(
                '<span style="color: #FFD700; font-size: 18px; font-weight: bold;">🥇 第{}名</span>',
                obj.rank
            )
        elif obj.rank == 2:
            return format_html(
                '<span style="color: #C0C0C0; font-size: 18px; font-weight: bold;">🥈 第{}名</span>',
                obj.rank
            )
        elif obj.rank == 3:
            return format_html(
                '<span style="color: #CD7F32; font-size: 18px; font-weight: bold;">🥉 第{}名</span>',
                obj.rank
            )
        else:
            return format_html(
                '<span style="color: #6C757D; font-size: 16px; font-weight: bold;">第{}名</span>',
                obj.rank
            )
    get_rank_display.short_description = '排名'
    get_rank_display.admin_order_field = 'rank'
    
    def get_user_info(self, obj):
        """显示用户信息"""
        colors = {
            'hardware': '#FF6B6B',
            'software': '#4ECDC4',
            'marketing': '#45B7D1'
        }
        color = colors.get(obj.user.department, '#6C757D')
        return format_html(
            '<strong style="font-size: 14px;">{}</strong><br>'
            '<small style="color: {};">{}</small>',
            obj.user.name,
            color,
            obj.user.get_department_display()
        )
    get_user_info.short_description = '用户'
    get_user_info.admin_order_field = 'user__name'
    
    def get_final_score_display(self, obj):
        """显示最终分值，带颜色标识"""
        if obj.final_score >= 90:
            color = '#28A745'  # 绿色 - 优秀
            level = '优秀'
        elif obj.final_score >= 80:
            color = '#17A2B8'  # 青色 - 良好
            level = '良好'
        elif obj.final_score >= 70:
            color = '#FFC107'  # 黄色 - 一般
            level = '一般'
        else:
            color = '#DC3545'  # 红色 - 待改进
            level = '待改进'
        
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 16px;">{:.2f}</span><br>'
            '<small style="color: {};">{}</small>',
            color, obj.final_score, color, level
        )
    get_final_score_display.short_description = '最终分值'
    get_final_score_display.admin_order_field = 'final_score'
    
    def get_month_display(self, obj):
        """显示月份"""
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            obj.month.strftime('%Y年%m月')
        )
    get_month_display.short_description = '月份'
    get_month_display.admin_order_field = 'month'
    
    def get_score_breakdown(self, obj):
        """显示分值构成概览"""
        return format_html(
            '<small>'
            '工时: {:.1f} | 完成率: {:.1f}<br>'
            '任务评分: {:.1f} | 他人评价: {:.1f}<br>'
            '管理员评分: {}'
            '</small>',
            obj.work_hours_score,
            obj.completion_rate_score,
            obj.task_rating_score,
            obj.peer_evaluation_score,
            f'{obj.admin_final_score:.1f}' if obj.admin_final_score else '未评价'
        )
    get_score_breakdown.short_description = '分值构成'
    
    # 自定义操作
    actions = ['recalculate_scores', 'export_scores']
    
    def recalculate_scores(self, request, queryset):
        """重新计算选中的绩效分值"""
        count = queryset.count()
        self.message_user(
            request,
            f'已选择 {count} 个绩效记录进行重新计算。（重新计算功能待实现）',
            level='info'
        )
    recalculate_scores.short_description = "重新计算选中的绩效分值"
    
    def export_scores(self, request, queryset):
        """导出选中的绩效分值"""
        count = queryset.count()
        self.message_user(
            request,
            f'已选择 {count} 个绩效记录进行导出。（导出功能待实现）',
            level='info'
        )
    export_scores.short_description = "导出选中的绩效分值"
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加，只能通过系统计算生成
    
    def has_change_permission(self, request, obj=None):
        """只有管理员可以修改管理员最终评分"""
        if request.user.is_superuser or (hasattr(request.user, 'role') and request.user.role == 'admin'):
            return True
        return False
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('user')
    
    def changelist_view(self, request, extra_context=None):
        """添加统计信息到列表页面"""
        extra_context = extra_context or {}
        
        # 计算统计信息
        from django.db.models import Avg, Max, Min, Count
        
        stats = PerformanceScore.objects.aggregate(
            avg_score=Avg('final_score'),
            max_score=Max('final_score'),
            min_score=Min('final_score'),
            total_records=Count('id')
        )
        
        # 按部门统计
        dept_stats = {}
        for dept_code, dept_name in Department.choices:
            dept_avg = PerformanceScore.objects.filter(
                user__department=dept_code
            ).aggregate(avg=Avg('final_score'))['avg']
            dept_stats[dept_name] = round(dept_avg, 2) if dept_avg else 0
        
        extra_context.update({
            'avg_score': round(stats['avg_score'], 2) if stats['avg_score'] else 0,
            'max_score': round(stats['max_score'], 2) if stats['max_score'] else 0,
            'min_score': round(stats['min_score'], 2) if stats['min_score'] else 0,
            'total_records': stats['total_records'],
            'dept_stats': dept_stats,
        })
        
        return super().changelist_view(request, extra_context)


class PeerEvaluationInline(admin.TabularInline):
    """他人评价内联显示"""
    model = PeerEvaluation
    extra = 0
    readonly_fields = ('evaluator', 'score', 'ranking', 'comment', 'is_anonymous', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MonthlyEvaluation)
class MonthlyEvaluationAdmin(admin.ModelAdmin):
    """
    月度综合评价管理界面
    支持查看所有成员的评价详情
    """
    
    list_display = (
        'get_user_info',
        'get_month_display',
        'get_self_evaluation_summary',
        'get_peer_evaluation_summary',
        'get_admin_evaluation_status',
        'created_at'
    )
    list_filter = (
        'month',
        'user__department',
        'admin_evaluated_by',
        'created_at'
    )
    search_fields = ('user__name', 'user__email')
    ordering = ('-month', 'user__name')
    
    inlines = [PeerEvaluationInline]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'month'),
            'description': '被评价人和评价月份'
        }),
        ('自我评价 - 企业文化理解', {
            'fields': (
                'culture_understanding_score',
                'culture_understanding_text',
                'culture_understanding_option'
            ),
            'description': '员工对企业文化的理解程度'
        }),
        ('自我评价 - 团队契合度', {
            'fields': (
                'team_fit_option',
                'team_fit_text',
                'team_fit_ranking'
            ),
            'description': '员工与团队的契合程度和对其他成员的排名'
        }),
        ('自我评价 - 本月成长', {
            'fields': (
                'monthly_growth_score',
                'monthly_growth_text',
                'monthly_growth_option'
            ),
            'description': '员工本月的成长情况'
        }),
        ('自我评价 - 本月最大贡献', {
            'fields': (
                'biggest_contribution_score',
                'biggest_contribution_text',
                'biggest_contribution_option'
            ),
            'description': '员工本月的最大贡献'
        }),
        ('管理员最终评价', {
            'fields': (
                'admin_final_score',
                'admin_final_comment',
                'admin_evaluated_by',
                'admin_evaluated_at'
            ),
            'description': '管理员对该员工的最终评价'
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': '评价创建和修改时间'
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'admin_evaluated_at')
    
    def get_user_info(self, obj):
        """显示用户信息"""
        colors = {
            'hardware': '#FF6B6B',
            'software': '#4ECDC4',
            'marketing': '#45B7D1'
        }
        color = colors.get(obj.user.department, '#6C757D')
        return format_html(
            '<strong style="font-size: 14px;">{}</strong><br>'
            '<small style="color: {};">{}</small>',
            obj.user.name,
            color,
            obj.user.get_department_display()
        )
    get_user_info.short_description = '被评价人'
    get_user_info.admin_order_field = 'user__name'
    
    def get_month_display(self, obj):
        """显示月份"""
        return format_html(
            '<span style="font-weight: bold; color: #007BFF;">{}</span>',
            obj.month.strftime('%Y年%m月')
        )
    get_month_display.short_description = '评价月份'
    get_month_display.admin_order_field = 'month'
    
    def get_self_evaluation_summary(self, obj):
        """显示自我评价概要"""
        avg_score = (
            obj.culture_understanding_score +
            obj.monthly_growth_score +
            obj.biggest_contribution_score
        ) / 3
        
        return format_html(
            '<small>'
            '企业文化: {} 分<br>'
            '本月成长: {} 分<br>'
            '最大贡献: {} 分<br>'
            '<strong>平均: {:.1f} 分</strong>'
            '</small>',
            obj.culture_understanding_score,
            obj.monthly_growth_score,
            obj.biggest_contribution_score,
            avg_score
        )
    get_self_evaluation_summary.short_description = '自我评价'
    
    def get_peer_evaluation_summary(self, obj):
        """显示他人评价概要"""
        peer_evaluations = obj.peer_evaluations.all()
        if peer_evaluations:
            avg_score = sum(pe.score for pe in peer_evaluations) / len(peer_evaluations)
            avg_ranking = sum(pe.ranking for pe in peer_evaluations) / len(peer_evaluations)
            anonymous_count = sum(1 for pe in peer_evaluations if pe.is_anonymous)
            
            return format_html(
                '<small>'
                '评价人数: {} 人<br>'
                '平均评分: {:.1f} 分<br>'
                '平均排名: {:.1f}<br>'
                '匿名评价: {} 个'
                '</small>',
                len(peer_evaluations),
                avg_score,
                avg_ranking,
                anonymous_count
            )
        else:
            return format_html('<small style="color: #6C757D;">暂无他人评价</small>')
    get_peer_evaluation_summary.short_description = '他人评价'
    
    def get_admin_evaluation_status(self, obj):
        """显示管理员评价状态"""
        if obj.admin_final_score:
            return format_html(
                '<span style="color: #28A745; font-weight: bold;">{} 分</span><br>'
                '<small>评价人: {}<br>时间: {}</small>',
                obj.admin_final_score,
                obj.admin_evaluated_by.name if obj.admin_evaluated_by else '未知',
                obj.admin_evaluated_at.strftime('%m-%d %H:%M') if obj.admin_evaluated_at else '未知'
            )
        else:
            return format_html(
                '<span style="color: #DC3545; font-weight: bold;">未评价</span>'
            )
    get_admin_evaluation_status.short_description = '管理员评价'
    
    # 自定义操作
    actions = ['mark_for_admin_evaluation', 'export_evaluations']
    
    def mark_for_admin_evaluation(self, request, queryset):
        """标记需要管理员评价"""
        unevaluated = queryset.filter(admin_final_score__isnull=True)
        count = unevaluated.count()
        self.message_user(
            request,
            f'已标记 {count} 个评价需要管理员评价。',
            level='warning'
        )
    mark_for_admin_evaluation.short_description = "标记选中评价需要管理员评价"
    
    def export_evaluations(self, request, queryset):
        """导出选中的评价"""
        count = queryset.count()
        self.message_user(
            request,
            f'已选择 {count} 个评价进行导出。（导出功能待实现）',
            level='info'
        )
    export_evaluations.short_description = "导出选中的评价"
    
    def save_model(self, request, obj, form, change):
        """保存管理员评价时记录评价人和时间"""
        if 'admin_final_score' in form.changed_data and obj.admin_final_score:
            from django.utils import timezone
            obj.admin_evaluated_by = request.user
            obj.admin_evaluated_at = timezone.now()
            
            # 记录管理员评价历史
            AdminEvaluationHistory.objects.create(
                monthly_evaluation=obj,
                admin_user=request.user,
                previous_score=form.initial.get('admin_final_score'),
                new_score=obj.admin_final_score,
                previous_comment=form.initial.get('admin_final_comment', ''),
                new_comment=obj.admin_final_comment,
                action_type='update' if change else 'create'
            )
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related(
            'user', 'admin_evaluated_by'
        ).prefetch_related('peer_evaluations')
    
    def changelist_view(self, request, extra_context=None):
        """添加统计信息到列表页面"""
        extra_context = extra_context or {}
        
        # 计算统计信息
        from django.db.models import Avg, Count
        
        total_evaluations = MonthlyEvaluation.objects.count()
        admin_evaluated = MonthlyEvaluation.objects.filter(admin_final_score__isnull=False).count()
        pending_admin = total_evaluations - admin_evaluated
        
        avg_culture_score = MonthlyEvaluation.objects.aggregate(
            avg=Avg('culture_understanding_score')
        )['avg']
        avg_growth_score = MonthlyEvaluation.objects.aggregate(
            avg=Avg('monthly_growth_score')
        )['avg']
        avg_contribution_score = MonthlyEvaluation.objects.aggregate(
            avg=Avg('biggest_contribution_score')
        )['avg']
        
        extra_context.update({
            'total_evaluations': total_evaluations,
            'admin_evaluated': admin_evaluated,
            'pending_admin': pending_admin,
            'avg_culture_score': round(avg_culture_score, 2) if avg_culture_score else 0,
            'avg_growth_score': round(avg_growth_score, 2) if avg_growth_score else 0,
            'avg_contribution_score': round(avg_contribution_score, 2) if avg_contribution_score else 0,
        })
        
        return super().changelist_view(request, extra_context)


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
