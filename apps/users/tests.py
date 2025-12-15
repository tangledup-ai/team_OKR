"""
Tests for user authentication and management
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User, Department


class UserModelTest(TestCase):
    """测试用户模型"""
    
    def setUp(self):
        self.user_data = {
            'username': 'test@example.com',
            'email': 'test@example.com',
            'name': '测试用户',
            'department': Department.SOFTWARE,
            'role': 'member',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """测试创建用户"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, '测试用户')
        self.assertEqual(user.department, Department.SOFTWARE)
        self.assertEqual(user.role, 'member')
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.id)
    
    def test_user_str_representation(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), '测试用户 (test@example.com)')


class AuthenticationTest(APITestCase):
    """测试认证功能"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('users:login')
        
        # Create test user
        self.user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            name='测试用户',
            department=Department.SOFTWARE,
            role='member',
            password='testpass123'
        )
    
    def test_login_success(self):
        """测试成功登录"""
        data = {
            'email': 'user@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'user@example.com')
        self.assertEqual(response.data['user']['name'], '测试用户')
    
    def test_login_invalid_credentials(self):
        """测试无效凭证登录"""
        data = {
            'email': 'user@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_missing_fields(self):
        """测试缺少字段"""
        data = {'email': 'user@example.com'}
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_nonexistent_user(self):
        """测试不存在的用户"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserRegistrationTest(APITestCase):
    """测试用户注册功能（管理员）"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('users:register')
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin',
            password='adminpass123'
        )
        
        # Create regular user
        self.user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            name='普通用户',
            department=Department.HARDWARE,
            role='member',
            password='userpass123'
        )
    
    def test_register_user_as_admin(self):
        """测试管理员注册新用户"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'email': 'newuser@example.com',
            'name': '新用户',
            'department': Department.MARKETING,
            'role': 'member',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'newuser@example.com')
        self.assertEqual(response.data['name'], '新用户')
        self.assertEqual(response.data['department'], Department.MARKETING)
        
        # Verify user was created in database
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(user.check_password('newpass123'))
    
    def test_register_user_as_non_admin(self):
        """测试非管理员无法注册用户"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'email': 'newuser@example.com',
            'name': '新用户',
            'department': Department.SOFTWARE,
            'role': 'member',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_register_user_unauthenticated(self):
        """测试未认证用户无法注册"""
        data = {
            'email': 'newuser@example.com',
            'name': '新用户',
            'department': Department.SOFTWARE,
            'role': 'member',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_register_user_password_mismatch(self):
        """测试密码不匹配"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'email': 'newuser@example.com',
            'name': '新用户',
            'department': Department.SOFTWARE,
            'role': 'member',
            'password': 'newpass123',
            'password_confirm': 'differentpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
    
    def test_register_user_invalid_department(self):
        """测试无效的部门"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'email': 'newuser@example.com',
            'name': '新用户',
            'department': 'invalid_dept',
            'role': 'member',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('department', response.data)


class UserListTest(APITestCase):
    """测试用户列表功能"""
    
    def setUp(self):
        self.client = APIClient()
        self.list_url = reverse('users:user-list')
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1@example.com',
            email='user1@example.com',
            name='用户1',
            department=Department.SOFTWARE,
            role='member',
            password='pass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2@example.com',
            email='user2@example.com',
            name='用户2',
            department=Department.HARDWARE,
            role='member',
            password='pass123'
        )
        
        self.admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin',
            password='adminpass123'
        )
    
    def test_list_users_authenticated(self):
        """测试认证用户可以查看用户列表"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response is paginated, check results key
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 3)
        else:
            self.assertEqual(len(response.data), 3)
    
    def test_list_users_unauthenticated(self):
        """测试未认证用户无法查看用户列表"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserDetailTest(APITestCase):
    """测试用户详情功能"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            name='测试用户',
            department=Department.SOFTWARE,
            role='member',
            password='pass123'
        )
        
        self.detail_url = reverse('users:user-detail', kwargs={'pk': self.user.id})
    
    def test_get_user_detail_authenticated(self):
        """测试认证用户可以查看用户详情"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')
        self.assertEqual(response.data['name'], '测试用户')
        self.assertIn('last_login', response.data)
    
    def test_get_user_detail_unauthenticated(self):
        """测试未认证用户无法查看用户详情"""
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserUpdateTest(APITestCase):
    """测试用户更新功能"""
    
    def setUp(self):
        self.client = APIClient()
        
        self.admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            name='管理员',
            department=Department.SOFTWARE,
            role='admin',
            password='adminpass123'
        )
        
        self.user = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            name='测试用户',
            department=Department.SOFTWARE,
            role='member',
            password='pass123'
        )
        
        self.update_url = reverse('users:user-detail', kwargs={'pk': self.user.id})
    
    def test_update_user_as_admin(self):
        """测试管理员可以更新用户信息"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'name': '更新后的名字',
            'department': Department.HARDWARE
        }
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '更新后的名字')
        self.assertEqual(response.data['department'], Department.HARDWARE)
        
        # Verify in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, '更新后的名字')
        self.assertEqual(self.user.department, Department.HARDWARE)
    
    def test_update_user_as_non_admin(self):
        """测试非管理员无法更新用户信息"""
        self.client.force_authenticate(user=self.user)
        
        data = {'name': '尝试更新'}
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_user_invalid_department(self):
        """测试更新为无效部门"""
        self.client.force_authenticate(user=self.admin)
        
        data = {'department': 'invalid_dept'}
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('department', response.data)
