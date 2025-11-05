import React, { useState, useEffect } from 'react';
import { Card, Button, Spinner } from 'flowbite-react';
import { useEmulatorStore } from '../../store/emulatorStore';
import './TaskPanel.css';

export const TaskPanel: React.FC = () => {
  const { tasks, loading, error, loadTasks, setCurrentTask } = useEmulatorStore();
  const [activeTask, setActiveTask] = useState<number | null>(null);

  useEffect(() => {
    loadTasks().catch((error) => {
      console.warn('Не удалось загрузить задачи:', error);
    });
  }, [loadTasks]);

  const handleTaskSelect = async (taskId: number) => {
    // Toggle behavior: if same task is clicked, close it; otherwise open new task
    if (activeTask === taskId) {
      setActiveTask(null);
      await setCurrentTask(null);
    } else {
      setActiveTask(taskId);
      await setCurrentTask(taskId);
    }
  };


  return (
    <Card className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <h5 className="text-xl font-bold text-white-900 font-heading">Задания</h5>
        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-8">
          <Spinner size="lg" />
          <span className="ml-2 text-gray-600">Загрузка задач...</span>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      ) : (
        <div className="space-y-3 mb-6">
          {tasks.map((task) => (
            <div key={task.id} className="space-y-2">
              <Button
                color={activeTask === task.id ? "success" : "light"}
                size="sm"
                className={`w-full justify-start transition-all duration-300 ${activeTask === task.id
                  ? 'ring-2 ring-green-500 transform scale-105'
                  : 'hover:scale-102'
                  }`}
                onClick={() => handleTaskSelect(task.id)}
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                {task.title}
              </Button>
            </div>
          ))}
        </div>
      )}

      {activeTask && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 animate-fadeInUp">
          <h4 className="text-lg font-semibold text-blue-900 mb-2 font-heading">
            {tasks.find(t => t.id === activeTask)?.title}
          </h4>
          <p className="text-blue-800 text-sm leading-relaxed font-body">
            {tasks.find(t => t.id === activeTask)?.description}
          </p>
          <div className="mt-3 flex items-center">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-1.5 animate-pulse"></div>
              Активно
            </span>
          </div>
        </div>
      )}
    </Card>
  );
};