import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="text-center py-32">
      <h1 className="text-7xl text-gray-300 font-bold mb-4">404</h1>
      <p className="text-lg text-gray-400 mb-6">页面不存在</p>
      <Link to="/forum" className="text-gray-700 hover:text-black underline">返回论坛首页</Link>
    </div>
  );
}
