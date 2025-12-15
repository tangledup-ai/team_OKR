from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, Department


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    自定义用户管理界面
    支持按部门、角色、状态过滤，支持邮箱和姓名搜索
    """
    
    # 列表页面显示字段
    list_display = (
        'email', 
        'name', 
        'get_department_display', 
        'get_role_display', 
        'is_active',
        'last_login',
        'created_at'
    )
    
    # 列表页面过滤器
    list_filter = (
        'department', 
        'role', 
        'is_active', 
        'is_staff',
        'is_superuser',
        'created_at',
        'last_login'
    )
    
    # 搜索字段
    search_fields = ('email', 'name', 'username')
    
    # 排序
    ordering = ('-created_at',)
    
    # 每页显示数量
    list_per_page = 25
    
    # 可编辑字段（在列表页面直接编辑）
    list_editable = ('is_active',)
    
    # 详情页面字段分组
    fieldsets = (
        ('登录信息', {
            'fields': ('email', 'username', 'password'),
            'description': '用户登录相关信息'
        }),
        ('个人信息', {
            'fields': ('name', 'department', 'role'),
            'description': '用户基本信息和部门分配'
        }),
        ('权限设置', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': '用户权限控制'
        }),
        ('高级权限', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',),
            'description': '详细权限分配（高级用户）'
        }),
        ('时间信息', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': '时间戳信息'
        }),
    )
    
    # 添加用户页面字段
    add_fieldsets = (
        ('基本信息', {
            'classes': ('wide',),
            'fields': ('email', 'username', 'name', 'department', 'role'),
            'description': '创建新用户的基本信息'
        }),
        ('密码设置', {
            'classes': ('wide',),
            'fields': ('password1', 'password2'),
        }),
        ('权限设置', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff'),
        }),
    )
    
    # 只读字段
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    # 自定义显示方法
    def get_department_display(self, obj):
        """显示部门信息，带颜色标识"""
        colors = {
            'hardware': '#FF6B6B',  # 红色
            'software': '#4ECDC4',  # 青色  
            'marketing': '#45B7D1'  # 蓝色
        }
        color = colors.get(obj.department, '#6C757D')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_department_display()
        )
    get_department_display.short_description = '部门'
    get_department_display.admin_order_field = 'department'
    
    def get_role_display(self, obj):
        """显示角色信息，带图标"""
        if obj.role == 'admin':
            return format_html(
                '<span style="color: #DC3545;">👑 {}</span>',
                obj.get_role_display()
            )
        else:
            return format_html(
                '<span style="color: #6C757D;">👤 {}</span>',
                obj.get_role_display()
            )
    get_role_display.short_description = '角色'
    get_role_display.admin_order_field = 'role'
    
    def get_status_display(self, obj):
        """显示用户状态，带颜色标识"""
        if obj.is_active:
            return format_html(
                '<span style="color: #28A745; font-weight: bold;">✓ 激活</span>'
            )
        else:
            return format_html(
                '<span style="color: #DC3545; font-weight: bold;">✗ 停用</span>'
            )
    get_status_display.short_description = '状态'
    get_status_display.admin_order_field = 'is_active'
    
    # 自定义操作
    actions = ['activate_users', 'deactivate_users', 'reset_passwords']
    
    def activate_users(self, request, queryset):
        """批量激活用户"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'成功激活 {updated} 个用户账户。')
    activate_users.short_description = "激活选中的用户"
    
    def deactivate_users(self, request, queryset):
        """批量停用用户"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'成功停用 {updated} 个用户账户。')
    deactivate_users.short_description = "停用选中的用户"
    
    def reset_passwords(self, request, queryset):
        """批量重置密码提醒"""
        count = queryset.count()
        self.message_user(
            request, 
            f'已选择 {count} 个用户进行密码重置。请手动为这些用户设置新密码。',
            level='warning'
        )
    reset_passwords.short_description = "标记选中用户需要重置密码"
    
    # 权限控制
    def has_add_permission(self, request):
        """只有管理员可以添加用户"""
        return request.user.is_superuser or (
            hasattr(request.user, 'role') and request.user.role == 'admin'
        )
    
    def has_change_permission(self, request, obj=None):
        """管理员可以修改所有用户，普通用户只能修改自己"""
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        if obj is not None:
            return obj == request.user
        return False
    
    def has_delete_permission(self, request, obj=None):
        """只有超级管理员可以删除用户"""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """根据用户权限过滤查询集"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        elif hasattr(request.user, 'role') and request.user.role == 'admin':
            return qs
        else:
            # 普通用户只能看到自己
            return qs.filter(id=request.user.id)
    
    def get_form(self, request, obj=None, **kwargs):
        """根据用户权限自定义表单"""
        form = super().get_form(request, obj, **kwargs)
        
        # 非超级管理员不能修改超级用户权限
        if not request.user.is_superuser:
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'is_staff' in form.base_fields and obj and obj.is_superuser:
                form.base_fields['is_staff'].disabled = True
        
        return form


# 自定义Admin站点标题和头部
admin.site.site_header = 'OKR绩效管理系统'
admin.site.site_title = 'OKR管理后台'
admin.site.index_title = '欢迎使用OKR绩效管理系统'
