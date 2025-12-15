"""
Integration tests for user authentication system
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Department


class UserAuthenticationIntegrationTest(TestCase):
    """集成测试：完整的用户认证流程"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin',
            password='admin123'
        )
    
    def test_complete_user_lifecycle(self):
        """测试完整的用户生命周期：注册 -> 登录 -> 查看列表 -> 更新"""
        
        # Step 1: Admin logs in
        login_response = self.client.post('/api/users/auth/login/', {
            'email': 'admin@example.com',
            'password': 'admin123'
        }, format='json')
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        access_token = login_response.data['access']
        
        # Step 2: Admin registers a new user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        register_response = self.client.post('/api/users/auth/register/', {
            'email': 'newuser@example.com',
            'name': '新用户',
            'department': Department.HARDWARE,
            'role': 'member',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }, format='json')
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        new_user_id = register_response.data['id']
        
        # Step 3: New user logs in
        new_user_login = self.client.post('/api/users/auth/login/', {
            'email': 'newuser@example.com',
            'password': 'newpass123'
        }, format='json')
        
        self.assertEqual(new_user_login.status_code, status.HTTP_200_OK)
        self.assertEqual(new_user_login.data['user']['name'], '新用户')
        
        # Step 4: New user views user list
        new_user_token = new_user_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_user_token}')
        list_response = self.client.get('/api/users/')
        
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        
        # Step 5: Admin updates the new user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        update_response = self.client.patch(f'/api/users/{new_user_id}/', {
            'name': '更新后的名字',
            'department': Department.SOFTWARE
        }, format='json')
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['name'], '更新后的名字')
        self.assertEqual(update_response.data['department'], Department.SOFTWARE)
        
        # Step 6: Verify the update persisted
        detail_response = self.client.get(f'/api/users/{new_user_id}/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['name'], '更新后的名字')
    
    def test_authentication_with_email_backend(self):
        """测试使用邮箱认证后端"""
        
        # Create a user
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            name='测试用户',
            department=Department.SOFTWARE,
            role='member',
            password='testpass123'
        )
        
        # Login with email (not username)
        response = self.client.post('/api/users/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_permission_enforcement(self):
        """测试权限控制"""
        
        # Create regular user
        user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            name='普通用户',
            department=Department.SOFTWARE,
            role='member',
            password='userpass123'
        )
        
        # Login as regular user
        login_response = self.client.post('/api/users/auth/login/', {
            'email': 'user@example.com',
            'password': 'userpass123'
        }, format='json')
        
        user_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        
        # Try to register a new user (should fail - not admin)
        register_response = self.client.post('/api/users/auth/register/', {
            'email': 'another@example.com',
            'name': '另一个用户',
            'department': Department.HARDWARE,
            'role': 'member',
            'password': 'pass123',
            'password_confirm': 'pass123'
        }, format='json')
        
        self.assertEqual(register_response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to update another user (should fail - not admin)
        update_response = self.client.patch(f'/api/users/{self.admin.id}/', {
            'name': '尝试修改管理员'
        }, format='json')
        
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)
