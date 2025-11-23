import React from 'react';
import './TaskList.css';

interface TaskListProps {
  selectedTasks: { [key: number]: boolean };
  onTaskToggle: (taskId: number, checked: boolean) => void;
}

const tasks = [
  { id: 1, title: 'Сумма элементов массива' },
  { id: 2, title: 'Свертка двух массивов' }
];

export const TaskList: React.FC<TaskListProps> = ({ selectedTasks, onTaskToggle }) => {
  const handleToggle = (taskId: number) => {
    const isChecked = selectedTasks[taskId] || false;
    onTaskToggle(taskId, !isChecked);
  };

  return (
    <div className="task-list-container">
      <ul className="task-list">
        {tasks.map(task => (
          <li key={task.id} className="task-item">
            <label className="task-label">
              <input
                type="checkbox"
                checked={selectedTasks[task.id] || false}
                onChange={() => handleToggle(task.id)}
                className="task-checkbox"
              />
              <span className="task-text">{task.title}</span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
};

