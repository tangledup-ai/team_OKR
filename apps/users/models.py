"""
User models for OKR Performance System
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class Department(models.TextChoices):
    HARDWARE = 'hardware', '硬件部门'
    SOFTWARE = 'software', '软件部门'
    MARKETING = 'marketing', '市场部门'


class User(AbstractUser):
    """团队成员模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='姓名')
    email = models.EmailField(unique=True, verbose_name='邮箱')
    department = models.CharField(
        max_length=20,
        choices=Department.choices,
        verbose_name='部门'
    )
    role = models.CharField(
        max_length=10,
        choices=[('admin', '管理员'), ('member', '成员')],
        default='member',
        verbose_name='角色'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email})"
