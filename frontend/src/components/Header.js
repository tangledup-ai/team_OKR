import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { PlusIcon, UserCircleIcon, StarIcon, ClipboardDocumentListIcon } from '@heroicons/react/24/outline';

const Header = ({ onCreateTask }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const getDepartmentLabel = (department) => {
    const labels = {
      'hardware': '硬件部门',
      'software': '软件部门',
      'marketing': '市场部门'
    };
    return labels[department] || department;
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                OKR 任务看板
              </h1>
              <span className="text-sm text-gray-500">
                团队协作 · 绩效管理
              </span>
            </div>

            {/* Navigation */}
            <nav className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === '/dashboard'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <ClipboardDocumentListIcon className="h-4 w-4" />
                <span>任务看板</span>
              </button>
              
              <button
                onClick={() => navigate('/evaluations')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  location.pathname === '/evaluations'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <StarIcon className="h-4 w-4" />
                <span>评价中心</span>
              </button>
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            {location.pathname === '/dashboard' && onCreateTask && (
              <button
                onClick={onCreateTask}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                创建任务
              </button>
            )}

            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <UserCircleIcon className="h-8 w-8 text-gray-400" />
                <div className="text-sm">
                  <div className="font-medium text-gray-900">{user?.name}</div>
                  <div className="text-gray-500">{getDepartmentLabel(user?.department)}</div>
                </div>
              </div>
              
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md hover:bg-gray-100"
              >
                退出
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;