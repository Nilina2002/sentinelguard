import { useEffect, useState } from "react";
import api from "../api/client";
import ImageCard from "../components/ImageCard";
import { toast } from "react-toastify";
import Loading from "../components/Loading";
import { useAuth } from "../context/AuthContext";

interface ImageType {
  id: number;
  image_url: string;
  created_at: string;
  is_deleted: boolean;
  owner: {
    id: number;
    email: string;
    username: string;
    avatar_url: string | null;
  };
  like_count: number;
  comment_count: number;
  liked_by_me: boolean;
}

export default function Home() {
  const { user } = useAuth();
  const [images, setImages] = useState<ImageType[]>([]);
  const [loading, setLoading] = useState(true);
  const currentUserId = (user?.data?.id ?? user?.id ?? null) as number | null;

  const fetchImages = async () => {
    try {
      const res = await api.get("/images");
      setImages(res.data);
    } catch {
      toast.error("Unable to load the feed. Please try again shortly.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchImages();
  }, []);

  if (loading) return <Loading message="Loading your feed…" />;

  return (
    <div className="mx-auto w-full max-w-5xl space-y-8">
      <header className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-20 top-6 h-40 w-40 rounded-full bg-sky-100/80 blur-3xl" />
          <div className="absolute bottom-0 left-1/3 h-36 w-36 rounded-full bg-emerald-100/60 blur-3xl" />
        </div>
        <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-slate-600">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Community feed
            </div>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
              Browse shared images. To request removal of NCII, select <strong className="font-semibold text-slate-800">Report</strong> on a post to start the verification flow.
            </p>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
              Powered by the <span className="font-semibold">SentinelGuard Privacy Engine</span>
            </p>
          </div>
          <div className="shrink-0 rounded-2xl border border-emerald-100 bg-emerald-50/70 px-4 py-3 text-xs leading-relaxed text-emerald-900 sm:max-w-xs">
            <span className="font-semibold">Safety note:</span> Only submit claims when you have a legitimate removal request and required evidence.
          </div>
        </div>
      </header>

      {images.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-20 text-center shadow-sm">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
            <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-slate-900">No posts yet</h2>
          <p className="mt-2 max-w-sm text-sm text-slate-500">Upload a photo from the sidebar to publish your first post.</p>
        </div>
      ) : (
        <div className="mx-auto w-full max-w-3xl space-y-6">
          {images.map((img) => (
            <ImageCard key={img.id} {...img} currentUserId={currentUserId} />
          ))}
        </div>
      )}

      <div className="mx-auto flex w-full max-w-3xl items-center justify-center">
        <div className="inline-flex items-center gap-3 rounded-full border border-slate-200 bg-white/80 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 shadow-sm">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span>
            Powered by the <span className="text-slate-800">SentinelGuard Privacy Engine</span>
          </span>
        </div>
      </div>
    </div>
  );
}
