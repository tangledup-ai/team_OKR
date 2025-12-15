"""
Tests for review system
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date
from apps.tasks.models import Task, TaskStatus
from apps.users.models import Department
from .models import Review, ReviewType
from .services import ReviewService

User = get_user_model()


class ReviewModelTest(TestCase):
    """评价模型测试"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin'
        )
        
        self.member_user = User.objects.create_user(
            username='member@test.com',
            email='member@test.com',
            password='testpass123',
            name='成员',
            department=Department.SOFTWARE,
            role='member'
        )
        
        self.task = Task.objects.create(
            title='测试任务',
            description='测试任务描述',
            difficulty_score=5,
            revenue_amount=Decimal('1000.00'),
            status=TaskStatus.COMPLETED,
            owner=self.member_user,
            created_by=self.admin_user
        )
    
    def test_create_task_review(self):
        """测试创建任务评价"""
        review = Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.admin_user,
            rating=8,
            comment='很好的任务完成质量',
            is_anonymous=False
        )
        
        self.assertEqual(review.type, ReviewType.TASK)
        self.assertEqual(review.task, self.task)
        self.assertEqual(review.reviewer, self.admin_user)
        self.assertEqual(review.rating, 8)
        self.assertFalse(review.is_anonymous)
    
    def test_create_monthly_review(self):
        """测试创建月度评价"""
        review = Review.objects.create(
            type=ReviewType.MONTHLY,
            reviewee=self.member_user,
            reviewer=self.admin_user,
            rating=9,
            comment='本月表现优秀',
            month=date(2024, 1, 1),
            is_anonymous=True
        )
        
        self.assertEqual(review.type, ReviewType.MONTHLY)
        self.assertEqual(review.reviewee, self.member_user)
        self.assertEqual(review.reviewer, self.admin_user)
        self.assertEqual(review.rating, 9)
        self.assertTrue(review.is_anonymous)
    
    def test_rating_validation(self):
        """测试评分范围验证"""
        # 测试有效评分
        review = Review(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.admin_user,
            rating=5,
            comment='测试评论'
        )
        review.full_clean()  # 应该不抛出异常
        
        # 测试无效评分会在序列化器层面验证，这里只测试模型约束


