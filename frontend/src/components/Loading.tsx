type LoadingProps = {
  message?: string;
  fullScreen?: boolean;
};

const Loading = ({ message = "Loading…", fullScreen = false }: LoadingProps) => {
  const inner = (
    <>
      <div
        className="h-10 w-10 rounded-full border-2 border-teal-200 border-t-teal-600 animate-spin"
        aria-hidden
      />
      <p className="mt-4 text-center text-sm font-medium text-slate-600">{message}</p>
    </>
  );

  if (fullScreen) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-slate-100 via-surface to-slate-50">
        {inner}
      </div>
    );
  }

  return (
    <div className="flex min-h-[12rem] flex-col items-center justify-center py-12" role="status" aria-live="polite">
      {inner}
    </div>
  );
};

export default Loading;
