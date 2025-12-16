import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { reportService } from '../services/reportService';
import { evaluationService } from '../services/evaluationService';
import Header from '../components/Header';
import RankingDisplay from '../components/RankingDisplay';
import EvaluationDisplay from '../components/EvaluationDisplay';
import AdminEvaluationForm from '../components/AdminEvaluationForm';
import PersonalReportModal from '../components/PersonalReportModal';
import DepartmentReportModal from '../components/DepartmentReportModal';

const MonthlyReportPage = () => {
  const { user } = useAuth();
  const [selectedMonth, setSelectedMonth] = useState(reportService.getPreviousMonth());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Data states
  const [performanceScores, setPerformanceScores] = useState([]);
  const [evaluationSummary, setEvaluationSummary] = useState([]);
  const [departmentStats, setDepartmentStats] = useState([]);
  const [allEvaluations, setAllEvaluations] = useState([]);
  
  // Modal states
  const [showPersonalReport, setShowPersonalReport] = useState(false);
  const [showDepartmentReport, setShowDepartmentReport] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedDepartment, setSelectedDepartment] = useState(null);
  
  // Admin evaluation states
  const [showAdminEvaluation, setShowAdminEvaluation] = useState(false);
  const [pendingEvaluations, setPendingEvaluations] = useState([]);

  useEffect(() => {
    loadReportData();
  }, [selectedMonth]);

  const loadReportData = async () => {
    try {
      setLoading(true);
      setError('');

      // Load performance scores and rankings
      const scoresResponse = await reportService.getPerformanceScores(selectedMonth);
      setPerformanceScores(scoresResponse.results || scoresResponse);

      // Load evaluation summary
      const summaryResponse = await evaluationService.getEvaluationSummary(selectedMonth);
      setEvaluationSummary(summaryResponse);

      // Load department statistics
      try {
        const deptStats = await reportService.getDepartmentStats(selectedMonth);
        setDepartmentStats(deptStats);
      } catch (err) {
        console.warn('Department stats not available:', err);
        setDepartmentStats([]);
      }

      // Load admin evaluations if user is admin
      if (user?.role === 'admin') {
        const adminEvals = await evaluationService.adminViewAllEvaluations(selectedMonth);
        setAllEvaluations(adminEvals);
        
        // Filter pending evaluations (those without admin final score)
        const pending = adminEvals.filter(eval => !eval.admin_final_score);
        setPendingEvaluations(pending);
      }

    } catch (err) {
      setError('加载月度报告失败');
      console.error('Error loading report data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMonthChange = (event) => {
    setSelectedMonth(event.target.value);
  };

  const handleViewPersonalReport = (userToView) => {
    setSelectedUser(userToView);
    setShowPersonalReport(true);
  };

  const handleViewDepartmentReport = (department) => {
    setSelectedDepartment(department);
    setShowDepartmentReport(true);
  };

  const handleAdminEvaluationSubmit = async (evaluationData) => {
    try {
      await evaluationService.batchAdminEvaluation(evaluationData);
      await loadReportData(); // Reload data after admin evaluation
      setShowAdminEvaluation(false);
    } catch (err) {
      console.error('Error submitting admin evaluation:', err);
      setError('提交管理员评价失败');
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="container mx-auto px-4 py-6">
        {/* Header Section */}
        <div className="mb-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">月度报告</h1>
            <div className="flex items-center space-x-4">
              <select
                value={selectedMonth}
                onChange={handleMonthChange}
                className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {/* Generate last 12 months */}
                {Array.from({ length: 12 }, (_, i) => {
                  const date = new Date();
                  date.setMonth(date.getMonth() - i - 1);
                  const monthStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-01`;
                  return (
                    <option key={monthStr} value={monthStr}>
                      {formatMonth(monthStr)}
                    </option>
                  );
                })}
              </select>
              
              {user?.role === 'admin' && pendingEvaluations.length > 0 && (
                <button
                  onClick={() => setShowAdminEvaluation(true)}
                  className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 focus:ring-2 focus:ring-orange-500"
                >
                  待评价 ({pendingEvaluations.length})
                </button>
              )}
            </div>
          </div>
          
          <p className="text-gray-600 mt-2">
            {formatMonth(selectedMonth)} 团队绩效报告总览
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Rankings */}
          <div className="lg:col-span-2">
            <RankingDisplay
              performanceScores={performanceScores}
              onViewPersonalReport={handleViewPersonalReport}
              currentUser={user}
            />
          </div>

          {/* Right Column - Department Stats & Evaluations */}
          <div className="space-y-6">
            {/* Department Performance */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">部门表现</h3>
              {departmentStats.length > 0 ? (
                <div className="space-y-4">
                  {departmentStats.map((dept) => (
                    <div
                      key={dept.department}
                      className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => handleViewDepartmentReport(dept.department)}
                    >
                      <div className="flex justify-between items-center">
                        <h4 className="font-medium text-gray-900">
                          {getDepartmentName(dept.department)}
                        </h4>
                        <span className="text-sm text-gray-500">
                          {dept.member_count}人
                        </span>
                      </div>
                      <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">平均分:</span>
                          <span className="ml-1 font-medium">{dept.avg_score}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">完成任务:</span>
                          <span className="ml-1 font-medium">{dept.completed_tasks}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">暂无部门数据</p>
              )}
            </div>

            {/* Evaluation Summary */}
            <EvaluationDisplay
              evaluationSummary={evaluationSummary}
              selectedMonth={selectedMonth}
              onViewPersonalReport={handleViewPersonalReport}
            />
          </div>
        </div>
      </div>

      {/* Modals */}
      {showPersonalReport && selectedUser && (
        <PersonalReportModal
          user={selectedUser}
          month={selectedMonth}
          onClose={() => {
            setShowPersonalReport(false);
            setSelectedUser(null);
          }}
        />
      )}

      {showDepartmentReport && selectedDepartment && (
        <DepartmentReportModal
          department={selectedDepartment}
          month={selectedMonth}
          onClose={() => {
            setShowDepartmentReport(false);
            setSelectedDepartment(null);
          }}
        />
      )}

      {showAdminEvaluation && user?.role === 'admin' && (
        <AdminEvaluationForm
          evaluations={pendingEvaluations}
          month={selectedMonth}
          onClose={() => setShowAdminEvaluation(false)}
          onSubmit={handleAdminEvaluationSubmit}
        />
      )}
    </div>
  );
};

export default MonthlyReportPage;