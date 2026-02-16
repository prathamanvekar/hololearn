import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Crosshair,
  History,
  Target,
  Trophy,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import api from "../services/api";
import { useAppContext } from "../context/useAppContext";
import { exportQuizSummaryPdf } from "../utils/pdfExport";

const PASS_PERCENTAGE = 60;

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = Math.floor(totalSeconds % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function getQuestionText(question, fallbackIndex) {
  return (
    question?.question ||
    question?.prompt ||
    question?.text ||
    `Question ${fallbackIndex + 1}`
  );
}

function getOptions(question) {
  const raw = question?.options ?? question?.choices ?? question?.answers ?? [];
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw.map((option, index) => {
    if (typeof option === "string") {
      return { id: String.fromCharCode(65 + index), text: option };
    }
    return {
      id: option?.id || option?.key || String.fromCharCode(65 + index),
      text:
        option?.text || option?.value || option?.label || `Option ${index + 1}`,
    };
  });
}

function getCorrectAnswer(question) {
  return (
    question?.correct_answer ||
    question?.correctOption ||
    question?.correct_option ||
    question?.answer ||
    null
  );
}

function getExplanation(question) {
  return (
    question?.explanation || question?.reason || "No explanation available."
  );
}

export default function Quiz() {
  const { student, documents } = useAppContext();

  const [view, setView] = useState("setup");
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [history, setHistory] = useState([]);

  const [config, setConfig] = useState({
    documentId: "",
    topic: "",
    difficulty: "medium",
  });

  const [quizMeta, setQuizMeta] = useState({
    id: null,
    topic: "",
    sourceLabel: "",
  });
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [result, setResult] = useState(null);

  useEffect(() => {
    if (view !== "quiz") {
      return undefined;
    }

    const timer = setInterval(() => {
      setElapsedSeconds((seconds) => seconds + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [view]);

  useEffect(() => {
    if (!student?.id) {
      return;
    }

    const loadHistory = async () => {
      setLoadingHistory(true);
      try {
        const response = await api.getQuizHistory(student.id);
        const entries = response?.history ?? response?.items ?? response ?? [];
        setHistory(Array.isArray(entries) ? entries : []);
      } catch {
        setHistory([]);
      } finally {
        setLoadingHistory(false);
      }
    };

    loadHistory();
  }, [student?.id]);

  const progressPercentage = useMemo(() => {
    if (questions.length === 0) {
      return 0;
    }
    return ((currentIndex + 1) / questions.length) * 100;
  }, [currentIndex, questions.length]);

  const selectedQuestion = questions[currentIndex] || null;
  const selectedOptions = selectedQuestion ? getOptions(selectedQuestion) : [];

  const handleStartQuiz = async () => {
    if (!student?.id || generating) {
      return;
    }

    if (!config.documentId && !config.topic.trim()) {
      return;
    }

    setGenerating(true);
    try {
      const payload = {
        student_id: student.id,
        difficulty: config.difficulty,
        num_questions: 1,
      };

      if (config.documentId) {
        payload.document_id = config.documentId;
      } else {
        payload.topic = config.topic.trim();
      }

      const response = await api.generateQuiz(payload);
      const generatedQuestions =
        response?.questions ??
        response?.quiz?.questions ??
        response?.items ??
        [];

      const normalizedQuestions = Array.isArray(generatedQuestions)
        ? generatedQuestions
        : [];
      if (normalizedQuestions.length === 0) {
        return;
      }

      const selectedDoc = documents.find(
        (doc) =>
          String(doc?.id ?? doc?.document_id) === String(config.documentId),
      );

      setQuizMeta({
        id: response?.quiz_id ?? response?.id ?? response?.quiz?.id ?? null,
        topic:
          config.topic.trim() ||
          selectedDoc?.title ||
          selectedDoc?.filename ||
          "General Knowledge",
        sourceLabel:
          selectedDoc?.title || selectedDoc?.filename || "General Knowledge",
      });
      setQuestions(normalizedQuestions);
      setAnswers({});
      setCurrentIndex(0);
      setElapsedSeconds(0);
      setResult(null);
      setView("quiz");
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!student?.id || questions.length === 0 || submitting) {
      return;
    }

    setSubmitting(true);
    try {
      const responses = questions.reduce((accumulator, question, index) => {
        const questionId = question?.id ?? question?.question_id ?? index;
        const selectedAnswer = answers[index];
        if (selectedAnswer !== null && selectedAnswer !== undefined) {
          accumulator[String(questionId)] = String(selectedAnswer);
        }
        return accumulator;
      }, {});

      const payload = {
        student_id: student.id,
        quiz_id: quizMeta.id,
        responses,
        time_taken_seconds: elapsedSeconds,
      };

      const response = await api.submitQuiz(payload);

      const fallbackScore = questions.reduce((count, question, index) => {
        const selected = answers[index];
        const correct = getCorrectAnswer(question);
        return selected && correct && String(selected) === String(correct)
          ? count + 1
          : count;
      }, 0);

      const score =
        response?.score ?? response?.correct_answers ?? fallbackScore;
      const total =
        response?.total ?? response?.total_questions ?? questions.length;
      const percentage =
        response?.percentage ??
        response?.score_percentage ??
        (total > 0 ? (score / total) * 100 : 0);

      const review = questions.map((question, index) => {
        const selected = answers[index] ?? null;
        const correct = getCorrectAnswer(question);
        const normalizedOptions = getOptions(question);

        const resolveLabel = (value) => {
          if (value === null || value === undefined) {
            return "Not answered";
          }

          const foundOption = normalizedOptions.find(
            (option) => String(option.id) === String(value),
          );
          if (foundOption) {
            return `${foundOption.id}. ${foundOption.text}`;
          }
          return String(value);
        };

        return {
          question: getQuestionText(question, index),
          yourAnswer: resolveLabel(selected),
          correctAnswer: resolveLabel(correct),
          explanation: getExplanation(question),
          isCorrect:
            selected !== null &&
            correct !== null &&
            String(selected) === String(correct),
        };
      });

      setResult({
        score,
        total,
        percentage,
        timeTaken: response?.time_taken ?? elapsedSeconds,
        review,
      });
      setView("results");

      const latestHistoryResponse = await api.getQuizHistory(student.id);
      const entries =
        latestHistoryResponse?.history ??
        latestHistoryResponse?.items ??
        latestHistoryResponse ??
        [];
      setHistory(Array.isArray(entries) ? entries : []);
    } finally {
      setSubmitting(false);
    }
  };

  const restartSetup = () => {
    setView("setup");
    setQuestions([]);
    setAnswers({});
    setCurrentIndex(0);
    setElapsedSeconds(0);
  };

  const retrySameTopic = () => {
    setView("setup");
  };

  const handleExportQuizSummary = () => {
    if (!result) {
      return;
    }
    exportQuizSummaryPdf({
      studentName: student?.name || "Student",
      topic: quizMeta?.topic,
      sourceLabel: quizMeta?.sourceLabel,
      result: {
        ...result,
        timeTaken: formatTime(Number(result?.timeTaken ?? 0)),
      },
    });
  };

  if (view === "quiz" && selectedQuestion) {
    return (
      <section className="glass-panel p-4 md:p-5 animate-fade-in space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.14em] text-slate-400">
              Quiz In Progress
            </p>
            <h3 className="text-lg font-semibold hologram-text">
              Question {currentIndex + 1} of {questions.length}
            </h3>
          </div>
          <span className="badge badge-purple">
            Time: {formatTime(elapsedSeconds)}
          </span>
        </div>

        <div className="h-2 rounded-full bg-slate-900/70 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500 transition-all"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>

        <div className="card">
          <p className="text-slate-100 font-medium leading-relaxed">
            {getQuestionText(selectedQuestion, currentIndex)}
          </p>
          <div className="mt-4 space-y-2">
            {selectedOptions.map((option) => {
              const isSelected =
                String(answers[currentIndex]) === String(option.id);
              return (
                <button
                  key={`${currentIndex}-${option.id}`}
                  type="button"
                  className={`w-full text-left rounded-xl border px-3 py-2.5 transition-colors ${
                    isSelected
                      ? "border-cyan-300/60 bg-cyan-500/12 text-cyan-100"
                      : "border-white/12 bg-slate-900/40 text-slate-200 hover:border-cyan-300/35"
                  }`}
                  onClick={() =>
                    setAnswers((previous) => ({
                      ...previous,
                      [currentIndex]: option.id,
                    }))
                  }
                >
                  <span className="font-semibold mr-2">{option.id}.</span>
                  <span>{option.text}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {questions.map((_, index) => {
            const visited = answers[index] !== undefined;
            const isActive = index === currentIndex;
            return (
              <button
                key={`step-${index}`}
                type="button"
                onClick={() => setCurrentIndex(index)}
                className={`h-9 min-w-9 px-2 rounded-lg border text-sm ${
                  isActive
                    ? "border-cyan-300/65 bg-cyan-500/15 text-cyan-100"
                    : visited
                      ? "border-purple-300/40 bg-purple-500/10 text-purple-100"
                      : "border-white/12 text-slate-300"
                }`}
              >
                {index + 1}
              </button>
            );
          })}
        </div>

        <div className="flex items-center justify-between gap-2 pt-1">
          <button
            type="button"
            className="btn-ghost"
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((index) => Math.max(index - 1, 0))}
          >
            <ChevronLeft size={16} /> Previous
          </button>

          {currentIndex < questions.length - 1 ? (
            <button
              type="button"
              className="btn-primary"
              onClick={() =>
                setCurrentIndex((index) =>
                  Math.min(index + 1, questions.length - 1),
                )
              }
            >
              Next <ChevronRight size={16} />
            </button>
          ) : (
            <button
              type="button"
              className="btn-primary"
              onClick={handleSubmitQuiz}
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit Quiz"}
            </button>
          )}
        </div>
      </section>
    );
  }

  if (view === "results" && result) {
    const passed = Number(result.percentage) >= PASS_PERCENTAGE;

    return (
      <section className="glass-panel p-4 md:p-5 animate-fade-in space-y-4">
        <header className="text-center card">
          <div className="mx-auto mb-2 h-14 w-14 rounded-full border border-white/15 flex items-center justify-center bg-slate-900/65">
            {passed ? (
              <Trophy className="text-cyan-200" size={26} />
            ) : (
              <Target className="text-pink-300" size={24} />
            )}
          </div>
          <p className="text-4xl font-bold hologram-text">
            {Math.round(result.percentage)}%
          </p>
          <p
            className={`mt-1 text-sm ${passed ? "text-cyan-100" : "text-pink-200"}`}
          >
            {passed
              ? "Great work! You passed."
              : "Keep going. You can improve on retry."}
          </p>

          <div className="mt-3 flex flex-wrap justify-center gap-2">
            <span className="badge badge-cyan">Score: {result.score}</span>
            <span className="badge badge-purple">Total: {result.total}</span>
            <span className="badge badge-pink">
              Time: {formatTime(result.timeTaken)}
            </span>
          </div>
        </header>

        <div className="space-y-3">
          {result.review.map((item, index) => (
            <article key={`review-${index}`} className="card">
              <div className="flex items-start gap-2">
                {item.isCorrect ? (
                  <CheckCircle2 className="text-cyan-200 mt-0.5" size={16} />
                ) : (
                  <Crosshair className="text-pink-300 mt-0.5" size={16} />
                )}
                <div>
                  <h4 className="text-sm font-semibold text-slate-100">
                    Q{index + 1}. {item.question}
                  </h4>
                  <p className="text-xs text-slate-300 mt-1">
                    Your answer: {item.yourAnswer}
                  </p>
                  <p className="text-xs text-cyan-100">
                    Correct answer: {item.correctAnswer}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {item.explanation}
                  </p>
                </div>
              </div>
            </article>
          ))}
        </div>

        <div className="flex flex-wrap gap-2 pt-1">
          <button
            type="button"
            className="btn-ghost"
            onClick={handleExportQuizSummary}
          >
            Export PDF
          </button>
          <button type="button" className="btn-primary" onClick={restartSetup}>
            Take Another Quiz
          </button>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => {
              setConfig((previous) => ({
                ...previous,
                topic: quizMeta.topic,
                documentId: "",
              }));
              retrySameTopic();
            }}
          >
            Retry Same Topic
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="glass-panel p-4 md:p-5 animate-fade-in space-y-5">
      <header className="border-b border-white/10 pb-3">
        <p className="text-xs uppercase tracking-[0.14em] text-slate-400">
          Adaptive Assessment
        </p>
        <h3 className="text-lg font-semibold hologram-text">Quiz Generator</h3>
      </header>

      <div className="card space-y-3">
        <div>
          <label className="text-xs text-slate-400 mb-1 block">
            Document Source
          </label>
          <select
            className="input-field"
            value={config.documentId}
            onChange={(event) =>
              setConfig((previous) => ({
                ...previous,
                documentId: event.target.value,
              }))
            }
          >
            <option value="">General Knowledge</option>
            {documents.map((doc, index) => {
              const id = doc?.id ?? doc?.document_id ?? `doc-${index}`;
              const label =
                doc?.title ?? doc?.filename ?? `Document ${index + 1}`;
              return (
                <option key={id} value={id}>
                  {label}
                </option>
              );
            })}
          </select>
        </div>

        {!config.documentId ? (
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Topic</label>
            <input
              className="input-field"
              placeholder="e.g., Photosynthesis, Algebra, World War II"
              value={config.topic}
              onChange={(event) =>
                setConfig((previous) => ({
                  ...previous,
                  topic: event.target.value,
                }))
              }
            />
          </div>
        ) : null}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">
              Difficulty
            </label>
            <select
              className="input-field"
              value={config.difficulty}
              onChange={(event) =>
                setConfig((previous) => ({
                  ...previous,
                  difficulty: event.target.value,
                }))
              }
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
        </div>

        <button
          type="button"
          className="btn-primary"
          onClick={handleStartQuiz}
          disabled={generating}
        >
          {generating ? "Generating Quiz..." : "Start Quiz"}
        </button>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-slate-100">
            Recent Quiz History
          </h4>
          <History size={15} className="text-slate-300" />
        </div>

        {loadingHistory ? (
          <p className="text-sm text-slate-300">Loading history...</p>
        ) : history.length === 0 ? (
          <p className="text-sm text-slate-400">No previous attempts yet.</p>
        ) : (
          <ul className="space-y-2">
            {history.slice(0, 6).map((entry, index) => {
              const score = entry?.score ?? entry?.correct_answers ?? 0;
              const total =
                entry?.total_points ??
                entry?.total ??
                entry?.total_questions ??
                0;
              const percent =
                entry?.percentage ??
                entry?.score_percentage ??
                (total > 0 ? (score / total) * 100 : 0);
              const label =
                entry?.topic || entry?.title || `Attempt ${index + 1}`;

              return (
                <li
                  key={`${entry?.attempt_id ?? entry?.id ?? index}`}
                  className="rounded-xl border border-white/12 bg-slate-900/45 px-3 py-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm text-slate-200 truncate">{label}</p>
                    <span className="badge badge-cyan">
                      {Math.round(percent)}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    {score}/{total} correct
                  </p>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
