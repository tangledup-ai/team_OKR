#!/usr/bin/env python
"""
演示绩效分值计算引擎的使用
"""
import os
import sys
import django
from datetime import date
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User, Department
from apps.tasks.models import Task, TaskStatus, ScoreDistribution, ScoreAllocation
from apps.reports.models import WorkHours, MonthlyEvaluation, PeerEvaluation, PerformanceScore
from apps.reports.services import PerformanceScoreService
from apps.reviews.models import Review, ReviewType
from django.utils import timezone
from datetime import datetime


def create_demo_data():
    """创建演示数据"""
    print("创建演示数据...")
    
    # 创建用户
    admin_user = User.objects.create_user(
        username='admin_demo',
        email='admin@demo.com',
        password='demo123',
        name='管理员',
        department=Department.SOFTWARE,
        role='admin'
    )
    
    user1 = User.objects.create_user(
        username='user1_demo',
        email='user1@demo.com',
        password='demo123',
        name='张三',
        department=Department.SOFTWARE,
        role='member'
    )
    
    user2 = User.objects.create_user(
        username='user2_demo',
        email='user2@demo.com',
        password='demo123',
        name='李四',
        department=Department.HARDWARE,
        role='member'
    )
    
    # 创建任务
    task1 = Task.objects.create(
        title='开发用户认证模块',
        description='实现JWT认证和权限控制',
        difficulty_score=8,
        revenue_amount=Decimal('10000.00'),
        status=TaskStatus.COMPLETED,
        owner=user1,
        created_by=admin_user,
        completed_at=timezone.make_aware(datetime(2024, 1, 15, 10, 0, 0))
    )
    
    task2 = Task.objects.create(
        title='设计数据库架构',
        description='设计系统数据库表结构',
        difficulty_score=6,
        revenue_amount=Decimal('5000.00'),
        status=TaskStatus.COMPLETED,
        owner=user2,
        created_by=admin_user,
        completed_at=timezone.make_aware(datetime(2024, 1, 20, 14, 0, 0))
    )
    
    # 添加协作者
    task1.collaborators.add(user2)
    
    # 创建分值分配
    distribution1 = ScoreDistribution.objects.create(
        task=task1,
        total_score=Decimal('8.00'),
        penalty_coefficient=Decimal('1.000')
    )
    
    ScoreAllocation.objects.create(
        distribution=distribution1,
        user=user1,
        base_score=Decimal('4.00'),
        adjusted_score=Decimal('4.00'),
        percentage=Decimal('50.00')
    )
    
    ScoreAllocation.objects.create(
        distribution=distribution1,
        user=user2,
        base_score=Decimal('4.00'),
        adjusted_score=Decimal('4.00'),
        percentage=Decimal('50.00')
    )
    
    distribution2 = ScoreDistribution.objects.create(
        task=task2,
        total_score=Decimal('6.00'),
        penalty_coefficient=Decimal('1.000')
    )
    
    ScoreAllocation.objects.create(
        distribution=distribution2,
        user=user2,
        base_score=Decimal('6.00'),
        adjusted_score=Decimal('6.00'),
        percentage=Decimal('100.00')
    )
    
    # 创建工作小时记录
    WorkHours.objects.create(
        user=user1,
        month=date(2024, 1, 1),
        hours=Decimal('280.00'),
        recorded_by=admin_user
    )
    
    WorkHours.objects.create(
        user=user2,
        month=date(2024, 1, 1),
        hours=Decimal('320.00'),
        recorded_by=admin_user
    )
    
    # 创建任务评价
    Review.objects.create(
        type=ReviewType.TASK,
        task=task1,
        reviewer=admin_user,
        rating=9,
        comment='任务完成得很好，代码质量高',
        is_anonymous=False
    )
    
    Review.objects.create(
        type=ReviewType.TASK,
        task=task2,
        reviewer=user1,
        rating=7,
        comment='设计合理，但可以进一步优化',
        is_anonymous=False
    )
    
    # 创建月度评价
    evaluation1 = MonthlyEvaluation.objects.create(
        user=user1,
        month=date(2024, 1, 1),
        culture_understanding_score=8,
        culture_understanding_text='对企业文化有深入理解',
        culture_understanding_option='选项A',
        team_fit_option='选项B',
        team_fit_text='与团队配合良好',
        team_fit_ranking=[str(user2.id), str(admin_user.id)],
        monthly_growth_score=7,
        monthly_growth_text='本月在技术方面有显著提升',
        monthly_growth_option='选项C',
        biggest_contribution_score=9,
        biggest_contribution_text='完成了核心认证模块',
        biggest_contribution_option='选项D',
        admin_final_score=8,
        admin_final_comment='表现优秀，继续保持',
        admin_evaluated_by=admin_user
    )
    
    evaluation2 = MonthlyEvaluation.objects.create(
        user=user2,
        month=date(2024, 1, 1),
        culture_understanding_score=7,
        culture_understanding_text='理解企业文化',
        culture_understanding_option='选项A',
        team_fit_option='选项B',
        team_fit_text='团队协作能力强',
        team_fit_ranking=[str(user1.id), str(admin_user.id)],
        monthly_growth_score=8,
        monthly_growth_text='在系统设计方面有进步',
        monthly_growth_option='选项C',
        biggest_contribution_score=7,
        biggest_contribution_text='完成了数据库设计',
        biggest_contribution_option='选项D',
        admin_final_score=7,
        admin_final_comment='表现良好，需要继续努力',
        admin_evaluated_by=admin_user
    )
    
    # 创建他人评价
    PeerEvaluation.objects.create(
        monthly_evaluation=evaluation1,
        evaluator=user2,
        score=8,
        ranking=1,
        comment='张三工作认真，技术能力强',
        is_anonymous=False
    )
    
    PeerEvaluation.objects.create(
        monthly_evaluation=evaluation2,
        evaluator=user1,
        score=7,
        ranking=2,
        comment='李四设计能力不错，但需要提高效率',
        is_anonymous=False
    )
    
    print("演示数据创建完成！")
    return admin_user, user1, user2


