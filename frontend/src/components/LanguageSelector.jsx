import { Check, ChevronDown, Languages } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

const languageOptions = [
  { code: "en", name: "English", flag: "🇬🇧" },
  { code: "hi", name: "Hindi", flag: "🇮🇳" },
];

export default function LanguageSelector({
  language = "en",
  bilingual = false,
  onLanguageChange = () => {},
  onToggleBilingual = () => {},
}) {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  const selected = useMemo(
    () =>
      languageOptions.find((item) => item.code === language) ??
      languageOptions[0],
    [language],
  );

  useEffect(() => {
    const handleOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    window.addEventListener("click", handleOutside);
    return () => window.removeEventListener("click", handleOutside);
  }, []);

  return (
    <div className="flex items-center gap-2 relative z-50" ref={dropdownRef}>
      <div className="relative z-50">
        <button
          type="button"
          onClick={() => setOpen((previous) => !previous)}
          className="btn-ghost min-w-44 justify-between"
          aria-expanded={open}
          aria-haspopup="listbox"
        >
          <span className="flex items-center gap-2">
            <Languages size={16} className="text-cyan-200" />
            <span>{selected.flag}</span>
            <span>{selected.name}</span>
          </span>
          <ChevronDown
            size={16}
            className={`transition-transform duration-200 ${open ? "rotate-180" : "rotate-0"}`}
          />
        </button>

        <div
          className={`absolute right-0 mt-2 w-52 z-50 overflow-hidden rounded-xl border border-white/15 bg-slate-950/80 backdrop-blur-xl transition-all duration-200 origin-top ${
            open
              ? "opacity-100 scale-100 translate-y-0"
              : "opacity-0 scale-95 -translate-y-1 pointer-events-none"
          }`}
        >
          <ul role="listbox" className="p-1.5">
            {languageOptions.map((option) => {
              const isSelected = option.code === selected.code;

              return (
                <li key={option.code}>
                  <button
                    type="button"
                    className={`w-full rounded-lg px-2.5 py-2 text-left text-sm flex items-center justify-between transition-colors ${
                      isSelected
                        ? "bg-cyan-400/15 text-cyan-100"
                        : "text-slate-300 hover:bg-white/5"
                    }`}
                    onClick={() => {
                      onLanguageChange(option.code);
                      setOpen(false);
                    }}
                  >
                    <span className="flex items-center gap-2">
                      <span>{option.flag}</span>
                      <span>{option.name}</span>
                    </span>
                    {isSelected ? (
                      <Check size={14} className="text-cyan-200" />
                    ) : null}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      <button
        type="button"
        className={`btn-ghost ${bilingual ? "border-cyan-300/60 text-cyan-100 hologram-glow" : ""}`}
        onClick={onToggleBilingual}
      >
        Bilingual
      </button>
    </div>
  );
}
