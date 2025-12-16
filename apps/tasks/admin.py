from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Task, ScoreDistribution, ScoreAllocation, TaskStatus


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    任务管理界面
    支持状态筛选、负责人筛选、难度筛选等功能
    """
    
    # 列表页面显示字段
    list_display = (
        'title',
        'status',
        'get_difficulty_display',
        'get_revenue_display',
        'get_owner_info',
        'get_collaborators_count',
        'get_progress_info',
        'created_at'
    )
    
    # 列表页面过滤器
    list_filter = (
        'status',
        'difficulty_score',
        'owner__department',
        'owner',
        'created_at',
        'completed_at'
    )
    
    # 搜索字段
    search_fields = ('title', 'description', 'owner__name', 'owner__email')
    
    # 排序
    ordering = ('-created_at',)
    
    # 每页显示数量
    list_per_page = 25
    
    # 可编辑字段（在列表页面直接编辑）
    list_editable = ('status',)
    
    # 水平过滤器
    filter_horizontal = ('collaborators',)
    
    # 自动完成字段
    autocomplete_fields = ['owner', 'collaborators', 'created_by']
    
    # 详情页面字段分组
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description'),
            'description': '任务的基本信息'
        }),
        ('评分设置', {
            'fields': ('difficulty_score', 'revenue_amount'),
            'description': '任务难度分值和变现金额设置'
        }),
        ('人员分配', {
            'fields': ('owner', 'collaborators', 'created_by'),
            'description': '任务负责人和协作者分配'
        }),
        ('状态管理', {
            'fields': ('status', 'postpone_reason'),
            'description': '任务状态和推迟原因'
        }),
        ('时间记录', {
            'fields': ('created_at', 'started_at', 'completed_at', 'postponed_at'),
            'classes': ('collapse',),
            'description': '任务各阶段时间记录'
        }),
    )
    
    # 只读字段
    readonly_fields = ('created_at', 'started_at', 'completed_at', 'postponed_at')
    
    # 自定义显示方法
    def get_status_display_colored(self, obj):
        """显示带颜色的状态"""
        colors = {
            TaskStatus.TODO: '#6C757D',        # 灰色
            TaskStatus.IN_PROGRESS: '#007BFF', # 蓝色
            TaskStatus.COMPLETED: '#28A745',   # 绿色
            TaskStatus.POSTPONED: '#DC3545'    # 红色
        }
        icons = {
            TaskStatus.TODO: '⏳',
            TaskStatus.IN_PROGRESS: '🔄',
            TaskStatus.COMPLETED: '✅',
            TaskStatus.POSTPONED: '⏸️'
        }
        color = colors.get(obj.status, '#6C757D')
        icon = icons.get(obj.status, '❓')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    get_status_display_colored.short_description = '状态'
    get_status_display_colored.admin_order_field = 'status'
    
    def get_difficulty_display(self, obj):
        """显示难度分值，带颜色标识"""
        if obj.difficulty_score >= 8:
            color = '#DC3545'  # 红色 - 高难度
        elif obj.difficulty_score >= 5:
            color = '#FFC107'  # 黄色 - 中等难度
        else:
            color = '#28A745'  # 绿色 - 低难度
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} 分</span>',
            color,
            obj.difficulty_score
        )
    get_difficulty_display.short_description = '难度分值'
    get_difficulty_display.admin_order_field = 'difficulty_score'
    
    def get_revenue_display(self, obj):
        """显示变现金额"""
        if obj.revenue_amount > 0:
            return format_html(
                '<span style="color: #28A745; font-weight: bold;">¥{:,.2f}</span>',
                obj.revenue_amount
            )
        else:
            return format_html('<span style="color: #6C757D;">-</span>')
    get_revenue_display.short_description = '变现金额'
    get_revenue_display.admin_order_field = 'revenue_amount'
    
    def get_owner_info(self, obj):
        """显示负责人信息"""
        colors = {
            'hardware': '#FF6B6B',
            'software': '#4ECDC4',
            'marketing': '#45B7D1'
        }
        color = colors.get(obj.owner.department, '#6C757D')
        return format_html(
            '<strong>{}</strong><br><small style="color: {};">{}</small>',
            obj.owner.name,
            color,
            obj.owner.get_department_display()
        )
    get_owner_info.short_description = '负责人'
    get_owner_info.admin_order_field = 'owner__name'
    
    def get_collaborators_count(self, obj):
        """显示协作者数量"""
        count = obj.collaborators.count()
        if count > 0:
            return format_html(
                '<span style="color: #007BFF; font-weight: bold;">{} 人</span>',
                count
            )
        else:
            return format_html('<span style="color: #6C757D;">无</span>')
    get_collaborators_count.short_description = '协作者'
    
    def get_progress_info(self, obj):
        """显示进度信息"""
        if obj.status == TaskStatus.COMPLETED and obj.completed_at:
            duration = obj.completed_at - obj.created_at
            return format_html(
                '<small style="color: #28A745;">已完成<br>用时: {} 天</small>',
                duration.days
            )
        elif obj.status == TaskStatus.IN_PROGRESS and obj.started_at:
            from django.utils import timezone
            duration = timezone.now() - obj.started_at
            return format_html(
                '<small style="color: #007BFF;">进行中<br>已用: {} 天</small>',
                duration.days
            )
        elif obj.status == TaskStatus.POSTPONED:
            return format_html(
                '<small style="color: #DC3545;">已推迟<br>原因: {}</small>',
                obj.postpone_reason[:20] + '...' if len(obj.postpone_reason) > 20 else obj.postpone_reason
            )
        else:
            return format_html('<small style="color: #6C757D;">待开始</small>')
    get_progress_info.short_description = '进度信息'
    
    # 自定义操作
    actions = ['mark_as_completed', 'mark_as_in_progress', 'mark_as_postponed', 'calculate_scores']
    
    def mark_as_completed(self, request, queryset):
        """批量标记为已完成"""
        from django.utils import timezone
        updated = queryset.filter(status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS]).update(
            status=TaskStatus.COMPLETED,
            completed_at=timezone.now()
        )
        self.message_user(request, f'成功将 {updated} 个任务标记为已完成。')
    mark_as_completed.short_description = "标记选中任务为已完成"
    
    def mark_as_in_progress(self, request, queryset):
        """批量标记为进行中"""
        from django.utils import timezone
        updated = queryset.filter(status=TaskStatus.TODO).update(
            status=TaskStatus.IN_PROGRESS,
            started_at=timezone.now()
        )
        self.message_user(request, f'成功将 {updated} 个任务标记为进行中。')
    mark_as_in_progress.short_description = "标记选中任务为进行中"
    
    def mark_as_postponed(self, request, queryset):
        """批量标记为推迟"""
        from django.utils import timezone
        updated = queryset.filter(status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS]).update(
            status=TaskStatus.POSTPONED,
            postponed_at=timezone.now(),
            postpone_reason='管理员批量操作'
        )
        self.message_user(request, f'成功将 {updated} 个任务标记为推迟。', level='warning')
    mark_as_postponed.short_description = "标记选中任务为推迟"
    
    def calculate_scores(self, request, queryset):
        """批量计算分值分配"""
        completed_tasks = queryset.filter(status=TaskStatus.COMPLETED)
        calculated_count = 0
        
        for task in completed_tasks:
            try:
                ScoreDistribution.calculate_and_create(task)
                calculated_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'任务 "{task.title}" 分值计算失败: {str(e)}',
                    level='error'
                )
        
        if calculated_count > 0:
            self.message_user(
                request,
                f'成功为 {calculated_count} 个已完成任务计算分值分配。',
                level='success'
            )
    calculate_scores.short_description = "为选中的已完成任务计算分值分配"
    
    def get_queryset(self, request):
        """优化查询，预加载相关对象"""
        return super().get_queryset(request).select_related(
            'owner', 'created_by'
        ).prefetch_related('collaborators')
    
    def changelist_view(self, request, extra_context=None):
        """添加统计信息到列表页面"""
        extra_context = extra_context or {}
        
        # 计算统计信息
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status=TaskStatus.COMPLETED).count()
        in_progress_tasks = Task.objects.filter(status=TaskStatus.IN_PROGRESS).count()
        postponed_tasks = Task.objects.filter(status=TaskStatus.POSTPONED).count()
        
        avg_difficulty = Task.objects.aggregate(avg=Avg('difficulty_score'))['avg']
        avg_difficulty = round(avg_difficulty, 2) if avg_difficulty else 0
        
        extra_context.update({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'postponed_tasks': postponed_tasks,
            'avg_difficulty': avg_difficulty,
        })
        
        return super().changelist_view(request, extra_context)


class ScoreAllocationInline(admin.TabularInline):
    model = ScoreAllocation
    extra = 0
    readonly_fields = ('user', 'base_score', 'adjusted_score', 'percentage')
    can_delete = False
    
    def get_user_display(self, obj):
        """显示用户信息"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.user.name,
            obj.user.get_department_display()
        )
    get_user_display.short_description = '用户'


