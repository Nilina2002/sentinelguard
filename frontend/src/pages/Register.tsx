import type { ChangeEvent } from "react";
import { useState } from "react";
import api from "../api/client";
import { Link, useNavigate } from "react-router-dom";
import Loading from "../components/Loading";
import { toast } from "react-toastify";
import { useAuth } from "../context/AuthContext";
import logoIcon from "../assets/logo_icon.png";

export default function Register() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const handleAvatarChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;

    if (avatarPreview) {
      URL.revokeObjectURL(avatarPreview);
    }

    setAvatarFile(selected);
    setAvatarPreview(URL.createObjectURL(selected));
  };

  const handleRegister = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("email", email);
      formData.append("username", username);
      formData.append("password", password);
      if (phone) {
        formData.append("phone", phone);
      }
      if (avatarFile) {
        formData.append("avatar", avatarFile);
      }

      const res = await api.post("/auth/register", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      if (!res.data.success) throw new Error(res.data.message || "Registration failed");

      const userRes = await api.get("/users/me");
      setUser(userRes.data);

      toast.success("Account created successfully.");
      navigate("/home");
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { message?: string } }; message?: string };
      toast.error(`Unable to create account. ${ax.response?.data?.message || ax.message || "Please try again."}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading message="Creating your account…" fullScreen />;

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-50">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -right-24 top-12 h-72 w-72 rounded-full bg-indigo-100/70 blur-3xl" />
        <div className="absolute left-0 top-1/3 h-80 w-80 rounded-full bg-sky-100/70 blur-3xl" />
        <div className="absolute bottom-0 right-1/3 h-72 w-72 rounded-full bg-emerald-100/60 blur-3xl" />
      </div>
      <div className="relative mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-12">
        <div className="grid w-full gap-10 lg:grid-cols-[1.05fr,0.95fr]">
          <div className="order-2 flex flex-col justify-center lg:order-1">
            <div className="inline-flex items-center gap-4 rounded-2xl border border-slate-200/70 bg-slate-50/70 px-5 py-3 shadow-sm backdrop-blur">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 shadow-md ring-1 ring-slate-200/70">
                <img src={logoIcon} alt="SnapSafe logo" className="h-10 w-70" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">SnapSafe</p>
                <p className="text-sm font-semibold text-slate-900">Verified Community Feed</p>
              </div>
            </div>
            {/* <h1 className="mt-6 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
              Join the professional safety community
            </h1> */}
          </div>

          <div className="order-1 flex items-center justify-center lg:order-2">
            <div className="auth-card w-full max-w-md">
              <h2 className="text-xl font-semibold text-slate-900 text-center">Create your SnapSafe account</h2>
              <p className="mt-1 text-sm text-slate-500 text-center font-semibold">Set up your profile and start sharing safely.</p>

              <div className="mt-6 space-y-4">
                <div>
                  <label htmlFor="register-avatar" className="auth-label">
                    Profile photo
                  </label>
                  <div className="flex items-center gap-4">
                    {avatarPreview ? (
                      <img
                        src={avatarPreview}
                        alt="Avatar preview"
                        className="h-14 w-14 rounded-full border border-slate-200 object-cover"
                      />
                    ) : (
                      <div className="flex h-14 w-14 items-center justify-center rounded-full border border-dashed border-slate-300 text-xs font-semibold text-slate-400">
                        Add
                      </div>
                    )}
                    <label className="btn-ghost cursor-pointer">
                      <input id="register-avatar" type="file" accept="image/*" onChange={handleAvatarChange} className="sr-only" />
                      {avatarFile ? "Change photo" : "Upload photo"}
                    </label>
                  </div>
                </div>
                <div>
                  <label htmlFor="register-email" className="auth-label">
                    Email
                  </label>
                  <div className="relative">
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7l9 6 9-6M4 7h16v10H4z" />
                      </svg>
                    </span>
                    <input
                      id="register-email"
                      type="email"
                      autoComplete="email"
                      required
                      className="auth-input pl-11"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="register-username" className="auth-label">
                    Username
                  </label>
                  <div className="relative">
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5.121 17.804A8 8 0 1119 12" />
                      </svg>
                    </span>
                    <input
                      id="register-username"
                      type="text"
                      autoComplete="username"
                      required
                      className="auth-input pl-11"
                      placeholder="yourname"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="register-phone" className="auth-label">
                    Mobile number
                  </label>
                  <div className="relative">
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 5a2 2 0 012-2h4a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5zm12 2h4a2 2 0 012 2v10a2 2 0 01-2 2h-4" />
                      </svg>
                    </span>
                    <input
                      id="register-phone"
                      type="tel"
                      autoComplete="tel"
                      className="auth-input pl-11"
                      placeholder="07xxxxxxxx"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="register-password" className="auth-label">
                    Password
                  </label>
                  <div className="relative">
                    <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 11h10v8H7zM9 11V8a3 3 0 016 0v3" />
                      </svg>
                    </span>
                    <input
                      id="register-password"
                      type="password"
                      autoComplete="new-password"
                      required
                      className="auth-input pl-11"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <button type="button" onClick={handleRegister} className="btn-primary mt-6 w-full cursor-pointer">
                Create account
              </button>

              <p className="mt-6 text-center text-sm text-slate-500">
                Already have an account?{" "}
                <Link to="/login" className="font-semibold text-brand hover:text-brand-hover">
                  Login
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
