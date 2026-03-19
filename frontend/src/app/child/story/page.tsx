"use client";

import { useEffect, useState, Suspense, useRef, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useChildStore } from "@/store/child";
import { useAuthStore } from "@/store/auth";
import {
  getStorySession,
  startStoryStream,
  continueStoryStream,
} from "@/services/api";
import type { StoryOption } from "@/types";

interface HistoryEntry {
  text: string;
  choice?: string;
}

function StoryContent() {
  const searchParams = useSearchParams();
  const sessionIdParam = searchParams.get("sessionId");
  const isNewStory = searchParams.get("newStory") === "1";
  const newChildId = searchParams.get("childId");
  const newTheme = searchParams.get("theme");
  const newCharacter = searchParams.get("character");
  const newScene = searchParams.get("scene");

  const router = useRouter();
  const { currentChild, loadFromStorage: loadChild } = useChildStore();
  const { loadFromStorage: loadAuth } = useAuthStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const startedRef = useRef(false);

  const [sessionId, setSessionId] = useState(
    sessionIdParam ? parseInt(sessionIdParam) : 0
  );
  const [sceneText, setSceneText] = useState("");
  const [options, setOptions] = useState<StoryOption[]>([]);
  const [isFinished, setIsFinished] = useState(false);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [storyTitle, setStoryTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [showExitConfirm, setShowExitConfirm] = useState(false);

  useEffect(() => {
    loadAuth();
    loadChild();
  }, [loadAuth, loadChild]);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sceneText, loading, streaming]);

  // --- Load existing session (resume) ---
  const loadSession = useCallback(async (sid: number) => {
    try {
      const res = await getStorySession(sid);
      const data = res.data.data as {
        messages: { role: string; content: string }[];
        choices: {
          scene_index: number;
          option_key: string;
          option_text: string;
        }[];
        current_scene_index: number;
        is_finished: boolean;
        last_options: StoryOption[];
        story: {
          title: string;
          theme: string;
          main_character: string;
          scene: string;
        } | null;
      };

      if (data.story?.title) setStoryTitle(data.story.title);

      const narratorMsgs = data.messages.filter((m) => m.role === "narrator");
      const choiceMap: Record<number, string> = {};
      for (const c of data.choices) {
        choiceMap[c.scene_index] = c.option_text;
      }

      const restoredHistory: HistoryEntry[] = [];
      for (let i = 0; i < narratorMsgs.length - 1; i++) {
        restoredHistory.push({
          text: narratorMsgs[i].content,
          choice: choiceMap[i] || undefined,
        });
      }
      setHistory(restoredHistory);

      if (narratorMsgs.length > 0) {
        setSceneText(narratorMsgs[narratorMsgs.length - 1].content);
      }
      setSceneIndex(data.current_scene_index);
      setIsFinished(data.is_finished);

      if (!data.is_finished && data.last_options?.length > 0) {
        setOptions(data.last_options);
      }

      if (data.is_finished) {
        const sysMsgs = data.messages.filter((m) => m.role === "system");
        if (sysMsgs.length > 0) {
          try {
            const parsed = JSON.parse(
              sysMsgs[sysMsgs.length - 1].content
            );
            setSummary(
              parsed.summary || sysMsgs[sysMsgs.length - 1].content
            );
          } catch {
            setSummary(sysMsgs[sysMsgs.length - 1].content);
          }
        }
      }
    } catch {
      /* ignore */
    }
    setInitialLoading(false);
  }, []);

  // --- Start a new story (streaming) ---
  const startNewStory = useCallback(async () => {
    if (!newChildId || !newTheme || !newCharacter || !newScene) return;
    setStreaming(true);
    setInitialLoading(false);

    await startStoryStream(
      {
        child_id: parseInt(newChildId),
        theme: newTheme,
        main_character: newCharacter,
        scene: newScene,
      },
      {
        onInit: (data) => {
          setSessionId(data.session_id);
          window.history.replaceState(
            null,
            "",
            `/child/story?sessionId=${data.session_id}`
          );
        },
        onTitle: (data) => setStoryTitle(data.title),
        onToken: (data) => setSceneText((prev) => prev + data.text),
        onComplete: (data) => {
          setSceneText(data.scene_text);
          setOptions(data.options || []);
          setIsFinished(data.is_finished);
          setSceneIndex(data.scene_index);
          setStreaming(false);
          if (data.is_finished && data.summary) setSummary(data.summary);
        },
        onError: (msg) => {
          console.error("SSE error:", msg);
          setStreaming(false);
        },
      }
    );
  }, [newChildId, newTheme, newCharacter, newScene]);

  // Init
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    if (isNewStory) {
      startNewStory();
    } else if (sessionIdParam) {
      loadSession(parseInt(sessionIdParam));
    } else {
      setInitialLoading(false);
    }
  }, [isNewStory, sessionIdParam, startNewStory, loadSession]);

  // --- Continue story (streaming) ---
  const handleChoice = async (option: StoryOption) => {
    if (!sessionId) return;
    setLoading(true);
    setStreaming(true);
    setHistory((prev) => [...prev, { text: sceneText, choice: option.text }]);
    setSceneText("");
    setOptions([]);

    await continueStoryStream(
      { session_id: sessionId, selected_option: option.key },
      {
        onToken: (data) => setSceneText((prev) => prev + data.text),
        onComplete: (data) => {
          setSceneText(data.scene_text);
          setOptions(data.options || []);
          setIsFinished(data.is_finished);
          setSceneIndex(data.scene_index);
          setStreaming(false);
          setLoading(false);
          if (data.is_finished && data.summary) setSummary(data.summary);
        },
        onError: (msg) => {
          console.error("SSE error:", msg);
          setStreaming(false);
          setLoading(false);
        },
      }
    );
  };

  const handleExit = () => {
    if (isFinished) {
      router.push("/child/home");
    } else {
      setShowExitConfirm(true);
    }
  };

  if (initialLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-indigo-100 to-purple-100">
        <div className="text-center">
          <div className="mb-3 text-6xl animate-bounce">📖</div>
          <p className="text-xl text-purple-600">故事加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-100 via-purple-50 to-pink-100 p-4 pb-8">
      <div className="mx-auto max-w-lg">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <button
            onClick={handleExit}
            className="flex items-center gap-1 rounded-full bg-white/70 px-3 py-1.5 text-sm text-gray-600 shadow-sm backdrop-blur transition hover:bg-white"
          >
            ← 退出
          </button>
          <span className="rounded-full bg-purple-200 px-3 py-1 text-sm font-medium text-purple-700">
            {storyTitle || "故事冒险"}
          </span>
          <span className="text-2xl">{currentChild?.avatar_url || "🧒"}</span>
        </div>

        {/* Exit confirmation */}
        {showExitConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
            <div className="w-full max-w-xs rounded-3xl bg-white p-6 text-center shadow-xl">
              <div className="mb-3 text-5xl">🤔</div>
              <h3 className="mb-2 text-lg font-bold text-gray-800">
                要离开故事吗？
              </h3>
              <p className="mb-5 text-sm text-gray-500">
                别担心，下次回来可以继续哦！
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowExitConfirm(false)}
                  className="flex-1 rounded-2xl bg-purple-500 py-2.5 font-medium text-white"
                >
                  继续故事
                </button>
                <button
                  onClick={() => router.push("/child/home")}
                  className="flex-1 rounded-2xl bg-gray-100 py-2.5 font-medium text-gray-700"
                >
                  回首页
                </button>
              </div>
            </div>
          </div>
        )}

        {/* History */}
        {history.length > 0 && (
          <div className="mb-4 max-h-60 space-y-3 overflow-y-auto rounded-2xl bg-white/40 p-3 backdrop-blur">
            {history.map((h, i) => (
              <div key={i} className="rounded-xl bg-white/60 p-3">
                <div className="mb-1 text-[10px] font-medium text-purple-400">
                  第 {i + 1} 幕
                </div>
                <p className="text-sm leading-relaxed text-gray-600">
                  {h.text}
                </p>
                {h.choice && (
                  <div className="mt-1.5 inline-block rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-600">
                    → {h.choice}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Current scene */}
        {isFinished ? (
          <>
            <div className="mb-4 text-center">
              <div className="mb-2 text-6xl">🌟</div>
              <h2 className="text-2xl font-bold text-purple-700">
                故事结束啦！
              </h2>
            </div>
            <div className="mb-4 rounded-3xl bg-white/80 p-5 shadow-lg backdrop-blur">
              <p className="whitespace-pre-wrap leading-relaxed text-gray-700">
                {sceneText}
              </p>
            </div>
            {summary && (
              <div className="mb-4 rounded-2xl bg-gradient-to-r from-amber-100 to-yellow-100 p-4">
                <h3 className="mb-1 text-sm font-bold text-amber-800">
                  故事总结
                </h3>
                <p className="text-sm text-amber-700">{summary}</p>
              </div>
            )}
            <div className="flex flex-col gap-3">
              <button
                onClick={() => router.push("/child/story-config")}
                className="w-full rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 py-4 text-lg font-bold text-white shadow-lg"
              >
                开始新故事 ✨
              </button>
              <button
                onClick={() => router.push("/child/home")}
                className="w-full rounded-2xl bg-white py-3 font-medium text-gray-600 shadow"
              >
                返回首页
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="mb-1 text-center text-xs font-medium text-purple-400">
              第 {sceneIndex + 1} 幕
            </div>
            <div className="mb-5 rounded-3xl bg-white/80 p-5 shadow-lg backdrop-blur">
              {sceneText ? (
                <p className="whitespace-pre-wrap leading-relaxed text-gray-700">
                  {sceneText}
                  {streaming && (
                    <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse rounded-sm bg-purple-400" />
                  )}
                </p>
              ) : streaming ? (
                <div className="flex items-center gap-2 text-purple-500">
                  <span className="inline-block h-4 w-1.5 animate-pulse rounded-sm bg-purple-400" />
                  <span className="text-sm">故事正在生成中...</span>
                </div>
              ) : null}
            </div>

            {!streaming && !loading && options.length > 0 && (
              <div className="space-y-3">
                <p className="text-center text-sm font-medium text-purple-600">
                  你想怎么做？
                </p>
                {options.map((opt) => (
                  <button
                    key={opt.key}
                    onClick={() => handleChoice(opt)}
                    className="w-full rounded-2xl bg-white p-4 text-left shadow-md transition hover:scale-[1.02] hover:shadow-lg"
                  >
                    <span className="mr-2 inline-flex h-8 w-8 items-center justify-center rounded-full bg-purple-100 text-sm font-bold text-purple-600">
                      {opt.key}
                    </span>
                    <span className="text-gray-800">{opt.text}</span>
                  </button>
                ))}
              </div>
            )}

            {streaming && !sceneText && (
              <div className="text-center">
                <div className="mb-2 text-5xl animate-bounce">✨</div>
                <p className="text-purple-600">准备故事中...</p>
              </div>
            )}
          </>
        )}
        <div ref={scrollRef} />
      </div>
    </div>
  );
}

export default function StoryPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-indigo-100 to-purple-100">
          <div className="text-center">
            <div className="mb-3 text-6xl animate-bounce">📖</div>
            <p className="text-xl text-purple-600">加载中...</p>
          </div>
        </div>
      }
    >
      <StoryContent />
    </Suspense>
  );
}