@admin.register(ScoreDistribution)
class ScoreDistributionAdmin(admin.ModelAdmin):
    """
    分值分配管理界面
    显示任务分值分配详情和历史记录
    """
    
    list_display = (
        'get_task_info',
        'total_score',
        'get_penalty_display',
        'get_participants_count',
        'calculated_at'
    )
    list_filter = ('penalty_coefficient', 'calculated_at', 'task__status')
    search_fields = ('task__title', 'task__owner__name')
    ordering = ('-calculated_at',)
    readonly_fields = ('task', 'total_score', 'penalty_coefficient', 'calculated_at')
    inlines = [ScoreAllocationInline]
    
    def get_task_info(self, obj):
        """显示任务信息"""
        return format_html(
            '<strong>{}</strong><br><small>负责人: {} | 难度: {} 分</small>',
            obj.task.title,
            obj.task.owner.name,
            obj.task.difficulty_score
        )
    get_task_info.short_description = '任务信息'
    get_task_info.admin_order_field = 'task__title'
    
    def get_penalty_display(self, obj):
        """显示惩罚系数"""
        if obj.penalty_coefficient < 1:
            return format_html(
                '<span style="color: #DC3545; font-weight: bold;">{} (推迟惩罚)</span>',
                obj.penalty_coefficient
            )
        else:
            return format_html(
                '<span style="color: #28A745;">{} (正常)</span>',
                obj.penalty_coefficient
            )
    get_penalty_display.short_description = '惩罚系数'
    get_penalty_display.admin_order_field = 'penalty_coefficient'
    
    def get_participants_count(self, obj):
        """显示参与者数量"""
        count = obj.allocations.count()
        return format_html(
            '<span style="color: #007BFF; font-weight: bold;">{} 人</span>',
            count
        )
    get_participants_count.short_description = '参与者'
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加，只能通过系统计算生成
    
    def has_change_permission(self, request, obj=None):
        return False  # 不允许修改，保证数据完整性
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related('task', 'task__owner')


