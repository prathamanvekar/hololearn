import { Globe, Languages } from "lucide-react";
import { useAppContext } from "../context/useAppContext";

export default function Settings() {
  const { language, setPrimaryLanguage, toggleBilingual } = useAppContext();

  const primaryLabel = language.primary === "hi" ? "Hindi" : "English";

  return (
    <section className="grid gap-4 lg:gap-5 animate-fade-in">
      <div className="glass-panel p-5 md:p-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.16em] text-slate-400">
              Preferences
            </p>
            <h2 className="text-xl font-semibold text-slate-100 mt-1">
              Settings
            </h2>
            <p className="text-sm text-slate-300 mt-2 max-w-2xl">
              Choose English or Hindi. If Bilingual is enabled, answers return
              in English first followed by a Hindi translation.
            </p>
          </div>
          <div className="h-10 w-10 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center">
            <Globe size={18} className="text-cyan-200" />
          </div>
        </div>
      </div>

      <div className="glass-panel p-5 md:p-6">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl border border-white/10 bg-white/5 flex items-center justify-center">
            <Languages size={17} className="text-purple-200" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-100">Language</p>
            <p className="text-xs text-slate-400">Current: {primaryLabel}</p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setPrimaryLanguage("en")}
            className={`btn-ghost ${
              language.primary === "en"
                ? "border-cyan-300/60 text-cyan-100 hologram-glow"
                : ""
            }`}
          >
            English
          </button>
          <button
            type="button"
            onClick={() => setPrimaryLanguage("hi")}
            className={`btn-ghost ${
              language.primary === "hi"
                ? "border-cyan-300/60 text-cyan-100 hologram-glow"
                : ""
            }`}
          >
            Hindi
          </button>

          <button
            type="button"
            onClick={toggleBilingual}
            className={`btn-ghost ${
              language.bilingual
                ? "border-cyan-300/60 text-cyan-100 hologram-glow"
                : ""
            }`}
          >
            Bilingual
          </button>
        </div>
      </div>
    </section>
  );
}
