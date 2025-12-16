import React, { useState, useEffect } from 'react';
import { XMarkIcon, StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { evaluationService } from '../services/evaluationService';

const TaskReviewModal = ({ task, onClose, onSubmit, currentUser }) => {
  const [formData, setFormData] = useState({
    rating: 0,
    comment: '',
    is_anonymous: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [existingReviews, setExistingReviews] = useState([]);
  const [reviewSummary, setReviewSummary] = useState(null);
  const [hoveredRating, setHoveredRating] = useState(0);

  useEffect(() => {
    if (task?.id) {
      loadTaskReviews();
      loadReviewSummary();
    }
  }, [task?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadTaskReviews = async () => {
    try {
      const reviews = await evaluationService.getTaskReviews(task.id);
      setExistingReviews(reviews);
    } catch (err) {
      console.error('Failed to load task reviews:', err);
    }
  };

  const loadReviewSummary = async () => {
    try {
      const summary = await evaluationService.getTaskReviewSummary(task.id);
      setReviewSummary(summary);
    } catch (err) {
      console.error('Failed to load review summary:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.rating === 0) {
      setError('请选择评分');
      return;
    }

    if (!formData.comment.trim()) {
      setError('请输入评价内容');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const reviewData = {
        task: task.id,
        rating: formData.rating,
        comment: formData.comment.trim(),
        is_anonymous: formData.is_anonymous
      };

      await evaluationService.submitTaskReview(reviewData);
      
      if (onSubmit) {
        onSubmit();
      }
      
      // Reload reviews to show the new one
      await loadTaskReviews();
      await loadReviewSummary();
      
      // Reset form
      setFormData({
        rating: 0,
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
    setFormData(prev => ({ ...prev, rating }));
  };

  const handleRatingHover = (rating) => {
    setHoveredRating(rating);
  };

  const handleRatingLeave = () => {
    setHoveredRating(0);
  };

  const renderStars = () => {
    const stars = [];
    const displayRating = hoveredRating || formData.rating;
    
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

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const canReview = task?.status === 'completed' && 
                   task?.owner?.id !== currentUser?.id && 
                   !task?.collaborators?.some(c => c.id === currentUser?.id);

  const hasUserReviewed = existingReviews.some(review => 
    review.reviewer?.id === currentUser?.id
  );

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-10 mx-auto p-5 border w-full max-w-4xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            任务评价 - {task?.title}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Review Summary */}
        {reviewSummary && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium text-gray-900 mb-2">评价汇总</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">平均评分:</span>
                <span className="ml-2 font-medium">{reviewSummary.average_rating}/10</span>
              </div>
              <div>
                <span className="text-gray-600">评价数量:</span>
                <span className="ml-2 font-medium">{reviewSummary.review_count}</span>
              </div>
              <div>
                <span className="text-gray-600">管理员评价:</span>
                <span className="ml-2 font-medium">{reviewSummary.admin_review_count}</span>
              </div>
              <div>
                <span className="text-gray-600">调整系数:</span>
                <span className="ml-2 font-medium">{reviewSummary.adjustment_factor}</span>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Review Form */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-4">提交评价</h4>
            
            {!canReview ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <p className="text-yellow-800 text-sm">
                  {task?.status !== 'completed' 
                    ? '只能对已完成的任务进行评价'
                    : '不能评价自己参与的任务'
                  }
                </p>
              </div>
            ) : hasUserReviewed ? (
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                <p className="text-blue-800 text-sm">
                  您已经对此任务进行过评价
                </p>
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
                      {formData.rating > 0 ? `${formData.rating}/10` : '请选择评分'}
                    </span>
                  </div>
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
                    placeholder="请输入您对此任务的评价..."
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
                    {loading ? '提交中...' : '提交评价'}
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Existing Reviews */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-4">
              已有评价 ({existingReviews.length})
            </h4>
            
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {existingReviews.length === 0 ? (
                <p className="text-gray-500 text-sm">暂无评价</p>
              ) : (
                existingReviews.map((review) => (
                  <div key={review.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">
                          {review.is_anonymous ? '匿名用户' : review.reviewer?.name}
                        </span>
                        {review.reviewer?.role === 'admin' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                            管理员
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="flex items-center">
                          {[...Array(review.rating)].map((_, i) => (
                            <StarIconSolid key={i} className="h-4 w-4 text-yellow-400" />
                          ))}
                          {[...Array(10 - review.rating)].map((_, i) => (
                            <StarIcon key={i} className="h-4 w-4 text-gray-300" />
                          ))}
                        </div>
                        <span className="text-sm font-medium">{review.rating}/10</span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{review.comment}</p>
                    <p className="text-xs text-gray-500">
                      {formatDateTime(review.created_at)}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskReviewModal;