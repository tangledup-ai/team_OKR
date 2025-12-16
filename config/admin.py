"""
Django Admin Configuration for OKR Performance System
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html


class OKRAdminSite(AdminSite):
    """自定义Admin站点"""
    
    site_header = '🎯 OKR绩效管理系统'
    site_title = 'OKR管理后台'
    index_title = '欢迎使用OKR绩效管理系统'
    
    def index(self, request, extra_context=None):
        """自定义首页，添加统计信息"""
        extra_context = extra_context or {}
        
        # 导入模型
        from apps.users.models import User
        from apps.tasks.models import Task, TaskStatus
        from apps.reviews.models import Review
        from apps.reports.models import PerformanceScore, MonthlyEvaluation
        from django.db.models import Count, Avg
        
        # 计算统计数据
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_tasks': Task.objects.count(),
            'completed_tasks': Task.objects.filter(status=TaskStatus.COMPLETED).count(),
            'in_progress_tasks': Task.objects.filter(status=TaskStatus.IN_PROGRESS).count(),
            'total_reviews': Review.objects.count(),
            'total_evaluations': MonthlyEvaluation.objects.count(),
            'pending_admin_evaluations': MonthlyEvaluation.objects.filter(admin_final_score__isnull=True).count(),
        }
        
        # 部门统计
        dept_stats = User.objects.values('department').annotate(
            count=Count('id')
        ).order_by('department')
        
        # 最新活动
        recent_tasks = Task.objects.select_related('owner').order_by('-created_at')[:5]
        recent_reviews = Review.objects.select_related('reviewer').order_by('-created_at')[:5]
        
        extra_context.update({
            'stats': stats,
            'dept_stats': dept_stats,
            'recent_tasks': recent_tasks,
            'recent_reviews': recent_reviews,
        })
        
        return super().index(request, extra_context)


# 创建自定义admin站点实例
admin_site = OKRAdminSite(name='okr_admin')

# 配置Admin界面美化
admin.site.site_header = '🎯 OKR绩效管理系统'
admin.site.site_title = 'OKR管理后台'
admin.site.index_title = '欢迎使用OKR绩效管理系统'


def admin_view_decorator(view_func):
    """Admin视图装饰器，添加通用功能"""
    def wrapper(request, *args, **kwargs):
        # 可以在这里添加通用的权限检查、日志记录等
        return view_func(request, *args, **kwargs)
    return wrapper


# 自定义Admin操作
def export_to_excel(modeladmin, request, queryset):
    """通用导出到Excel功能"""
    # 这里可以实现通用的Excel导出逻辑
    modeladmin.message_user(
        request,
        f'已选择 {queryset.count()} 条记录进行导出。（导出功能待实现）',
        level='info'
    )
export_to_excel.short_description = "导出选中记录到Excel"


def send_notification(modeladmin, request, queryset):
    """通用发送通知功能"""
    # 这里可以实现通用的通知发送逻辑
    modeladmin.message_user(
        request,
        f'已向 {queryset.count()} 条记录相关用户发送通知。（通知功能待实现）',
        level='success'
    )
send_notification.short_description = "向相关用户发送通知"


# 通用Admin Mixin类
class BaseAdminMixin:
    """基础Admin Mixin，提供通用功能"""
    
    def get_readonly_fields(self, request, obj=None):
        """根据用户权限动态设置只读字段"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        
        # 非超级管理员不能修改某些敏感字段
        if not request.user.is_superuser:
            sensitive_fields = ['created_at', 'updated_at', 'id']
            readonly_fields.extend([f for f in sensitive_fields if f in self.get_fields(request, obj)])
        
        return readonly_fields
    
    def has_delete_permission(self, request, obj=None):
        """删除权限控制"""
        # 只有超级管理员可以删除记录
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """优化查询性能"""
        qs = super().get_queryset(request)
        
        # 根据模型自动添加select_related和prefetch_related
        if hasattr(self.model, '_meta'):
            # 自动添加外键字段的select_related
            foreign_keys = [
                field.name for field in self.model._meta.get_fields()
                if field.many_to_one and not field.null
            ]
            if foreign_keys:
                qs = qs.select_related(*foreign_keys[:3])  # 限制数量避免过度优化
        
        return qs


class ExportMixin:
    """导出功能Mixin"""
    
    def get_export_formats(self):
        """获取支持的导出格式"""
        return ['excel', 'csv', 'pdf']
    
    def export_data(self, request, queryset, format='excel'):
        """导出数据"""
        # 这里实现具体的导出逻辑
        self.message_user(
            request,
            f'已导出 {queryset.count()} 条记录为 {format.upper()} 格式。（导出功能待实现）',
            level='info'
        )


class StatisticsMixin:
    """统计信息Mixin"""
    
    def get_statistics(self, request, queryset=None):
        """获取统计信息"""
        if queryset is None:
            queryset = self.get_queryset(request)
        
        return {
            'total_count': queryset.count(),
            'created_today': queryset.filter(
                created_at__date=timezone.now().date()
            ).count() if hasattr(queryset.model, 'created_at') else 0,
        }
    
    def changelist_view(self, request, extra_context=None):
        """在列表页面添加统计信息"""
        extra_context = extra_context or {}
        extra_context['statistics'] = self.get_statistics(request)
        return super().changelist_view(request, extra_context)


# 权限检查装饰器
def admin_required(view_func):
    """要求管理员权限的装饰器"""
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or 
                (hasattr(request.user, 'role') and request.user.role == 'admin')):
            from django.contrib import messages
            messages.error(request, '您没有权限执行此操作。')
            return redirect('admin:index')
        return view_func(request, *args, **kwargs)
    return wrapper


# 日志记录功能
class AdminLogMixin:
    """Admin操作日志Mixin"""
    
    def log_addition(self, request, object, message):
        """记录添加操作"""
        super().log_addition(request, object, message)
        # 这里可以添加自定义日志记录逻辑
    
    def log_change(self, request, object, message):
        """记录修改操作"""
        super().log_change(request, object, message)
        # 这里可以添加自定义日志记录逻辑
    
    def log_deletion(self, request, object, object_repr):
        """记录删除操作"""
        super().log_deletion(request, object, object_repr)
        # 这里可以添加自定义日志记录逻辑