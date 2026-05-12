import type { ReactNode } from "react";
import { useState } from "react";
import Sidebar from "./Sidebar";

export default function MainLayout({ children }: { children: ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-br from-slate-100 via-surface to-slate-100/80 lg:flex-row">
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed((prev) => !prev)} />
      <main className="flex-1 min-h-screen min-w-0 overflow-x-hidden">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
          {children}
        </div>
      </main>
    </div>
  );
}
