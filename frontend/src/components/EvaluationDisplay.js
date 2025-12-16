import React from 'react';

const EvaluationDisplay = ({ evaluationSummary, selectedMonth, onViewPersonalReport }) => {
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

  const getCompletionStatus = (summary) => {
    const selfCompleted = summary.self_evaluation_completed;
    const adminCompleted = summary.admin_evaluation_completed;
    const peerCount = summary.peer_evaluation_count || 0;

    if (selfCompleted && adminCompleted && peerCount > 0) {
      return { status: 'complete', text: '已完成', color: 'bg-green-100 text-green-800' };
    } else if (selfCompleted && peerCount > 0) {
      return { status: 'pending-admin', text: '待管理员评价', color: 'bg-yellow-100 text-yellow-800' };
    } else if (selfCompleted) {
      return { status: 'pending-peer', text: '待他人评价', color: 'bg-blue-100 text-blue-800' };
    } else {
      return { status: 'pending-self', text: '待自我评价', color: 'bg-gray-100 text-gray-800' };
    }
  };

  if (!evaluationSummary || evaluationSummary.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">评价状态</h3>
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-4">📝</div>
          <p className="text-gray-500">暂无评价数据</p>
          <p className="text-sm text-gray-400 mt-2">请等待成员提交评价</p>
        </div>
      </div>
    );
  }

  // Calculate statistics
  const totalMembers = evaluationSummary.length;
  const completedSelfEvaluations = evaluationSummary.filter(s => s.self_evaluation_completed).length;
  const completedAdminEvaluations = evaluationSummary.filter(s => s.admin_evaluation_completed).length;
  const totalPeerEvaluations = evaluationSummary.reduce((sum, s) => sum + (s.peer_evaluation_count || 0), 0);

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">评价状态</h3>
        <p className="text-sm text-gray-600 mt-1">
          {formatMonth(selectedMonth)} 评价完成情况
        </p>
      </div>

      {/* Statistics */}
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{completedSelfEvaluations}/{totalMembers}</div>
            <div className="text-gray-600">自我评价</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{completedAdminEvaluations}/{totalMembers}</div>
            <div className="text-gray-600">管理员评价</div>
          </div>
        </div>
        <div className="mt-3 text-center">
          <div className="text-lg font-bold text-purple-600">{totalPeerEvaluations}</div>
          <div className="text-sm text-gray-600">他人评价总数</div>
        </div>
      </div>

      {/* Member List */}
      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {evaluationSummary.map((summary) => {
          const completionStatus = getCompletionStatus(summary);
          
          return (
            <div
              key={summary.user.id}
              className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => onViewPersonalReport(summary.user)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900">{summary.user.name}</h4>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getDepartmentColor(summary.user.department)}`}>
                        {getDepartmentName(summary.user.department)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                      <span>自评: {summary.self_evaluation_completed ? '✓' : '✗'}</span>
                      <span>他评: {summary.peer_evaluation_count || 0}</span>
                      <span>管理员: {summary.admin_evaluation_completed ? '✓' : '✗'}</span>
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${completionStatus.color}`}>
                    {completionStatus.text}
                  </span>
                  {summary.average_peer_score && (
                    <div className="text-sm text-gray-600 mt-1">
                      平均分: {parseFloat(summary.average_peer_score).toFixed(1)}
                    </div>
                  )}
                </div>
              </div>

              {/* Progress indicators */}
              <div className="mt-3 flex space-x-2">
                <div className={`h-2 flex-1 rounded ${summary.self_evaluation_completed ? 'bg-blue-500' : 'bg-gray-200'}`}></div>
                <div className={`h-2 flex-1 rounded ${summary.peer_evaluation_count > 0 ? 'bg-purple-500' : 'bg-gray-200'}`}></div>
                <div className={`h-2 flex-1 rounded ${summary.admin_evaluation_completed ? 'bg-green-500' : 'bg-gray-200'}`}></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="p-4 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-center space-x-4 text-xs text-gray-500">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-2 bg-blue-500 rounded"></div>
            <span>自我评价</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-2 bg-purple-500 rounded"></div>
            <span>他人评价</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-2 bg-green-500 rounded"></div>
            <span>管理员评价</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluationDisplay;