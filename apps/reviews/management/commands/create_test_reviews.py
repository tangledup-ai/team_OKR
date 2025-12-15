"""
Management command to create test review data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tasks.models import Task, TaskStatus
from apps.reviews.models import Review, ReviewType
from datetime import date
import random

User = get_user_model()


class Command(BaseCommand):
    help = '创建测试评价数据'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='要创建的评价数量'
        )
        
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除现有评价数据'
        )
    
    def handle(self, *args, **options):
        if options['clear']:
            Review.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('已清除所有评价数据')
            )
        
        # 获取用户和已完成的任务
        users = list(User.objects.filter(is_active=True))
        completed_tasks = list(Task.objects.filter(status=TaskStatus.COMPLETED))
        
        if len(users) < 2:
            self.stdout.write(
                self.style.ERROR('需要至少2个用户才能创建评价数据')
            )
            return
        
        if not completed_tasks:
            self.stdout.write(
                self.style.ERROR('需要至少1个已完成的任务才能创建任务评价')
            )
            return
        
        count = options['count']
        created_count = 0
        
        # 创建任务评价
        for _ in range(count // 2):
            task = random.choice(completed_tasks)
            reviewer = random.choice(users)
            
            # 确保评价人不是任务参与者
            if reviewer == task.owner or reviewer in task.collaborators.all():
                continue
            
            # 检查是否已经评价过
            if Review.objects.filter(
                type=ReviewType.TASK,
                task=task,
                reviewer=reviewer
            ).exists():
                continue
            
            Review.objects.create(
                type=ReviewType.TASK,
                task=task,
                reviewer=reviewer,
                rating=random.randint(6, 10),
                comment=f'这是对任务"{task.title}"的测试评价',
                is_anonymous=random.choice([True, False])
            )
            created_count += 1
        
        # 创建月度评价
        for _ in range(count // 2):
            reviewer = random.choice(users)
            reviewee = random.choice([u for u in users if u != reviewer])
            
            # 检查是否已经评价过
            if Review.objects.filter(
                type=ReviewType.MONTHLY,
                reviewer=reviewer,
                reviewee=reviewee,
                month=date(2024, 1, 1)
            ).exists():
                continue
            
            Review.objects.create(
                type=ReviewType.MONTHLY,
                reviewee=reviewee,
                reviewer=reviewer,
                rating=random.randint(7, 10),
                comment=f'这是对{reviewee.name}的月度评价',
                month=date(2024, 1, 1),
                is_anonymous=random.choice([True, False])
            )
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'成功创建了 {created_count} 条评价记录')
        )