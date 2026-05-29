import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './components/Toast';
import Layout from './components/Layout';
import GuestLayout from './components/GuestLayout';
import Forum from './pages/Forum';
import Login from './pages/Login';
import Register from './pages/Register';
import PostDetail from './pages/PostDetail';
import CreatePost from './pages/CreatePost';
import Chat from './pages/Chat';
import Profile from './pages/Profile';
import UserProfile from './pages/UserProfile';
import Search from './pages/Search';
import Notifications from './pages/Notifications';
import Admin from './pages/Admin';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
        <Routes>
          <Route element={<GuestLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
          </Route>

          <Route element={<Layout />}>
            <Route path="/forum" element={<Forum />} />
            <Route path="/post/:postId" element={<PostDetail />} />
            <Route path="/create-post" element={<CreatePost />} />
            <Route path="/chat/:peerId" element={<Chat />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/user/:userId" element={<UserProfile />} />
            <Route path="/search" element={<Search />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/admin" element={<Admin />} />
          </Route>

          <Route path="/" element={<Forum />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
