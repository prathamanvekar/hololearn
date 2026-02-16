import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

http.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
);

export const chatApi = {
  sendMessage: async (payload) => {
    const response = await http.post("/chat/send", payload);
    return response.data;
  },
};

export const documentsApi = {
  upload: async (formData) => {
    const response = await http.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  listByStudent: async (studentId) => {
    const response = await http.get(`/documents/list/${studentId}`);
    return response.data;
  },

  deleteById: async (documentId) => {
    const response = await http.delete(`/documents/${documentId}`);
    return response.data;
  },
};

export const speechApi = {
  transcribe: async (formData) => {
    const response = await http.post("/speech/transcribe", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },
};

export const profileApi = {
  getByStudent: async (studentId) => {
    const response = await http.get(`/profile/${studentId}`);
    return response.data;
  },

  updateByStudent: async (studentId, payload) => {
    const response = await http.put(`/profile/${studentId}`, payload);
    return response.data;
  },

  create: async (payload) => {
    const response = await http.post("/profile/create", payload);
    return response.data;
  },
};

export const quizApi = {
  generate: async (payload) => {
    const response = await http.post("/quiz/generate", payload);
    return response.data;
  },

  getById: async (quizId) => {
    const response = await http.get(`/quiz/${quizId}`);
    return response.data;
  },

  submit: async (payload) => {
    const response = await http.post("/quiz/submit", payload);
    return response.data;
  },

  historyByStudent: async (studentId) => {
    const response = await http.get(`/quiz/history/${studentId}`);
    return response.data;
  },
};

export const dashboardApi = {
  getByStudent: async (studentId) => {
    const response = await http.get(`/dashboard/${studentId}`);
    return response.data;
  },

  getPerformanceChart: async (studentId) => {
    const response = await http.get(
      `/dashboard/${studentId}/performance-chart`,
    );
    return response.data;
  },
};

const api = {
  chat: chatApi,
  documents: documentsApi,
  speech: speechApi,
  profile: profileApi,
  quiz: quizApi,
  dashboard: dashboardApi,
  uploadDocument: async (formData, onUploadProgress) => {
    const response = await http.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress,
    });
    return response.data;
  },
  getDocuments: async (studentId) => {
    const response = await http.get(`/documents/list/${studentId}`);
    return response.data;
  },
  generateQuiz: async (payload) => {
    const response = await http.post("/quiz/generate", payload);
    return response.data;
  },
  submitQuiz: async (payload) => {
    const response = await http.post("/quiz/submit", payload);
    return response.data;
  },
  getQuizHistory: async (studentId) => {
    const response = await http.get(`/quiz/history/${studentId}`);
    return response.data;
  },
  getDashboard: async (studentId) => {
    const response = await http.get(`/dashboard/${studentId}`);
    return response.data;
  },
  getPerformanceChart: async (studentId) => {
    const response = await http.get(
      `/dashboard/${studentId}/performance-chart`,
    );
    return response.data;
  },
  deleteDocument: async (documentId) => {
    const response = await http.delete(`/documents/${documentId}`);
    return response.data;
  },
  transcribeAudio: async (audioInput) => {
    const formData =
      audioInput instanceof FormData
        ? audioInput
        : (() => {
            const payload = new FormData();
            payload.append("audio", audioInput, "voice.webm");
            return payload;
          })();
    return speechApi.transcribe(formData);
  },
};

export { API_BASE_URL, http };
export default api;
