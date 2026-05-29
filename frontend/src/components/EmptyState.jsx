export default function EmptyState({ message = '暂无内容' }) {
  return (
    <div className="text-center py-16 text-gray-400 text-sm">
      {message}
    </div>
  );
}