def demonstrate_performance_calculation():
    """演示绩效分值计算"""
    print("\n" + "="*60)
    print("绩效分值计算引擎演示")
    print("="*60)
    
    # 创建演示数据
    admin_user, user1, user2 = create_demo_data()
    
    # 计算月份
    target_month = date(2024, 1, 1)
    
    print(f"\n正在计算 {target_month.strftime('%Y年%m月')} 的绩效分值...")
    
    # 1. 演示单个用户绩效计算
    print(f"\n1. 计算用户 {user1.name} 的绩效分值:")
    print("-" * 40)
    
    performance_score1 = PerformanceScoreService.calculate_user_performance_score(user1, target_month)
    
    print(f"工作小时: {performance_score1.work_hours} 小时 -> 标准化分数: {performance_score1.work_hours_score}")
    print(f"完成任务比例: {performance_score1.completion_rate}% -> 标准化分数: {performance_score1.completion_rate_score}")
    print(f"难度平均分: {performance_score1.avg_difficulty_score}")
    print(f"变现金额: {performance_score1.total_revenue} 元 -> 标准化分数: {performance_score1.revenue_score}")
    print(f"部门平均分: {performance_score1.department_avg_score}")
    print(f"任务评分: {performance_score1.task_rating_score}")
    print(f"企业文化理解: {performance_score1.culture_understanding_score}")
    print(f"团队契合度: {performance_score1.team_fit_score}")
    print(f"本月成长: {performance_score1.monthly_growth_score}")
    print(f"本月最大贡献: {performance_score1.biggest_contribution_score}")
    print(f"他人评价: {performance_score1.peer_evaluation_score}")
    print(f"管理员最终评分: {performance_score1.admin_final_score}")
    print(f"最终分值: {performance_score1.final_score}/100")
    
    # 2. 演示批量计算
    print(f"\n2. 批量计算所有用户的绩效分值:")
    print("-" * 40)
    
    all_scores = PerformanceScoreService.batch_calculate_monthly_scores(target_month)
    
    print("排名结果:")
    for score in all_scores:
        print(f"第{score.rank}名: {score.user.name} ({score.user.get_department_display()}) - {score.final_score}分")
    
    # 3. 演示权重配置
    print(f"\n3. 权重配置:")
    print("-" * 40)
    
    weights = PerformanceScoreService.WEIGHTS
    print("各维度权重分配:")
    for dimension, weight in weights.items():
        weight_percent = float(weight) * 100
        print(f"  {dimension}: {weight_percent}%")
    
    total_weight = sum(weights.values())
    print(f"总权重: {float(total_weight) * 100}%")
    
    # 4. 演示用户绩效汇总
    print(f"\n4. 用户绩效详细汇总 ({user1.name}):")
    print("-" * 40)
    
    summary = PerformanceScoreService.get_user_performance_summary(user1, target_month)
    if summary:
        print(f"用户: {summary['user'].name}")
        print(f"月份: {summary['month'].strftime('%Y年%m月')}")
        print(f"最终分值: {summary['final_score']}")
        print(f"排名: 第{summary['rank']}名")
        print("\n各维度详情:")
        for dim_name, dim_data in summary['dimensions'].items():
            print(f"  {dim_name}:")
            print(f"    原始值: {dim_data['raw_value']}")
            print(f"    标准化分数: {dim_data['score']}")
            print(f"    权重: {dim_data['weight']}%")
    
    # 5. 演示部门绩效汇总
    print(f"\n5. 部门绩效汇总 (软件部门):")
    print("-" * 40)
    
    dept_summary = PerformanceScoreService.get_department_performance_summary(Department.SOFTWARE, target_month)
    if dept_summary:
        print(f"部门: {dept_summary['department']}")
        print(f"月份: {dept_summary['month'].strftime('%Y年%m月')}")
        print(f"成员数量: {dept_summary['member_count']}")
        print(f"平均分: {dept_summary['avg_score']}")
        print(f"部门OKR总分: {dept_summary['total_okr_score']}")
        if dept_summary['top_performer']:
            print(f"最佳表现者: {dept_summary['top_performer'].user.name} ({dept_summary['top_performer'].final_score}分)")
    
    print(f"\n演示完成！")
    print("="*60)


def cleanup_demo_data():
    """清理演示数据"""
    print("\n清理演示数据...")
    
    # 删除演示用户（级联删除相关数据）
    User.objects.filter(username__endswith='_demo').delete()
    
    print("演示数据清理完成！")


if __name__ == '__main__':
    try:
        demonstrate_performance_calculation()
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理演示数据
        cleanup_demo_data()