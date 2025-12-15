import React, { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const CreateTaskModal = ({ users, onClose, onCreate, currentUser }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    difficulty_score: 5,
    revenue_amount: 0,
    owner: currentUser?.id || '',
    collaborators: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await onCreate(formData);
    } catch (err) {
      setError(err.response?.data?.message || '创建任务失败');
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

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            创建新任务
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
        )}

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
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '创建中...' : '创建任务'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateTaskModal;