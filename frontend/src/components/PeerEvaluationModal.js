import React, { useState, useEffect } from 'react';
import { XMarkIcon, UserIcon, StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { evaluationService } from '../services/evaluationService';

const PeerEvaluationModal = ({ month, onClose, onSubmit, currentUser }) => {
  const [teamMembers, setTeamMembers] = useState([]);
  const [selectedMember, setSelectedMember] = useState(null);
  const [formData, setFormData] = useState({
    score: 0,
    ranking: 1,
    comment: '',
    is_anonymous: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hoveredRating, setHoveredRating] = useState(0);
  const [existingEvaluations, setExistingEvaluations] = useState([]);

  useEffect(() => {
    loadTeamMembers();
    loadExistingEvaluations();
  }, [month]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadTeamMembers = async () => {
    try {
      const members = await evaluationService.getTeamMembers();
      setTeamMembers(members);
    } catch (err) {
      console.error('Failed to load team members:', err);
    }
  };

  const loadExistingEvaluations = async () => {
    try {
      const evaluations = await evaluationService.getPeerEvaluations(month);
      setExistingEvaluations(evaluations);
    } catch (err) {
      console.error('Failed to load existing evaluations:', err);
    }
  };

  const handleMemberSelect = (member) => {
    setSelectedMember(member);
    setFormData({
      score: 0,
      ranking: 1,
      comment: '',
      is_anonymous: false
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedMember) {
      setError('请选择要评价的成员');
      return;
    }

    if (formData.score === 0) {
      setError('请选择评分');
      return;
    }

    if (!formData.comment.trim()) {
      setError('请输入评价内容');
      return;
    }

    if (formData.ranking < 1 || formData.ranking > teamMembers.length) {
      setError(`排名必须在1到${teamMembers.length}之间`);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const evaluationData = {
        evaluee: selectedMember.id,
        score: formData.score,
        ranking: formData.ranking,
        comment: formData.comment.trim(),
        is_anonymous: formData.is_anonymous
      };

      await evaluationService.submitPeerEvaluation(evaluationData, month);
      
      if (onSubmit) {
        onSubmit();
      }
      
      // Reload existing evaluations
      await loadExistingEvaluations();
      
      // Reset form
      setSelectedMember(null);
      setFormData({
        score: 0,
        ranking: 1,
        comment: '',
        is_anonymous: false
      });
      
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.non_field_errors?.[0] || '提交评价失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRatingClick = (rating) => {
    setFormData(prev => ({ ...prev, score: rating }));
  };

  const handleRatingHover = (rating) => {
    setHoveredRating(rating);
  };

  const handleRatingLeave = () => {
    setHoveredRating(0);
  };

  const renderStars = () => {
    const stars = [];
    const displayRating = hoveredRating || formData.score;
    
    for (let i = 1; i <= 10; i++) {
      stars.push(
        <button
          key={i}
          type="button"
          className={`p-1 transition-colors ${
            i <= displayRating ? 'text-yellow-400' : 'text-gray-300'
          } hover:text-yellow-400`}
          onClick={() => handleRatingClick(i)}
          onMouseEnter={() => handleRatingHover(i)}
          onMouseLeave={handleRatingLeave}
        >
          {i <= displayRating ? (
            <StarIconSolid className="h-6 w-6" />
          ) : (
            <StarIcon className="h-6 w-6" />
          )}
        </button>
      );
    }
    
    return stars;
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

  const hasEvaluatedMember = (memberId) => {
    return existingEvaluations.some(evaluation => 
      evaluation.monthly_evaluation?.user?.id === memberId
    );
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-6xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            {formatMonth(month)} 他人评价
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Member Selection */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-4">选择评价对象</h4>
            
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {teamMembers.map((member) => {
                const hasEvaluated = hasEvaluatedMember(member.id);
                return (
                  <div
                    key={member.id}
                    className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer transition-all ${
                      selectedMember?.id === member.id
                        ? 'border-primary-500 bg-primary-50'
                        : hasEvaluated
                        ? 'border-green-200 bg-green-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                    onClick={() => !hasEvaluated && handleMemberSelect(member)}
                  >
                    <div className="flex items-center space-x-3">
                      <UserIcon className="h-5 w-5 text-gray-400" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">{member.name}</div>
                        <div className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getDepartmentColor(member.department)}`}>
                          {getDepartmentLabel(member.department)}
                        </div>
                      </div>
                    </div>
                    {hasEvaluated && (
                      <span className="text-xs text-green-600 font-medium">已评价</span>
                    )}
                  </div>
                );
              })}
            </div>

            {teamMembers.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <UserIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>暂无团队成员数据</p>
              </div>
            )}
          </div>

          {/* Evaluation Form */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-4">
              {selectedMember ? `评价 ${selectedMember.name}` : '请先选择评价对象'}
            </h4>
            
            {!selectedMember ? (
              <div className="text-center py-8 text-gray-500">
                <p>请从左侧选择要评价的团队成员</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="rounded-md bg-red-50 p-4">
                    <div className="text-sm text-red-700">{error}</div>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    评分 (1-10分) <span className="text-red-500">*</span>
                  </label>
                  <div className="flex items-center space-x-1">
                    {renderStars()}
                    <span className="ml-3 text-sm text-gray-600">
                      {formData.score > 0 ? `${formData.score}/10` : '请选择评分'}
                    </span>
                  </div>
                </div>

                <div>
                  <label htmlFor="ranking" className="block text-sm font-medium text-gray-700">
                    排名 (1-{teamMembers.length}) <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="ranking"
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    value={formData.ranking}
                    onChange={(e) => setFormData(prev => ({ ...prev, ranking: parseInt(e.target.value) }))}
                  >
                    {[...Array(teamMembers.length)].map((_, i) => (
                      <option key={i + 1} value={i + 1}>第 {i + 1} 名</option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    1表示最优秀，{teamMembers.length}表示相对较弱
                  </p>
                </div>

                <div>
                  <label htmlFor="comment" className="block text-sm font-medium text-gray-700">
                    评价内容 <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    id="comment"
                    rows={4}
                    required
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    value={formData.comment}
                    onChange={(e) => setFormData(prev => ({ ...prev, comment: e.target.value }))}
                    placeholder="请输入您对该成员的评价..."
                  />
                </div>

                <div className="flex items-center">
                  <input
                    id="is_anonymous"
                    type="checkbox"
                    className="rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50"
                    checked={formData.is_anonymous}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_anonymous: e.target.checked }))}
                  />
                  <label htmlFor="is_anonymous" className="ml-2 text-sm text-gray-700">
                    匿名评价
                  </label>
                </div>

                <div className="flex items-center justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setSelectedMember(null)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                  >
                    重新选择
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 disabled:opacity-50"
                  >
                    {loading ? '提交中...' : '提交评价'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Existing Evaluations */}
        {existingEvaluations.length > 0 && (
          <div className="mt-8">
            <h4 className="text-md font-medium text-gray-900 mb-4">
              已提交的评价 ({existingEvaluations.length})
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {existingEvaluations.map((evaluation) => (
                <div key={evaluation.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <UserIcon className="h-4 w-4 text-gray-400" />
                      <span className="text-sm font-medium text-gray-900">
                        {evaluation.monthly_evaluation?.user?.name}
                      </span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getDepartmentColor(evaluation.monthly_evaluation?.user?.department)}`}>
                        {getDepartmentLabel(evaluation.monthly_evaluation?.user?.department)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium">{evaluation.score}/10</span>
                      <span className="text-xs text-gray-500">排名: {evaluation.ranking}</span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">{evaluation.comment}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{evaluation.is_anonymous ? '匿名评价' : '实名评价'}</span>
                    <span>{formatDateTime(evaluation.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PeerEvaluationModal;