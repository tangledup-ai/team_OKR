from django.contrib import admin
from .models import Task, ScoreDistribution, ScoreAllocation


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'difficulty_score', 'revenue_amount', 'owner', 'created_at')
    list_filter = ('status', 'difficulty_score', 'created_at')
    search_fields = ('title', 'description', 'owner__name')
    ordering = ('-created_at',)
    filter_horizontal = ('collaborators',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'difficulty_score', 'revenue_amount')
        }),
        ('人员分配', {
            'fields': ('owner', 'collaborators', 'created_by')
        }),
        ('状态管理', {
            'fields': ('status', 'postpone_reason')
        }),
        ('时间记录', {
            'fields': ('created_at', 'started_at', 'completed_at', 'postponed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'started_at', 'completed_at', 'postponed_at')


class ScoreAllocationInline(admin.TabularInline):
    model = ScoreAllocation
    extra = 0
    readonly_fields = ('user', 'base_score', 'adjusted_score', 'percentage')
    can_delete = False


@admin.register(ScoreDistribution)
class ScoreDistributionAdmin(admin.ModelAdmin):
    list_display = ('task', 'total_score', 'penalty_coefficient', 'calculated_at')
    list_filter = ('penalty_coefficient', 'calculated_at')
    search_fields = ('task__title', 'task__owner__name')
    ordering = ('-calculated_at',)
    readonly_fields = ('task', 'total_score', 'penalty_coefficient', 'calculated_at')
    inlines = [ScoreAllocationInline]
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加，只能通过系统计算生成


@admin.register(ScoreAllocation)
class ScoreAllocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_task_title', 'base_score', 'adjusted_score', 'percentage')
    list_filter = ('distribution__calculated_at', 'user__department')
    search_fields = ('user__name', 'distribution__task__title')
    ordering = ('-distribution__calculated_at',)
    readonly_fields = ('distribution', 'user', 'base_score', 'adjusted_score', 'percentage')
    
    def get_task_title(self, obj):
        return obj.distribution.task.title
    get_task_title.short_description = '任务标题'
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加，只能通过系统计算生成
