import { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-16 right-5 z-[200] flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-5 py-3 rounded-lg shadow-lg text-sm font-medium animate-slide-in
              ${t.type === 'success' ? 'bg-green-50 text-green-600 border border-green-200' : ''}
              ${t.type === 'error' ? 'bg-red-50 text-red-500 border border-red-200' : ''}
              ${t.type === 'info' ? 'bg-blue-50 text-blue-500 border border-blue-200' : ''}
            `}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
}
