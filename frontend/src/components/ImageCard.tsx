import { useState } from "react";
import ReportModal from "./ReportModal";

interface ImageProps {
  id: number;
  image_url: string;
}

export default function ImageCard({ id, image_url }: ImageProps) {
  const normalizedPath = image_url.replace(/\\/g, "/");
  const imageUrl = `http://localhost:8000/${normalizedPath}`;

  const [open, setOpen] = useState(false);

  return (
    <>
      <article className="group overflow-hidden rounded-2xl border border-slate-200/90 bg-surface-elevated shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
        <div className="relative aspect-[4/3] overflow-hidden bg-slate-100">
          <img
            src={imageUrl}
            alt={`Shared image ${id}`}
            className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.02]"
            onError={(e) => {
              (e.target as HTMLImageElement).src = "/placeholder-image.jpg";
              console.error(`Failed to load image: ${imageUrl}`);
            }}
          />
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-slate-100 px-4 py-3">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">Post #{id}</span>
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:border-rose-300 hover:bg-rose-100"
            onClick={() => setOpen(true)}
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Report
          </button>
        </div>
      </article>

      {open && (
        <ReportModal isOpen={open} imageId={id} imageUrl={imageUrl} onClose={() => setOpen(false)} />
      )}
    </>
  );
}
