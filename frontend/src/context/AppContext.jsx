import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import api from "../services/api";
import AppStateContext from "./AppStateContext";

const DEFAULT_VIEW = "chat";
const STORAGE_STUDENT_ID_KEY = "hololearn_student_id";

const initialLanguage = {
  primary: "en",
  secondary: "hi",
  bilingual: false,
};

const initialLoading = {
  initializing: true,
  profile: false,
  documents: false,
  speaking: false,
};

function toNumericStudentId(value) {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function getStoredStudentId() {
  if (typeof window === "undefined") {
    return null;
  }
  return toNumericStudentId(
    window.localStorage.getItem(STORAGE_STUDENT_ID_KEY),
  );
}

function persistStudentId(studentId) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_STUDENT_ID_KEY, String(studentId));
}

export function AppProvider({ children }) {
  const initialStudentId = getStoredStudentId();
  const [student, setStudent] = useState({
    id: initialStudentId,
    profile: null,
  });
  const [currentView, setCurrentView] = useState(DEFAULT_VIEW);
  const [language, setLanguage] = useState(initialLanguage);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(initialLoading);
  const [avatar, setAvatar] = useState({
    speaking: false,
    message: "",
  });

  const synthRef = useRef(
    typeof window !== "undefined" ? window.speechSynthesis : null,
  );

  const setLoadingState = useCallback((key, value) => {
    setLoading((previous) => ({ ...previous, [key]: value }));
  }, []);

  const setStudentId = useCallback((studentId) => {
    const normalizedId = toNumericStudentId(studentId);
    if (!normalizedId) {
      return;
    }
    persistStudentId(normalizedId);
    setStudent((previous) => ({ ...previous, id: normalizedId }));
  }, []);

  const updateProfileState = useCallback((profile) => {
    setStudent((previous) => ({ ...previous, profile }));
  }, []);

  const setPrimaryLanguage = useCallback((primary) => {
    setLanguage((previous) => ({ ...previous, primary }));
  }, []);

  const setSecondaryLanguage = useCallback((secondary) => {
    setLanguage((previous) => ({ ...previous, secondary }));
  }, []);

  const toggleBilingual = useCallback(() => {
    setLanguage((previous) => ({
      ...previous,
      bilingual: !previous.bilingual,
    }));
  }, []);

  const loadProfile = useCallback(
    async (studentId = student.id) => {
      const normalizedId = toNumericStudentId(studentId);
      if (!normalizedId) {
        return null;
      }

      setLoadingState("profile", true);

      try {
        const response = await api.profile.getByStudent(normalizedId);
        const profile = response?.profile ?? response;
        setStudent((previous) => ({ ...previous, id: normalizedId, profile }));
        return profile;
      } catch {
        setStudent((previous) => ({
          ...previous,
          id: normalizedId,
          profile: null,
        }));
        return null;
      } finally {
        setLoadingState("profile", false);
      }
    },
    [setLoadingState, student.id],
  );

  const loadDocuments = useCallback(
    async (studentId = student.id) => {
      const normalizedId = toNumericStudentId(studentId);
      if (!normalizedId) {
        setDocuments([]);
        return [];
      }

      setLoadingState("documents", true);

      try {
        const response = await api.documents.listByStudent(normalizedId);
        const docs = response?.documents ?? response?.items ?? response ?? [];
        const normalizedDocs = Array.isArray(docs) ? docs : [];
        setDocuments(normalizedDocs);
        return normalizedDocs;
      } catch {
        setDocuments([]);
        return [];
      } finally {
        setLoadingState("documents", false);
      }
    },
    [setLoadingState, student.id],
  );

  const speakWithAvatar = useCallback(
    (message, options = {}) => {
      const text = typeof message === "string" ? message.trim() : "";
      if (!text) {
        return;
      }

      setAvatar({ speaking: true, message: text });
      setLoadingState("speaking", true);

      const synthesis = synthRef.current;
      if (
        !synthesis ||
        typeof window === "undefined" ||
        !window.SpeechSynthesisUtterance
      ) {
        setLoadingState("speaking", false);
        setAvatar({ speaking: false, message: text });
        return;
      }

      synthesis.cancel();

      const utterance = new window.SpeechSynthesisUtterance(text);
      utterance.rate = options.rate ?? 1;
      utterance.pitch = options.pitch ?? 1;
      utterance.volume = options.volume ?? 1;
      utterance.lang = options.lang ?? language.primary ?? "en-US";

      utterance.onend = () => {
        setAvatar({ speaking: false, message: text });
        setLoadingState("speaking", false);
      };

      utterance.onerror = () => {
        setAvatar({ speaking: false, message: text });
        setLoadingState("speaking", false);
      };

      synthesis.speak(utterance);
    },
    [language.primary, setLoadingState],
  );

  useEffect(() => {
    let isMounted = true;
    const synthesis = synthRef.current;

    const ensureStudentId = async () => {
      const existing = getStoredStudentId() ?? toNumericStudentId(student.id);
      if (existing) {
        persistStudentId(existing);
        setStudent((previous) => ({ ...previous, id: existing }));
        return existing;
      }

      try {
        const created = await api.profile.create({
          name: "HoloLearn Demo",
          email: `demo-${Date.now()}@hololearn.local`,
          preferred_language: language.primary,
          secondary_language: language.secondary,
        });

        const createdId = toNumericStudentId(
          created?.student_id ?? created?.id,
        );
        if (createdId) {
          persistStudentId(createdId);
          setStudent((previous) => ({ ...previous, id: createdId }));
          return createdId;
        }
      } catch {
        return null;
      }

      return null;
    };

    const initialize = async () => {
      setLoadingState("initializing", true);

      try {
        const ensuredStudentId = await ensureStudentId();
        if (ensuredStudentId) {
          await Promise.all([
            loadProfile(ensuredStudentId),
            loadDocuments(ensuredStudentId),
          ]);
        }
      } finally {
        if (isMounted) {
          setLoadingState("initializing", false);
        }
      }
    };

    initialize();

    return () => {
      isMounted = false;
      if (synthesis) {
        synthesis.cancel();
      }
    };
  }, [
    language.primary,
    language.secondary,
    loadDocuments,
    loadProfile,
    setLoadingState,
    student.id,
  ]);

  const value = useMemo(
    () => ({
      student,
      setStudent,
      setStudentId,
      updateProfileState,
      currentView,
      setCurrentView,
      language,
      setLanguage,
      setPrimaryLanguage,
      setSecondaryLanguage,
      toggleBilingual,
      documents,
      setDocuments,
      loading,
      avatar,
      setAvatar,
      loadProfile,
      loadDocuments,
      speakWithAvatar,
    }),
    [
      avatar,
      currentView,
      documents,
      language,
      loadDocuments,
      loadProfile,
      loading,
      setStudentId,
      setPrimaryLanguage,
      setSecondaryLanguage,
      speakWithAvatar,
      student,
      toggleBilingual,
      updateProfileState,
    ],
  );

  return (
    <AppStateContext.Provider value={value}>
      {children}
    </AppStateContext.Provider>
  );
}
