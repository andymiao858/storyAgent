import axios from "axios";
import type {
  ApiResponse,
  AuthData,
  Child,
  ParentSettings,
  StoryStartResponse,
  StoryContinueResponse,
  StoryHistoryItem,
  GrowthReport,
} from "@/types";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// Auth
export const authRegister = (email: string, password: string) =>
  api.post<ApiResponse<AuthData>>("/api/auth/register", { email, password });

export const authLogin = (email: string, password: string) =>
  api.post<ApiResponse<AuthData>>("/api/auth/login", { email, password });

export const authMe = () => api.get<ApiResponse<{ id: number; email: string; role: string }>>("/api/auth/me");

// Children
export const listChildren = () => api.get<ApiResponse<Child[]>>("/api/children");

export const createChild = (data: {
  nickname: string;
  age: number;
  interests: string[];
  reading_level: string;
  avatar_url?: string;
}) => api.post<ApiResponse<Child>>("/api/children", data);

export const getChild = (childId: number) =>
  api.get<ApiResponse<Child>>(`/api/children/${childId}`);

export const updateChild = (childId: number, data: Partial<Child>) =>
  api.put<ApiResponse<Child>>(`/api/children/${childId}`, data);

// Parent Settings
export const getParentSettings = () =>
  api.get<ApiResponse<ParentSettings>>("/api/parent/settings");

export const updateParentSettings = (data: Partial<ParentSettings>) =>
  api.put<ApiResponse<ParentSettings>>("/api/parent/settings", data);

// Story (non-streaming, kept for fallback)
export const startStory = (data: {
  child_id: number;
  theme: string;
  main_character: string;
  scene: string;
}) => api.post<ApiResponse<StoryStartResponse>>("/api/story/start", data);

export const continueStory = (data: { session_id: number; selected_option: string }) =>
  api.post<ApiResponse<StoryContinueResponse>>("/api/story/continue", data);

// ---- SSE streaming helpers ----

export interface SSECallbacks {
  onInit?: (data: { story_id: number; session_id: number }) => void;
  onTitle?: (data: { title: string }) => void;
  onToken?: (data: { text: string }) => void;
  onComplete?: (data: {
    scene_text: string;
    options: { key: string; text: string }[];
    is_finished: boolean;
    scene_index: number;
    summary?: string;
  }) => void;
  onError?: (msg: string) => void;
}

async function consumeSSE(url: string, body: object, callbacks: SSECallbacks) {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const response = await fetch(`http://localhost:8000${url}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!response.ok || !response.body) {
    callbacks.onError?.(`HTTP ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    let currentEvent = "";
    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        const raw = line.slice(6);
        try {
          const data = JSON.parse(raw);
          switch (currentEvent) {
            case "init":
              callbacks.onInit?.(data);
              break;
            case "title":
              callbacks.onTitle?.(data);
              break;
            case "token":
              callbacks.onToken?.(data);
              break;
            case "complete":
              callbacks.onComplete?.(data);
              break;
            case "error":
              callbacks.onError?.(data.message || "Unknown error");
              break;
          }
        } catch { /* skip malformed JSON */ }
        currentEvent = "";
      }
    }
  }
}

export const startStoryStream = (
  data: { child_id: number; theme: string; main_character: string; scene: string },
  callbacks: SSECallbacks,
) => consumeSSE("/api/story/start/stream", data, callbacks);

export const continueStoryStream = (
  data: { session_id: number; selected_option: string },
  callbacks: SSECallbacks,
) => consumeSSE("/api/story/continue/stream", data, callbacks);

export const getStoryHistory = (childId: number) =>
  api.get<ApiResponse<StoryHistoryItem[]>>(`/api/story/history/${childId}`);

export const getStorySession = (sessionId: number) =>
  api.get<ApiResponse<unknown>>(`/api/story/session/${sessionId}`);

export const getLatestSessionForStory = (storyId: number) =>
  api.get<ApiResponse<{ session_id: number }>>(`/api/story/story/${storyId}/session`);

// Reports
export const getReports = (childId: number) =>
  api.get<ApiResponse<GrowthReport[]>>(`/api/reports/${childId}`);

export const getLatestReport = (childId: number) =>
  api.get<ApiResponse<GrowthReport>>(`/api/reports/${childId}/latest`);

export default api;
