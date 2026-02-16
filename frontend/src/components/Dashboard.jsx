import {
  Brain,
  Clock3,
  FileText,
  LoaderCircle,
  Sparkles,
  Target,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import api from "../services/api";
import { useAppContext } from "../context/useAppContext";
import PerformanceChart from "./PerformanceChart";
import { exportDashboardSummaryPdf } from "../utils/pdfExport";

function toActivityIcon(type = "") {
  const value = String(type).toLowerCase();
  if (value.includes("quiz")) {
    return <Brain size={15} className="text-cyan-200" />;
  }
  if (value.includes("document") || value.includes("upload")) {
    return <FileText size={15} className="text-purple-200" />;
  }
  return <Sparkles size={15} className="text-pink-200" />;
}

function normalizeArray(value) {
  return Array.isArray(value) ? value : [];
}

export default function Dashboard() {
  const { student, documents } = useAppContext();
  const [dashboardData, setDashboardData] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!student?.id) {
      setLoading(false);
      return;
    }

    let mounted = true;

    const loadDashboard = async () => {
      setLoading(true);
      setError("");
      try {
        const [summary, chart] = await Promise.all([
          api.getDashboard(student.id),
          api.getPerformanceChart(student.id),
        ]);

        if (!mounted) {
          return;
        }

        setDashboardData(summary || {});
        setChartData(
          normalizeArray(
            chart?.daily_averages ??
              chart?.data ??
              chart?.chart ??
              chart?.items ??
              chart,
          ).map((entry) => ({
            date: entry?.date,
            average_score: Number(entry?.average_score ?? entry?.score ?? 0),
          })),
        );
      } catch {
        if (mounted) {
          setError("Unable to load dashboard analytics right now.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, [student?.id]);

  const stats = useMemo(() => {
    const statistics = dashboardData?.statistics ?? {};
    const documentsCount =
      dashboardData?.documents_count ??
      statistics?.documents_uploaded ??
      dashboardData?.stats?.documents ??
      dashboardData?.documents ??
      documents.length;
    const quizzesTaken =
      dashboardData?.quizzes_taken ??
      statistics?.total_quizzes_taken ??
      dashboardData?.stats?.quizzes_taken ??
      dashboardData?.quizzes ??
      0;
    const averageScore =
      dashboardData?.average_score ??
      statistics?.average_quiz_score ??
      dashboardData?.stats?.average_score ??
      dashboardData?.avg_score ??
      0;
    const studyTime =
      dashboardData?.study_time ??
      statistics?.total_study_time_minutes ??
      dashboardData?.stats?.study_time ??
      dashboardData?.study_minutes ??
      0;

    return {
      documentsCount: Number(documentsCount || 0),
      quizzesTaken: Number(quizzesTaken || 0),
      averageScore: Number(averageScore || 0),
      studyTime: Number(studyTime || 0),
    };
  }, [dashboardData, documents.length]);

  const streakDays =
    dashboardData?.streak_days ??
    dashboardData?.streak?.current_streak ??
    dashboardData?.streak ??
    dashboardData?.stats?.streak_days ??
    0;
  const strongAreas = normalizeArray(
    dashboardData?.strong_areas ?? dashboardData?.strengths,
  ).slice(0, 6);
  const weakAreas = normalizeArray(
    dashboardData?.weak_areas ?? dashboardData?.weaknesses,
  ).slice(0, 6);
  const recommendations = normalizeArray(
    dashboardData?.recommendations ?? dashboardData?.suggestions,
  ).slice(0, 6);
  const activities = normalizeArray(
    dashboardData?.recent_activity ?? dashboardData?.activity,
  ).slice(0, 8);

  const handleExportSummary = () => {
    exportDashboardSummaryPdf({
      studentName:
        dashboardData?.student?.name ||
        dashboardData?.statistics?.student_name ||
        student?.name ||
        "Student",
      stats,
      streakDays,
      strongAreas,
      weakAreas,
      recommendations,
    });
  };

  if (loading) {
    return (
      <section className="glass-panel p-6 min-h-[420px] flex items-center justify-center">
        <div className="flex items-center gap-2 text-slate-200">
          <LoaderCircle size={18} className="animate-spin" />
          <span>Loading dashboard...</span>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="glass-panel p-6 min-h-[320px] flex items-center justify-center">
        <div className="card max-w-lg text-center">
          <p className="text-pink-200 font-semibold">Dashboard Error</p>
          <p className="text-slate-300 text-sm mt-1">{error}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-4 animate-fade-in">
      <header className="glass-panel p-4 md:p-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-slate-400">
            Learning Analytics
          </p>
          <h3 className="text-xl font-semibold hologram-text">
            Student Dashboard
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge badge-pink">🔥 {streakDays} day streak</span>
          <button
            type="button"
            className="btn-ghost"
            onClick={handleExportSummary}
          >
            Export PDF
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        <article className="card bg-gradient-to-br from-cyan-500/18 to-cyan-900/8">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-300">Documents</p>
            <FileText size={18} className="text-cyan-200" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">
            {stats.documentsCount}
          </p>
        </article>

        <article className="card bg-gradient-to-br from-purple-500/18 to-purple-900/8">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-300">Quizzes Taken</p>
            <Brain size={18} className="text-purple-200" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">
            {stats.quizzesTaken}
          </p>
        </article>

        <article className="card bg-gradient-to-br from-pink-500/18 to-pink-900/8">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-300">Average Score</p>
            <Target size={18} className="text-pink-200" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">
            {Math.round(stats.averageScore)}%
          </p>
        </article>

        <article className="card bg-gradient-to-br from-emerald-500/18 to-emerald-900/8">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-300">Study Time</p>
            <Clock3 size={18} className="text-emerald-200" />
          </div>
          <p className="text-2xl font-bold text-white mt-2">
            {stats.studyTime} min
          </p>
        </article>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.5fr_1fr] gap-4">
        <article className="glass-panel p-4 md:p-5">
          <h4 className="text-sm font-semibold text-slate-100 mb-3">
            Performance Trend
          </h4>
          {chartData.length > 0 ? (
            <PerformanceChart data={chartData} />
          ) : (
            <div className="card text-center py-10">
              <p className="text-slate-300">No performance data yet.</p>
              <p className="text-xs text-slate-400 mt-1">
                Complete quizzes to populate the chart.
              </p>
            </div>
          )}
        </article>

        <article className="glass-panel p-4 md:p-5 space-y-3">
          <div>
            <h4 className="text-sm font-semibold text-emerald-300 mb-2">
              Strong Areas
            </h4>
            {strongAreas.length > 0 ? (
              <ul className="space-y-1.5">
                {strongAreas.map((area, index) => (
                  <li
                    key={`strong-${index}`}
                    className="rounded-lg border border-emerald-300/25 bg-emerald-500/10 px-2.5 py-2 text-sm text-emerald-100"
                  >
                    {typeof area === "string"
                      ? area
                      : area?.topic || area?.name || `Area ${index + 1}`}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-400">
                No strong areas identified yet.
              </p>
            )}
          </div>

          <div>
            <h4 className="text-sm font-semibold text-yellow-300 mb-2">
              Weak Areas
            </h4>
            {weakAreas.length > 0 ? (
              <ul className="space-y-1.5">
                {weakAreas.map((area, index) => (
                  <li
                    key={`weak-${index}`}
                    className="rounded-lg border border-yellow-300/25 bg-yellow-500/10 px-2.5 py-2 text-sm text-yellow-100"
                  >
                    {typeof area === "string"
                      ? area
                      : area?.topic || area?.name || `Area ${index + 1}`}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-400">
                No weak areas identified yet.
              </p>
            )}
          </div>
        </article>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <article className="glass-panel p-4 md:p-5">
          <h4 className="text-sm font-semibold text-slate-100 mb-3">
            Recommendations
          </h4>
          {recommendations.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {recommendations.map((item, index) => {
                const title =
                  typeof item === "string"
                    ? item
                    : item?.topic ||
                      item?.title ||
                      item?.recommendation ||
                      `Topic ${index + 1}`;
                const subtitle =
                  typeof item === "object"
                    ? item?.reason || item?.description || ""
                    : "";

                return (
                  <div
                    key={`rec-${index}`}
                    className="rounded-xl border border-white/12 bg-slate-900/45 px-3 py-2"
                  >
                    <p className="text-sm text-slate-100">{title}</p>
                    {subtitle ? (
                      <p className="text-xs text-slate-400 mt-1">{subtitle}</p>
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400">
              No recommendations available yet.
            </p>
          )}
        </article>

        <article className="glass-panel p-4 md:p-5">
          <h4 className="text-sm font-semibold text-slate-100 mb-3">
            Recent Activity
          </h4>
          {activities.length > 0 ? (
            <ul className="space-y-2">
              {activities.map((activity, index) => {
                const type = activity?.type || activity?.category || "activity";
                const title =
                  activity?.title ||
                  activity?.message ||
                  `Activity ${index + 1}`;
                const time =
                  activity?.time || activity?.timestamp || activity?.date || "";

                return (
                  <li
                    key={`act-${index}`}
                    className="rounded-xl border border-white/12 bg-slate-900/45 px-3 py-2"
                  >
                    <div className="flex items-start gap-2.5">
                      <div className="mt-0.5">{toActivityIcon(type)}</div>
                      <div className="min-w-0">
                        <p className="text-sm text-slate-100 truncate">
                          {title}
                        </p>
                        {time ? (
                          <p className="text-xs text-slate-400 mt-0.5">
                            {String(time)}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-slate-400">No activity yet.</p>
          )}
        </article>
      </div>
    </section>
  );
}
