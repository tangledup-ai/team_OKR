import api from './api';

export const reportService = {
  // Monthly Report APIs
  getMonthlyReportOverview: async (month) => {
    const response = await api.get(`/api/reports/monthly-reports/overview/?month=${month}`);
    return response.data;
  },

  getPersonalReport: async (userId, month) => {
    const response = await api.get(`/api/reports/monthly-reports/personal/?user_id=${userId}&month=${month}`);
    return response.data;
  },

  getDepartmentReport: async (department, month) => {
    const response = await api.get(`/api/reports/monthly-reports/department/?department=${department}&month=${month}`);
    return response.data;
  },

  // Performance Score APIs
  getPerformanceScores: async (month) => {
    const response = await api.get(`/api/reports/performance-scores/?month=${month}`);
    return response.data;
  },

  getUserPerformanceScore: async (userId, month) => {
    const response = await api.get(`/api/reports/performance-scores/user/?user_id=${userId}&month=${month}`);
    return response.data;
  },

  getDepartmentPerformanceScores: async (department, month) => {
    const response = await api.get(`/api/reports/performance-scores/department/?department=${department}&month=${month}`);
    return response.data;
  },

  // Monthly Evaluation APIs (from existing evaluationService)
  getEvaluationSummary: async (month) => {
    const response = await api.get(`/api/reports/monthly-evaluations/summary/?month=${month}`);
    return response.data;
  },

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

  // Work Hours APIs
  getWorkHours: async (month, userId = null) => {
    let url = `/api/reports/work-hours/?month=${month}`;
    if (userId) {
      url += `&user=${userId}`;
    }
    const response = await api.get(url);
    return response.data;
  },

  // Department Statistics
  getDepartmentStats: async (month) => {
    const response = await api.get(`/api/reports/department-stats/?month=${month}`);
    return response.data;
  },

  // Rankings
  getMonthlyRankings: async (month) => {
    const response = await api.get(`/api/reports/rankings/?month=${month}`);
    return response.data;
  },

  // Utility functions
  formatMonth: (date) => {
    if (typeof date === 'string') {
      return date;
    }
    return date.toISOString().split('T')[0].substring(0, 7) + '-01';
  },

  getCurrentMonth: () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
  },

  getPreviousMonth: () => {
    const now = new Date();
    const prevMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    return `${prevMonth.getFullYear()}-${String(prevMonth.getMonth() + 1).padStart(2, '0')}-01`;
  }
};