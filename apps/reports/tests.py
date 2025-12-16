"""
Tests for reports app
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
import json
from .models import MonthlyEvaluation, PeerEvaluation, WorkHours, AdminEvaluationHistory
from apps.users.models import Department

User = get_user_model()


class MonthlyEvaluationModelTest(TestCase):
    """月度评价模型测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='测试用户',
            department=Department.SOFTWARE
        )
        
    def test_create_monthly_evaluation(self):
        """测试创建月度评价"""
        evaluation = MonthlyEvaluation.objects.create(
            user=self.user,
            month=date(2024, 1, 1),
            culture_understanding_score=8,
            culture_understanding_text='理解企业文化',
            culture_understanding_option='选项A',
            team_fit_option='选项B',
            team_fit_text='团队契合度很好',
            team_fit_ranking=['user1', 'user2'],
            monthly_growth_score=7,
            monthly_growth_text='本月成长很多',
            monthly_growth_option='选项C',
            biggest_contribution_score=9,
            biggest_contribution_text='完成了重要项目',
            biggest_contribution_option='选项D'
        )
        
        self.assertEqual(evaluation.user, self.user)
        self.assertEqual(evaluation.culture_understanding_score, 8)
        self.assertEqual(evaluation.monthly_growth_score, 7)
        self.assertEqual(evaluation.biggest_contribution_score, 9)
        self.assertEqual(evaluation.team_fit_ranking, ['user1', 'user2'])
        
    def test_unique_user_month_constraint(self):
        """测试用户月份唯一约束"""
        MonthlyEvaluation.objects.create(
            user=self.user,
            month=date(2024, 1, 1),
            culture_understanding_score=8,
            culture_understanding_text='理解企业文化',
            culture_understanding_option='选项A',
            team_fit_option='选项B',
            team_fit_text='团队契合度很好',
            team_fit_ranking=[],
            monthly_growth_score=7,
            monthly_growth_text='本月成长很多',
            monthly_growth_option='选项C',
            biggest_contribution_score=9,
            biggest_contribution_text='完成了重要项目',
            biggest_contribution_option='选项D'
        )
        
        # 尝试创建相同用户相同月份的评价应该失败
        with self.assertRaises(Exception):
            MonthlyEvaluation.objects.create(
                user=self.user,
                month=date(2024, 1, 1),
                culture_understanding_score=5,
                culture_understanding_text='另一个评价',
                culture_understanding_option='选项E',
                team_fit_option='选项F',
                team_fit_text='另一个团队契合度',
                team_fit_ranking=[],
                monthly_growth_score=6,
                monthly_growth_text='另一个成长',
                monthly_growth_option='选项G',
                biggest_contribution_score=8,
                biggest_contribution_text='另一个贡献',
                biggest_contribution_option='选项H'
            )


class PeerEvaluationModelTest(TestCase):
    """他人评价模型测试"""
    
    def setUp(self):
        self.evaluator = User.objects.create_user(
            username='evaluator',
            email='evaluator@example.com',
            password='testpass123',
            name='评价人',
            department=Department.SOFTWARE
        )
        
        self.evaluee = User.objects.create_user(
            username='evaluee',
            email='evaluee@example.com',
            password='testpass123',
            name='被评价人',
            department=Department.HARDWARE
        )
        
        self.monthly_evaluation = MonthlyEvaluation.objects.create(
            user=self.evaluee,
            month=date(2024, 1, 1),
            culture_understanding_score=8,
            culture_understanding_text='理解企业文化',
            culture_understanding_option='选项A',
            team_fit_option='选项B',
            team_fit_text='团队契合度很好',
            team_fit_ranking=[],
            monthly_growth_score=7,
            monthly_growth_text='本月成长很多',
            monthly_growth_option='选项C',
            biggest_contribution_score=9,
            biggest_contribution_text='完成了重要项目',
            biggest_contribution_option='选项D'
        )
        
    def test_create_peer_evaluation(self):
        """测试创建他人评价"""
        peer_evaluation = PeerEvaluation.objects.create(
            monthly_evaluation=self.monthly_evaluation,
            evaluator=self.evaluator,
            score=8,
            ranking=2,
            comment='表现很好',
            is_anonymous=False
        )
        
        self.assertEqual(peer_evaluation.evaluator, self.evaluator)
        self.assertEqual(peer_evaluation.monthly_evaluation, self.monthly_evaluation)
        self.assertEqual(peer_evaluation.score, 8)
        self.assertEqual(peer_evaluation.ranking, 2)
        self.assertFalse(peer_evaluation.is_anonymous)
        
    def test_unique_evaluation_evaluator_constraint(self):
        """测试评价和评价人唯一约束"""
        PeerEvaluation.objects.create(
            monthly_evaluation=self.monthly_evaluation,
            evaluator=self.evaluator,
            score=8,
            ranking=2,
            comment='表现很好',
            is_anonymous=False
        )
        
        # 尝试创建相同评价人对相同月度评价的重复评价应该失败
        with self.assertRaises(Exception):
            PeerEvaluation.objects.create(
                monthly_evaluation=self.monthly_evaluation,
                evaluator=self.evaluator,
                score=7,
                ranking=3,
                comment='另一个评价',
                is_anonymous=True
            )


