"""
Management command to create test users for development
"""
from django.core.management.base import BaseCommand
from apps.users.models import User, Department


class Command(BaseCommand):
    help = '创建测试用户（开发环境使用）'

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(email='admin@example.com').exists():
            admin = User.objects.create_user(
                username='admin@example.com',
                email='admin@example.com',
                name='系统管理员',
                department=Department.SOFTWARE,
                role='admin',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS(
                f'✓ 创建管理员用户: {admin.email} (密码: admin123)'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                '管理员用户已存在: admin@example.com'
            ))

        # Create test users for each department
        test_users = [
            {
                'email': 'software@example.com',
                'name': '张三',
                'department': Department.SOFTWARE,
                'password': 'user123'
            },
            {
                'email': 'hardware@example.com',
                'name': '李四',
                'department': Department.HARDWARE,
                'password': 'user123'
            },
            {
                'email': 'marketing@example.com',
                'name': '王五',
                'department': Department.MARKETING,
                'password': 'user123'
            },
        ]

        for user_data in test_users:
            if not User.objects.filter(email=user_data['email']).exists():
                user = User.objects.create_user(
                    username=user_data['email'],
                    email=user_data['email'],
                    name=user_data['name'],
                    department=user_data['department'],
                    role='member',
                    password=user_data['password']
                )
                self.stdout.write(self.style.SUCCESS(
                    f'✓ 创建测试用户: {user.email} (密码: {user_data["password"]})'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'测试用户已存在: {user_data["email"]}'
                ))

        self.stdout.write(self.style.SUCCESS('\n所有测试用户创建完成！'))
        self.stdout.write(self.style.SUCCESS('可以使用以下凭证登录:'))
        self.stdout.write('  管理员: admin@example.com / admin123')
        self.stdout.write('  软件部门: software@example.com / user123')
        self.stdout.write('  硬件部门: hardware@example.com / user123')
        self.stdout.write('  市场部门: marketing@example.com / user123')
