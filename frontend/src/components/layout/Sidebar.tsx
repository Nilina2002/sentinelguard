import { NavLink, useNavigate } from "react-router-dom";
import api from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import logoIcon from "../../assets/logo_icon.png";

type SidebarProps = {
  collapsed: boolean;
  onToggle: () => void;
};

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const navClass = ({ isActive }: { isActive: boolean }) =>
    [
      "flex items-center gap-3 whitespace-nowrap rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
      collapsed ? "justify-center lg:justify-start" : "",
      isActive
        ? "bg-white/10 text-white shadow-inner"
        : "text-slate-400 hover:bg-white/5 hover:text-white",
    ].join(" ");

  const handleLogout = async () => {
    try {
      await api.post("/auth/logout");
      setUser(null);
      navigate("/login");
    } catch {
      console.error("Logout failed");
    }
  };

  return (
    <aside
      className={`sticky top-0 z-40 flex w-full flex-col border-b border-slate-800/80 bg-slate-950 text-white shadow-lg shadow-slate-900/20 lg:h-screen lg:shrink-0 lg:border-b-0 lg:border-r lg:shadow-xl ${
        collapsed ? "lg:w-20" : "lg:w-64"
      }`}
    >
      <div
        className={`flex flex-col gap-1 border-b border-slate-800/80 px-4 py-4 lg:py-6 ${
          collapsed ? "lg:px-2" : "lg:px-4"
        }`}
      >
        <div
          className={`flex items-center justify-between gap-3 ${
            collapsed ? "lg:flex-col lg:items-center lg:justify-center" : ""
          }`}
        >
          <div className={`flex items-center gap-3 ${collapsed ? "lg:flex-col" : ""}`}>
            <div
              className={`flex items-center justify-center rounded-xl bg-white shadow-md ring-1 ring-white/10 ${
                collapsed ? "h-10 w-10" : "h-11 w-11"
              }`}
            >
              <img src={logoIcon} alt="SnapSafe logo" className="h-10 w-70 cursor-pointer" onClick={() => navigate("/home")} />
            </div>
            {!collapsed && (
              <div>
                <h1 className="text-lg font-bold tracking-tight cursor-pointer" onClick={() => navigate("/home")}> 
                  SnapSafe
                </h1>
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={onToggle}
            className={`flex items-center cursor-pointer justify-center rounded-lg border border-slate-800/80 text-slate-300 transition hover:bg-white/5 hover:text-white ${
              collapsed ? "h-8 w-8 lg:mt-1" : "h-9 w-9"
            }`}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h10" />
            </svg>
          </button>
        </div>
      </div>

      <nav className={`${collapsed ? "hidden lg:flex" : "flex"} flex-1 flex-row gap-2 overflow-x-auto p-3 lg:flex-col lg:gap-0.5`}>
        <NavLink to="/home" className={navClass} end>
          <svg className="h-5 w-5 shrink-0 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          {!collapsed && "Feed"}
        </NavLink>
        <NavLink to="/upload" className={navClass}>
          <svg className="h-5 w-5 shrink-0 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          {!collapsed && "Upload"}
        </NavLink>
        <NavLink to="/profile" className={navClass}>
          <svg className="h-5 w-5 shrink-0 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          {!collapsed && "Profile"}
        </NavLink>
      </nav>

      <div className={`${collapsed ? "hidden lg:block" : "block"} border-t border-slate-800/80 p-4 lg:mt-auto`}>
        <button
          type="button"
          onClick={handleLogout}
          className={`flex w-full items-center justify-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2.5 text-sm font-medium text-rose-200 transition hover:bg-rose-500/20 hover:text-white cursor-pointer ${
            collapsed ? "lg:justify-center" : ""
          }`}
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          {!collapsed && "Logout"}
        </button>
      </div>
    </aside>
  );
}
