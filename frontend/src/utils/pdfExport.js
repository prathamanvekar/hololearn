import { jsPDF } from "jspdf";

function sanitizeFilename(value, fallback = "summary") {
  const raw = String(value || fallback).trim() || fallback;
  return raw
    .replace(/[\\/:*?"<>|]+/g, "-")
    .replace(/\s+/g, "-")
    .slice(0, 80)
    .toLowerCase();
}

function createDoc(title) {
  const doc = new jsPDF({
    orientation: "portrait",
    unit: "pt",
    format: "a4",
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const marginX = 40;
  let y = 44;

  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.text(title, marginX, y);
  y += 18;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(100, 100, 100);
  doc.text(`Generated: ${new Date().toLocaleString()}`, marginX, y);

  doc.setTextColor(20, 20, 20);
  y += 18;

  const state = {
    doc,
    marginX,
    pageWidth,
    y,
  };

  return state;
}

function ensurePage(state, neededHeight = 16) {
  const bottom = state.doc.internal.pageSize.getHeight() - 40;
  if (state.y + neededHeight <= bottom) {
    return;
  }
  state.doc.addPage();
  state.y = 44;
}

function addSectionTitle(state, text) {
  ensurePage(state, 24);
  state.doc.setFont("helvetica", "bold");
  state.doc.setFontSize(12);
  state.doc.text(String(text), state.marginX, state.y);
  state.y += 16;
}

function addLine(state, label, value = "") {
  const safeValue = value === null || value === undefined ? "-" : String(value);
  const content = label ? `${label}: ${safeValue}` : safeValue;
  const maxWidth = state.pageWidth - state.marginX * 2;
  const lines = state.doc.splitTextToSize(content, maxWidth);

  state.doc.setFont("helvetica", "normal");
  state.doc.setFontSize(10);

  lines.forEach((line) => {
    ensurePage(state, 14);
    state.doc.text(line, state.marginX, state.y);
    state.y += 13;
  });
}

function saveDoc(state, baseName) {
  const filename = `${sanitizeFilename(baseName)}-${Date.now()}.pdf`;
  state.doc.save(filename);
}

export function exportDashboardSummaryPdf({
  studentName,
  stats,
  streakDays,
  strongAreas,
  weakAreas,
  recommendations,
}) {
  const state = createDoc("HoloLearn Dashboard Summary");

  addSectionTitle(state, "Student");
  addLine(state, "Name", studentName || "Unknown Student");

  addSectionTitle(state, "Performance Snapshot");
  addLine(state, "Documents", stats?.documentsCount ?? 0);
  addLine(state, "Quizzes Taken", stats?.quizzesTaken ?? 0);
  addLine(
    state,
    "Average Score",
    `${Math.round(Number(stats?.averageScore ?? 0))}%`,
  );
  addLine(state, "Study Time", `${Number(stats?.studyTime ?? 0)} min`);
  addLine(state, "Current Streak", `${Number(streakDays ?? 0)} day(s)`);

  addSectionTitle(state, "Strong Areas");
  if (Array.isArray(strongAreas) && strongAreas.length > 0) {
    strongAreas.slice(0, 10).forEach((item, index) => {
      const topic =
        typeof item === "string"
          ? item
          : item?.topic || item?.name || `Area ${index + 1}`;
      addLine(state, `#${index + 1}`, topic);
    });
  } else {
    addLine(state, "", "No strong areas identified yet.");
  }

  addSectionTitle(state, "Weak Areas");
  if (Array.isArray(weakAreas) && weakAreas.length > 0) {
    weakAreas.slice(0, 10).forEach((item, index) => {
      const topic =
        typeof item === "string"
          ? item
          : item?.topic || item?.name || `Area ${index + 1}`;
      addLine(state, `#${index + 1}`, topic);
    });
  } else {
    addLine(state, "", "No weak areas identified yet.");
  }

  addSectionTitle(state, "Recommendations");
  if (Array.isArray(recommendations) && recommendations.length > 0) {
    recommendations.slice(0, 12).forEach((item, index) => {
      const title =
        typeof item === "string"
          ? item
          : item?.topic ||
            item?.title ||
            item?.recommendation ||
            `Recommendation ${index + 1}`;
      const reason =
        typeof item === "object" ? item?.reason || item?.description || "" : "";
      addLine(state, `#${index + 1}`, reason ? `${title} — ${reason}` : title);
    });
  } else {
    addLine(state, "", "No recommendations available yet.");
  }

  saveDoc(state, `${studentName || "student"}-dashboard-summary`);
}

export function exportQuizSummaryPdf({
  studentName,
  topic,
  sourceLabel,
  result,
}) {
  const state = createDoc("HoloLearn Quiz Summary");

  addSectionTitle(state, "Quiz");
  addLine(state, "Student", studentName || "Unknown Student");
  addLine(state, "Topic", topic || sourceLabel || "General Knowledge");
  addLine(state, "Source", sourceLabel || "General Knowledge");

  addSectionTitle(state, "Result");
  addLine(state, "Score", `${result?.score ?? 0}/${result?.total ?? 0}`);
  addLine(
    state,
    "Percentage",
    `${Math.round(Number(result?.percentage ?? 0))}%`,
  );
  addLine(state, "Time", result?.timeTaken ?? "00:00");

  addSectionTitle(state, "Question Review");
  const review = Array.isArray(result?.review) ? result.review : [];
  if (review.length === 0) {
    addLine(state, "", "No review items available.");
  } else {
    review.forEach((item, index) => {
      addLine(state, `Q${index + 1}`, item?.question || "-");
      addLine(state, "Your Answer", item?.yourAnswer || "Not answered");
      addLine(state, "Correct Answer", item?.correctAnswer || "-");
      addLine(state, "Status", item?.isCorrect ? "Correct" : "Incorrect");
      addLine(
        state,
        "Explanation",
        item?.explanation || "No explanation available.",
      );
      state.y += 4;
    });
  }

  saveDoc(state, `${studentName || "student"}-${topic || "quiz"}-summary`);
}
