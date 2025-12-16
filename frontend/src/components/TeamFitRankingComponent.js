import React, { useState, useEffect } from 'react';
import { useDrag, useDrop } from 'react-dnd';
import { UserIcon, Bars3Icon } from '@heroicons/react/24/outline';

const ItemType = 'TEAM_MEMBER';

const DraggableTeamMember = ({ member, index, moveItem }) => {
  const [{ isDragging }, drag] = useDrag({
    type: ItemType,
    item: { index },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [, drop] = useDrop({
    accept: ItemType,
    hover: (draggedItem) => {
      if (draggedItem.index !== index) {
        moveItem(draggedItem.index, index);
        draggedItem.index = index;
      }
    },
  });

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

  return (
    <div
      ref={(node) => drag(drop(node))}
      className={`flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg cursor-move transition-all ${
        isDragging ? 'opacity-50 shadow-lg' : 'hover:shadow-md'
      }`}
    >
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-full text-sm font-medium text-gray-600">
          {index + 1}
        </div>
        <UserIcon className="h-5 w-5 text-gray-400" />
        <div>
          <div className="text-sm font-medium text-gray-900">{member.name}</div>
          <div className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getDepartmentColor(member.department)}`}>
            {getDepartmentLabel(member.department)}
          </div>
        </div>
      </div>
      <Bars3Icon className="h-5 w-5 text-gray-400" />
    </div>
  );
};

const TeamFitRankingComponent = ({ members, ranking, onChange }) => {
  const [orderedMembers, setOrderedMembers] = useState([]);

  useEffect(() => {
    // Initialize ordered members based on ranking
    if (ranking && ranking.length > 0 && members.length > 0) {
      const ordered = ranking.map(id => members.find(member => member.id === id)).filter(Boolean);
      // Add any members not in ranking to the end
      const missingMembers = members.filter(member => !ranking.includes(member.id));
      setOrderedMembers([...ordered, ...missingMembers]);
    } else {
      setOrderedMembers([...members]);
    }
  }, [members, ranking]);

  const moveItem = (fromIndex, toIndex) => {
    const newOrderedMembers = [...orderedMembers];
    const [movedItem] = newOrderedMembers.splice(fromIndex, 1);
    newOrderedMembers.splice(toIndex, 0, movedItem);
    
    setOrderedMembers(newOrderedMembers);
    
    // Update the ranking array with new order
    const newRanking = newOrderedMembers.map(member => member.id);
    onChange(newRanking);
  };

  if (members.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <UserIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
        <p>暂无团队成员数据</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-600 mb-3">
        拖拽下方成员卡片进行排序，排名越靠前表示契合度越高
      </div>
      
      <div className="space-y-2">
        {orderedMembers.map((member, index) => (
          <DraggableTeamMember
            key={member.id}
            member={member}
            index={index}
            moveItem={moveItem}
          />
        ))}
      </div>
      
      <div className="text-xs text-gray-500 mt-3">
        当前排序：{orderedMembers.map((member, index) => `${index + 1}. ${member.name}`).join(' → ')}
      </div>
    </div>
  );
};

export default TeamFitRankingComponent;