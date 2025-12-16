import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { taskService } from '../services/taskService';
import { evaluationService } from '../services/evaluationService';
import Header from '../components/Header';
import TaskReviewModal from '../components/TaskReviewModal';
import SelfEvaluationModal from '../components/SelfEvaluationModal';
import PeerEvaluationModal from '../components/PeerEvaluationModal';
import { 
  StarIcon, 
  UserGroupIcon, 
  DocumentTextIcon,
  CalendarIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const EvaluationPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('task-reviews');
  const [completedTasks, setCompletedTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [showTaskReviewModal, setShowTaskReviewModal] = useState(false);
  const [showSelfEvaluationModal, setShowSelfEvaluationModal] = useState(false);
  const [showPeerEvaluationModal, setShowPeerEvaluationModal] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date().toISOString().slice(0, 7) + '-01');
  const [loading, setLoading] = useState(false);
  const [myEvaluation, setMyEvaluation] = useState(null);
  const [evaluationSummary, setEvaluationSummary] = useState([]);

  useEffect(() => {
    loadCompletedTasks();
    loadMyEvaluation();
    loadEvaluationSummary();
  }, [currentMonth]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadCompletedTasks = async () => {
    try {
      setLoading(true);
      const tasks = await taskService.getTasksByStatus('completed');
      // Filter tasks that the current user can review (not their own tasks)
      const reviewableTasks = tasks.filter(task => 
        task.owner?.id !== user?.id && 
        !task.collaborators?.some(c => c.id === user?.id)
      );
      setCompletedTasks(reviewableTasks);
    } catch (err) {
      console.error('Failed to load completed tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadMyEvaluation = async () => {
    try {
      const evaluation = await evaluationService.getMyEvaluation(currentMonth);
      setMyEvaluation(evaluation);
    } catch (err) {
      // No evaluation found is fine
      setMyEvaluation(null);
    }
  };

  const loadEvaluationSummary = async () => {
    try {
      const summary = await evaluationService.getEvaluationSummary(currentMonth);
      setEvaluationSummary(summary);
    } catch (err) {
      console.error('Failed to load evaluation summary:', err);
      setEvaluationSummary([]);
    }
  };

  const handleTaskReview = (task) => {
    setSelectedTask(task);
    setShowTaskReviewModal(true);
  };

  const handleTaskReviewSubmit = () => {
    // Refresh completed tasks to update review status
    loadCompletedTasks();
  };

  const handleSelfEvaluationSubmit = () => {
    loadMyEvaluation();
    loadEvaluationSummary();
  };

  const handlePeerEvaluationSubmit = () => {
    loadEvaluationSummary();
  };

  const formatMonth = (monthStr) => {
    const date = new Date(monthStr);
    return `${date.getFullYear()}年${date.getMonth() + 1}月`;
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const getDepartmentColor = (department) => {
    const colors = {
      'hardware': 'bg-blue-100 text-blue-800',
      'software': 'bg-green-100 text-green-800',
      'marketing': 'bg-purple-100 text-purple-800'
    };
    return colors[department] || 'bg-gray-100 text-gray-800';
  };

  const getDepartmentLabel = (department) => {
    const labels = {
      'hardware': '硬件',
      'software': '软件',
      'marketing': '市场'
    };
    return labels[department] || department;
  };

  const tabs = [
    { id: 'task-reviews', name: '任务评价', icon: StarIcon },
    { id: 'self-evaluation', name: '自我评价', icon: DocumentTextIcon },
    { id: 'peer-evaluation', name: '他人评价', icon: UserGroupIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">评价中心</h1>
          <p className="mt-2 text-gray-600">
            对已完成的任务进行评价，提交月度自我评价和他人评价
          </p>
        </div>

        {/* Month Selector */}
        <div className="mb-6">
          <label htmlFor="month" className="block text-sm font-medium text-gray-700 mb-2">
            选择月份
          </label>
          <div className="flex items-center space-x-2">
            <CalendarIcon className="h-5 w-5 text-gray-400" />
            <input
              type="month"
              id="month"
              className="border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              value={currentMonth.slice(0, 7)}
              onChange={(e) => setCurrentMonth(e.target.value + '-01')}
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white shadow rounded-lg">
          {activeTab === 'task-reviews' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-medium text-gray-900">可评价的已完成任务</h2>
                <button
                  onClick={loadCompletedTasks}
                  disabled={loading}
                  className="px-4 py-2 text-sm font-medium text-primary-600 bg-primary-50 border border-primary-200 rounded-md hover:bg-primary-100 disabled:opacity-50"
                >
                  {loading ? '刷新中...' : '刷新'}
                </button>
              </div>

              {completedTasks.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircleIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">暂无可评价的已完成任务</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {completedTasks.map((task) => (
                    <div key={task.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between mb-3">
                        <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
                          {task.title}
                        </h3>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          已完成
                        </span>
                      </div>

                      <div className="space-y-2 text-xs text-gray-600 mb-4">
                        <div className="flex items-center justify-between">
                          <span>难度:</span>
                          <span className="font-medium">{task.difficulty_score}/10</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>负责人:</span>
                          <span>{task.owner?.name}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>完成时间:</span>
                          <span>{formatDateTime(task.completed_at)}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => handleTaskReview(task)}
                        className="w-full px-3 py-2 text-sm font-medium text-primary-600 bg-primary-50 border border-primary-200 rounded-md hover:bg-primary-100"
                      >
                        评价任务
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'self-evaluation' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-medium text-gray-900">
                  {formatMonth(currentMonth)} 自我评价
                </h2>
                <button
                  onClick={() => setShowSelfEvaluationModal(true)}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
                >
                  {myEvaluation ? '更新评价' : '提交评价'}
                </button>
              </div>

              {myEvaluation ? (
                <div className="space-y-6">
                  <div className="bg-green-50 border border-green-200 rounded-md p-4">
                    <div className="flex items-center">
                      <CheckCircleIcon className="h-5 w-5 text-green-400 mr-2" />
                      <span className="text-green-800 font-medium">已完成自我评价</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-medium text-gray-900 mb-2">企业文化理解</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">评分:</span>
                          <span className="font-medium">{myEvaluation.culture_understanding_score}/10</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">选项:</span>
                          <span className="font-medium">{myEvaluation.culture_understanding_option}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">描述:</span>
                          <p className="mt-1 text-gray-900">{myEvaluation.culture_understanding_text}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-medium text-gray-900 mb-2">团队契合度</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">选项:</span>
                          <span className="font-medium">{myEvaluation.team_fit_option}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">描述:</span>
                          <p className="mt-1 text-gray-900">{myEvaluation.team_fit_text}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-medium text-gray-900 mb-2">本月成长</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">评分:</span>
                          <span className="font-medium">{myEvaluation.monthly_growth_score}/10</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">选项:</span>
                          <span className="font-medium">{myEvaluation.monthly_growth_option}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">描述:</span>
                          <p className="mt-1 text-gray-900">{myEvaluation.monthly_growth_text}</p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h3 className="font-medium text-gray-900 mb-2">本月最大贡献</h3>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">评分:</span>
                          <span className="font-medium">{myEvaluation.biggest_contribution_score}/10</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">选项:</span>
                          <span className="font-medium">{myEvaluation.biggest_contribution_option}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">描述:</span>
                          <p className="mt-1 text-gray-900">{myEvaluation.biggest_contribution_text}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500 mb-4">尚未提交 {formatMonth(currentMonth)} 的自我评价</p>
                  <button
                    onClick={() => setShowSelfEvaluationModal(true)}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
                  >
                    立即提交
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'peer-evaluation' && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-medium text-gray-900">
                  {formatMonth(currentMonth)} 他人评价
                </h2>
                <button
                  onClick={() => setShowPeerEvaluationModal(true)}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
                >
                  评价他人
                </button>
              </div>

              {evaluationSummary.length === 0 ? (
                <div className="text-center py-12">
                  <UserGroupIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">暂无评价数据</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {evaluationSummary.map((summary) => (
                      <div key={summary.user?.id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium text-gray-900">
                              {summary.user?.name}
                            </span>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getDepartmentColor(summary.user?.department)}`}>
                              {getDepartmentLabel(summary.user?.department)}
                            </span>
                          </div>
                        </div>

                        <div className="space-y-2 text-xs text-gray-600">
                          <div className="flex items-center justify-between">
                            <span>自我评价:</span>
                            <span className={`font-medium ${summary.self_evaluation_completed ? 'text-green-600' : 'text-red-600'}`}>
                              {summary.self_evaluation_completed ? '已完成' : '未完成'}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>他人评价数:</span>
                            <span className="font-medium">{summary.peer_evaluation_count}</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span>管理员评价:</span>
                            <span className={`font-medium ${summary.admin_evaluation_completed ? 'text-green-600' : 'text-red-600'}`}>
                              {summary.admin_evaluation_completed ? '已完成' : '未完成'}
                            </span>
                          </div>
                          {summary.average_peer_score && (
                            <div className="flex items-center justify-between">
                              <span>平均评分:</span>
                              <span className="font-medium">{summary.average_peer_score.toFixed(1)}/10</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showTaskReviewModal && selectedTask && (
        <TaskReviewModal
          task={selectedTask}
          onClose={() => {
            setShowTaskReviewModal(false);
            setSelectedTask(null);
          }}
          onSubmit={handleTaskReviewSubmit}
          currentUser={user}
        />
      )}

      {showSelfEvaluationModal && (
        <SelfEvaluationModal
          month={currentMonth}
          onClose={() => setShowSelfEvaluationModal(false)}
          onSubmit={handleSelfEvaluationSubmit}
          currentUser={user}
        />
      )}

      {showPeerEvaluationModal && (
        <PeerEvaluationModal
          month={currentMonth}
          onClose={() => setShowPeerEvaluationModal(false)}
          onSubmit={handlePeerEvaluationSubmit}
          currentUser={user}
        />
      )}
    </div>
  );
};

export default EvaluationPage;