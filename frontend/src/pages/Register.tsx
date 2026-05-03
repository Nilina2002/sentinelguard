import { useState } from "react";
import api from "../api/client";
import { Link, useNavigate } from "react-router-dom";
import Loading from "../components/Loading";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const handleRegister = async () => {
    setLoading(true);
    try {
      const res = await api.post("/auth/register", { email, password });
      if (!res.data.success) throw new Error(res.data.message || "Registration failed");

      const userRes = await api.get("/users/me");
      setUser(userRes.data);

      toast.success("Account created");
      navigate("/home");
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } }; message?: string };
      toast.error(`Registration failed: ${ax.response?.data?.message || ax.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Creating your account…" fullScreen />;

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-slate-950 px-4 py-12">
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "radial-gradient(ellipse 80% 50% at 50% -20%, rgb(45 212 191 / 0.35), transparent), radial-gradient(ellipse 60% 40% at 0% 100%, rgb(34 211 238 / 0.2), transparent)",
        }}
      />
      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-cyan-600 shadow-lg shadow-teal-900/40">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Join SentinelGuard</h1>
          <p className="mt-2 text-sm text-slate-400">Create an account to upload content and use verified reporting.</p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-8 shadow-2xl shadow-black/40 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-white">Register</h2>
          <p className="mt-1 text-sm text-slate-500">Choose a strong password you do not reuse elsewhere.</p>

          <div className="mt-6 space-y-4">
            <div>
              <label htmlFor="register-email" className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                Email
              </label>
              <input
                id="register-email"
                type="email"
                autoComplete="email"
                className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-white placeholder:text-slate-600 outline-none transition focus:border-teal-500/50 focus:ring-4 focus:ring-teal-500/15"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="register-password" className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-slate-400">
                Password
              </label>
              <input
                id="register-password"
                type="password"
                autoComplete="new-password"
                className="w-full rounded-xl border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm text-white placeholder:text-slate-600 outline-none transition focus:border-teal-500/50 focus:ring-4 focus:ring-teal-500/15"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <button
            type="button"
            onClick={handleRegister}
            className="mt-6 w-full rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-900/30 transition hover:from-emerald-400 hover:to-teal-500 focus:outline-none focus:ring-4 focus:ring-emerald-500/30"
          >
            Create account
          </button>

          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-teal-400 hover:text-teal-300">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
