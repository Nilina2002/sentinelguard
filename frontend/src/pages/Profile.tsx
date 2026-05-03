import { useAuth } from "../context/AuthContext";

function emailFromUser(user: unknown): string {
  if (!user || typeof user !== "object") return "—";
  const u = user as { data?: { email?: string }; email?: string };
  if (u.data && typeof u.data === "object" && "email" in u.data && typeof u.data.email === "string") {
    return u.data.email;
  }
  if (typeof u.email === "string") return u.email;
  return "—";
}

export default function Profile() {
  const { user } = useAuth();
  const email = emailFromUser(user);

  return (
    <div className="mx-auto max-w-lg space-y-8">
      <header>
        <p className="text-xs font-semibold uppercase tracking-widest text-teal-600">Account</p>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Profile</h1>
        <p className="mt-2 text-sm text-slate-600">Your session details for SentinelGuard.</p>
      </header>

      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-surface-elevated shadow-sm">
        <div className="h-24 bg-gradient-to-r from-slate-800 via-slate-700 to-teal-900" />
        <div className="relative px-6 pb-6 pt-0">
          <div className="-mt-12 flex h-24 w-24 items-center justify-center rounded-2xl border-4 border-surface-elevated bg-gradient-to-br from-teal-400 to-cyan-600 text-2xl font-bold text-white shadow-lg">
            {email.charAt(0).toUpperCase()}
          </div>
          <h2 className="mt-4 text-lg font-semibold text-slate-900">Signed in</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex flex-col gap-0.5 rounded-xl bg-slate-50 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <dt className="font-medium text-slate-500">Email</dt>
              <dd className="font-medium text-slate-900 break-all">{email}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