class MonthlyEvaluationAPITest(APITestCase):
    """月度评价API测试"""
    
    def setUp(self):
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            name='用户1',
            department=Department.SOFTWARE
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            name='用户2',
            department=Department.HARDWARE
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin'
        )
        
        # 获取JWT令牌
        self.user1_token = str(RefreshToken.for_user(self.user1).access_token)
        self.user2_token = str(RefreshToken.for_user(self.user2).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)
        
    def test_submit_self_evaluation(self):
        """测试提交自我评价"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_token}')
        
        data = {
            'month': '2024-01-01',
            'culture_understanding_score': 8,
            'culture_understanding_text': '理解企业文化',
            'culture_understanding_option': '选项A',
            'team_fit_option': '选项B',
            'team_fit_text': '团队契合度很好',
            'team_fit_ranking': [str(self.user2.id), str(self.admin_user.id)],
            'monthly_growth_score': 7,
            'monthly_growth_text': '本月成长很多',
            'monthly_growth_option': '选项C',
            'biggest_contribution_score': 9,
            'biggest_contribution_text': '完成了重要项目',
            'biggest_contribution_option': '选项D'
        }
        
        url = reverse('reports:monthly-evaluations-submit-self-evaluation')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MonthlyEvaluation.objects.count(), 1)
        
        evaluation = MonthlyEvaluation.objects.first()
        self.assertEqual(evaluation.user, self.user1)
        self.assertEqual(evaluation.culture_understanding_score, 8)
        self.assertEqual(evaluation.team_fit_ranking, [str(self.user2.id), str(self.admin_user.id)])
        
    def test_submit_self_evaluation_invalid_score(self):
        """测试提交无效分值的自我评价"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_token}')
        
        data = {
            'month': '2024-01-01',
            'culture_understanding_score': 11,  # 超出范围
            'culture_understanding_text': '理解企业文化',
            'culture_understanding_option': '选项A',
            'team_fit_option': '选项B',
            'team_fit_text': '团队契合度很好',
            'team_fit_ranking': [str(self.user2.id), str(self.admin_user.id)],
            'monthly_growth_score': 7,
            'monthly_growth_text': '本月成长很多',
            'monthly_growth_option': '选项C',
            'biggest_contribution_score': 9,
            'biggest_contribution_text': '完成了重要项目',
            'biggest_contribution_option': '选项D'
        }
        
        url = reverse('reports:monthly-evaluations-submit-self-evaluation')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MonthlyEvaluation.objects.count(), 0)
        
    def test_submit_self_evaluation_invalid_ranking(self):
        """测试提交无效排名的自我评价"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_token}')
        
        data = {
            'month': '2024-01-01',
            'culture_understanding_score': 8,
            'culture_understanding_text': '理解企业文化',
            'culture_understanding_option': '选项A',
            'team_fit_option': '选项B',
            'team_fit_text': '团队契合度很好',
            'team_fit_ranking': [str(self.user1.id)],  # 包含自己的ID
            'monthly_growth_score': 7,
            'monthly_growth_text': '本月成长很多',
            'monthly_growth_option': '选项C',
            'biggest_contribution_score': 9,
            'biggest_contribution_text': '完成了重要项目',
            'biggest_contribution_option': '选项D'
        }
        
        url = reverse('reports:monthly-evaluations-submit-self-evaluation')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MonthlyEvaluation.objects.count(), 0)
        
    def test_submit_peer_evaluation(self):
        """测试提交他人评价"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user1_token}')
        
        data = {
            'evaluee_id': str(self.user2.id),
            'score': 8,
            'ranking': 1,
            'comment': '表现很好',
            'is_anonymous': False
        }
        
        url = reverse('reports:monthly-evaluations-submit-peer-evaluation')
        response = self.client.post(f'{url}?month=2024-01-01', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PeerEvaluation.objects.count(), 1)


