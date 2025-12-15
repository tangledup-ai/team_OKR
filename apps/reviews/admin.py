from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Avg, Count
from .models import Review, ReviewType


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'type', 'get_task_or_reviewee', 'reviewer_display', 'rating', 
        'is_anonymous', 'created_at'
    )
    list_filter = (
        'type', 'is_anonymous', 'rating', 'created_at', 
        'reviewer__role', 'reviewer__department'
    )
    search_fields = (
        'comment', 'reviewer__name', 'reviewee__name', 
        'task__title', 'reviewer__email'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('评价信息', {
            'fields': ('type', 'task', 'reviewee', 'month')
        }),
        ('评价内容', {
            'fields': ('reviewer', 'rating', 'comment', 'is_anonymous')
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def get_task_or_reviewee(self, obj):
        """显示任务或被评价人"""
        if obj.type == ReviewType.TASK and obj.task:
            return format_html(
                '<span style="color: #0066cc;">任务: {}</span>',
                obj.task.title
            )
        elif obj.type == ReviewType.MONTHLY and obj.reviewee:
            return format_html(
                '<span style="color: #cc6600;">用户: {}</span>',
                obj.reviewee.name
            )
        return '-'
    get_task_or_reviewee.short_description = '评价对象'
    
    def reviewer_display(self, obj):
        """显示评价人信息"""
        role_color = '#cc0000' if obj.reviewer.role == 'admin' else '#006600'
        return format_html(
            '<span style="color: {};">{} ({})</span>',
            role_color,
            obj.reviewer.name,
            obj.reviewer.get_role_display()
        )
    reviewer_display.short_description = '评价人'
    
    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).select_related(
            'reviewer', 'reviewee', 'task'
        )
    
    def changelist_view(self, request, extra_context=None):
        """添加统计信息到列表页面"""
        extra_context = extra_context or {}
        
        # 计算统计信息
        total_reviews = Review.objects.count()
        task_reviews = Review.objects.filter(type=ReviewType.TASK).count()
        monthly_reviews = Review.objects.filter(type=ReviewType.MONTHLY).count()
        
        avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg']
        avg_rating = round(avg_rating, 2) if avg_rating else 0
        
        anonymous_count = Review.objects.filter(is_anonymous=True).count()
        
        extra_context.update({
            'total_reviews': total_reviews,
            'task_reviews': task_reviews,
            'monthly_reviews': monthly_reviews,
            'avg_rating': avg_rating,
            'anonymous_count': anonymous_count,
        })
        
        return super().changelist_view(request, extra_context)
    
    def has_add_permission(self, request):
        """限制通过Admin添加评价"""
        return False  # 评价应该通过API提交
    
    def has_change_permission(self, request, obj=None):
        """限制修改评价"""
        return request.user.is_superuser  # 只有超级管理员可以修改
    
    def has_delete_permission(self, request, obj=None):
        """限制删除评价"""
        return request.user.is_superuser  # 只有超级管理员可以删除
