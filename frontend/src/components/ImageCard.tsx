import { useState } from "react";
import ReportModal from "./ReportModal";

interface ImageProps {
  id: number;
  image_url: string;
  created_at: string;
  owner: {
    id: number;
    email: string;
    username: string;
    avatar_url: string | null;
  };
  like_count: number;
  comment_count: number;
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "Just now";

  const diffMs = Date.now() - date.getTime();
  const diffMinutes = Math.floor(diffMs / 60000);
  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d`;

  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function nameFromEmail(email: string): string {
  const [local] = email.split("@");
  if (!local) return "Community member";
  return local
    .split(/[._-]+/)
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function initialsFromName(name: string): string {
  const parts = name.split(" ").filter(Boolean);
  const initials = parts.slice(0, 2).map((part) => part[0]);
  return initials.join("") || "CM";
}

function avatarUrlFromPath(path: string | null): string | null {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const normalized = path.replace(/\\/g, "/");
  return `http://localhost:8000/${normalized}`;
}

export default function ImageCard({ id, image_url, created_at, owner, like_count, comment_count }: ImageProps) {
  const normalizedPath = image_url.replace(/\\/g, "/");
  const imageUrl = `http://localhost:8000/${normalizedPath}`;
  const ownerName = owner.username || nameFromEmail(owner.email);
  const ownerInitials = initialsFromName(ownerName);
  const timestamp = formatRelativeTime(created_at);
  const avatarUrl = avatarUrlFromPath(owner.avatar_url);

  const [open, setOpen] = useState(false);

  return (
    <>
      <article className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
        <div className="flex items-center justify-between gap-3 px-3 py-2.5 sm:px-4 sm:py-3">
          <div className="flex items-center gap-3">
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt={ownerName}
                className="h-9 w-9 rounded-full border border-slate-200 object-cover"
              />
            ) : (
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                {ownerInitials}
              </div>
            )}
            <div>
              <p className="text-sm font-semibold text-slate-900">@{ownerName}</p>
              <p className="text-[11px] text-slate-500">Post #{id}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">{timestamp}</span>
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
              Verified
            </span>
          </div>
        </div>

        <div className="relative aspect-[16/10] overflow-hidden bg-slate-100">
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

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-3 py-2.5 sm:px-4 sm:py-3">
          <div className="flex items-center gap-3 text-xs font-semibold text-slate-600">
            <button type="button" className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 transition hover:bg-slate-100">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M14 9l-2-2-6 6 2 2 6-6zM7 21h10a2 2 0 002-2V7" />
              </svg>
              Like {like_count}
            </button>
            <button type="button" className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 transition hover:bg-slate-100">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M7 8h10M7 12h6m-7 7h12a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Comment {comment_count}
            </button>
            <button type="button" className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 transition hover:bg-slate-100">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M4 12v7a1 1 0 001 1h14a1 1 0 001-1v-7M12 5v10m0 0l-3-3m3 3l3-3" />
              </svg>
              Share
            </button>
          </div>
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg border border-rose-200 bg-rose-50 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:border-rose-300 hover:bg-rose-100 cursor-pointer"
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
