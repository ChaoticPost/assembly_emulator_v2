import React from 'react';
import { Card, Button } from 'flowbite-react';
import { useEmulatorStore } from '../../store/emulatorStore';
import './ControlPanel.css';

export const ControlPanel: React.FC = () => {
  const { executeStep, executeRemaining, reset, loadTask1Data, loadTask2Data, loading, current_task } = useEmulatorStore();

  return (
    <Card className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <h5 className="control-panel-title text-xl font-bold font-heading">Управление</h5>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Button
          color="light"
          size="lg"
          className="step-button h-16 flex flex-col items-center justify-center space-y-2"
          onClick={executeStep}
          disabled={loading}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-sm font-medium">Следующий шаг</span>
        </Button>

        <Button
          color="success"
          size="lg"
          className="execute-button h-16 flex flex-col items-center justify-center space-y-2 bg-green-600 hover:bg-green-700 text-white border-0"
          onClick={executeRemaining}
          disabled={loading}
        >
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
          </svg>
          <span className="text-sm font-medium">Выполнить целиком</span>
        </Button>

        {current_task === 1 && (
          <Button
            color="info"
            size="lg"
            className="h-16 flex flex-col items-center justify-center space-y-2"
            onClick={loadTask1Data}
            disabled={loading}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span className="text-sm font-medium">Загрузить данные для 1 задачи</span>
          </Button>
        )}

        {current_task === 2 && (
          <Button
            color="info"
            size="lg"
            className="h-16 flex flex-col items-center justify-center space-y-2"
            onClick={loadTask2Data}
            disabled={loading}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span className="text-sm font-medium">Загрузить данные для 2 задачи</span>
          </Button>
        )}

        <Button
          color="failure"
          size="lg"
          className="reset-button h-16 flex flex-col items-center justify-center space-y-2 bg-red-600 hover:bg-red-700 text-white border-0"
          onClick={reset}
          disabled={loading}
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span className="text-sm font-medium">Сброс</span>
        </Button>
      </div>
    </Card>
  );
};