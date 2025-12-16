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
      console.error('Error submitting admin evaluation:', e