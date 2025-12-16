import React from 'react';

const RankingDisplay = ({ performanceScores, onViewPersonalReport, currentUser }) => {
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

  const getRankBadgeColor = (rank) => {
    if (rank === 1) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    if (rank === 2) return 'bg-gray-100 text-gray-800 border-gray-200';
    if (rank === 3) return 'bg-orange-100 text-orange-800 border-orange-200';
    return 'bg-blue-50 text-blue-700 border-blue-200';
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  if (!performanceScores || performanceScores.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">个人排名</h3>
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-4">📊</div>
          <p className="text-gray-500">暂无排名数据</p>
          <p className="text-sm text-gray-400 mt-2">请等待绩效分值计算完成</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">个人排名</h3>
        <p className="text-sm text-gray-600 mt-1">
          基于综合绩效分值排序，共 {performanceScores.length} 人
        </p>
      </div>

      <div className="divide-y divide-gray-200">
        {performanceScores.map((score) => (
          <div
            key={score.user.id}
            className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
              score.user.id === currentUser?.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
            }`}
            onClick={() => onViewPersonalReport(score.user)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {/* Rank Badge */}
                <div className={`flex items-center justify-center w-12 h-12 rounded-full border-2 font-bold ${getRankBadgeColor(score.rank)}`}>
                  <span className="text-lg">
                    {getRankIcon(score.rank)}
                  </span>
                </div>

                {/* User Info */}
                <div>
                  <div className="flex items-center space-x-2">
                    <h4 className="font-medium text-gray-900">
                      {score.user.name}
                      {score.user.id === currentUser?.id && (
                        <span className="ml-2 text-xs text-blue-600 font-normal">(我)</span>
                      )}
                    </h4>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getDepartmentColor(score.user.department)}`}>
                      {getDepartmentName(score.user.department)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">{score.user.email}</p>
                </div>
              </div>

              {/* Score */}
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">
                  {score.final_score}
                </div>
                <div className="text-sm text-gray-500">综合得分</div>
              </div>
            </div>

            {/* Score Breakdown Preview */}
            <div className="mt-3 grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="font-medium text-gray-900">{score.work_hours_score}</div>
                <div className="text-gray-500">工作小时</div>
              </div>
              <div className="text-center">
                <div className="font-medium text-gray-900">{score.completion_rate_score}</div>
                <div className="text-gray-500">完成率</div>
              </div>
              <div className="text-center">
                <div className="font-medium text-gray-900">{score.avg_difficulty_score}</div>
                <div className="text-gray-500">难度平均</div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-3">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min((score.final_score / 100) * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center">
          点击任意成员查看详细报告 • 蓝色高亮为您的排名
        </p>
      </div>
    </div>
  );
};

export default RankingDisplay;