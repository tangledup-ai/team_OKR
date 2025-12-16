import api from './api';

export const evaluationService = {
  // Task Review APIs
  submitTaskReview: async (reviewData) => {
    const response = await api.post('/api/reviews/api/reviews/task-review/', reviewData);
    return response.data;
  },

  getTaskReviews: async (taskId) => {
    const response = await api.get(`/api/reviews/api/reviews/task-reviews/${taskId}/`);
    return response.data;
  },

  getTaskReviewSummary: async (taskId) => {
    const response = await api.get(`/api/reviews/api/reviews/task-summary/${taskId}/`);
    return response.data;
  },

  // Monthly Evaluation APIs
  submitSelfEvaluation: async (evaluationData) => {
    const response = await api.post('/api/reports/monthly-evaluations/self-evaluation/', evaluationData);
    return response.data;
  },

  submitPeerEvaluation: async (evaluationData, month) => {
    const response = await api.post(`/api/reports/monthly-evaluations/peer-evaluation/?month=${month}`, evaluationData);
    return response.data;
  },

  getMyEvaluation: async (month) => {
    const response = await api.get(`/api/reports/monthly-evaluations/my-evaluation/?month=${month}`);
    return response.data;
  },

  getUserEvaluation: async (userId, month) => {
    const response = await api.get(`/api/reports/monthly-evaluations/?user=${userId}&month=${month}`);
    // Handle both paginated and non-paginated responses
    const results = response.data.results || response.data;
    return Array.isArray(results) ? results[0] : results;
  },

  getTeamMembers: async () => {
    const response = await api.get('/api/reports/monthly-evaluations/team-members/');
    return response.data;
  },

  getPeerEvaluations: async (month, evalueeId = null) => {
    let url = `/api/reports/monthly-evaluations/peer-evaluations/?month=${month}`;
    if (evalueeId) {
      url += `&evaluee=${evalueeId}`;
    }
    const response = await api.get(url);
    return response.data;
  },

  getEvaluationSummary: async (month) => {
    const response = await api.get(`/api/reports/monthly-evaluations/summary/?month=${month}`);
    return response.data;
  },

  // Admin APIs
  adminViewAllEvaluations: async (month) => {
    const response = await api.get(`/api/reports/monthly-evaluations/admin-view-all/?month=${month}`);
    return response.data;
  },

  submitAdminEvaluation: async (evaluationId, evaluationData) => {
    const response = await api.patch(`/api/reports/monthly-evaluations/${evaluationId}/admin-evaluation/`, evaluationData);
    return response.data;
  },

  batchAdminEvaluation: async (evaluationsData) => {
    const response = await api.post('/api/reports/monthly-evaluations/batch-admin-evaluation/', {
      evaluations: evaluationsData
    });
    return response.data;
  },

  getAdminEvaluationHistory: async (userId = null, month = null) => {
    let url = '/api/reports/monthly-evaluations/admin-history/';
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (month) params.append('month', month);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await api.get(url);
    return response.data;
  }
};