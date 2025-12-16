import React, { useState } from 'react';

const AdminEvaluationForm = ({ evaluations, month, onClose, onSubmit }) => {
  const [evaluationData, setEvaluationData] = useState(
    evaluations.map(evaluation => ({
      evaluation_id: evaluation.id,
      admin_final_score: evaluation.admin_final_score || 5,
      admin_final_comment: evaluation.admin_final_comment || ''
    }))
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
      'hardware': 'bg-blue-100 text-blue-800',
      'software': 'bg-green-100 text-green-800',
      'marketing': 'bg-purple-100 text-purple-800'
    };
    return colors[dept] || 'bg-gray-100 text-gray-800';
  };

  const handleScoreChange = (index, score) => {
    const newData = [...evaluationData];
    newData[index].admin_final_score = parseInt(score);
    setEvaluationData(newData);
  };

  const handleCommentChange = (index, comment) => {
    const newData = [...evaluationData];
    newData[index].admin_final_comment = comment;
    setEvaluationData(newData);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate all scores are between 1-10
    const invalidScores = evaluationData.filter(data => 
      !data.admin_final_score || data.admin_final_score < 1 || data.admin_final_score > 10
    );
    
    if (invalidScores.length > 0) {
      setError('所有评分必须在1到10之间');
      return;
    }

    // Validate all comments are provided
    const missingComments = evaluationData.filter(data => !data.admin_final_comment.trim());
    
    if (missingComments.length > 0) {
      setError('请为所有成员提供评价文字');
      return;
    }

    try {
      setLoading(true);
      setError('');
      await onSubmit(evaluationData);
    } catch (err) {
      setError('提交评价失败，请重试');
      console.error('Error submitting admin evaluation:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50 rounded-t-lg">
          <div>
            <h2 className="text-xl font-bold text-gray-900">管理员月度评价</h2>
            <p className="text-sm text-gray-500 mt-1">
              {formatMonth(month)} • 待评价 {evaluations.length} 人
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="px-6 pt-4">
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          </div>
        )}

        {/* Form Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <form id="admin-evaluation-form" onSubmit={handleSubmit} className="space-y-6">
            {evaluations.map((evaluation, index) => (
              <div key={evaluation.id} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 font-bold">
                      {evaluation.user.name.charAt(0)}
                    </div>
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{evaluation.user.name}</h3>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDepartmentColor(evaluation.user.department)}`}>
                        {getDepartmentName(evaluation.user.department)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Score Input */}
                  <div className="flex items-center space-x-2">
                    <label className="text-sm font-medium text-gray-700">最终评分:</label>
                    <input
                      type="number"
                      min="1"
                      max="10"
                      value={evaluationData[index].admin_final_score}
                      onChange={(e) => handleScoreChange(index, e.target.value)}
                      className="w-20 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      required
                    />
                  </div>
                </div>

                {/* Previous Evaluations Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4 text-sm bg-gray-50 p-3 rounded-md">
                  <div>
                    <span className="text-gray-500">自评得分:</span>
                    <span className="ml-2 font-medium text-gray-900">
                      {evaluation.culture_understanding_score + evaluation.monthly_growth_score + evaluation.biggest_contribution_score} / 30
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">他人评价:</span>
                    <span className="ml-2 font-medium text-gray-900">
                      {evaluation.peer_evaluations?.length || 0} 条
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">工作状态:</span>
                    <span className="ml-2 font-medium text-green-600">正常</span>
                  </div>
                </div>

                {/* Comment Input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    管理员评价
                  </label>
                  <textarea
                    rows="3"
                    value={evaluationData[index].admin_final_comment}
                    onChange={(e) => handleCommentChange(index, e.target.value)}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    placeholder="请输入对该成员本月表现的最终评价..."
                    required
                  />
                </div>
              </div>
            ))}
          </form>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg flex justify-end space-x-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            取消
          </button>
          <button
            type="submit"
            form="admin-evaluation-form"
            disabled={loading}
            className={`px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {loading ? '提交中...' : '提交所有评价'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminEvaluationForm;
