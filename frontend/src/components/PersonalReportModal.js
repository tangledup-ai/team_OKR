import React, { useState, useEffect } from 'react';
import { reportService } from '../services/reportService';
import { evaluationService } from '../services/evaluationService';

const PersonalReportModal = ({ user, month, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [performanceScore, setPerformanceScore] = useState(null);
  const [monthlyEvaluation, setMonthlyEvaluation] = useState(null);
  const [peerEvaluations, setPeerEvaluations] = useState([]);
  const [workHours, setWorkHours] = useState(null);

  useEffect(() => {
    loadPersonalReportData();
  }, [user.id, month]);

  const loadPersonalReportData = async () => {
    try {
      setLoading(true);
      setError('');

      // Load performance score
      try {
        const scoreData = await reportService.getUserPerformanceScore(user.id, month);
        setPerformanceScore(scoreData);
      } catch (err) {
        console.warn('Performance score not available:', err);
        setPerformanceScore(null);
      }

      // Load monthly evaluation
      try {
        const evalData = await evaluationService.getUserEvaluation(user.id, month);
        if (evalData) {
          setMonthlyEvaluation(evalData);
        }
      } catch (err) {
        console.warn('Monthly evaluation not available:', err);
        setMonthlyEvaluation(null);
      }

      // Load peer evaluations
      try {
        const peerData = await evaluationService.getPeerEvaluations(month, user.id);
        setPeerEvaluations(peerData);
      } catch (err) {
        console.warn('Peer evaluations not available:', err);
        setPeerEvaluations([]);
      }

      // Load work hours
      try {
        const hoursData = await reportService.getWorkHours(month, user.id);
        setWorkHours(hoursData.results?.[0] || hoursData[0] || null);
      } catch (err) {
        console.warn('Work hours not available:', err);
        setWorkHours(null);
      }

    } catch (err) {
      setError('加载个人报告失败');
      console.error('Error loading personal report:', err);
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

  const getScoreDimensions = () => {
    if (!performanceScore) return [];

    return [
      { name: '工作小时', score: performanceScore.work_hours_score, weight: '10%', rawValue: `${performanceScore.work_hours}小时` },
      { name: '完成任务比例', score: performanceScore.completion_rate_score, weight: '15%', rawValue: `${performanceScore.completion_rate}%` },
      { name: '难度平均分', score: performanceScore.avg_difficulty_score, weight: '10%', rawValue: `${performanceScore.avg_difficulty_score}分` },
      { name: '变现金额', score: performanceScore.revenue_score, weight: '10%', rawValue: `¥${performanceScore.total_revenue}` },
      { name: '部门平均分', score: performanceScore.department_avg_score, weight: '5%', rawValue: `${performanceScore.department_avg_score}分` },
      { name: '任务评分', score: performanceScore.task_rating_score, weight: '10%', rawValue: `${performanceScore.task_rating_score}分` },
      { name: '企业文化理解', score: performanceScore.culture_understanding_score, weight: '5%', rawValue: `${performanceScore.culture_understanding_score}分` },
      { name: '团队契合度', score: performanceScore.team_fit_score, weight: '5%', rawValue: `${performanceScore.team_fit_score}分` },
      { name: '本月成长', score: performanceScore.monthly_growth_score, weight: '5%', rawValue: `${performanceScore.monthly_growth_score}分` },
      { name: '本月最大贡献', score: performanceScore.biggest_contribution_score, weight: '5%', rawValue: `${performanceScore.biggest_contribution_score}分` },
      { name: '他人评价', score: performanceScore.peer_evaluation_score, weight: '5%', rawValue: `${performanceScore.peer_evaluation_score}分` },
      { name: '管理员最终评分', score: performanceScore.admin_final_score || 0, weight: '15%', rawValue: performanceScore.admin_final_score ? `${performanceScore.admin_final_score}分` : '未评价' }
    ];
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold">{user.name} - 个人报告</h2>
              <p className="text-blue-100 mt-1">
                {getDepartmentName(user.department)} • {formatMonth(month)}
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
              {/* Performance Score Overview */}
              {performanceScore && (
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-gray-900 mb-2">
                      {performanceScore.final_score}
                    </div>
                    <div className="text-lg text-gray-600 mb-4">综合绩效分值</div>
                    <div className="flex justify-center items-center space-x-4 text-sm text-gray-600">
                      <span>排名: #{performanceScore.rank}</span>
                      <span>•</span>
                      <span>计算时间: {new Date(performanceScore.calculated_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Score Dimensions */}
              {performanceScore && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">分值明细</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {getScoreDimensions().map((dimension, index) => (
                      <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-medium text-gray-900">{dimension.name}</span>
                          <span className="text-sm text-gray-500">权重 {dimension.weight}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-2xl font-bold text-blue-600">{dimension.score}</span>
                          <span className="text-sm text-gray-600">{dimension.rawValue}</span>
                        </div>
                        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
                            style={{ width: `${Math.min((dimension.score / 10) * 100, 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Monthly Evaluation */}
              {monthlyEvaluation && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">月度自我评价</h3>
                  <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">企业文化理解</h4>
                      <div className="flex items-center space-x-4 mb-2">
                        <span className="text-lg font-bold text-blue-600">{monthlyEvaluation.culture_understanding_score}分</span>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">{monthlyEvaluation.culture_understanding_option}</span>
                      </div>
                      <p className="text-gray-700 text-sm">{monthlyEvaluation.culture_understanding_text}</p>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">团队契合度</h4>
                      <div className="mb-2">
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded">{monthlyEvaluation.team_fit_option}</span>
                      </div>
                      <p className="text-gray-700 text-sm">{monthlyEvaluation.team_fit_text}</p>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">本月成长</h4>
                      <div className="flex items-center space-x-4 mb-2">
                        <span className="text-lg font-bold text-purple-600">{monthlyEvaluation.monthly_growth_score}分</span>
                        <span className="px-2 py-1 bg-purple-100 text-purple-800 text-sm rounded">{monthlyEvaluation.monthly_growth_option}</span>
                      </div>
                      <p className="text-gray-700 text-sm">{monthlyEvaluation.monthly_growth_text}</p>
                    </div>

                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">本月最大贡献</h4>
                      <div className="flex items-center space-x-4 mb-2">
                        <span className="text-lg font-bold text-orange-600">{monthlyEvaluation.biggest_contribution_score}分</span>
                        <span className="px-2 py-1 bg-orange-100 text-orange-800 text-sm rounded">{monthlyEvaluation.biggest_contribution_option}</span>
                      </div>
                      <p className="text-gray-700 text-sm">{monthlyEvaluation.biggest_contribution_text}</p>
                    </div>

                    {monthlyEvaluation.admin_final_score && (
                      <div className="border-t pt-4">
                        <h4 className="font-medium text-gray-900 mb-2">管理员最终评价</h4>
                        <div className="flex items-center space-x-4 mb-2">
                          <span className="text-lg font-bold text-red-600">{monthlyEvaluation.admin_final_score}分</span>
                          <span className="text-sm text-gray-500">
                            评价时间: {new Date(monthlyEvaluation.admin_evaluated_at).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-gray-700 text-sm">{monthlyEvaluation.admin_final_comment}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Peer Evaluations */}
              {peerEvaluations.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">他人评价 ({peerEvaluations.length})</h3>
                  <div className="space-y-4">
                    {peerEvaluations.map((evaluation, index) => (
                      <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-medium text-gray-900">{evaluation.evaluator_name}</span>
                          <div className="flex items-center space-x-4">
                            <span className="text-lg font-bold text-blue-600">{evaluation.score}分</span>
                            <span className="text-sm text-gray-500">排名 #{evaluation.ranking}</span>
                          </div>
                        </div>
                        <p className="text-gray-700 text-sm">{evaluation.comment}</p>
                        <div className="text-xs text-gray-500 mt-2">
                          {new Date(evaluation.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Work Hours */}
              {workHours && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">工作小时</h3>
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700">本月工作小时</span>
                      <span className="text-2xl font-bold text-green-600">{workHours.hours}小时</span>
                    </div>
                    <div className="text-xs text-gray-500 mt-2">
                      记录人: {workHours.recorded_by?.name} • 
                      记录时间: {new Date(workHours.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PersonalReportModal;