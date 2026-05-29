import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function GuestLayout() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-gray-600"></div>
      </div>
    );
  }

  if (user) {
    return <Navigate to="/forum" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <Outlet />
    </div>
  );
}
