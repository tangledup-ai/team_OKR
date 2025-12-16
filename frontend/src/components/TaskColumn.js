import React, { useState } from 'react';
import { useDrop } from 'react-dnd';
import TaskCard from './TaskCard';
import PostponeReasonModal from './PostponeReasonModal';

const TaskColumn = ({ status, title, tasks, onTaskMove, onTaskClick, onTaskReview, currentUser }) => {
  const [showPostponeModal, setShowPostponeModal] = useState(false);
  const [postponeTaskId, setPostponeTaskId] = useState(null);

  const [{ isOver }, drop] = useDrop({
    accept: 'task',
    drop: (item) => {
      if (item.status !== status) {
        if (status === 'postponed') {
          // Show postpone reason modal
          setPostponeTaskId(item.id);
          setShowPostponeModal(true);
        } else {
          onTaskMove(item.id, status);
        }
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
    }),
  });

  const handlePostponeSubmit = (reason) => {
    if (postponeTaskId) {
      onTaskMove(postponeTaskId, 'postponed', reason);
      setPostponeTaskId(null);
      setShowPostponeModal(false);
    }
  };

  const getColumnColor = () => {
    const colors = {
      'todo': 'border-gray-300 bg-gray-50',
      'in_progress': 'border-blue-300 bg-blue-50',
      'completed': 'border-green-300 bg-green-50',
      'postponed': 'border-red-300 bg-red-50'
    };
    return colors[status] || 'border-gray-300 bg-gray-50';
  };

  const getHeaderColor = () => {
    const colors = {
      'todo': 'text-gray-700 bg-gray-100',
      'in_progress': 'text-blue-700 bg-blue-100',
      'completed': 'text-green-700 bg-green-100',
      'postponed': 'text-red-700 bg-red-100'
    };
    return colors[status] || 'text-gray-700 bg-gray-100';
  };

  return (
    <div
      ref={drop}
      className={`
        drop-zone rounded-lg border-2 border-dashed p-4 min-h-96
        ${getColumnColor()}
        ${isOver ? 'drag-over' : ''}
      `}
    >
      <div className={`rounded-md px-3 py-2 mb-4 ${getHeaderColor()}`}>
        <h3 className="font-semibold text-sm">
          {title}
          <span className="ml-2 text-xs opacity-75">
            ({tasks.length})
          </span>
        </h3>
      </div>

      <div className="space-y-3 custom-scrollbar max-h-96 overflow-y-auto">
        {tasks.map(task => (
          <TaskCard
            key={task.id}
            task={task}
            onClick={() => onTaskClick(task)}
            onReview={onTaskReview}
            currentUser={currentUser}
          />
        ))}
        
        {tasks.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            <p className="text-sm">暂无任务</p>
          </div>
        )}
      </div>

      {showPostponeModal && (
        <PostponeReasonModal
          onSubmit={handlePostponeSubmit}
          onClose={() => {
            setShowPostponeModal(false);
            setPostponeTaskId(null);
          }}
        />
      )}
    </div>
  );
};

export default TaskColumn;