import type { ChangeEvent } from "react";
import { useState } from "react";
import api from "../api/client";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";

type UserData = {
  email?: string;
  username?: string;
  phone?: string | null;
  avatar_url?: string | null;
};

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
            <h2 className="text-lg font-semibold text-slate-900">Signed in</h2>
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
    </div>
  );
}
