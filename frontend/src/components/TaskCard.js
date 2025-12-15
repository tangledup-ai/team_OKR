import React from 'react';
import { useDrag } from 'react-dnd';
import { UserIcon, CalendarIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';

const TaskCard = ({ task, onClick, currentUser }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'task',
    item: { id: task.id, status: task.status },
    canDrag: () => {
      // Only allow dragging if user is owner or collaborator
      return task.owner?.id === currentUser?.id || 
             task.collaborators?.some(c => c.id === currentUser?.id);
    },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const getDifficultyColor = (score) => {
    if (score <= 3) return 'bg-green-100 text-green-800';
    if (score <= 6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric'
    });
  };

  const canEdit = task.owner?.id === currentUser?.id || 
                  task.collaborators?.some(c => c.id === currentUser?.id);

  return (
    <div
      ref={drag}
      onClick={onClick}
      className={`
        task-card bg-white rounded-lg shadow-sm border border-gray-200 p-4 cursor-pointer
        ${isDragging ? 'drag-preview' : ''}
        ${!canEdit ? 'opacity-75' : ''}
      `}
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-medium text-gray-900 text-sm line-clamp-2">
          {task.title}
        </h4>
        <span className={`
          inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
          ${getDifficultyColor(task.difficulty_score)}
        `}>
          {task.difficulty_score}
        </span>
      </div>

      {task.description && (
        <p className="text-gray-600 text-xs mb-3 line-clamp-2">
          {task.description}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-2">
          <div className="flex items-center">
            <UserIcon className="h-3 w-3 mr-1" />
            <span>{task.owner?.name}</span>
          </div>
          
          {task.collaborators && task.collaborators.length > 0 && (
            <span className="text-gray-400">
              +{task.collaborators.length}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {task.revenue_amount > 0 && (
            <div className="flex items-center text-green-600">
              <CurrencyDollarIcon className="h-3 w-3 mr-1" />
              <span>{task.revenue_amount}</span>
            </div>
          )}
          
          {(task.completed_at || task.started_at) && (
            <div className="flex items-center">
              <CalendarIcon className="h-3 w-3 mr-1" />
              <span>
                {formatDate(task.completed_at || task.started_at)}
              </span>
            </div>
          )}
        </div>
      </div>

      {task.postpone_reason && (
        <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700">
          推迟原因: {task.postpone_reason}
        </div>
      )}

      {!canEdit && (
        <div className="mt-2 text-xs text-gray-400">
          只读 - 您不是此任务的参与者
        </div>
      )}
    </div>
  );
};

export default TaskCard;