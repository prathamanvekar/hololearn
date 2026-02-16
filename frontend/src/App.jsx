import { LoaderCircle } from "lucide-react";
import { lazy, Suspense } from "react";
import "./App.css";
import LanguageSelector from "./components/LanguageSelector";
import Sidebar from "./components/Sidebar";
import { useAppContext } from "./context/useAppContext";

function PlaceholderPanel({ title, description }) {
  return (
    <div className="glass-panel h-full min-h-[320px] p-5 md:p-6 animate-fade-in">
      <span className="badge badge-purple mb-3">Coming Online</span>
      <h3 className="text-xl font-semibold hologram-text mb-2">{title}</h3>
      <p className="text-slate-300">{description}</p>
    </div>
  );
}

const ChatInterface = lazy(() =>
  import("./components/ChatInterface").then((module) => ({
    default:
      module.default ??
      (() => (
        <PlaceholderPanel
          title="Chat Interface"
          description="This module is not generated yet. Add ChatInterface to enable live AI conversations."
        />
      )),
  })),
);

const HolographicAvatar = lazy(() =>
  import("./components/HolographicAvatar").then((module) => ({
    default:
      module.default ??
      (() => (
        <PlaceholderPanel
          title="Holographic Avatar"
          description="This module is not generated yet. Add HolographicAvatar to render the 3D tutor."
        />
      )),
  })),
);

const Dashboard = lazy(() =>
  import("./components/Dashboard").then((module) => ({
    default:
      module.default ??
      (() => (
        <PlaceholderPanel
          title="Dashboard"
          description="This module is not generated yet. Add Dashboard to view analytics and insights."
        />
      )),
  })),
);

const DocumentUpload = lazy(() =>
  import("./components/DocumentUpload").then((module) => ({
    default:
      module.default ??
      (() => (
        <PlaceholderPanel
          title="Documents"
          description="This module is not generated yet. Add DocumentUpload to manage learning files."
        />
      )),
  })),
);

const Quiz = lazy(() =>
  import("./components/Quiz").then((module) => ({
    default:
      module.default ??
      (() => (
        <PlaceholderPanel
          title="Quiz"
          description="This module is not generated yet. Add Quiz to start adaptive assessments."
        />
      )),
  })),
);

const Settings = lazy(() =>
  import("./components/Settings").then((module) => ({
    default:
      module.default ??
      (() => (
        <PlaceholderPanel
          title="Settings"
          description="This module is not generated yet. Add Settings to manage preferences."
        />
      )),
  })),
);

function RenderView() {
  const { currentView } = useAppContext();

  if (currentView === "chat") {
    return (
      <div className="content-area animate-slide-in">
        <Suspense
          fallback={
            <div className="glass-panel min-h-[320px] p-5">
              Loading chat module...
            </div>
          }
        >
          <ChatInterface />
        </Suspense>
        <Suspense
          fallback={
            <div className="glass-panel min-h-[320px] p-5">
              Loading avatar module...
            </div>
          }
        >
          <HolographicAvatar />
        </Suspense>
      </div>
    );
  }

  if (currentView === "dashboard") {
    return (
      <div className="animate-slide-in">
        <Suspense
          fallback={
            <div className="glass-panel min-h-[320px] p-5">
              Loading dashboard...
            </div>
          }
        >
          <Dashboard />
        </Suspense>
      </div>
    );
  }

  if (currentView === "documents") {
    return (
      <div className="animate-slide-in">
        <Suspense
          fallback={
            <div className="glass-panel min-h-[320px] p-5">
              Loading documents...
            </div>
          }
        >
          <DocumentUpload />
        </Suspense>
      </div>
    );
  }

  if (currentView === "settings") {
    return (
      <div className="animate-slide-in">
        <Suspense
          fallback={
            <div className="glass-panel min-h-[320px] p-5">
              Loading settings...
            </div>
          }
        >
          <Settings />
        </Suspense>
      </div>
    );
  }

  return (
    <div className="animate-slide-in">
      <Suspense
        fallback={
          <div className="glass-panel min-h-[320px] p-5">Loading quiz...</div>
        }
      >
        <Quiz />
      </Suspense>
    </div>
  );
}

export default function App() {
  const {
    currentView,
    setCurrentView,
    language,
    setPrimaryLanguage,
    toggleBilingual,
    student,
    loading,
  } = useAppContext();

  if (loading.initializing) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center px-6">
        <div className="glass-panel p-8 md:p-10 text-center max-w-md w-full animate-fade-in">
          <LoaderCircle
            size={36}
            className="mx-auto mb-4 text-cyan-200 animate-spin"
          />
          <h2 className="text-2xl font-semibold hologram-text mb-2">
            Initializing HoloLearn
          </h2>
          <p className="text-slate-300">
            Loading your profile, documents, and assistant context...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Sidebar currentView={currentView} onChangeView={setCurrentView} />

      <main className="main-content">
        <header className="main-header">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-cyan-400/35 via-purple-500/35 to-pink-500/35 border border-cyan-300/30" />
            <div>
              <p className="text-xs uppercase tracking-[0.16em] text-slate-400">
                HoloLearn
              </p>
              <h2 className="text-base sm:text-lg font-semibold text-slate-100">
                AI Learning Assistant
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            <LanguageSelector
              language={language.primary}
              bilingual={language.bilingual}
              onLanguageChange={setPrimaryLanguage}
              onToggleBilingual={toggleBilingual}
            />
            <span className="badge badge-cyan">
              Student: {student?.id ?? "N/A"}
            </span>
          </div>
        </header>

        <RenderView />
      </main>
    </div>
  );
}
