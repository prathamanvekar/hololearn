import {
  Brain,
  FolderOpen,
  LayoutDashboard,
  MessageSquare,
  Settings2,
} from "lucide-react";

const navItems = [
  { key: "chat", label: "Chat", icon: MessageSquare },
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "documents", label: "Documents", icon: FolderOpen },
  { key: "quiz", label: "Quiz", icon: Brain },
];

export default function Sidebar({
  currentView = "chat",
  onChangeView = () => {},
}) {
  const isSettingsActive = currentView === "settings";

  return (
    <aside className="w-full md:w-72 md:min-h-screen p-3 md:p-4">
      <div className="glass-panel h-full p-4 md:p-5 flex flex-col gap-5">
        <div className="flex items-center gap-3 pb-2 border-b border-white/10">
          <div className="h-10 w-10 rounded-xl flex items-center justify-center bg-gradient-to-br from-cyan-400/40 via-purple-500/40 to-pink-500/40 border border-cyan-300/40 hologram-glow animate-pulse-glow">
            <Brain size={20} className="text-cyan-200" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
              AI Learning
            </p>
            <h1 className="text-lg font-semibold hologram-text">HoloLearn</h1>
          </div>
        </div>

        <nav className="flex flex-col gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.key;

            return (
              <button
                key={item.key}
                type="button"
                onClick={() => onChangeView(item.key)}
                className={`w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-all duration-200 ${
                  isActive
                    ? "bg-gradient-to-r from-cyan-400/25 via-purple-500/25 to-pink-500/25 border border-cyan-300/50 text-cyan-100 shadow-[0_0_24px_rgba(0,212,255,0.24)]"
                    : "border border-transparent text-slate-300 hover:border-white/15 hover:bg-white/5"
                }`}
              >
                <Icon
                  size={18}
                  className={isActive ? "text-cyan-200" : "text-slate-400"}
                />
                <span className="font-medium">{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="mt-auto pt-2 border-t border-white/10">
          <button
            type="button"
            onClick={() => onChangeView("settings")}
            className={`w-full flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-200 ${
              isSettingsActive
                ? "bg-gradient-to-r from-cyan-400/25 via-purple-500/25 to-pink-500/25 border border-cyan-300/50 text-cyan-100 shadow-[0_0_24px_rgba(0,212,255,0.24)]"
                : "border border-white/10 text-slate-300 hover:border-cyan-300/40 hover:bg-cyan-500/5"
            }`}
          >
            <Settings2
              size={18}
              className={isSettingsActive ? "text-cyan-200" : "text-slate-400"}
            />
            <span className="font-medium">Settings</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
