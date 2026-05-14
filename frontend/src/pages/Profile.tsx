import type { ChangeEvent } from "react";
import { useEffect, useState } from "react";
import api from "../api/client";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";
import ImageCard from "../components/ImageCard";

type UserData = {
  email?: string;
  username?: string;
  phone?: string | null;
  avatar_url?: string | null;
};

type ReportHistoryItem = {
  id: number;
  status: string;
  similarity_score: number | null;
  matches_found: number;
  created_at: string;
};

type UserImageItem = {
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
};

const SIMILARITY_THRESHOLD = 0.98;

function userDataFromAuth(user: unknown): UserData {
  if (!user || typeof user !== "object") return {};
  const u = user as { data?: UserData } & UserData;
  if (u.data && typeof u.data === "object") return u.data;
  return u;
}

function avatarUrlFromPath(path?: string | null): string | null {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const normalized = path.replace(/\\/g, "/");
  return `http://localhost:8000/${normalized}`;
}

export default function Profile() {
  const { user, setUser } = useAuth();
  const userData = userDataFromAuth(user);
  const email = userData.email || "—";
  const username = userData.username || "—";
  const phone = userData.phone || "—";
  const avatarUrl = avatarUrlFromPath(userData.avatar_url);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportHistory, setReportHistory] = useState<ReportHistoryItem[]>([]);
  const [reportsLoading, setReportsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"reports" | "uploads">("reports");
  const [myImages, setMyImages] = useState<UserImageItem[]>([]);
  const [imagesLoading, setImagesLoading] = useState(false);

  const handleAvatarChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;

    if (avatarPreview) {
      URL.revokeObjectURL(avatarPreview);
    }

    setAvatarFile(selected);
    setAvatarPreview(URL.createObjectURL(selected));
  };

  const handleAvatarUpload = async () => {
    if (!avatarFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("avatar", avatarFile);

      const res = await api.put("/users/me/avatar", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUser(res.data);
      toast.success("Profile photo updated.");
      setAvatarFile(null);
      setAvatarPreview(null);
    } catch (error: unknown) {
      const ax = error as { response?: { data?: { message?: string } }; message?: string };
      toast.error(ax.response?.data?.message || ax.message || "Unable to update photo.");
    } finally {
      setLoading(false);
    }
  };

  const fetchReportHistory = async () => {
    try {
      setReportsLoading(true);
      const res = await api.get("/reports/me");
      setReportHistory(res.data || []);
    } catch (error: unknown) {
      const ax = error as { response?: { data?: { message?: string } }; message?: string };
      toast.error(ax.response?.data?.message || ax.message || "Unable to load report history.");
    } finally {
      setReportsLoading(false);
    }
  };

  const fetchMyImages = async () => {
    try {
      setImagesLoading(true);
      const res = await api.get("/images/me");
      setMyImages(res.data || []);
    } catch (error: unknown) {
      const ax = error as { response?: { data?: { message?: string } }; message?: string };
      toast.error(ax.response?.data?.message || ax.message || "Unable to load your uploads.");
    } finally {
      setImagesLoading(false);
    }
  };

  useEffect(() => {
    fetchReportHistory();
  }, []);

  useEffect(() => {
    if (activeTab === "uploads" && myImages.length === 0) {
      fetchMyImages();
    }
  }, [activeTab, myImages.length]);

  const formatReportDate = (value: string) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    return date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const statusLabel = (status: string) => {
    switch (status) {
      case "processed":
        return "Resolved";
      case "verified":
        return "Verified";
      case "rejected":
        return "Rejected";
      default:
        return "Pending";
    }
  };

  const statusClasses = (status: string) => {
    switch (status) {
      case "processed":
        return "border-emerald-200 bg-emerald-50 text-emerald-700";
      case "verified":
        return "border-sky-200 bg-sky-50 text-sky-700";
      case "rejected":
        return "border-rose-200 bg-rose-50 text-rose-700";
      default:
        return "border-slate-200 bg-slate-50 text-slate-600";
    }
  };

  const similarityPercent = (score: number | null) => {
    if (score === null || Number.isNaN(score)) return 0;
    const percent = Math.round(score * 100);
    return Math.max(0, Math.min(100, percent));
  };

  const similarityMessage = (status: string, score: number | null) => {
    if (score === null) return "Similarity pending. We will update after matching.";
    if (status === "processed") return "Strong match confirmed. Removal actioned.";
    if (status === "rejected") return "No strong match found against the threshold.";
    if (score >= SIMILARITY_THRESHOLD) return "Strong match detected and awaiting final action.";
    return "Below the match threshold. Reviewed by the system.";
  };

  const handleDeleteImage = async (imageId: number) => {
    const confirmed = window.confirm("Delete this photo from your profile? This cannot be undone.");
    if (!confirmed) return;
    try {
      await api.delete(`/images/${imageId}`);
      setMyImages((prev) =>
        prev.map((image) => (image.id === imageId ? { ...image, is_deleted: true } : image))
      );
      toast.success("Photo removed from your profile.");
    } catch (error: unknown) {
      const ax = error as { response?: { data?: { message?: string } }; message?: string };
      toast.error(ax.response?.data?.message || ax.message || "Unable to delete photo.");
    }
  };
  
  if (loading) return <div className="p-6 text-center text-sm text-slate-500">Updating profile photo…</div>;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-20 top-6 h-36 w-36 rounded-full bg-sky-100/80 blur-3xl" />
          <div className="absolute bottom-0 left-1/3 h-28 w-28 rounded-full bg-emerald-100/60 blur-3xl" />
        </div>
        <div className="relative">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-slate-600">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            YOUR PROFILE
          </div>
          <p className="mt-2 text-sm text-slate-600">Your SentinelGuard session details and identity information.</p>
        </div>
      </header>

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="h-28 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-700" />
        <div className="relative px-6 pb-6 pt-0 sm:px-8">
          <div className="-mt-12 flex h-24 w-24 items-center justify-center overflow-hidden rounded-3xl border-4 border-white bg-brand text-2xl font-semibold text-white shadow-lg">
            {avatarPreview ? (
              <img src={avatarPreview} alt={username} className="h-full w-full object-cover" />
            ) : avatarUrl ? (
              <img src={avatarUrl} alt={username} className="h-full w-full object-cover" />
            ) : (
              email.charAt(0).toUpperCase()
            )}
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-900">Hello {username}!</h2>
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-emerald-700">
              Active session
            </span>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <label className="btn-ghost cursor-pointer">
              <input type="file" accept="image/*" onChange={handleAvatarChange} className="sr-only" />
              {avatarPreview ? "Change selection" : "Change photo"}
            </label>
            <button
              type="button"
              onClick={handleAvatarUpload}
              disabled={!avatarFile}
              className="btn-primary disabled:pointer-events-none disabled:opacity-40 cursor-pointer"
            >
              Save photo
            </button>
          </div>
          <dl className="mt-5 space-y-3 text-sm">
            <div className="flex flex-col gap-0.5 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <dt className="font-medium text-slate-500">Username</dt>
              <dd className="font-medium text-slate-900 break-all">{username}</dd>
            </div>
            <div className="flex flex-col gap-0.5 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <dt className="font-medium text-slate-500">Email</dt>
              <dd className="font-medium text-slate-900 break-all">{email}</dd>
            </div>
            <div className="flex flex-col gap-0.5 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <dt className="font-medium text-slate-500">Mobile</dt>
              <dd className="font-medium text-slate-900 break-all">{phone}</dd>
            </div>
          </dl>
        </div>
      </div>

      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-6 py-5 sm:px-8">
          <div>
            <h3 className="text-base font-semibold text-slate-900">Your activity</h3>
            <p className="mt-1 text-xs text-slate-500">Manage reports and uploaded photos in one place.</p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-semibold text-slate-600">
            <button
              type="button"
              onClick={() => setActiveTab("reports")}
              className={`rounded-full px-3 py-1 cursor-pointer transition ${
                activeTab === "reports" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"
              }`}
            >
              Reports
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("uploads")}
              className={`rounded-full px-3 py-1 cursor-pointer transition ${
                activeTab === "uploads" ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"
              }`}
            >
              My uploads
            </button>
          </div>
        </div>

        <div className="space-y-4 px-6 py-6 sm:px-8">
          {activeTab === "reports" ? (
            reportsLoading ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
                Loading report history…
              </div>
            ) : reportHistory.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
                No reports yet. Use the Report button on any post to get started.
              </div>
            ) : (
              reportHistory.map((report) => {
                const percent = similarityPercent(report.similarity_score);
                return (
                  <div key={report.id} className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs uppercase tracking-wide text-slate-400">Report ID</p>
                        <p className="text-lg font-semibold text-slate-900">#{report.id}</p>
                        <p className="mt-1 text-xs text-slate-500">Submitted {formatReportDate(report.created_at)}</p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide ${statusClasses(report.status)}`}>
                          {statusLabel(report.status)}
                        </span>
                        <span className="text-xs text-slate-500">Matches found: {report.matches_found}</span>
                      </div>
                    </div>

                    <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Similarity score</p>
                        <p className="text-xs font-semibold text-slate-700">{percent}%</p>
                      </div>
                      <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
                        <div
                          className={`h-full rounded-full ${percent >= 98 ? "bg-emerald-500" : percent >= 90 ? "bg-amber-500" : "bg-rose-500"}`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                      <p className="mt-2 text-xs text-slate-500">{similarityMessage(report.status, report.similarity_score)}</p>
                    </div>
                  </div>
                );
              })
            )
          ) : imagesLoading ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
              Loading your uploads…
            </div>
          ) : myImages.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
              You have not uploaded any photos yet.
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                <span>{myImages.length} uploads</span>
                <button
                  type="button"
                  onClick={fetchMyImages}
                  className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  Refresh
                </button>
              </div>
              <div className="space-y-6">
                {myImages.map((image) => (
                  <ImageCard
                    key={image.id}
                    {...image}
                    showDelete
                    onDelete={handleDeleteImage}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
