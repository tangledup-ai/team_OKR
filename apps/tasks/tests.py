"""
Tests for Task models and APIs
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import Task, TaskStatus, ScoreDistribution, ScoreAllocation
from .services import TaskScoreService
from apps.users.models import Department

User = get_user_model()


class TaskModelTest(TestCase):
    """Test Task model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            name='Test User',
            department=Department.SOFTWARE,
            password='testpass123'
        )
    
    def test_task_creation(self):
        """Test task creation with valid data"""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            difficulty_score=5,
            revenue_amount=Decimal('1000.00'),
            owner=self.user
        )
        
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, 'Test Description')
        self.assertEqual(task.difficulty_score, 5)
        self.assertEqual(task.revenue_amount, Decimal('1000.00'))
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.owner, self.user)
        self.assertIsNotNone(task.id)
        self.assertIsNotNone(task.created_at)
    
    def test_task_str_representation(self):
        """Test task string representation"""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            difficulty_score=5,
            owner=self.user
        )
        self.assertEqual(str(task), 'Test Task')


class TaskAPITest(APITestCase):
    """Test Task API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            name='Test User',
            department=Department.SOFTWARE,
            password='testpass123'
        )
        
        self.collaborator = User.objects.create_user(
            username='collaborator@example.com',
            email='collaborator@example.com',
            name='Collaborator',
            department=Department.HARDWARE,
            password='testpass123'
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
    
    def test_create_task(self):
        """Test task creation via API"""
        url = reverse('tasks:task-list')
        data = {
            'title': 'API Test Task',
            'description': 'Test task created via API',
            'difficulty_score': 7,
            'revenue_amount': '2000.50',
            'owner_id': str(self.user.id),
            'collaborator_ids': [str(self.collaborator.id)]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'API Test Task')
        self.assertEqual(response.data['difficulty_score'], 7)
        self.assertEqual(response.data['revenue_amount'], '2000.50')
        self.assertEqual(response.data['status'], TaskStatus.TODO)
        self.assertEqual(len(response.data['collaborators']), 1)
    
    def test_create_task_invalid_difficulty(self):
        """Test task creation with invalid difficulty score"""
        url = reverse('tasks:task-list')
        data = {
            'title': 'Invalid Task',
            'description': 'Task with invalid difficulty',
            'difficulty_score': 15,  # Invalid: > 10
            'revenue_amount': '1000.00',
            'owner_id': str(self.user.id)
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('difficulty_score', response.data)
    
    def test_create_task_negative_revenue(self):
        """Test task creation with negative revenue amount"""
        url = reverse('tasks:task-list')
        data = {
            'title': 'Invalid Revenue Task',
            'description': 'Task with negative revenue',
            'difficulty_score': 5,
            'revenue_amount': '-100.00',  # Invalid: negative
            'owner_id': str(self.user.id)
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('revenue_amount', response.data)
    
    def test_list_tasks(self):
        """Test task list API"""
        # Create test tasks
        task1 = Task.objects.create(
            title='Task 1',
            description='First task',
            difficulty_score=3,
            owner=self.user
        )
        
        task2 = Task.objects.create(
            title='Task 2',
            description='Second task',
            difficulty_score=7,
            status=TaskStatus.COMPLETED,
            owner=self.user
        )
        
        url = reverse('tasks:task-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_tasks_filter_by_status(self):
        """Test task list filtering by status"""
        # Create tasks with different statuses
        Task.objects.create(
            title='Todo Task',
            description='Todo task',
            difficulty_score=3,
            owner=self.user
        )
        
        Task.objects.create(
            title='Completed Task',
            description='Completed task',
            difficulty_score=7,
            status=TaskStatus.COMPLETED,
            owner=self.user
        )
        
        # Filter by completed status
        url = reverse('tasks:task-list')
        response = self.client.get(url, {'status': TaskStatus.COMPLETED})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], TaskStatus.COMPLETED)
    
    def test_retrieve_task(self):
        """Test task detail retrieval"""
        task = Task.objects.create(
            title='Detail Task',
            description='Task for detail test',
            difficulty_score=5,
            revenue_amount=Decimal('1500.00'),
            owner=self.user
        )
        
        url = reverse('tasks:task-detail', kwargs={'pk': task.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Detail Task')
        self.assertEqual(response.data['difficulty_score'], 5)
        self.assertEqual(response.data['revenue_amount'], '1500.00')
    
    def test_update_task(self):
        """Test task update"""
        task = Task.objects.create(
            title='Original Task',
            description='Original description',
            difficulty_score=3,
            owner=self.user
        )
        
        url = reverse('tasks:task-detail', kwargs={'pk': task.id})
        data = {
            'title': 'Updated Task',
            'description': 'Updated description',
            'difficulty_score': 8,
            'revenue_amount': '3000.00'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Task')
        self.assertEqual(response.data['difficulty_score'], 8)
        self.assertEqual(response.data['revenue_amount'], '3000.00')
    
    def test_update_task_permission_denied(self):
        """Test task update permission denied for non-owner/collaborator"""
        other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            name='Other User',
            department=Department.MARKETING,
            password='testpass123'
        )
        
        task = Task.objects.create(
            title='Other User Task',
            description='Task owned by other user',
            difficulty_score=5,
            owner=other_user
        )
        
        url = reverse('tasks:task-detail', kwargs={'pk': task.id})
        data = {'title': 'Hacked Task'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_tasks_by_status(self):
        """Test tasks grouped by status"""
        # Create tasks with different statuses
        Task.objects.create(
            title='Todo Task',
            description='Todo task',
            difficulty_score=3,
            status=TaskStatus.TODO,
            owner=self.user
        )
        
        Task.objects.create(
            title='In Progress Task',
            description='In progress task',
            difficulty_score=5,
            status=TaskStatus.IN_PROGRESS,
            owner=self.user
        )
        
        Task.objects.create(
            title='Completed Task',
            description='Completed task',
            difficulty_score=7,
            status=TaskStatus.COMPLETED,
            owner=self.user
        )
        
        url = reverse('tasks:task-by-status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('todo', response.data)
        self.assertIn('in_progress', response.data)
        self.assertIn('completed', response.data)
        self.assertIn('postponed', response.data)
        
        self.assertEqual(len(response.data['todo']), 1)
        self.assertEqual(len(response.data['in_progress']), 1)
        self.assertEqual(len(response.data['completed']), 1)
        self.assertEqual(len(response.data['postponed']), 0)
    
    def test_task_stats(self):
        """Test task statistics"""
        # Create tasks with different statuses
        Task.objects.create(
            title='Todo Task',
            description='Todo task',
            difficulty_score=3,
            status=TaskStatus.TODO,
            owner=self.user
        )
        
        Task.objects.create(
            title='Completed Task',
            description='Completed task',
            difficulty_score=7,
            status=TaskStatus.COMPLETED,
            owner=self.user
        )
        
        # Create a task where user is collaborator
        other_task = Task.objects.create(
            title='Collaboration Task',
            description='Task where user is collaborator',
            difficulty_score=5,
            owner=self.collaborator
        )
        other_task.collaborators.add(self.user)
        
        url = reverse('tasks:task-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_tasks'], 3)
        self.assertEqual(response.data['owned_tasks'], 2)
        self.assertEqual(response.data['collaborated_tasks'], 1)
        self.assertEqual(response.data['completed_tasks'], 1)
        self.assertEqual(response.data['todo_tasks'], 2)  # 1 owned + 1 collaborated
    
    def test_update_task_status_to_in_progress(self):
        """Test updating task status to in_progress records started_at timestamp"""
        task = Task.objects.create(
            title='Status Test Task',
            description='Task for status testing',
            difficulty_score=5,
            owner=self.user
        )
        
        url = reverse('tasks:task-update-status', kwargs={'pk': task.id})
        data = {'status': TaskStatus.IN_PROGRESS}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(response.data['started_at'])
        
        # Verify in database
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(task.started_at)
    
    def test_update_task_status_to_completed(self):
        """Test updating task status to completed records completed_at timestamp"""
        task = Task.objects.create(
            title='Completion Test Task',
            description='Task for completion testing',
            difficulty_score=5,
            status=TaskStatus.IN_PROGRESS,
            owner=self.user
        )
        
        url = reverse('tasks:task-update-status', kwargs={'pk': task.id})
        data = {'status': TaskStatus.COMPLETED}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], TaskStatus.COMPLETED)
        self.assertIsNotNone(response.data['completed_at'])
        
        # Verify in database
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
    
    def test_update_task_status_to_postponed_with_reason(self):
        """Test updating task status to postponed with reason"""
        task = Task.objects.create(
            title='Postpone Test Task',
            description='Task for postpone testing',
            difficulty_score=5,
            owner=self.user
        )
        
        url = reverse('tasks:task-update-status', kwargs={'pk': task.id})
        data = {
            'status': TaskStatus.POSTPONED,
            'postpone_reason': 'Waiting for client feedback'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], TaskStatus.POSTPONED)
        self.assertEqual(response.data['postpone_reason'], 'Waiting for client feedback')
        self.assertIsNotNone(response.data['postponed_at'])
        
        # Verify in database
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.POSTPONED)
        self.assertEqual(task.postpone_reason, 'Waiting for client feedback')
        self.assertIsNotNone(task.postponed_at)
    
    def test_update_task_status_to_postponed_without_reason_fails(self):
        """Test updating task status to postponed without reason fails"""
        task = Task.objects.create(
            title='Postpone Fail Test Task',
            description='Task for postpone failure testing',
            difficulty_score=5,
            owner=self.user
        )
        
        url = reverse('tasks:task-update-status', kwargs={'pk': task.id})
        data = {'status': TaskStatus.POSTPONED}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('postpone_reason', response.data)
    
    def test_update_task_status_permission_denied(self):
        """Test status update permission denied for non-owner/collaborator"""
        other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            name='Other User',
            department=Department.MARKETING,
            password='testpass123'
        )
        
        task = Task.objects.create(
            title='Other User Task',
            description='Task owned by other user',
            difficulty_score=5,
            owner=other_user
        )
        
        url = reverse('tasks:task-update-status', kwargs={'pk': task.id})
        data = {'status': TaskStatus.COMPLETED}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_collaborator_can_update_task_status(self):
        """Test that collaborators can update task status"""
        task = Task.objects.create(
            title='Collaboration Task',
            description='Task for collaboration testing',
            difficulty_score=5,
            owner=self.collaborator
        )
        task.collaborators.add(self.user)
        
        url = reverse('tasks:task-update-status', kwargs={'pk': task.id})
        data = {'status': TaskStatus.IN_PROGRESS}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], TaskStatus.IN_PROGRESS)
        
        # Verify in database
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(task.started_at)
    
    def test_status_change_clears_postpone_reason(self):
        """Test that changing status from postponed clears postpone reason"""
        task = Task.objects.create(
            title='Clear Reason Test Task',
            description='Task for testing reason clearing',
            difficulty_score=5,
            status=TaskStatus.POSTPONED,
            postpone_reason='Original reason',
            owner=self.user
        )
        
        url = reverse('tasks:task-update-status', kwargs={'pk': task.id})
        data = {'status': TaskStatus.IN_PROGRESS}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], TaskStatus.IN_PROGRESS)
        self.assertEqual(response.data['postpone_reason'], '')
        
        # Verify in database
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task.postpone_reason, '')
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access task APIs"""
        self.client.force_authenticate(user=None)
        
        url = reverse('tasks:task-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ScoreDistributionModelTest(TestCase):
    """Test ScoreDistribution and ScoreAllocation models"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            name='Task Owner',
            department=Department.SOFTWARE,
            password='testpass123'
        )
        
        self.collaborator1 = User.objects.create_user(
            username='collab1@example.com',
            email='collab1@example.com',
            name='Collaborator 1',
            department=Department.HARDWARE,
            password='testpass123'
        )
        
        self.collaborator2 = User.objects.create_user(
            username='collab2@example.com',
            email='collab2@example.com',
            name='Collaborator 2',
            department=Department.MARKETING,
            password='testpass123'
        )
    
    def test_single_owner_task_score_distribution(self):
        """Test score distribution for task with only owner"""
        task = Task.objects.create(
            title='Single Owner Task',
            description='Task with only owner',
            difficulty_score=8,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        
        distribution = ScoreDistribution.calculate_and_create(task)
        
        # Check distribution
        self.assertEqual(distribution.total_score, Decimal('8.00'))
        self.assertEqual(distribution.penalty_coefficient, Decimal('1.000'))
        self.assertEqual(distribution.allocations.count(), 1)
        
        # Check allocation
        allocation = distribution.allocations.first()
        self.assertEqual(allocation.user, self.owner)
        self.assertEqual(allocation.base_score, Decimal('8.00'))
        self.assertEqual(allocation.adjusted_score, Decimal('8.00'))
        self.assertEqual(allocation.percentage, Decimal('100.00'))
    
    def test_multi_participant_task_score_distribution(self):
        """Test score distribution for task with owner and collaborators"""
        task = Task.objects.create(
            title='Multi Participant Task',
            description='Task with owner and collaborators',
            difficulty_score=10,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        task.collaborators.add(self.collaborator1, self.collaborator2)
        
        distribution = ScoreDistribution.calculate_and_create(task)
        
        # Check distribution
        self.assertEqual(distribution.total_score, Decimal('10.00'))
        self.assertEqual(distribution.penalty_coefficient, Decimal('1.000'))
        self.assertEqual(distribution.allocations.count(), 3)
        
        # Check owner allocation (50%)
        owner_allocation = distribution.allocations.get(user=self.owner)
        self.assertEqual(owner_allocation.base_score, Decimal('5.00'))
        self.assertEqual(owner_allocation.adjusted_score, Decimal('5.00'))
        self.assertEqual(owner_allocation.percentage, Decimal('50.00'))
        
        # Check collaborator allocations (25% each)
        collab1_allocation = distribution.allocations.get(user=self.collaborator1)
        self.assertEqual(collab1_allocation.base_score, Decimal('2.50'))
        self.assertEqual(collab1_allocation.adjusted_score, Decimal('2.50'))
        self.assertEqual(collab1_allocation.percentage, Decimal('25.00'))
        
        collab2_allocation = distribution.allocations.get(user=self.collaborator2)
        self.assertEqual(collab2_allocation.base_score, Decimal('2.50'))
        self.assertEqual(collab2_allocation.adjusted_score, Decimal('2.50'))
        self.assertEqual(collab2_allocation.percentage, Decimal('25.00'))
        
        # Verify total score conservation
        total_allocated = sum(alloc.adjusted_score for alloc in distribution.allocations.all())
        self.assertEqual(total_allocated, distribution.total_score)
    
    def test_postponed_task_penalty(self):
        """Test penalty coefficient for postponed tasks"""
        from django.utils import timezone
        
        task = Task.objects.create(
            title='Postponed Task',
            description='Task that was postponed',
            difficulty_score=5,
            status=TaskStatus.POSTPONED,
            postponed_at=timezone.now(),  # Set postponed timestamp
            owner=self.owner
        )
        # Mark as completed after being postponed
        task.status = TaskStatus.COMPLETED
        task.save()
        
        distribution = ScoreDistribution.calculate_and_create(task)
        
        # Check penalty is applied
        self.assertEqual(distribution.penalty_coefficient, Decimal('0.800'))
        self.assertEqual(distribution.total_score, Decimal('4.00'))  # 5 * 0.8
        
        # Check allocation
        allocation = distribution.allocations.first()
        self.assertEqual(allocation.adjusted_score, Decimal('4.00'))
    
    def test_score_distribution_for_incomplete_task_fails(self):
        """Test that score distribution fails for incomplete tasks"""
        task = Task.objects.create(
            title='Incomplete Task',
            description='Task that is not completed',
            difficulty_score=5,
            status=TaskStatus.IN_PROGRESS,
            owner=self.owner
        )
        
        with self.assertRaises(ValueError) as context:
            ScoreDistribution.calculate_and_create(task)
        
        self.assertIn('只有已完成的任务才能计算分值分配', str(context.exception))
    
    def test_score_distribution_replaces_existing(self):
        """Test that new score distribution replaces existing one"""
        task = Task.objects.create(
            title='Replace Test Task',
            description='Task for testing replacement',
            difficulty_score=6,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        
        # Create first distribution
        distribution1 = ScoreDistribution.calculate_and_create(task)
        first_id = distribution1.id
        
        # Create second distribution (should replace first)
        distribution2 = ScoreDistribution.calculate_and_create(task)
        
        # Check that only one distribution exists
        self.assertEqual(ScoreDistribution.objects.filter(task=task).count(), 1)
        self.assertNotEqual(distribution2.id, first_id)
        
        # Check that old distribution is deleted
        with self.assertRaises(ScoreDistribution.DoesNotExist):
            ScoreDistribution.objects.get(id=first_id)


class TaskScoreServiceTest(TestCase):
    """Test TaskScoreService"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            name='Task Owner',
            department=Department.SOFTWARE,
            password='testpass123'
        )
        
        self.collaborator = User.objects.create_user(
            username='collab@example.com',
            email='collab@example.com',
            name='Collaborator',
            department=Department.HARDWARE,
            password='testpass123'
        )
    
    def test_round_to_two_decimals(self):
        """Test decimal rounding function"""
        # Test various rounding scenarios
        self.assertEqual(
            TaskScoreService._round_to_two_decimals(Decimal('3.14159')),
            Decimal('3.14')
        )
        self.assertEqual(
            TaskScoreService._round_to_two_decimals(Decimal('3.145')),
            Decimal('3.15')  # Round half up
        )
        self.assertEqual(
            TaskScoreService._round_to_two_decimals(Decimal('3.144')),
            Decimal('3.14')
        )
    
    def test_get_user_monthly_score(self):
        """Test getting user's monthly score"""
        # Create completed tasks for the user
        task1 = Task.objects.create(
            title='Task 1',
            description='First task',
            difficulty_score=6,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        
        task2 = Task.objects.create(
            title='Task 2',
            description='Second task',
            difficulty_score=4,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        task2.collaborators.add(self.collaborator)
        
        # Calculate distributions
        TaskScoreService.calculate_task_score_distribution(task1)
        TaskScoreService.calculate_task_score_distribution(task2)
        
        # Get monthly score for owner
        from django.utils import timezone
        now = timezone.now()
        owner_score = TaskScoreService.get_user_monthly_score(self.owner, now.year, now.month)
        
        # Owner should get: 6.00 (task1) + 2.00 (50% of task2) = 8.00
        self.assertEqual(owner_score, Decimal('8.00'))
        
        # Get monthly score for collaborator
        collab_score = TaskScoreService.get_user_monthly_score(self.collaborator, now.year, now.month)
        
        # Collaborator should get: 2.00 (50% of task2)
        self.assertEqual(collab_score, Decimal('2.00'))
    
    def test_get_user_task_count(self):
        """Test getting user's task count"""
        # Create completed tasks
        task1 = Task.objects.create(
            title='Task 1',
            description='First task',
            difficulty_score=5,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        
        task2 = Task.objects.create(
            title='Task 2',
            description='Second task',
            difficulty_score=3,
            status=TaskStatus.COMPLETED,
            owner=self.collaborator
        )
        task2.collaborators.add(self.owner)
        
        # Calculate distributions
        TaskScoreService.calculate_task_score_distribution(task1)
        TaskScoreService.calculate_task_score_distribution(task2)
        
        # Get task count for owner
        from django.utils import timezone
        now = timezone.now()
        owner_count = TaskScoreService.get_user_task_count(self.owner, now.year, now.month)
        
        # Owner participated in 2 tasks
        self.assertEqual(owner_count, 2)
        
        # Get task count for collaborator
        collab_count = TaskScoreService.get_user_task_count(self.collaborator, now.year, now.month)
        
        # Collaborator participated in 1 task
        self.assertEqual(collab_count, 1)


class ScoreDistributionAPITest(APITestCase):
    """Test Score Distribution API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            name='Task Owner',
            department=Department.SOFTWARE,
            password='testpass123'
        )
        
        self.collaborator = User.objects.create_user(
            username='collab@example.com',
            email='collab@example.com',
            name='Collaborator',
            department=Department.HARDWARE,
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            name='Other User',
            department=Department.MARKETING,
            password='testpass123'
        )
        
        # Authenticate as owner
        self.client.force_authenticate(user=self.owner)
    
    def test_calculate_task_score_api(self):
        """Test calculate task score API endpoint"""
        task = Task.objects.create(
            title='API Score Task',
            description='Task for API score testing',
            difficulty_score=8,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        task.collaborators.add(self.collaborator)
        
        url = reverse('tasks:task-calculate-score', kwargs={'pk': task.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_score'], '8.00')
        self.assertEqual(response.data['penalty_coefficient'], '1.000')
        self.assertEqual(len(response.data['allocations']), 2)
        
        # Check owner allocation
        owner_alloc = next(alloc for alloc in response.data['allocations'] 
                          if alloc['user']['id'] == str(self.owner.id))
        self.assertEqual(owner_alloc['adjusted_score'], '4.00')
        self.assertEqual(owner_alloc['percentage'], '50.00')
        
        # Check collaborator allocation
        collab_alloc = next(alloc for alloc in response.data['allocations'] 
                           if alloc['user']['id'] == str(self.collaborator.id))
        self.assertEqual(collab_alloc['adjusted_score'], '4.00')
        self.assertEqual(collab_alloc['percentage'], '50.00')
    
    def test_calculate_score_incomplete_task_fails(self):
        """Test calculate score fails for incomplete task"""
        task = Task.objects.create(
            title='Incomplete Task',
            description='Task that is not completed',
            difficulty_score=5,
            status=TaskStatus.IN_PROGRESS,
            owner=self.owner
        )
        
        url = reverse('tasks:task-calculate-score', kwargs={'pk': task.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('只有已完成的任务才能计算分值分配', response.data['detail'])
    
    def test_calculate_score_permission_denied(self):
        """Test calculate score permission denied for non-participant"""
        task = Task.objects.create(
            title='Other User Task',
            description='Task owned by other user',
            difficulty_score=5,
            status=TaskStatus.COMPLETED,
            owner=self.other_user
        )
        
        url = reverse('tasks:task-calculate-score', kwargs={'pk': task.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_task_score_distribution(self):
        """Test get task score distribution API"""
        task = Task.objects.create(
            title='Distribution Task',
            description='Task for distribution testing',
            difficulty_score=6,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        
        # Calculate distribution first
        TaskScoreService.calculate_task_score_distribution(task)
        
        url = reverse('tasks:task-score-distribution', kwargs={'pk': task.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_score'], '6.00')
        self.assertEqual(len(response.data['allocations']), 1)
    
    def test_get_score_distribution_not_calculated(self):
        """Test get score distribution when not calculated"""
        task = Task.objects.create(
            title='No Distribution Task',
            description='Task without distribution',
            difficulty_score=5,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        
        url = reverse('tasks:task-score-distribution', kwargs={'pk': task.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('该任务尚未计算分值分配', response.data['detail'])
    
    def test_score_allocation_monthly_stats(self):
        """Test score allocation monthly stats API"""
        # Create and complete tasks
        task1 = Task.objects.create(
            title='Stats Task 1',
            description='First task for stats',
            difficulty_score=8,
            status=TaskStatus.COMPLETED,
            owner=self.owner
        )
        
        task2 = Task.objects.create(
            title='Stats Task 2',
            description='Second task for stats',
            difficulty_score=4,
            status=TaskStatus.COMPLETED,
            owner=self.collaborator
        )
        task2.collaborators.add(self.owner)
        
        # Calculate distributions
        TaskScoreService.calculate_task_score_distribution(task1)
        TaskScoreService.calculate_task_score_distribution(task2)
        
        url = reverse('tasks:score-allocation-monthly-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_score'], '10.00')  # 8.00 + 2.00
        self.assertEqual(response.data['task_count'], 2)
        self.assertEqual(len(response.data['allocations']), 2)
    
    def test_auto_calculate_score_on_completion(self):
        """Test that score is automatically calculated when task is completed"""
        task = Task.objects.create(
            title='Auto Calculate Task',
            description='Task for auto calculation testing',
            difficulty_score=7,
            status=TaskStatus.IN_PROGRESS,
            owner=self.owner
        )
        task.collaborators.add(self.collaborator)
        
        # Update status to completed
        url = reverse('tasks:task-update-status', kwargs={'pk': task.id})
        data = {'status': TaskStatus.COMPLETED}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], TaskStatus.COMPLETED)
        
        # Check that score distribution was automatically created
        task.refresh_from_db()
        self.assertTrue(hasattr(task, 'score_distribution'))
        self.assertEqual(task.score_distribution.total_score, Decimal('7.00'))