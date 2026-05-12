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

      toast.success("Signed in successfully.");
      navigate("/home");
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } }; message?: string };
      toast.error(`Unable to sign in. ${ax.response?.data?.message || ax.message || "Please try again."}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Loading…" fullScreen />;

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-50">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-24 top-10 h-72 w-72 rounded-full bg-sky-100/80 blur-3xl" />
        <div className="absolute right-0 top-1/3 h-80 w-80 rounded-full bg-emerald-100/70 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-indigo-100/60 blur-3xl" />
      </div>
      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-12">
        <div className="grid w-full gap-10 lg:grid-cols-[1.05fr,0.95fr]">
          <div className="order-2 flex flex-col justify-center lg:order-1">
            <div className="inline-flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/80 px-4 py-2 shadow-sm">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M12 3l7 4v5c0 4.418-3.134 8.418-7 9-3.866-.582-7-4.582-7-9V7l7-4z" />
                </svg>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">SentinelGuard</p>
                <p className="text-sm font-semibold text-slate-900">Verified Community Feed</p>
              </div>
            </div>
            {/* <h1 className="mt-6 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
              Welcome back to your safety network
            </h1> */}
          </div>

          <div className="order-1 flex items-center justify-center lg:order-2">
            <div className="auth-card w-full max-w-md">
              <h2 className="text-xl font-semibold text-slate-900 text-align-center text-center">Login</h2>
              <p className="mt-1 text-sm text-slate-500 text-center font-semibold">Welcome back to your safety network</p>

              <div className="mt-6 space-y-4">
                <div>
                  <label htmlFor="login-email" className="auth-label">
                    Email
                  </label>
                  <div className="relative">
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7l9 6 9-6M4 7h16v10H4z" />
                      </svg>
                    </span>
                    <input
                      id="login-email"
                      type="email"
                      autoComplete="email"
                      className="auth-input pl-11"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="login-password" className="auth-label">
                    Password
                  </label>
                  <div className="relative">
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 11h10v8H7zM9 11V8a3 3 0 016 0v3" />
                      </svg>
                    </span>
                    <input
                      id="login-password"
                      type="password"
                      autoComplete="current-password"
                      className="auth-input pl-11"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <button type="button" onClick={handleLogin} className="btn-primary mt-6 w-full cursor-pointer">
                Login
              </button>

              <p className="mt-6 text-center text-sm text-slate-500">
                New here?{" "}
                <Link to="/register" className="font-semibold text-brand hover:text-brand-hover">
                  Create an account
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
