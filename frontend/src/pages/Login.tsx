import { useState } from "react";
import api from "../api/client";
import { Link, useNavigate } from "react-router-dom";
import Loading from "../components/Loading";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const handleLogin = async () => {
    setLoading(true);
    try {
      const res = await api.post("/auth/login", { email, password });
      if (!res.data.success) throw new Error(res.data.message || "Login failed");

      const userRes = await api.get("/users/me");
      setUser(userRes.data);

      toast.success("Welcome back");
      navigate("/home");
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } }; message?: string };
      toast.error(`Login failed: ${ax.response?.data?.message || ax.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Signing you in…" fullScreen />;

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-slate-950 px-4 py-12">
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(ellipse 80% 50% at 50% -20%, rgb(45 212 191 / 0.35), transparent), radial-gradient(ellipse 60% 40% at 100% 100%, rgb(6 182 212 / 0.2), transparent)",
        }}
      />
      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-cyan-600 shadow-lg shadow-teal-900/40">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">SentinelGuard</h1>
          <p className="mt-2 text-sm text-slate-400">Sign in to access the community feed and reporting tools.</p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-8 shadow-2xl shadow-black/40 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-white">Sign in</h2>
          <p className="mt-1 text-sm text-slate-500">Use the email and password you registered with.</p>

          <div className="mt-6 space-y-4">
            <div>
              <label htmlFor="login-email" className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                Email
              </label>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-white placeholder:text-slate-600 outline-none ring-teal-500/0 transition focus:border-teal-500/50 focus:ring-4 focus:ring-teal-500/15"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="login-password" className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                autoComplete="current-password"
                className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-white placeholder:text-slate-600 outline-none ring-teal-500/0 transition focus:border-teal-500/50 focus:ring-4 focus:ring-teal-500/15"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="button"
            onClick={handleLogin}
            className="mt-6 w-full rounded-xl bg-gradient-to-r from-teal-500 to-cyan-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-teal-900/30 transition hover:from-teal-400 hover:to-cyan-500 focus:outline-none focus:ring-4 focus:ring-teal-500/30"
          >
            Sign in
          </button>

          <p className="mt-6 text-center text-sm text-slate-500">
            New here?{" "}
            <Link to="/register" className="font-semibold text-teal-400 hover:text-teal-300">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
