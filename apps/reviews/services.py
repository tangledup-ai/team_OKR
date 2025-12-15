"""
Review services for OKR Performance System
"""
from django.db.models import Avg, Count, Q
from decimal import Decimal, ROUND_HALF_UP
from .models import Review, ReviewType


class ReviewService:
    """评价服务类"""
    
    @staticmethod
    def calculate_average_rating(task_id):
        """计算任务平均评分"""
        reviews = Review.objects.filter(
            type=ReviewType.TASK,
            task_id=task_id
        )
        
        if not reviews.exists():
            return Decimal('0.00')
        
        avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return Decimal(str(avg_rating)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_weighted_average_rating(task_id):
        """计算任务的加权平均评分（管理员评分权重更高）"""
        admin_reviews = Review.objects.filter(
            type=ReviewType.TASK,
            task_id=task_id,
            reviewer__role='admin'
        )
        member_reviews = Review.objects.filter(
            type=ReviewType.TASK,
            task_id=task_id,
            reviewer__role='member'
        )
        
        admin_stats = admin_reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        member_stats = member_reviews.aggregate(
            avg_rating=Avg('rating'),
            count=Count('id')
        )
        
        admin_avg = admin_stats['avg_rating'] or 0
        member_avg = member_stats['avg_rating'] or 0
        admin_count = admin_stats['count'] or 0
        member_count = member_stats['count'] or 0
        
        if admin_count == 0 and member_count == 0:
            return Decimal('0.00')
        
        # 管理员评分权重为2，普通成员权重为1
        admin_weight = 2
        member_weight = 1
        
        total_weighted_score = (
            Decimal(str(admin_avg)) * admin_count * admin_weight +
            Decimal(str(member_avg)) * member_count * member_weight
        )
        total_weight = admin_count * admin_weight + member_count * member_weight
        
        if total_weight == 0:
            return Decimal('0.00')
        
        weighted_average = (total_weighted_score / total_weight).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return weighted_average
    
    @staticmethod
    def calculate_task_rating_adjustment(task_id):
        """计算任务评分调整系数"""
        weighted_average = ReviewService.calculate_weighted_average_rating(task_id)
        
        if weighted_average == 0:
            return Decimal('0.700')  # 没有评分时使用基础系数0.7
        
        # 调整系数 = (平均评分 / 10) * 0.3 + 0.7
        rating_factor = (weighted_average / Decimal('10')) * Decimal('0.3')
        adjustment_factor = rating_factor + Decimal('0.7')
        
        return adjustment_factor.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def get_user_monthly_reviews(user_id, month):
        """获取用户某月收到的所有评价"""
        return Review.objects.filter(
            type=ReviewType.MONTHLY,
            reviewee_id=user_id,
            month=month
        ).select_related('reviewer')
    
    @staticmethod
    def get_task_reviews_summary(task_id):
        """获取任务评价汇总信息"""
        reviews = Review.objects.filter(type=ReviewType.TASK, task_id=task_id)
        
        if not reviews.exists():
            return {
                'total_count': 0,
                'admin_count': 0,
                'member_count': 0,
                'average_rating': Decimal('0.00'),
                'weighted_average': Decimal('0.00'),
                'adjustment_factor': Decimal('0.700')
            }
        
        # 基本统计
        total_count = reviews.count()
        admin_count = reviews.filter(reviewer__role='admin').count()
        member_count = reviews.filter(reviewer__role='member').count()
        
        # 计算评分
        average_rating = ReviewService.calculate_average_rating(task_id)
        weighted_average = ReviewService.calculate_weighted_average_rating(task_id)
        adjustment_factor = ReviewService.calculate_task_rating_adjustment(task_id)
        
        return {
            'total_count': total_count,
            'admin_count': admin_count,
            'member_count': member_count,
            'average_rating': average_rating,
            'weighted_average': weighted_average,
            'adjustment_factor': adjustment_factor
        }
    
    @staticmethod
    def can_review_task(user, task):
        """检查用户是否可以评价某个任务"""
        # 任务必须已完成
        if not task.is_completed():
            return False, "只能对已完成的任务进行评价"
        
        # 用户不能评价自己参与的任务
        if user == task.owner or user in task.collaborators.all():
            return False, "不能评价自己参与的任务"
        
        # 检查是否已经评价过
        existing_review = Review.objects.filter(
            type=ReviewType.TASK,
            task=task,
            reviewer=user
        ).exists()
        
        if existing_review:
            return False, "您已经对该任务进行过评价"
        
        return True, "可以评价"
    
    @staticmethod
    def can_review_user_monthly(reviewer, reviewee, month):
        """检查是否可以进行月度评价"""
        # 不能评价自己
        if reviewer == reviewee:
            return False, "不能评价自己"
        
        # 检查是否已经评价过
        existing_review = Review.objects.filter(
            type=ReviewType.MONTHLY,
            reviewer=reviewer,
            reviewee=reviewee,
            month=month
        ).exists()
        
        if existing_review:
            return False, "您已经对该用户的该月度进行过评价"
        
        return True, "可以评价"
    
    @staticmethod
    def get_reviewable_tasks_for_user(user):
        """获取用户可以评价的任务列表"""
        from apps.tasks.models import Task, TaskStatus
        
        # 获取所有已完成的任务，排除用户参与的任务
        completed_tasks = Task.objects.filter(
            status=TaskStatus.COMPLETED
        ).exclude(
            Q(owner=user) | Q(collaborators=user)
        )
        
        # 排除已经评价过的任务
        reviewed_task_ids = Review.objects.filter(
            type=ReviewType.TASK,
            reviewer=user
        ).values_list('task_id', flat=True)
        
        reviewable_tasks = completed_tasks.exclude(id__in=reviewed_task_ids)
        
        return reviewable_tasks.select_related('owner').prefetch_related('collaborators')
    
    @staticmethod
    def get_reviewable_users_for_monthly(reviewer, month):
        """获取可以进行月度评价的用户列表"""
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # 获取所有活跃用户，排除自己
        all_users = User.objects.filter(is_active=True).exclude(id=reviewer.id)
        
        # 排除已经评价过的用户
        reviewed_user_ids = Review.objects.filter(
            type=ReviewType.MONTHLY,
            reviewer=reviewer,
            month=month
        ).values_list('reviewee_id', flat=True)
        
        reviewable_users = all_users.exclude(id__in=reviewed_user_ids)
        
        return reviewable_users