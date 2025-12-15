"""
Review models for OKR Performance System
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class ReviewType(models.TextChoices):
    TASK = 'task', '任务评价'
    MONTHLY = 'monthly', '月度评价'


class Review(models.Model):
    """评价模型"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(
        max_length=10,
        choices=ReviewType.choices,
        verbose_name='评价类型'
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reviews',
        verbose_name='任务'
    )
    reviewee = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_reviews',
        verbose_name='被评价人'
    )
    reviewer = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='given_reviews',
        verbose_name='评价人'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='评分'
    )
    comment = models.TextField(verbose_name='评论')
    is_anonymous = models.BooleanField(default=False, verbose_name='是否匿名')
    month = models.DateField(null=True, blank=True, verbose_name='月份')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'reviews'
        verbose_name = '评价'
        verbose_name_plural = '评价'
        indexes = [
            models.Index(fields=['type', 'task']),
            models.Index(fields=['month']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} - {self.rating}分"