class ReviewServiceTest(TestCase):
    """评价服务测试"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin'
        )
        
        self.member1 = User.objects.create_user(
            username='member1@test.com',
            email='member1@test.com',
            password='testpass123',
            name='成员1',
            department=Department.SOFTWARE,
            role='member'
        )
        
        self.member2 = User.objects.create_user(
            username='member2@test.com',
            email='member2@test.com',
            password='testpass123',
            name='成员2',
            department=Department.HARDWARE,
            role='member'
        )
        
        self.task = Task.objects.create(
            title='测试任务',
            description='测试任务描述',
            difficulty_score=6,
            revenue_amount=Decimal('1500.00'),
            status=TaskStatus.COMPLETED,
            owner=self.member1,
            created_by=self.admin_user
        )
    
    def test_calculate_average_rating(self):
        """测试计算平均评分"""
        # 创建几个评价
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.admin_user,
            rating=8,
            comment='很好'
        )
        
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.member2,
            rating=6,
            comment='一般'
        )
        
        avg_rating = ReviewService.calculate_average_rating(self.task.id)
        self.assertEqual(avg_rating, Decimal('7.00'))
    
    def test_calculate_weighted_average_rating(self):
        """测试计算加权平均评分"""
        # 管理员评价
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.admin_user,
            rating=8,
            comment='管理员评价'
        )
        
        # 普通成员评价
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.member2,
            rating=6,
            comment='成员评价'
        )
        
        # 加权平均 = (8*1*2 + 6*1*1) / (1*2 + 1*1) = 22/3 = 7.33
        weighted_avg = ReviewService.calculate_weighted_average_rating(self.task.id)
        self.assertEqual(weighted_avg, Decimal('7.33'))
    
    def test_calculate_task_rating_adjustment(self):
        """测试计算任务评分调整系数"""
        # 创建评价
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.admin_user,
            rating=8,
            comment='很好'
        )
        
        adjustment = ReviewService.calculate_task_rating_adjustment(self.task.id)
        # 调整系数 = (8/10) * 0.3 + 0.7 = 0.24 + 0.7 = 0.94
        self.assertEqual(adjustment, Decimal('0.940'))
    
    def test_can_review_task(self):
        """测试任务评价权限检查"""
        # 任务参与者不能评价
        can_review, message = ReviewService.can_review_task(self.member1, self.task)
        self.assertFalse(can_review)
        self.assertIn('不能评价自己参与的任务', message)
        
        # 其他用户可以评价
        can_review, message = ReviewService.can_review_task(self.member2, self.task)
        self.assertTrue(can_review)
        
        # 已评价过的用户不能再评价
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.member2,
            rating=7,
            comment='已评价'
        )
        
        can_review, message = ReviewService.can_review_task(self.member2, self.task)
        self.assertFalse(can_review)
        self.assertIn('已经对该任务进行过评价', message)


class ReviewAPITest(APITestCase):
    """评价API测试"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin@test.com',
            email='admin@test.com',
            password='testpass123',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin'
        )
        
        self.member1 = User.objects.create_user(
            username='member1@test.com',
            email='member1@test.com',
            password='testpass123',
            name='成员1',
            department=Department.SOFTWARE,
            role='member'
        )
        
        self.member2 = User.objects.create_user(
            username='member2@test.com',
            email='member2@test.com',
            password='testpass123',
            name='成员2',
            department=Department.HARDWARE,
            role='member'
        )
        
        self.task = Task.objects.create(
            title='测试任务',
            description='测试任务描述',
            difficulty_score=7,
            revenue_amount=Decimal('2000.00'),
            status=TaskStatus.COMPLETED,
            owner=self.member1,
            created_by=self.admin_user
        )
    
    def test_submit_task_review(self):
        """测试提交任务评价"""
        self.client.force_authenticate(user=self.member2)
        
        url = reverse('reviews:review-submit-task-review')
        data = {
            'task': str(self.task.id),
            'rating': 8,
            'comment': '任务完成得很好',
            'is_anonymous': False
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证评价已创建
        review = Review.objects.get(task=self.task, reviewer=self.member2)
        self.assertEqual(review.rating, 8)
        self.assertEqual(review.comment, '任务完成得很好')
        self.assertFalse(review.is_anonymous)
    
    def test_submit_task_review_validation(self):
        """测试任务评价验证"""
        self.client.force_authenticate(user=self.member2)
        
        url = reverse('reviews:review-submit-task-review')
        
        # 测试评分范围验证
        data = {
            'task': str(self.task.id),
            'rating': 11,  # 超出范围
            'comment': '测试评论',
            'is_anonymous': False
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rating', response.data)  # Check that rating field has validation error
    
    def test_submit_monthly_review(self):
        """测试提交月度评价"""
        self.client.force_authenticate(user=self.member2)
        
        url = reverse('reviews:review-submit-monthly-review')
        data = {
            'reviewee': str(self.member1.id),
            'rating': 9,
            'comment': '本月表现优秀',
            'month': '2024-01-01',
            'is_anonymous': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 验证评价已创建
        review = Review.objects.get(
            type=ReviewType.MONTHLY,
            reviewee=self.member1,
            reviewer=self.member2
        )
        self.assertEqual(review.rating, 9)
        self.assertTrue(review.is_anonymous)
    
    def test_get_task_reviews(self):
        """测试获取任务评价列表"""
        # 创建几个评价
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.admin_user,
            rating=8,
            comment='管理员评价'
        )
        
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.member2,
            rating=7,
            comment='成员评价',
            is_anonymous=True
        )
        
        self.client.force_authenticate(user=self.member1)
        
        url = reverse('reviews:review-list-task-reviews', kwargs={'task_id': str(self.task.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # 检查匿名评价的处理
        anonymous_review = next(r for r in response.data if r['is_anonymous'])
        self.assertEqual(anonymous_review['reviewer_name'], '匿名')
    
    def test_get_task_review_summary(self):
        """测试获取任务评价汇总"""
        # 创建评价
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.admin_user,
            rating=8,
            comment='管理员评价'
        )
        
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task,
            reviewer=self.member2,
            rating=6,
            comment='成员评价'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('reviews:review-get-task-review-summary', kwargs={'task_id': str(self.task.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertEqual(data['task_id'], str(self.task.id))
        self.assertEqual(data['review_count'], 2)
        self.assertEqual(data['admin_review_count'], 1)
        self.assertEqual(data['member_review_count'], 1)
        
        # 验证加权平均评分计算
        # (8*1*2 + 6*1*1) / (1*2 + 1*1) = 22/3 = 7.33
        self.assertEqual(Decimal(str(data['average_rating'])), Decimal('7.33'))