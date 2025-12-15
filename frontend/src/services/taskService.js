import api from './api';

export const taskService = {
  // Get all tasks
  getTasks: async () => {
    const response = await api.get('/api/tasks/tasks/');
    return response.data;
  },

  // Get tasks by status
  getTasksByStatus: async (status) => {
    const response = await api.get(`/api/tasks/tasks/?status=${status}`);
    return response.data;
  },

  // Get task by ID
  getTask: async (id) => {
    const response = await api.get(`/api/tasks/tasks/${id}/`);
    return response.data;
  },

  // Create new task
  createTask: async (taskData) => {
    const response = await api.post('/api/tasks/tasks/', taskData);
    return response.data;
  },

  // Update task
  updateTask: async (id, taskData) => {
    const response = await api.patch(`/api/tasks/tasks/${id}/`, taskData);
    return response.data;
  },

  // Update task status
  updateTaskStatus: async (id, status, postponeReason = null) => {
    const data = { status };
    if (postponeReason) {
      data.postpone_reason = postponeReason;
    }
    const response = await api.patch(`/api/tasks/tasks/${id}/`, data);
    return response.data;
  },

  // Delete task
  deleteTask: async (id) => {
    await api.delete(`/api/tasks/tasks/${id}/`);
  },

  // Get users for task assignment
  getUsers: async () => {
    const response = await api.get('/api/users/');
    return response.data;
  }
};