class AdminEvaluationHistoryTest(TestCase):
    """管理员评价历史测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            name='管理员',
            department=Department.HARDWARE,
            role='admin'
        )
        
        self.member_user = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='testpass123',
            name='成员',
            department=Department.SOFTWARE,
            role='member'
        )
        
        self.monthly_evaluation = MonthlyEvaluation.objects.create(
            user=self.member_user,
            month=date(2024, 1, 1),
            culture_understanding_score=8,
            culture_understanding_text='理解企业文化',
            culture_understanding_option='选项A',
            team_fit_option='选项B',
            team_fit_text='团队契合度',
            team_fit_ranking=[str(self.admin_user.id)],
            monthly_growth_score=7,
            monthly_growth_text='本月成长',
            monthly_growth_option='选项C',
            biggest_contribution_score=9,
            biggest_contribution_text='最大贡献',
            biggest_contribution_option='选项D'
        )
    
    def test_admin_evaluation_history_creation(self):
        """测试管理员评价历史记录创建"""
        history = AdminEvaluationHistory.objects.create(
            monthly_evaluation=self.monthly_evaluation,
            admin_user=self.admin_user,
            previous_score=None,
            new_score=8,
            previous_comment='',
            new_comment='表现良好',
            action_type='create'
        )
        
        self.assertEqual(history.monthly_evaluation, self.monthly_evaluation)
        self.assertEqual(history.admin_user, self.admin_user)
        self.assertEqual(history.new_score, 8)
        self.assertEqual(history.action_type, 'create')
    
    def test_admin_evaluation_history_update(self):
        """测试管理员评价历史记录更新"""
        # 创建初始历史记录
        AdminEvaluationHistory.objects.create(
            monthly_evaluation=self.monthly_evaluation,
            admin_user=self.admin_user,
            previous_score=None,
            new_score=8,
            previous_comment='',
            new_comment='表现良好',
            action_type='create'
        )
        
        # 创建更新历史记录
        update_history = AdminEvaluationHistory.objects.create(
            monthly_evaluation=self.monthly_evaluation,
            admin_user=self.admin_user,
            previous_score=8,
            new_score=9,
            previous_comment='表现良好',
            new_comment='表现优秀',
            action_type='update'
        )
        
        self.assertEqual(AdminEvaluationHistory.objects.count(), 2)
        self.assertEqual(update_history.previous_score, 8)
        self.assertEqual(update_history.new_score, 9)
        self.assertEqual(update_history.action_type, 'update')


class AdminEvaluationAPITest(APITestCase):
    """管理员评价API测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            name='管理员',
            department=Department.HARDWARE,
            role='admin'
        )
        
        self.member_user = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='testpass123',
            name='成员',
            department=Department.SOFTWARE,
            role='member'
        )
        
        self.monthly_evaluation = MonthlyEvaluation.objects.create(
            user=self.member_user,
            month=date(2024, 1, 1),
            culture_understanding_score=8,
            culture_understanding_text='理解企业文化',
            culture_understanding_option='选项A',
            team_fit_option='选项B',
            team_fit_text='团队契合度',
            team_fit_ranking=[str(self.admin_user.id)],
            monthly_growth_score=7,
            monthly_growth_text='本月成长',
            monthly_growth_option='选项C',
            biggest_contribution_score=9,
            biggest_contribution_text='最大贡献',
            biggest_contribution_option='选项D'
        )
    
    def test_admin_submit_final_evaluation(self):
        """测试管理员提交最终评价"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = f'/api/reports/monthly-evaluations/{self.monthly_evaluation.id}/admin-evaluation/'
        data = {
            'admin_final_score': 9,
            'admin_final_comment': '表现优秀，继续保持'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证评价已更新
        self.monthly_evaluation.refresh_from_db()
        self.assertEqual(self.monthly_evaluation.admin_final_score, 9)
        self.assertEqual(self.monthly_evaluation.admin_final_comment, '表现优秀，继续保持')
        self.assertEqual(self.monthly_evaluation.admin_evaluated_by, self.admin_user)
        
        # 验证历史记录已创建
        self.assertEqual(AdminEvaluationHistory.objects.count(), 1)
        history = AdminEvaluationHistory.objects.first()
        self.assertEqual(history.action_type, 'create')
        self.assertEqual(history.new_score, 9)
    
    def test_admin_update_final_evaluation(self):
        """测试管理员更新最终评价"""
        # 先提交一次评价
        self.monthly_evaluation.admin_final_score = 8
        self.monthly_evaluation.admin_final_comment = '表现良好'
        self.monthly_evaluation.admin_evaluated_by = self.admin_user
        self.monthly_evaluation.save()
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = f'/api/reports/monthly-evaluations/{self.monthly_evaluation.id}/admin-evaluation/'
        data = {
            'admin_final_score': 9,
            'admin_final_comment': '表现优秀，继续保持'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 验证历史记录已创建
        self.assertEqual(AdminEvaluationHistory.objects.count(), 1)
        history = AdminEvaluationHistory.objects.first()
        self.assertEqual(history.action_type, 'update')
        self.assertEqual(history.previous_score, 8)
        self.assertEqual(history.new_score, 9)
    
    def test_non_admin_cannot_submit_evaluation(self):
        """测试非管理员不能提交最终评价"""
        self.client.force_authenticate(user=self.member_user)
        
        url = f'/api/reports/monthly-evaluations/{self.monthly_evaluation.id}/admin-evaluation/'
        data = {
            'admin_final_score': 9,
            'admin_final_comment': '表现优秀'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_view_all_evaluations(self):
        """测试管理员查看所有成员评价"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api/reports/monthly-evaluations/admin-view-all/?month=2024-01-01'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user']['name'], '成员')
    
    def test_non_admin_cannot_view_all_evaluations(self):
        """测试非管理员不能查看所有成员评价"""
        self.client.force_authenticate(user=self.member_user)
        
        url = '/api/reports/monthly-evaluations/admin-view-all/?month=2024-01-01'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_view_evaluation_history(self):
        """测试管理员查看评价历史"""
        # 创建历史记录
        AdminEvaluationHistory.objects.create(
            monthly_evaluation=self.monthly_evaluation,
            admin_user=self.admin_user,
            previous_score=None,
            new_score=8,
            previous_comment='',
            new_comment='表现良好',
            action_type='create'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api/reports/monthly-evaluations/admin-history/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['action_type'], 'create')
    
    def test_batch_admin_evaluation(self):
        """测试批量管理员评价"""
        # 创建另一个成员和评价
        member2 = User.objects.create_user(
            username='member2',
            email='member2@test.com',
            password='testpass123',
            name='成员2',
            department=Department.MARKETING,
            role='member'
        )
        
        evaluation2 = MonthlyEvaluation.objects.create(
            user=member2,
            month=date(2024, 1, 1),
            culture_understanding_score=7,
            culture_understanding_text='理解企业文化',
            culture_understanding_option='选项A',
            team_fit_option='选项B',
            team_fit_text='团队契合度',
            team_fit_ranking=[str(self.admin_user.id), str(self.member_user.id)],
            monthly_growth_score=8,
            monthly_growth_text='本月成长',
            monthly_growth_option='选项C',
            biggest_contribution_score=6,
            biggest_contribution_text='最大贡献',
            biggest_contribution_option='选项D'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api/reports/monthly-evaluations/batch-admin-evaluation/'
        data = {
            'evaluations': [
                {
                    'evaluation_id': str(self.monthly_evaluation.id),
                    'admin_final_score': 9,
                    'admin_final_comment': '表现优秀'
                },
                {
                    'evaluation_id': str(evaluation2.id),
                    'admin_final_score': 7,
                    'admin_final_comment': '表现良好'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success_count'], 2)
        self.assertEqual(response.data['error_count'], 0)
        
        # 验证评价已更新
        self.monthly_evaluation.refresh_from_db()
        evaluation2.refresh_from_db()
        
        self.assertEqual(self.monthly_evaluation.admin_final_score, 9)
        self.assertEqual(evaluation2.admin_final_score, 7)
        
        # 验证历史记录已创建
        self.assertEqual(AdminEvaluationHistory.objects.count(), 2)
        



class WorkHoursAPITest(APITestCase):
    """工作小时API测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123',
            name='用户',
            department=Department.SOFTWARE
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin'
        )
        
        self.user_token = str(RefreshToken.for_user(self.user).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)
        
    def test_admin_create_work_hours(self):
        """测试管理员创建工作小时记录"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'user_id': str(self.user.id),
            'month': '2024-01-01',
            'hours': '160.50'
        }
        
        url = reverse('reports:work-hours-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WorkHours.objects.count(), 1)
        
        work_hours = WorkHours.objects.first()
        self.assertEqual(work_hours.user, self.user)
        self.assertEqual(work_hours.hours, Decimal('160.50'))
        self.assertEqual(work_hours.recorded_by, self.admin_user)
        
    def test_non_admin_cannot_create_work_hours(self):
        """测试非管理员不能创建工作小时记录"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.user_token}')
        
        data = {
            'user_id': str(self.user.id),
            'month': '2024-01-01',
            'hours': '160.50'
        }
        
        url = reverse('reports:work-hours-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(WorkHours.objects.count(), 0)
        
    def test_create_work_hours_invalid_hours(self):
        """测试创建无效工作小时记录"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')
        
        data = {
            'user_id': str(self.user.id),
            'month': '2024-01-01',
            'hours': '-10.00'  # 负数
        }
        
        url = reverse('reports:work-hours-list')
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(WorkHours.objects.count(), 0)


class PerformanceScoreServiceTest(TestCase):
    """绩效分值计算服务测试"""
    
    def setUp(self):
        """设置测试数据"""
        from .services import PerformanceScoreService
        from apps.tasks.models import Task, TaskStatus, ScoreDistribution, ScoreAllocation
        from apps.reviews.models import Review, ReviewType
        from django.utils import timezone
        
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            name='用户1',
            department=Department.SOFTWARE
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            name='用户2',
            department=Department.SOFTWARE
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin'
        )
        
        # 创建测试任务
        self.task1 = Task.objects.create(
            title='测试任务1',
            description='测试任务描述',
            difficulty_score=8,
            revenue_amount=Decimal('5000.00'),
            status=TaskStatus.COMPLETED,
            owner=self.user1,
            created_by=self.admin_user,
            completed_at=timezone.make_aware(datetime(2024, 1, 15, 10, 0, 0))
        )
        
        self.task2 = Task.objects.create(
            title='测试任务2',
            description='测试任务描述2',
            difficulty_score=6,
            revenue_amount=Decimal('3000.00'),
            status=TaskStatus.COMPLETED,
            owner=self.user1,
            created_by=self.admin_user,
            completed_at=timezone.make_aware(datetime(2024, 1, 20, 14, 0, 0))
        )
        
        # 添加协作者
        self.task1.collaborators.add(self.user2)
        
        # 创建分值分配
        self.distribution1 = ScoreDistribution.objects.create(
            task=self.task1,
            total_score=Decimal('8.00'),
            penalty_coefficient=Decimal('1.000')
        )
        
        ScoreAllocation.objects.create(
            distribution=self.distribution1,
            user=self.user1,
            base_score=Decimal('4.00'),
            adjusted_score=Decimal('4.00'),
            percentage=Decimal('50.00')
        )
        
        ScoreAllocation.objects.create(
            distribution=self.distribution1,
            user=self.user2,
            base_score=Decimal('4.00'),
            adjusted_score=Decimal('4.00'),
            percentage=Decimal('50.00')
        )
        
        self.distribution2 = ScoreDistribution.objects.create(
            task=self.task2,
            total_score=Decimal('6.00'),
            penalty_coefficient=Decimal('1.000')
        )
        
        ScoreAllocation.objects.create(
            distribution=self.distribution2,
            user=self.user1,
            base_score=Decimal('6.00'),
            adjusted_score=Decimal('6.00'),
            percentage=Decimal('100.00')
        )
        
        # 创建工作小时记录
        WorkHours.objects.create(
            user=self.user1,
            month=date(2024, 1, 1),
            hours=Decimal('250.00'),
            recorded_by=self.admin_user
        )
        
        # 创建任务评价
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task1,
            reviewer=self.admin_user,
            rating=9,
            comment='任务完成得很好',
            is_anonymous=False
        )
        
        Review.objects.create(
            type=ReviewType.TASK,
            task=self.task2,
            reviewer=self.user2,
            rating=7,
            comment='任务完成得不错',
            is_anonymous=False
        )
        
        # 创建月度评价
        self.monthly_evaluation = MonthlyEvaluation.objects.create(
            user=self.user1,
            month=date(2024, 1, 1),
            culture_understanding_score=8,
            culture_understanding_text='理解企业文化',
            culture_understanding_option='选项A',
            team_fit_option='选项B',
            team_fit_text='团队契合度很好',
            team_fit_ranking=[str(self.user2.id), str(self.admin_user.id)],
            monthly_growth_score=7,
            monthly_growth_text='本月成长很多',
            monthly_growth_option='选项C',
            biggest_contribution_score=9,
            biggest_contribution_text='完成了重要项目',
            biggest_contribution_option='选项D',
            admin_final_score=8,
            admin_final_comment='表现良好',
            admin_evaluated_by=self.admin_user
        )
        
        # 创建他人评价
        PeerEvaluation.objects.create(
            monthly_evaluation=self.monthly_evaluation,
            evaluator=self.user2,
            score=8,
            ranking=1,
            comment='表现很好',
            is_anonymous=False
        )
        
        self.service = PerformanceScoreService
        
    def test_calculate_work_hours_score(self):
        """测试工作小时标准化计算"""
        hours, score = self.service._calculate_work_hours_score(self.user1, date(2024, 1, 1))
        
        self.assertEqual(hours, Decimal('250.00'))
        # 250 / 300 * 10 = 8.33
        expected_score = Decimal('8.33')
        self.assertEqual(score, expected_score)
        
    def test_calculate_work_hours_score_no_record(self):
        """测试没有工作小时记录的情况"""
        hours, score = self.service._calculate_work_hours_score(self.user2, date(2024, 1, 1))
        
        self.assertEqual(hours, Decimal('0.00'))
        self.assertEqual(score, Decimal('0.00'))
        
    def test_calculate_work_hours_score_over_limit(self):
        """测试工作小时超过满分基准的情况"""
        WorkHours.objects.create(
            user=self.user2,
            month=date(2024, 1, 1),
            hours=Decimal('400.00'),  # 超过300小时
            recorded_by=self.admin_user
        )
        
        hours, score = self.service._calculate_work_hours_score(self.user2, date(2024, 1, 1))
        
        self.assertEqual(hours, Decimal('400.00'))
        self.assertEqual(score, Decimal('10.00'))  # 最大值限制为10
        
    def test_calculate_completion_rate_score(self):
        """测试完成任务比例标准化计算"""
        completion_rate, score = self.service._calculate_completion_rate_score(self.user1, date(2024, 1, 1))
        
        # user1有2个任务，都已完成，完成率100%
        self.assertEqual(completion_rate, Decimal('100.00'))
        self.assertEqual(score, Decimal('10.00'))
        
    def test_calculate_completion_rate_score_no_tasks(self):
        """测试没有分配任务的情况"""
        # 创建一个新用户，没有分配任务
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123',
            name='用户3',
            department=Department.HARDWARE
        )
        
        completion_rate, score = self.service._calculate_completion_rate_score(user3, date(2024, 1, 1))
        
        self.assertEqual(completion_rate, Decimal('0.00'))
        self.assertEqual(score, Decimal('0.00'))
        
    def test_calculate_avg_difficulty_score(self):
        """测试难度平均分计算"""
        avg_difficulty = self.service._calculate_avg_difficulty_score(self.user1, date(2024, 1, 1))
        
        # user1完成了难度为8和6的任务，平均难度为7
        expected_avg = Decimal('7.00')
        self.assertEqual(avg_difficulty, expected_avg)
        
    def test_calculate_revenue_score(self):
        """测试变现金额标准化计算"""
        total_revenue, score = self.service._calculate_revenue_score(self.user1, date(2024, 1, 1))
        
        # user1完成的任务变现金额总和为8000
        self.assertEqual(total_revenue, Decimal('8000.00'))
        # 8000 / 10000 * 5 = 4.00
        expected_score = Decimal('4.00')
        self.assertEqual(score, expected_score)
        
    def test_calculate_department_avg_score(self):
        """测试部门平均分计算"""
        dept_avg = self.service._calculate_department_avg_score(Department.SOFTWARE, date(2024, 1, 1))
        
        # SOFTWARE部门有user1(10分)、user2(4分)、admin_user(0分)，平均分为14/3=4.67
        expected_avg = Decimal('4.67')
        self.assertEqual(dept_avg, expected_avg)
        
    def test_calculate_task_rating_score(self):
        """测试任务评分标准化计算"""
        rating_score = self.service._calculate_task_rating_score(self.user1, date(2024, 1, 1))
        
        # user1的任务1被admin评分9分(权重2)，任务2被user2评分7分(权重1)
        # 加权平均 = (9*1*2 + 7*1*1) / (1*2 + 1*1) = 25/3 = 8.33
        expected_score = Decimal('8.33')
        self.assertEqual(rating_score, expected_score)
        
    def test_calculate_culture_understanding_score(self):
        """测试企业文化理解分数计算"""
        score = self.service._calculate_culture_understanding_score(self.user1, date(2024, 1, 1))
        
        self.assertEqual(score, Decimal('8.00'))
        
    def test_calculate_monthly_growth_score(self):
        """测试本月成长分数计算"""
        score = self.service._calculate_monthly_growth_score(self.user1, date(2024, 1, 1))
        
        self.assertEqual(score, Decimal('7.00'))
        
    def test_calculate_biggest_contribution_score(self):
        """测试本月最大贡献分数计算"""
        score = self.service._calculate_biggest_contribution_score(self.user1, date(2024, 1, 1))
        
        self.assertEqual(score, Decimal('9.00'))
        
    def test_get_admin_final_score(self):
        """测试获取管理员最终评分"""
        score = self.service._get_admin_final_score(self.user1, date(2024, 1, 1))
        
        self.assertEqual(score, Decimal('8.00'))
        
    def test_calculate_peer_evaluation_score(self):
        """测试他人评价综合分数计算"""
        score = self.service._calculate_peer_evaluation_score(self.user1, date(2024, 1, 1))
        
        # 评分8分，排名1（假设总共3个用户），排名分数=(3-1+1)/3*10=10
        # 综合分数=(8+10)/2=9
        expected_score = Decimal('9.00')
        self.assertEqual(score, expected_score)
        
    def test_calculate_weighted_final_score(self):
        """测试加权平均最终分值计算"""
        final_score = self.service._calculate_weighted_final_score(
            Decimal('8.33'),  # work_hours_score
            Decimal('10.00'), # completion_rate_score
            Decimal('7.00'),  # avg_difficulty_score
            Decimal('4.00'),  # revenue_score
            Decimal('4.67'),  # department_avg_score
            Decimal('8.33'),  # task_rating_score
            Decimal('8.00'),  # culture_understanding_score
            Decimal('5.00'),  # team_fit_score
            Decimal('7.00'),  # monthly_growth_score
            Decimal('9.00'),  # biggest_contribution_score
            Decimal('9.00'),  # peer_evaluation_score
            Decimal('8.00')   # admin_final_score
        )
        
        # 计算加权总分
        expected_weighted_sum = (
            Decimal('8.33') * Decimal('0.10') +  # 工作小时 10%
            Decimal('10.00') * Decimal('0.15') + # 完成任务比例 15%
            Decimal('7.00') * Decimal('0.10') +  # 难度平均分 10%
            Decimal('4.00') * Decimal('0.10') +  # 变现金额 10%
            Decimal('4.67') * Decimal('0.05') +  # 部门平均分 5%
            Decimal('8.33') * Decimal('0.10') +  # 任务评分 10%
            Decimal('8.00') * Decimal('0.05') +  # 企业文化理解 5%
            Decimal('5.00') * Decimal('0.03') +  # 团队契合度 3%
            Decimal('7.00') * Decimal('0.03') +  # 本月成长 3%
            Decimal('9.00') * Decimal('0.04') +  # 本月最大贡献 4%
            Decimal('9.00') * Decimal('0.05') +  # 他人评价 5%
            Decimal('8.00') * Decimal('0.15')    # 管理员最终评分 15%
        )
        
        expected_final = (expected_weighted_sum * 10).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        self.assertEqual(final_score, expected_final)
        
    def test_calculate_user_performance_score(self):
        """测试计算用户绩效分值"""
        performance_score = self.service.calculate_user_performance_score(self.user1, date(2024, 1, 1))
        
        self.assertIsNotNone(performance_score)
        self.assertEqual(performance_score.user, self.user1)
        self.assertEqual(performance_score.month, date(2024, 1, 1))
        self.assertEqual(performance_score.work_hours, Decimal('250.00'))
        self.assertEqual(performance_score.work_hours_score, Decimal('8.33'))
        self.assertEqual(performance_score.completion_rate, Decimal('100.00'))
        self.assertEqual(performance_score.completion_rate_score, Decimal('10.00'))
        self.assertEqual(performance_score.avg_difficulty_score, Decimal('7.00'))
        self.assertEqual(performance_score.total_revenue, Decimal('8000.00'))
        self.assertEqual(performance_score.revenue_score, Decimal('4.00'))
        self.assertTrue(performance_score.final_score > 0)
        self.assertEqual(performance_score.rank, 0)  # 排名在批量计算后更新
        
    def test_calculate_monthly_rankings(self):
        """测试计算月度排名"""
        # 先计算两个用户的绩效分值
        score1 = self.service.calculate_user_performance_score(self.user1, date(2024, 1, 1))
        score2 = self.service.calculate_user_performance_score(self.user2, date(2024, 1, 1))
        
        # 计算排名
        rankings = self.service.calculate_monthly_rankings(date(2024, 1, 1))
        
        self.assertEqual(len(rankings), 2)
        
        # 刷新数据
        score1.refresh_from_db()
        score2.refresh_from_db()
        
        # 验证排名已更新
        self.assertTrue(score1.rank > 0)
        self.assertTrue(score2.rank > 0)
        
        # 分数高的排名应该更靠前
        if score1.final_score > score2.final_score:
            self.assertTrue(score1.rank < score2.rank)
        elif score2.final_score > score1.final_score:
            self.assertTrue(score2.rank < score1.rank)
        else:
            # 分数相同时按用户名排序
            self.assertTrue(score1.rank != score2.rank)
            
    def test_batch_calculate_monthly_scores(self):
        """测试批量计算月度绩效分值"""
        scores = self.service.batch_calculate_monthly_scores(date(2024, 1, 1))
        
        # 应该为所有活跃用户计算分值
        active_user_count = User.objects.filter(is_active=True).count()
        self.assertEqual(len(scores), active_user_count)
        
        # 验证排名已计算
        for score in scores:
            self.assertTrue(score.rank > 0)
            
    def test_recalculate_user_score(self):
        """测试重新计算用户绩效分值"""
        # 先计算初始分值
        initial_score = self.service.calculate_user_performance_score(self.user1, date(2024, 1, 1))
        initial_final_score = initial_score.final_score
        
        # 修改工作小时
        work_hours = WorkHours.objects.get(user=self.user1, month=date(2024, 1, 1))
        work_hours.hours = Decimal('300.00')  # 提高到满分
        work_hours.save()
        
        # 重新计算
        updated_score = self.service.recalculate_user_score(self.user1, date(2024, 1, 1))
        
        # 分值应该有所提高
        self.assertTrue(updated_score.final_score > initial_final_score)
        self.assertEqual(updated_score.work_hours, Decimal('300.00'))
        self.assertEqual(updated_score.work_hours_score, Decimal('10.00'))
        
    def test_get_user_performance_summary(self):
        """测试获取用户绩效分值汇总信息"""
        # 先计算绩效分值
        self.service.calculate_user_performance_score(self.user1, date(2024, 1, 1))
        
        summary = self.service.get_user_performance_summary(self.user1, date(2024, 1, 1))
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary['user'], self.user1)
        self.assertEqual(summary['month'], date(2024, 1, 1))
        self.assertIn('final_score', summary)
        self.assertIn('rank', summary)
        self.assertIn('dimensions', summary)
        
        # 验证维度信息
        dimensions = summary['dimensions']
        self.assertIn('work_hours', dimensions)
        self.assertIn('completion_rate', dimensions)
        self.assertIn('avg_difficulty', dimensions)
        
        # 验证每个维度都有原始值、分数和权重
        for dimension_name, dimension_data in dimensions.items():
            self.assertIn('raw_value', dimension_data)
            self.assertIn('score', dimension_data)
            self.assertIn('weight', dimension_data)
            
    def test_get_department_performance_summary(self):
        """测试获取部门绩效汇总信息"""
        # 先计算绩效分值
        self.service.batch_calculate_monthly_scores(date(2024, 1, 1))
        
        summary = self.service.get_department_performance_summary(Department.SOFTWARE, date(2024, 1, 1))
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary['department'], Department.SOFTWARE)
        self.assertEqual(summary['month'], date(2024, 1, 1))
        self.assertIn('member_count', summary)
        self.assertIn('avg_score', summary)
        self.assertIn('total_okr_score', summary)
        self.assertIn('top_performer', summary)
        self.assertIn('performance_scores', summary)
        
        # 验证成员数量
        software_users = User.objects.filter(department=Department.SOFTWARE, is_active=True)
        self.assertEqual(summary['member_count'], software_users.count())
        
    def test_round_to_two_decimals(self):
        """测试两位小数四舍五入"""
        # 测试四舍五入
        result1 = self.service._round_to_two_decimals(Decimal('3.145'))
        self.assertEqual(result1, Decimal('3.15'))
        
        result2 = self.service._round_to_two_decimals(Decimal('3.144'))
        self.assertEqual(result2, Decimal('3.14'))
        
        # 测试已经是两位小数的情况
        result3 = self.service._round_to_two_decimals(Decimal('3.14'))
        self.assertEqual(result3, Decimal('3.14'))
        
        # 测试整数
        result4 = self.service._round_to_two_decimals(Decimal('3'))
        self.assertEqual(result4, Decimal('3.00'))