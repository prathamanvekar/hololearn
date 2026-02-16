import { Bot, Send, Sparkles, UserRound, Volume2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import api from "../services/api";
import { useAppContext } from "../context/useAppContext";
import VoiceInput from "./VoiceInput";

export default function ChatInterface() {
  const { student, language, speakWithAvatar, loading } = useAppContext();
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Welcome to **HoloLearn**. Ask anything, upload your learning docs, and I will adapt to your pace.",
      translation:
        "**HoloLearn** में आपका स्वागत है। कुछ भी पूछें, अपनी पढ़ाई के दस्तावेज़ अपलोड करें, और मैं आपकी गति के अनुसार मदद करूँगा।",
      sources: [],
      createdAt: new Date().toISOString(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [sending, setSending] = useState(false);

  const messageEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  const canSend = useMemo(
    () => inputValue.trim().length > 0 && !sending,
    [inputValue, sending],
  );

  const resizeInput = () => {
    if (!inputRef.current) {
      return;
    }
    inputRef.current.style.height = "0px";
    inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 180)}px`;
  };

  useEffect(() => {
    resizeInput();
  }, [inputValue]);

  const handleSend = async () => {
    const content = inputValue.trim();
    if (!content || sending) {
      return;
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      createdAt: new Date().toISOString(),
    };

    setMessages((previous) => [...previous, userMessage]);
    setInputValue("");
    setSending(true);

    try {
      const response = await api.chat.sendMessage({
        student_id: student?.id,
        message: content,
        language: language.primary,
        bilingual: language.bilingual,
      });

      const assistantText =
        response?.response ||
        response?.message ||
        response?.answer ||
        "I received your message.";

      const translationText =
        response?.translation ||
        response?.translated_response ||
        response?.response_secondary ||
        null;

      const sources = Array.isArray(response?.sources)
        ? response.sources
        : Array.isArray(response?.citations)
          ? response.citations
          : [];

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: assistantText,
        translation: translationText,
        sources,
        createdAt: new Date().toISOString(),
      };

      setMessages((previous) => [...previous, assistantMessage]);

      const ttsLang = language.primary === "hi" ? "hi-IN" : "en-US";

      speakWithAvatar(assistantText, { lang: ttsLang });
    } catch {
      const fallback =
        "I couldn't reach the backend right now. Please check that FastAPI is running on port 8000.";
      setMessages((previous) => [
        ...previous,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: fallback,
          createdAt: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <section className="glass-panel h-full min-h-105 p-4 md:p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-slate-400">
            AI Conversation
          </p>
          <h3 className="text-lg font-semibold hologram-text">
            Chat Assistant
          </h3>
        </div>
        <span className="badge badge-cyan">
          {loading.speaking ? "Speaking" : "Ready"}
        </span>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto pr-1 space-y-3">
        {messages.map((message) => {
          const isUser = message.role === "user";
          return (
            <article
              key={message.id}
              className={`animate-fade-in flex ${isUser ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] flex gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}
              >
                <div
                  className={`h-8 w-8 rounded-full border flex items-center justify-center shrink-0 mt-1 ${
                    isUser
                      ? "bg-purple-500/25 border-purple-300/40 text-purple-100"
                      : "bg-slate-800/70 border-cyan-300/30 text-cyan-100"
                  }`}
                >
                  {isUser ? <UserRound size={15} /> : <Bot size={15} />}
                </div>

                <div
                  className={`rounded-2xl px-3.5 py-3 border ${
                    isUser
                      ? "bg-purple-500/16 border-purple-300/35"
                      : "bg-slate-900/55 border-white/12"
                  }`}
                >
                  <p className="text-xs text-slate-400 mb-1">
                    {isUser ? "You" : "HoloLearn AI"}
                  </p>
                  <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-pre:bg-slate-900/70">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>

                  {!isUser && language.bilingual && message.translation ? (
                    <div className="mt-3 border-t border-white/10 pt-2">
                      <p className="text-[11px] uppercase tracking-[0.12em] text-slate-400 mb-1">
                        Translation
                      </p>
                      <div className="text-sm text-slate-200">
                        <ReactMarkdown>{message.translation}</ReactMarkdown>
                      </div>
                    </div>
                  ) : null}

                  {!isUser &&
                  Array.isArray(message.sources) &&
                  message.sources.length > 0 ? (
                    <div className="mt-3 border-t border-white/10 pt-2">
                      <p className="text-[11px] uppercase tracking-[0.12em] text-slate-400 mb-1">
                        Sources
                      </p>
                      <ul className="space-y-1">
                        {message.sources.map((source, index) => {
                          const label =
                            typeof source === "string"
                              ? source
                              : source?.title ||
                                source?.name ||
                                source?.url ||
                                `Source ${index + 1}`;
                          const url =
                            typeof source === "object" ? source?.url : null;

                          return (
                            <li
                              key={`${message.id}-source-${index}`}
                              className="text-xs text-cyan-100/90"
                            >
                              {url ? (
                                <a
                                  href={url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="hover:underline"
                                >
                                  {label}
                                </a>
                              ) : (
                                <span>{label}</span>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ) : null}

                  {!isUser ? (
                    <div className="mt-3">
                      <button
                        type="button"
                        onClick={() =>
                          speakWithAvatar(message.content, {
                            lang:
                              language.primary === "en"
                                ? "en-US"
                                : `${language.primary}-IN`,
                          })
                        }
                        className="btn-ghost py-1.5 px-2.5 text-xs"
                      >
                        <Volume2 size={14} /> Speak
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            </article>
          );
        })}

        {sending ? (
          <article className="mr-8 animate-fade-in">
            <div className="rounded-2xl px-3.5 py-3 border bg-slate-900/55 border-white/12 inline-flex items-center gap-2">
              <Sparkles size={15} className="text-cyan-200" />
              <div className="loading-dots" aria-label="Assistant is thinking">
                <span />
                <span />
                <span />
              </div>
            </div>
          </article>
        ) : null}

        <div ref={messageEndRef} />
      </div>

      <form
        className="border-t border-white/10 pt-3"
        onSubmit={(event) => {
          event.preventDefault();
          handleSend();
        }}
      >
        <div className="flex items-end gap-2">
          <VoiceInput
            language={language.primary}
            onTranscript={(text) =>
              setInputValue((previous) => `${previous} ${text}`.trim())
            }
          />
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            rows={2}
            className="input-field resize-none"
            placeholder="Ask your tutor anything..."
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSend();
              }
            }}
          />
          <button
            type="submit"
            className="btn-primary"
            disabled={!canSend}
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </section>
  );
}
