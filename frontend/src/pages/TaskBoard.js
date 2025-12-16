import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { taskService } from '../services/taskService';
import TaskColumn from '../components/TaskColumn';
import TaskModal from '../components/TaskModal';
import CreateTaskModal from '../components/CreateTaskModal';
import TaskReviewModal from '../components/TaskReviewModal';
import Header from '../components/Header';

const TASK_STATUSES = {
  TODO: 'todo',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  POSTPONED: 'postponed'
};

const STATUS_LABELS = {
  [TASK_STATUSES.TODO]: '未完成',
  [TASK_STATUSES.IN_PROGRESS]: '进行中',
  [TASK_STATUSES.COMPLETED]: '完成',
  [TASK_STATUSES.POSTPONED]: '推迟'
};

const TaskBoard = () => {
  const { user } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTask, setSelectedTask] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewTask, setReviewTask] = useState(null);
  const [users, setUsers] = useState([]);
  const [usersError, setUsersError] = useState('');

  useEffect(() => {
    loadTasks();
    loadUsers();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const data = await taskService.getTasks();
      setTasks(data.results || data);
    } catch (err) {
      setError('加载任务失败');
      console.error('Error loading tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      setUsersError('');
      const data = await taskService.getUsers();
      setUsers(data.results || data);
    } catch (err) {
      console.error('Error loading users:', err);
      setUsersError('无法加载用户列表');
    }
  };

  const handleTaskMove = async (taskId, newStatus, postponeReason = null) => {
    try {
      const updatedTask = await taskService.updateTaskStatus(taskId, newStatus, postponeReason);
      setTasks(prevTasks => 
        prevTasks.map(task => 
          task.id === taskId ? updatedTask : task
        )
      );
    } catch (err) {
      setError('更新任务状态失败');
      console.error('Error updating task status:', err);
    }
  };

  const handleTaskCreate = async (taskData) => {
    try {
      const newTask = await taskService.createTask(taskData);
      setTasks(prevTasks => [...prevTasks, newTask]);
      setShowCreateModal(false);
    } catch (err) {
      setError('创建任务失败');
      console.error('Error creating task:', err);
    }
  };

  const handleTaskUpdate = async (taskId, taskData) => {
    try {
      const updatedTask = await taskService.updateTask(taskId, taskData);
      setTasks(prevTasks => 
        prevTasks.map(task => 
          task.id === taskId ? updatedTask : task
        )
      );
      setSelectedTask(null);
    } catch (err) {
      setError('更新任务失败');
      console.error('Error updating task:', err);
    }
  };

  const getTasksByStatus = (status) => {
    return tasks.filter(task => task.status === status);
  };

  const handleTaskReview = (task) => {
    setReviewTask(task);
    setShowReviewModal(true);
  };

  const handleReviewSubmit = () => {
    // Refresh tasks to update any changes
    loadTasks();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onCreateTask={() => setShowCreateModal(true)} />
      
      {error && (
        <div className="mx-4 mt-4 rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.values(TASK_STATUSES).map(status => (
            <TaskColumn
              key={status}
              status={status}
              title={STATUS_LABELS[status]}
              tasks={getTasksByStatus(status)}
              onTaskMove={handleTaskMove}
              onTaskClick={setSelectedTask}
              onTaskReview={handleTaskReview}
              currentUser={user}
            />
          ))}
        </div>
      </div>

      {selectedTask && (
        <TaskModal
          task={selectedTask}
          users={users}
          usersError={usersError}
          onClose={() => setSelectedTask(null)}
          onUpdate={handleTaskUpdate}
          currentUser={user}
        />
      )}

      {showCreateModal && (
        <CreateTaskModal
          users={users}
          usersError={usersError}
          onClose={() => setShowCreateModal(false)}
          onCreate={handleTaskCreate}
          currentUser={user}
        />
      )}

      {showReviewModal && reviewTask && (
        <TaskReviewModal
          task={reviewTask}
          onClose={() => {
            setShowReviewModal(false);
            setReviewTask(null);
          }}
          onSubmit={handleReviewSubmit}
          currentUser={user}
        />
      )}
    </div>
  );
};

export default TaskBoard;