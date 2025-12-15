import React, { useState } from 'react';
import { XMarkIcon, UserIcon, CalendarIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';

const TaskModal = ({ task, users, onClose, onUpdate, currentUser }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    title: task.title,
    description: task.description || '',
    difficulty_score: task.difficulty_score,
    revenue_amount: task.revenue_amount || 0,
    owner: task.owner?.id || '',
    collaborators: task.collaborators?.map(c => c.id) || []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const canEdit = task.owner?.id === currentUser?.id || 
                  task.collaborators?.some(c => c.id === currentUser?.id);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await onUpdate(task.id, formData);
      setIsEditing(false);
    } catch (err) {
      setError(err.response?.data?.message || '更新任务失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCollaboratorChange = (userId, checked) => {
    setFormData(prev => ({
      ...prev,
      collaborators: checked
        ? [...prev.collaborators, userId]
        : prev.collaborators.filter(id => id !== userId)
    }));
  };

  const getStatusLabel = (status) => {
    const labels = {
      'todo': '未完成',
      'in_progress': '进行中',
      'completed': '完成',
      'postponed': '推迟'
    };
    return labels[status] || status;
  };

  const getStatusColor = (status) => {
    const colors = {
      'todo': 'bg-gray-100 text-gray-800',
      'in_progress': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'postponed': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return '未设置';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-3xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            任务详情
          </h3>
          <div className="flex items-center space-x-2">
            {canEdit && !isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1 text-sm font-medium text-primary-600 bg-primary-50 border border-primary-200 rounded-md hover:bg-primary-100"
              >
                编辑
              </button>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
        )}

        {isEditing ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                任务标题 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="title"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                任务描述
              </label>
              <textarea
                id="description"
                rows={3}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="difficulty_score" className="block text-sm font-medium text-gray-700">
                  难度分值 (1-10) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  id="difficulty_score"
                  min="1"
                  max="10"
                  required
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.difficulty_score}
                  onChange={(e) => setFormData(prev => ({ ...prev, difficulty_score: parseInt(e.target.value) }))}
                />
              </div>

              <div>
                <label htmlFor="revenue_amount" className="block text-sm font-medium text-gray-700">
                  变现金额
                </label>
                <input
                  type="number"
                  id="revenue_amount"
                  min="0"
                  step="0.01"
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.revenue_amount}
                  onChange={(e) => setFormData(prev => ({ ...prev, revenue_amount: parseFloat(e.target.value) || 0 }))}
                />
              </div>
            </div>

            <div>
              <label htmlFor="owner" className="block text-sm font-medium text-gray-700">
                负责人 <span className="text-red-500">*</span>
              </label>
              <select
                id="owner"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                value={formData.owner}
                onChange={(e) => setFormData(prev => ({ ...prev, owner: e.target.value }))}
              >
                <option value="">请选择负责人</option>
                {users.map(user => (
                  <option key={user.id} value={user.id}>
                    {user.name} ({user.department})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                协作者
              </label>
              <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-md p-2">
                {users.filter(user => user.id !== formData.owner).map(user => (
                  <label key={user.id} className="flex items-center py-1">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                      checked={formData.collaborators.includes(user.id)}
                      onChange={(e) => handleCollaboratorChange(user.id, e.target.checked)}
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      {user.name} ({user.department})
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 disabled:opacity-50"
              >
                {loading ? '保存中...' : '保存'}
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="text-xl font-semibold text-gray-900 mb-2">
                  {task.title}
                </h4>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                    {getStatusLabel(task.status)}
                  </span>
                  <span>难度: {task.difficulty_score}/10</span>
                  {task.revenue_amount > 0 && (
                    <span className="flex items-center text-green-600">
                      <CurrencyDollarIcon className="h-4 w-4 mr-1" />
                      {task.revenue_amount}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {task.description && (
              <div>
                <h5 className="text-sm font-medium text-gray-900 mb-2">任务描述</h5>
                <p className="text-gray-700 whitespace-pre-wrap">{task.description}</p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h5 className="text-sm font-medium text-gray-900 mb-2">负责人</h5>
                <div className="flex items-center">
                  <UserIcon className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-gray-700">
                    {task.owner?.name} ({task.owner?.department})
                  </span>
                </div>
              </div>

              {task.collaborators && task.collaborators.length > 0 && (
                <div>
                  <h5 className="text-sm font-medium text-gray-900 mb-2">协作者</h5>
                  <div className="space-y-1">
                    {task.collaborators.map(collaborator => (
                      <div key={collaborator.id} className="flex items-center">
                        <UserIcon className="h-5 w-5 text-gray-400 mr-2" />
                        <span className="text-gray-700">
                          {collaborator.name} ({collaborator.department})
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
              <div>
                <h5 className="font-medium text-gray-900 mb-1">创建时间</h5>
                <div className="flex items-center text-gray-600">
                  <CalendarIcon className="h-4 w-4 mr-1" />
                  {formatDateTime(task.created_at)}
                </div>
              </div>

              {task.started_at && (
                <div>
                  <h5 className="font-medium text-gray-900 mb-1">开始时间</h5>
                  <div className="flex items-center text-gray-600">
                    <CalendarIcon className="h-4 w-4 mr-1" />
                    {formatDateTime(task.started_at)}
                  </div>
                </div>
              )}

              {task.completed_at && (
                <div>
                  <h5 className="font-medium text-gray-900 mb-1">完成时间</h5>
                  <div className="flex items-center text-gray-600">
                    <CalendarIcon className="h-4 w-4 mr-1" />
                    {formatDateTime(task.completed_at)}
                  </div>
                </div>
              )}
            </div>

            {task.postpone_reason && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <h5 className="text-sm font-medium text-red-800 mb-2">推迟原因</h5>
                <p className="text-red-700 text-sm">{task.postpone_reason}</p>
              </div>
            )}

            {!canEdit && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <p className="text-yellow-800 text-sm">
                  您不是此任务的参与者，无法编辑任务信息。
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskModal;