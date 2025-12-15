"""
Tests for reports app
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
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