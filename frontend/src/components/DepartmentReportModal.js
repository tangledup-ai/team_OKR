import React, { useState, useEffect } from 'react';
import { reportService } from '../services/reportService';

const DepartmentReportModal = ({ department, month, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [departmentData, setDepartmentData] = useState(null);
  const [performanceScores, setPerformanceScores] = useState([]);

  useEffect(() => {
    loadDepartmentReportData();
  }, [department, month]);

  const loadDepartmentReportData = async () => {
    try {
      setLoading(true);
      setError('');

      // Load department performance scores
      try {
        const scoresData = await reportService.getDepartmentPerformanceScores(department, month);
        setPerformanceScores(scoresData.results || scoresData);
      } catch (err) {
        console.warn('Department performance scores not available:', err);
        setPerformanceScores([]);
      }

      // Load department statistics
      try {
        const deptStats = await reportService.getDepartmentStats(month);
        const currentDeptStats = deptStats.find(d => d.department === department);
        setDepartmentData(currentDeptStats);
      } catch (err) {
        console.warn('Department stats not available:', err);
        setDepartmentData(null);
      }

    } catch (err) {
      setError('加载部门报告失败');
      console.error('Error loading department report:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatMonth = (monthStr) => {
    const date = new Date(monthStr);
    return `${date.getFullYear()}年${date.getMonth() + 1}月`;
  };

  const getDepartmentName = (dept) => {
    const deptNames = {
      'hardware': '硬件部门',
      'software': '软件部门', 
      'marketing': '市场部门'
    };
    return deptNames[dept] || dept;
  };

  const getDepartmentColor = (dept) => {
    const colors = {
      'hardware': 'from-blue-500 to-blue-600',
      'software': 'from-green-500 to-green-600',
      'marketing': 'from-purple-500 to-purple-600'
    };
    return colors[dept] || 'from-gray-500 to-gray-600';
  };

  const calculateDepartmentStats = () => {
    if (performanceScores.length === 0) return null;

    const totalScore = performanceScores.reduce((sum, score) => sum + parseFloat(score.final_score), 0);
    const avgScore = totalScore / performanceScores.length;
    const topPerformer = performanceScores.reduce((top, current) => 
      parseFloat(current.final_score) > parseFloat(top.final_score) ? current : top
    );
    const avgWorkHours = performanceScores.reduce((sum, score) => sum + parseFloat(score.work_hours), 0) / performanceScores.length;
    const avgCompletionRate = performanceScores.reduce((sum, score) => sum + parseFloat(score.completion_rate), 0) / performanceScores.length;

    return {
      avgScore: avgScore.toFixed(2),
      topPerformer,
      avgWorkHours: avgWorkHours.toFixed(1),
      avgCompletionRate: avgCompletionRate.toFixed(1),
      memberCount: performanceScores.length
    };
  };

  const stats = calculateDepartmentStats();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className={`px-6 py-4 border-b border-gray-200 bg-gradient-to-r ${getDepartmentColor(department)} text-white`}>
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold">{getDepartmentName(department)} - 部门报告</h2>
              <p className="text-blue-100 mt-1">
                {formatMonth(month)} • {stats?.memberCount || 0} 名成员
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
            </div>
          ) : error ? (
            <div className="p-6">
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-700">{error}</div>
              </div>
            </div>
          ) : (
            <div className="p-6 space-y-6">
              {/* Department Overview */}
              {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600">{stats.avgScore}</div>
                    <div className="text-sm text-blue-800">平均绩效分值</div>
                  </div>
                  <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-green-600">{stats.avgWorkHours}h</div>
                    <div className="text-sm text-green-800">平均工作小时</div>
                  </div>
                  <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-purple-600">{stats.avgCompletionRate}%</div>
                    <div className="text-sm text-purple-800">平均完成率</div>
                  </div>
                  <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-orange-600">{departmentData?.completed_tasks || 0}</div>
                    <div className="text-sm text-orange-800">完成任务数</div>
                  </div>
                </div>
              )}

              {/* Top Performer */}
              {stats?.topPerformer && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">部门最佳表现</h3>
                  <div className="bg-gradient-to-r from-yellow-50 to-yellow-100 border border-yellow-200 rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                          🏆
                        </div>
                        <div>
                          <h4 className="text-lg font-bold text-gray-900">{stats.topPerformer.user.name}</h4>
                          <p className="text-sm text-gray-600">{stats.topPerformer.user.email}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-yellow-600">{stats.topPerformer.final_score}</div>
                        <div className="text-sm text-yellow-800">综合得分</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Department Members Performance */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">成员绩效排名</h3>
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="divide-y divide-gray-200">
                    {performanceScores.map((score, index) => (
                      <div key={score.user.id} className="p-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
                              index === 0 ? 'bg-yellow-500' : 
                              index === 1 ? 'bg-gray-400' : 
                              index === 2 ? 'bg-orange-500' : 'bg-blue-500'
                            }`}>
                              {index + 1}
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900">{score.user.name}</h4>
                              <p className="text-sm text-gray-500">{score.user.email}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xl font-bold text-gray-900">{score.final_score}</div>
                            <div className="text-sm text-gray-500">综合得分</div>
                          </div>
                        </div>
                        
                        {/* Performance breakdown */}
                        <div className="mt-3 grid grid-cols-4 gap-4 text-sm">
                          <div className="text-center">
                            <div className="font-medium text-blue-600">{score.work_hours_score}</div>
                            <div className="text-gray-500">工作小时</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-green-600">{score.completion_rate_score}</div>
                            <div className="text-gray-500">完成率</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-purple-600">{score.avg_difficulty_score}</div>
                            <div className="text-gray-500">难度平均</div>
                          </div>
                          <div className="text-center">
                            <div className="font-medium text-orange-600">{score.admin_final_score || 0}</div>
                            <div className="text-gray-500">管理员评分</div>
                          </div>
                        </div>

                        {/* Progress bar */}
                        <div className="mt-3">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`bg-gradient-to-r ${getDepartmentColor(department)} h-2 rounded-full transition-all duration-300`}
                              style={{ width: `${Math.min((score.final_score / 100) * 100, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Department Statistics Details */}
              {departmentData && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">部门统计详情</h3>
                  <div className="bg-white border border-gray-200 rounded-lg p-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{departmentData.total_okr_score}</div>
                        <div className="text-sm text-gray-600">部门OKR总分</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{departmentData.member_count}</div>
                        <div className="text-sm text-gray-600">成员数量</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">{departmentData.completed_tasks}</div>
                        <div className="text-sm text-gray-600">完成任务数</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-orange-600">{departmentData.avg_difficulty}</div>
                        <div className="text-sm text-gray-600">平均难度</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* No Data Message */}
              {performanceScores.length === 0 && (
                <div className="text-center py-12">
                  <div className="text-gray-400 text-6xl mb-4">📊</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">暂无数据</h3>
                  <p className="text-gray-500">该部门在选定月份暂无绩效数据</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DepartmentReportModal;