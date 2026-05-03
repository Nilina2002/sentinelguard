import { useEffect, useState } from "react";
import api from "../api/client";
import ImageCard from "../components/ImageCard";
import { toast } from "react-toastify";
import Loading from "../components/Loading";

interface ImageType {
  id: number;
  image_url: string;
}

export default function Home() {
  const [images, setImages] = useState<ImageType[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchImages = async () => {
    try {
      const res = await api.get("/images");
      setImages(res.data);
    } catch {
      toast.error("Could not load the feed. Try again in a moment.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  if (loading) return <Loading message="Loading your feed…" />;

  return (
    <div className="space-y-8">
      <header className="rounded-2xl border border-slate-200/80 bg-surface-elevated/80 p-6 shadow-sm shadow-slate-200/50 backdrop-blur-sm sm:p-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-teal-600">Community feed</p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Home</h1>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
              Browse shared images. If you need to request removal of non-consensual intimate imagery (NCII), use{" "}
              <strong className="font-semibold text-slate-800">Report</strong> on a post to start the verification flow.
            </p>
          </div>
          <div className="shrink-0 rounded-xl border border-teal-100 bg-teal-50/90 px-4 py-3 text-xs leading-relaxed text-teal-900 sm:max-w-xs">
            <span className="font-semibold">Safety note:</span> Reporting is serious. Only submit claims when you have a legitimate removal request and required evidence.
          </div>
        </div>
      </header>

      {images.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-surface-elevated/60 px-6 py-20 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
            <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-slate-800">No images yet</h2>
          <p className="mt-2 max-w-sm text-sm text-slate-500">Upload a photo from the sidebar to see it appear here for everyone signed in.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {images.map((img) => (
            <ImageCard key={img.id} {...img} />
          ))}
        </div>
      )}
    </div>
  );
}
