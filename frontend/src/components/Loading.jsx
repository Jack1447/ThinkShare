export default function Loading({ text = '加载中...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-300 border-t-gray-600 mb-3"></div>
      <span className="text-sm text-gray-400">{text}</span>
    </div>
  );
}
