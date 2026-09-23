"use client";

import * as React from "react";
import { useState, useRef, useEffect, useCallback } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  MessageSquareText,
  X,
  Send,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Sparkles,
  Bot,
  User,
  Lightbulb,
  ArrowRight,
  Maximize2,
  Minimize2,
} from "lucide-react";
import { assistantChat, assistantStream, listLectures, type AssistantChatResponse } from "@/lib/api";
import { cn } from "@/lib/format";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  evidence?: Array<{ time?: string; type?: string; snippet?: string }>;
  isStreaming?: boolean;
}

const QUICK_PROMPTS = [
  "What am I looking at right now?",
  "Explain this section simply",
  "What was shown but not explained?",
  "Give me a quiz hint",
  "Turn on captions",
  "Turn on audio descriptions",
];

const SELECTED_LECTURE_STORAGE_KEY = "eduaccess:selected-lecture-id";

function getClientSearchParams(): URLSearchParams | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search);
}

function resolveActiveJob(pathname: string): string | null {
  // 1. Path match: /lectures/:jobId (excluding index, new, upload)
  const routeMatch = pathname.match(/^\/lectures\/([^\/?#]+)/);
  if (routeMatch && routeMatch[1] && !["page", "new", "upload"].includes(routeMatch[1])) {
    return decodeURIComponent(routeMatch[1]);
  }

  // 2. Query param ONLY when on lecture or quiz route: ?job=..., ?jobId=...
  if (pathname.startsWith("/lectures") || pathname.startsWith("/quiz")) {
    const searchParams = getClientSearchParams();
    if (searchParams) {
      const qJob =
        searchParams.get("job") ||
        searchParams.get("jobId") ||
        searchParams.get("lecture_id") ||
        searchParams.get("id");
      if (qJob) return qJob;
    }
  }

  return null;
}

export default function GlobalAssistant() {
  const pathname = usePathname() ?? "/";
  const router = useRouter();

  const [isOpen, setIsOpen] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(() =>
    resolveActiveJob(pathname)
  );
  const [currentTime, setCurrentTime] = useState<number>(0);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi! I'm EduAccess AI, your accessible learning companion. Ask me anything about educational topics, code, or your lectures!",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const handleSendRef = useRef<(customText?: string) => Promise<void>>(async () => {});

  // Synchronize active job ID dynamically across navigation:
  // Clears to null when the user navigates away from a lecture to general pages.
  useEffect(() => {
    const resolved = resolveActiveJob(pathname);
    setActiveJobId(resolved);
    if (!resolved) {
      setCurrentTime(0);
    }
  }, [pathname]);

  // Window event listeners for real-time lecture changes & video time updates
  useEffect(() => {
    if (typeof window === "undefined") return;

    const onLectureChange = (e: Event) => {
      const customEvent = e as CustomEvent<{ jobId?: string | null }>;
      if (typeof customEvent.detail?.jobId !== "undefined") {
        setActiveJobId(customEvent.detail.jobId);
      }
    };

    const onTimeUpdate = (e: Event) => {
      const customEvent = e as CustomEvent<{ time?: number; jobId?: string }>;
      if (typeof customEvent.detail?.time === "number") {
        setCurrentTime(customEvent.detail.time);
      }
      if (customEvent.detail?.jobId) {
        setActiveJobId(customEvent.detail.jobId);
      }
    };

    window.addEventListener("eduaccess:lecture-change", onLectureChange);
    window.addEventListener("eduaccess:timeupdate", onTimeUpdate);

    return () => {
      window.removeEventListener("eduaccess:lecture-change", onLectureChange);
      window.removeEventListener("eduaccess:timeupdate", onTimeUpdate);
    };
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  // Speech recognition initialization
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const reco = new SpeechRecognition();
        reco.continuous = false;
        reco.interimResults = false;
        reco.lang = document.documentElement.lang === "ar" ? "ar-EG" : "en-US";
        reco.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          if (transcript) {
            setInputValue(transcript);
            handleSendRef.current(transcript);
          }
        };
        reco.onerror = () => setIsListening(false);
        reco.onend = () => setIsListening(false);
        recognitionRef.current = reco;
      }
    }
  }, []);

  const toggleMic = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch {
        setIsListening(false);
      }
    }
  };

  const speakText = (text: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = document.documentElement.lang === "ar" ? "ar-EG" : "en-US";
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleSend = async (customText?: string) => {
    const textToSend = (customText || inputValue).trim();
    if (!textToSend || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: textToSend,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsLoading(true);

    const activeJob = activeJobId || resolveActiveJob(pathname);

    const contextPayload = {
      page: pathname,
      lecture_id: activeJob || undefined,
      job_id: activeJob || undefined,
      timestamp: currentTime,
    };

    try {
      // Streaming assistant response
      const assistantId = (Date.now() + 2).toString();
      let streamedContent = "";
      let finalAction: string | undefined;
      let finalActionPayload: Record<string, unknown> | undefined;

      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          isStreaming: true,
        },
      ]);

      for await (const chunk of assistantStream({
        message: textToSend,
        context: contextPayload,
      })) {
        if (chunk.token) {
          streamedContent += chunk.token;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantId
                ? { ...msg, content: streamedContent }
                : msg
            )
          );
        }
        if (chunk.action) {
          finalAction = chunk.action;
          finalActionPayload = chunk.action_payload;
        }
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? {
                ...msg,
                content: streamedContent || "I could not retrieve an answer for that moment.",
                isStreaming: false,
              }
            : msg
        )
      );
      setIsLoading(false);

      if (speechEnabled && streamedContent) {
        speakText(streamedContent);
      }

      if (finalAction) {
        executeAssistantAction(finalAction, finalActionPayload);
      }
    } catch {
      try {
        const res = await assistantChat({
          message: textToSend,
          context: contextPayload,
        });
        const botMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: res.reply,
          evidence: res.evidence,
        };
        setMessages((prev) => [...prev.filter((m) => !m.isStreaming), botMsg]);
        if (speechEnabled && res.reply) speakText(res.reply);
        if (res.action) executeAssistantAction(res.action, res.action_payload);
      } catch (err) {
        setMessages((prev) => [
          ...prev.filter((m) => !m.isStreaming),
          {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: "Sorry, I had trouble retrieving that right now. Please try again!",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  handleSendRef.current = handleSend;

  const executeAssistantAction = (action: string, payload?: any) => {
    if (action === "navigate") {
      if (payload?.path) router.push(payload.path);
    } else if (action === "seek") {
      if (typeof payload?.seconds === "number") {
        window.dispatchEvent(
          new CustomEvent("eduaccess:seek", { detail: { seconds: payload.seconds } })
        );
      }
    } else if (action === "toggle_captions") {
      window.dispatchEvent(
        new CustomEvent("eduaccess:toggle_captions", { detail: { enabled: payload?.enabled } })
      );
    } else if (action === "toggle_audio_description") {
      window.dispatchEvent(
        new CustomEvent("eduaccess:toggle_audio_description", {
          detail: { enabled: payload?.enabled },
        })
      );
    } else if (action === "font_size") {
      window.dispatchEvent(
        new CustomEvent("eduaccess:font_size", { detail: { delta: payload?.delta } })
      );
    } else if (action === "open_quiz") {
      const match = pathname.match(/\/lectures\/([^\/]+)/);
      if (match) {
        router.push("/quiz");
      }
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="EduAccess AI Assistant"
        className={cn(
          "eduaccess-assistant-trigger fixed bottom-6 right-6 z-50 flex size-14 items-center justify-center rounded-full shadow-lg transition-all duration-300 focus:outline-none focus:ring-4 focus:ring-[#B85C38]/30 cursor-pointer",
          isOpen
            ? "bg-[#3F352E] text-white rotate-90 scale-95"
            : "bg-gradient-to-br from-[#B85C38] via-[#C97858] to-[#6C63A8] text-white hover:scale-105 shadow-[#B85C38]/30"
        )}
      >
        {isOpen ? (
          <X className="size-6" />
        ) : (
          <div className="relative">
            <MessageSquareText className="size-6" />
            <span className="absolute -top-1 -right-1 flex size-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#5F8A62] opacity-75"></span>
              <span className="relative inline-flex rounded-full size-3 bg-[#5F8A62]"></span>
            </span>
          </div>
        )}
      </button>

      {/* Floating Chat Drawer */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="EduAccess AI Assistant Dialog"
          className="eduaccess-assistant-panel fixed bottom-24 right-6 z-50 flex h-[580px] w-[380px] sm:w-[420px] flex-col rounded-3xl border border-[#E4D9CC] bg-[#FFFDFC]/98 shadow-2xl backdrop-blur-xl transition-all duration-300 overflow-hidden text-[#2F2924]"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#E7DED2] bg-[#FBF8F2] px-4 py-3.5">
            <div className="flex items-center gap-2.5">
              <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#B85C38] to-[#6C63A8] text-white shadow-xs">
                <Sparkles className="size-4" />
              </div>
              <div>
                <p className="text-sm font-bold text-[#2F2924] flex items-center gap-1.5">
                  EduAccess Assistant
                  {activeJobId ? (
                    <span className="rounded-full bg-[#E4F0E5] border border-[#B9D2BC] px-1.5 py-0.5 text-[10px] font-bold text-[#416A47] font-mono truncate max-w-[120px]">
                      {activeJobId}
                    </span>
                  ) : (
                    <span className="rounded-full bg-[#F5EFE6] border border-[#DDD0C0] px-1.5 py-0.5 text-[10px] font-medium text-[#7A7067]">
                      General AI
                    </span>
                  )}
                </p>
                <p className="text-[10.5px] text-[#7A7067]">
                  {activeJobId
                    ? `Bound to active lecture context (${currentTime.toFixed(0)}s)`
                    : "General educational AI assistant"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setSpeechEnabled(!speechEnabled)}
                aria-label={speechEnabled ? "Mute audio narration" : "Enable spoken responses"}
                className={cn(
                  "rounded-lg p-1.5 transition-colors cursor-pointer",
                  speechEnabled
                    ? "bg-[#B85C38]/15 text-[#B85C38]"
                    : "text-[#7A7067] hover:text-[#2F2924]"
                )}
              >
                {speechEnabled ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                aria-label="Close Assistant"
                className="rounded-lg p-1.5 text-[#7A7067] hover:bg-[#F1E8DC] hover:text-[#2F2924] transition-colors cursor-pointer"
              >
                <X className="size-4" />
              </button>
            </div>
          </div>

          {/* Quick Prompts Bar */}
          <div className="border-b border-[#E7DED2] bg-[#FBF8F2]/60 px-3 py-2 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                disabled={isLoading}
                className="whitespace-nowrap rounded-full border border-[#DDD0C0] bg-[#FFFDFC] px-2.5 py-1 text-[11px] font-medium text-[#51483F] hover:border-[#B85C38] hover:text-[#B85C38] hover:bg-[#FFF8F4] transition shadow-2xs cursor-pointer disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {messages.map((m) => (
              <div
                key={m.id}
                className={cn(
                  "flex gap-2.5 max-w-[88%]",
                  m.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                <div
                  className={cn(
                    "flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold shadow-xs",
                    m.role === "user"
                      ? "bg-[#3F352E] text-white"
                      : "bg-[#B85C38] text-white"
                  )}
                >
                  {m.role === "user" ? <User className="size-3.5" /> : <Bot className="size-3.5" />}
                </div>

                <div
                  className={cn(
                    "rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed shadow-xs",
                    m.role === "user"
                      ? "bg-[#B85C38] text-white rounded-tr-xs"
                      : "bg-[#F1E8DC] text-[#2F2924] border border-[#DDD0C0] rounded-tl-xs"
                  )}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  {m.isStreaming && (
                    <span className="inline-block w-1.5 h-3 ml-1 bg-[#B85C38] animate-pulse" />
                  )}

                  {m.evidence && m.evidence.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-[#DDD0C0]/80 space-y-1">
                      <p className="text-[10px] font-bold text-[#7A7067] uppercase tracking-wider">
                        Lecture Evidence:
                      </p>
                      {m.evidence.map((ev, i) => (
                        <div key={i} className="text-[11px] text-[#51483F] flex items-start gap-1">
                          {ev.time && (
                            <span className="font-mono text-[#B85C38] bg-[#FFF8F4] border border-[#E8C2B2] px-1 rounded text-[10px] font-bold">
                              {ev.time}
                            </span>
                          )}
                          <span className="truncate">{ev.snippet}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {m.role === "assistant" && m.content && !m.isStreaming && (
                    <div className="mt-1.5 flex justify-end">
                      <button
                        onClick={() => speakText(m.content)}
                        aria-label="Read response aloud"
                        className="text-[11px] text-[#7A7067] hover:text-[#2F2924] flex items-center gap-1 transition cursor-pointer"
                      >
                        <Volume2 className="size-3" /> Read
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="border-t border-[#E7DED2] bg-[#FFFDFC] p-3">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2 rounded-2xl border border-[#DDD0C0] bg-[#FBF8F2] px-3 py-1.5 focus-within:border-[#B85C38] focus-within:ring-2 focus-within:ring-[#B85C38]/20 transition"
            >
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={isListening ? "Listening..." : "Ask EduAccess AI anything..."}
                disabled={isLoading}
                className="flex-1 bg-transparent text-xs text-[#2F2924] placeholder:text-[#8C8177] focus:outline-none"
              />

              <button
                type="button"
                onClick={toggleMic}
                aria-label={isListening ? "Stop listening" : "Speech input"}
                className={cn(
                  "p-1.5 rounded-lg transition cursor-pointer",
                  isListening
                    ? "bg-[#B94A48] text-white animate-pulse"
                    : "text-[#7A7067] hover:text-[#2F2924]"
                )}
              >
                {isListening ? <MicOff className="size-4" /> : <Mic className="size-4" />}
              </button>

              <button
                type="submit"
                disabled={isLoading || !inputValue.trim()}
                aria-label="Send message"
                className="flex size-7 items-center justify-center rounded-xl bg-[#B85C38] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#9F4F32] transition shadow-xs cursor-pointer"
              >
                <Send className="size-3.5" />
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
