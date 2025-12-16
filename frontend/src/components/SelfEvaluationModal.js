import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { evaluationService } from '../services/evaluationService';
import TeamFitRankingComponent from './TeamFitRankingComponent';

const SelfEvaluationModal = ({ month, onClose, onSubmit, currentUser }) => {
  const [formData, setFormData] = useState({
    month: month,
    culture_understanding_score: 1,
    culture_understanding_text: '',
    culture_understanding_option: '',
    team_fit_option: '',
    team_fit_text: '',
    team_fit_ranking: [],
    monthly_growth_score: 1,
    monthly_growth_text: '',
    monthly_growth_option: '',
    biggest_contribution_score: 1,
    biggest_contribution_text: '',
    biggest_contribution_option: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [teamMembers, setTeamMembers] = useState([]);
  const [existingEvaluation, setExistingEvaluation] = useState(null);

  const cultureOptions = [
    '深度理解并积极践行',
    '基本理解并努力践行',
    '理解但践行不够',
    '理解有限需要改进'
  ];

  const teamFitOptions = [
    '完全融入团队',
    '基本融入团队',
    '融入程度一般',
    '需要更好融入'
  ];

  const growthOptions = [
    '技能显著提升',
    '技能有所提升',
    '技能提升有限',
    '技能需要加强'
  ];

  const contributionOptions = [
    '重大项目贡献',
    '重要任务完成',
    '日常工作优秀',
    '团队协作支持'
  ];

  useEffect(() => {
    loadTeamMembers();
    loadExistingEvaluation();
  }, [month]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadTeamMembers = async () => {
    try {
      const members = await evaluationService.getTeamMembers();
      setTeamMembers(members);
      // Initialize ranking with all team members
      setFormData(prev => ({
        ...prev,
        team_fit_ranking: members.map(member => member.id)
      }));
    } catch (err) {
      console.error('Failed to load team members:', err);
    }
  };

  const loadExistingEvaluation = async () => {
    try {
      const evaluation = await evaluationService.getMyEvaluation(month);
      if (evaluation) {
        setExistingEvaluation(evaluation);
        setFormData({
          month: month,
          culture_understanding_score: evaluation.culture_understanding_score,
          culture_understanding_text: evaluation.culture_understanding_text,
          culture_understanding_option: evaluation.culture_understanding_option,
          team_fit_option: evaluation.team_fit_option,
          team_fit_text: evaluation.team_fit_text,
          team_fit_ranking: evaluation.team_fit_ranking || [],
          monthly_growth_score: evaluation.monthly_growth_score,
          monthly_growth_text: evaluation.monthly_growth_text,
          monthly_growth_option: evaluation.monthly_growth_option,
          biggest_contribution_score: evaluation.biggest_contribution_score,
          biggest_contribution_text: evaluation.biggest_contribution_text,
          biggest_contribution_option: evaluation.biggest_contribution_option
        });
      }
    } catch (err) {
      // No existing evaluation is fine
      console.log('No existing evaluation found');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!formData.culture_understanding_text.trim()) {
      setError('请填写企业文化理解的文字描述');
      return;
    }
    if (!formData.culture_understanding_option) {
      setError('请选择企业文化理解选项');
      return;
    }
    if (!formData.team_fit_option) {
      setError('请选择团队契合度选项');
      return;
    }
    if (!formData.team_fit_text.trim()) {
      setError('请填写团队契合度的文字描述');
      return;
    }
    if (formData.team_fit_ranking.length !== teamMembers.length) {
      setError('请完成团队成员排名');
      return;
    }
    if (!formData.monthly_growth_text.trim()) {
      setError('请填写本月成长的文字描述');
      return;
    }
    if (!formData.monthly_growth_option) {
      setError('请选择本月成长选项');
      return;
    }
    if (!formData.biggest_contribution_text.trim()) {
      setError('请填写本月最大贡献的文字描述');
      return;
    }
    if (!formData.biggest_contribution_option) {
      setError('请选择本月最大贡献选项');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await evaluationService.submitSelfEvaluation(formData);
      
      if (onSubmit) {
        onSubmit();
      }
      
      onClose();
    } catch (err) {
      setError(err.response?.data?.message || '提交自我评价失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRankingChange = (newRanking) => {
    setFormData(prev => ({
      ...prev,
      team_fit_ranking: newRanking
    }));
  };

  const formatMonth = (monthStr) => {
    const date = new Date(monthStr);
    return `${date.getFullYear()}年${date.getMonth() + 1}月`;
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            {formatMonth(month)} 月度自我评价
            {existingEvaluation && (
              <span className="ml-2 text-sm text-blue-600">(更新现有评价)</span>
            )}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {/* 企业文化理解 */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="text-md font-medium text-gray-900 mb-4">1. 企业文化理解</h4>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  自评分数 (1-10分) <span className="text-red-500">*</span>
                </label>
                <select
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.culture_understanding_score}
                  onChange={(e) => setFormData(prev => ({ ...prev, culture_understanding_score: parseInt(e.target.value) }))}
                >
                  {[...Array(10)].map((_, i) => (
                    <option key={i + 1} value={i + 1}>{i + 1}分</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择最符合的描述 <span className="text-red-500">*</span>
                </label>
                <select
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.culture_understanding_option}
                  onChange={(e) => setFormData(prev => ({ ...prev, culture_understanding_option: e.target.value }))}
                >
                  <option value="">请选择</option>
                  {cultureOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  详细描述 <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.culture_understanding_text}
                  onChange={(e) => setFormData(prev => ({ ...prev, culture_understanding_text: e.target.value }))}
                  placeholder="请描述您对企业文化的理解和践行情况..."
                />
              </div>
            </div>
          </div>

          {/* 团队契合度 */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="text-md font-medium text-gray-900 mb-4">2. 团队契合度</h4>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择最符合的描述 <span className="text-red-500">*</span>
                </label>
                <select
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.team_fit_option}
                  onChange={(e) => setFormData(prev => ({ ...prev, team_fit_option: e.target.value }))}
                >
                  <option value="">请选择</option>
                  {teamFitOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  详细描述 <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.team_fit_text}
                  onChange={(e) => setFormData(prev => ({ ...prev, team_fit_text: e.target.value }))}
                  placeholder="请描述您与团队的契合情况..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  团队成员排名 <span className="text-red-500">*</span>
                </label>
                <p className="text-xs text-gray-500 mb-3">
                  请根据您认为的团队契合度对其他成员进行排名（拖拽排序）
                </p>
                <TeamFitRankingComponent
                  members={teamMembers}
                  ranking={formData.team_fit_ranking}
                  onChange={handleRankingChange}
                />
              </div>
            </div>
          </div>

          {/* 本月成长 */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="text-md font-medium text-gray-900 mb-4">3. 本月成长</h4>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  自评分数 (1-10分) <span className="text-red-500">*</span>
                </label>
                <select
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.monthly_growth_score}
                  onChange={(e) => setFormData(prev => ({ ...prev, monthly_growth_score: parseInt(e.target.value) }))}
                >
                  {[...Array(10)].map((_, i) => (
                    <option key={i + 1} value={i + 1}>{i + 1}分</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择最符合的描述 <span className="text-red-500">*</span>
                </label>
                <select
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.monthly_growth_option}
                  onChange={(e) => setFormData(prev => ({ ...prev, monthly_growth_option: e.target.value }))}
                >
                  <option value="">请选择</option>
                  {growthOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  详细描述 <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.monthly_growth_text}
                  onChange={(e) => setFormData(prev => ({ ...prev, monthly_growth_text: e.target.value }))}
                  placeholder="请描述您本月的成长和学习情况..."
                />
              </div>
            </div>
          </div>

          {/* 本月最大贡献 */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="text-md font-medium text-gray-900 mb-4">4. 本月最大贡献</h4>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  自评分数 (1-10分) <span className="text-red-500">*</span>
                </label>
                <select
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.biggest_contribution_score}
                  onChange={(e) => setFormData(prev => ({ ...prev, biggest_contribution_score: parseInt(e.target.value) }))}
                >
                  {[...Array(10)].map((_, i) => (
                    <option key={i + 1} value={i + 1}>{i + 1}分</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  选择最符合的描述 <span className="text-red-500">*</span>
                </label>
                <select
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.biggest_contribution_option}
                  onChange={(e) => setFormData(prev => ({ ...prev, biggest_contribution_option: e.target.value }))}
                >
                  <option value="">请选择</option>
                  {contributionOptions.map(option => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  详细描述 <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  value={formData.biggest_contribution_text}
                  onChange={(e) => setFormData(prev => ({ ...prev, biggest_contribution_text: e.target.value }))}
                  placeholder="请描述您本月最大的贡献..."
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {loading ? '提交中...' : (existingEvaluation ? '更新评价' : '提交评价')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SelfEvaluationModal;