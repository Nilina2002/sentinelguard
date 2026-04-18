const Loading = ({ message = "Loading..." }) => {
  return (
    <div className="flex flex-col items-center justify-center h-full py-10">
      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      <p className="mt-3 text-gray-600 text-sm">{message}</p>
    </div>
  );
};

export default Loading;