@admin.register(ScoreAllocation)
class ScoreAllocationAdmin(admin.ModelAdmin):
    """
    分值分配明细管理界面
    显示个人分值分配详情
    """
    
    list_display = (
        'get_user_info',
        'get_task_title',
        'base_score',
        'adjusted_score',
        'percentage',
        'get_calculated_at'
    )
    list_filter = (
        'distribution__calculated_at',
        'user__department',
        'user',
        'distribution__penalty_coefficient'
    )
    search_fields = ('user__name', 'distribution__task__title')
    ordering = ('-distribution__calculated_at', 'user__name')
    readonly_fields = ('distribution', 'user', 'base_score', 'adjusted_score', 'percentage')
    
    def get_user_info(self, obj):
        """显示用户信息"""
        colors = {
            'hardware': '#FF6B6B',
            'software': '#4ECDC4',
            'marketing': '#45B7D1'
        }
        color = colors.get(obj.user.department, '#6C757D')
        return format_html(
            '<strong>{}</strong><br><small style="color: {};">{}</small>',
            obj.user.name,
            color,
            obj.user.get_department_display()
        )
    get_user_info.short_description = '用户'
    get_user_info.admin_order_field = 'user__name'
    
    def get_task_title(self, obj):
        """显示任务标题"""
        return format_html(
            '<strong>{}</strong><br><small>难度: {} 分</small>',
            obj.distribution.task.title,
            obj.distribution.task.difficulty_score
        )
    get_task_title.short_description = '任务'
    get_task_title.admin_order_field = 'distribution__task__title'
    
    def get_calculated_at(self, obj):
        """显示计算时间"""
        return obj.distribution.calculated_at
    get_calculated_at.short_description = '计算时间'
    get_calculated_at.admin_order_field = 'distribution__calculated_at'
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加，只能通过系统计算生成
    
    def has_change_permission(self, request, obj=None):
        return False  # 不允许修改，保证数据完整性
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related(
            'user', 'distribution', 'distribution__task'
        )
