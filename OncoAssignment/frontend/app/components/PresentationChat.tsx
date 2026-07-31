"use client";

import {
  Activity,
  BookOpen,
  CheckCircle2,
  CircleStop,
  FileText,
  Gavel,
  History,
  Microscope,
  Play,
  Radio,
  RefreshCw,
  Stethoscope
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

type CaseImage = {
  file: string;
  caption: string;
  src: string;
};

type CaseData = {
  id: string;
  title: string;
  source: string;
  case_packet: {
    clinical_summary: string;
    imaging_findings: string;
    pathology_report: string;
  };
  images: CaseImage[];
};

type StreamMessage = {
  id: string;
  type: "status" | "section" | "done" | "error";
  title?: string;
  speaker?: string;
  content?: string;
};

type LogEvent = {
  agent: string;
  node: string;
  speaker: string;
  title: string;
  model: string;
  duration_s: number;
  elapsed_s: number;
  content: string;
};

type LogPayload = {
  case_id: string;
  stamp: string;
  started: string;
  total_seconds: number;
  events: LogEvent[];
};

type Mode = "replay" | "live";

type PresentationChatProps = {
  cases: CaseData[];
};

const speakerIcon = {
  Pathologist: Microscope,
  Oncologist: Stethoscope,
  Board: Activity,
  "Board Chair": Gavel,
};

// Short slug labels for the sidebar
const CASE_LABELS: Record<string, { tag: string; subtitle: string }> = {
  nsclc_egfr_l858r_advanced: {
    tag: "NSCLC",
    subtitle: "EGFR L858R · Text"
  },
  breast_her2_equivocal_then_fish_positive: {
    tag: "Breast",
    subtitle: "HER2 IHC→FISH · Text"
  },
  synchronous_sclc_nsclc: {
    tag: "SCLC+NSCLC",
    subtitle: "Dual Lesion · Image"
  }
};

function uid(suffix: string | number = "") {
  return `${Date.now()}-${suffix}-${Math.random().toString(16).slice(2)}`;
}

function parseSseChunk(buffer: string): {
  events: StreamMessage[];
  rest: string;
} {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  const events = parts
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => part.replace(/^data:\s*/, ""))
    .map((payload) => JSON.parse(payload) as Omit<StreamMessage, "id">)
    .map((event, index) => ({
      ...event,
      id: uid(index)
    }));

  return { events, rest };
}

function SpeakerBadge({ speaker }: { speaker?: string }) {
  if (!speaker) {
    return (
      <span className="message-badge neutral">
        <FileText size={14} aria-hidden="true" />
        System
      </span>
    );
  }

  const Icon = speakerIcon[speaker as keyof typeof speakerIcon] ?? BookOpen;
  const cssKey = speaker.toLowerCase().replace(/\s+/g, "-");
  return (
    <span className={`message-badge ${cssKey}`}>
      <Icon size={14} aria-hidden="true" />
      {speaker}
    </span>
  );
}

function Message({ message }: { message: StreamMessage }) {
  const useMarkdown =
    message.type === "section" || message.type === "done";

  return (
    <article className={`message ${message.type}`}>
      <div className="message-header">
        <SpeakerBadge speaker={message.speaker} />
        {message.title ? <h3>{message.title}</h3> : null}
      </div>
      {message.content ? (
        useMarkdown ? (
          <div className="message-body prose">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        ) : (
          <p>{message.content}</p>
        )
      ) : null}
    </article>
  );
}

const READY_REPLAY: StreamMessage = {
  id: "intro-replay",
  type: "status",
  title: "Replay",
  content: "Loading the most recent saved run for this case…"
};

const READY_LIVE: StreamMessage = {
  id: "intro-live",
  type: "status",
  title: "Ready",
  content:
    "Live mode: press Stream to run the two-agent tumor board protocol in real time."
};

export function PresentationChat({ cases }: PresentationChatProps) {
  const [selectedId, setSelectedId] = useState(cases[0]?.id ?? "");
  const [mode, setMode] = useState<Mode>("replay");
  const [messages, setMessages] = useState<StreamMessage[]>([READY_REPLAY]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingLog, setIsLoadingLog] = useState(false);
  const [loadedStamp, setLoadedStamp] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const reqRef = useRef(0);

  const selectedCase = cases.find((c) => c.id === selectedId) ?? cases[0];

  const imageCountLabel = useMemo(
    () =>
      selectedCase.images.length === 0
        ? "No images (text-only case)"
        : `${selectedCase.images.length} pathology source image${selectedCase.images.length === 1 ? "" : "s"}`,
    [selectedCase.images.length]
  );

  useEffect(() => {
    transcriptRef.current?.scrollTo({
      top: transcriptRef.current.scrollHeight,
      behavior: "smooth"
    });
  }, [messages]);

  // Replay: load the latest saved run for a case (instant render)
  const loadLatest = useCallback(
    async (caseId: string) => {
      const reqId = ++reqRef.current;
      setIsLoadingLog(true);
      setLoadedStamp(null);
      setMessages([READY_REPLAY]);
      try {
        const res = await fetch(`/api/log?case_id=${encodeURIComponent(caseId)}`, {
          cache: "no-store"
        });
        const data = (await res.json()) as LogPayload & { error?: string };
        if (reqId !== reqRef.current) return; // a newer request superseded this one
        if (!res.ok || data.error) {
          setMessages([
            {
              id: uid("noerr"),
              type: "error",
              title: "No saved run",
              content: data.error ?? "Could not load the latest run."
            }
          ]);
          return;
        }

        const header: StreamMessage = {
          id: uid("hdr"),
          type: "status",
          title: "Replay — saved run",
          content: `Loaded run ${data.stamp} · started ${data.started} · ${data.events.length} turns · ${data.total_seconds}s`
        };
        const sections: StreamMessage[] = data.events.map((e, i) => ({
          id: uid(i),
          type: "section",
          speaker: e.speaker,
          title: e.title,
          content: e.content
        }));
        const done: StreamMessage = {
          id: uid("done"),
          type: "done",
          speaker: "Board",
          title: "Replay complete",
          content: `Saved transcript for **${data.case_id}** (run ${data.stamp}).`
        };
        setLoadedStamp(data.stamp);
        setMessages([header, ...sections, done]);
      } catch (error) {
        if (reqId !== reqRef.current) return;
        setMessages([
          {
            id: uid("err"),
            type: "error",
            title: "Replay error",
            content:
              error instanceof Error ? error.message : "Unknown error loading the run."
          }
        ]);
      } finally {
        if (reqId === reqRef.current) setIsLoadingLog(false);
      }
    },
    []
  );

  // Replay mode always points to the latest run for the selected case.
  useEffect(() => {
    if (mode !== "replay") return;
    void loadLatest(selectedId);
  }, [mode, selectedId, loadLatest]);

  function selectCase(id: string) {
    if (isStreaming) return;
    setSelectedId(id);
    if (mode === "live") {
      setMessages([READY_LIVE]);
    }
    // replay mode auto-loads via the effect above
  }

  function switchMode(next: Mode) {
    if (isStreaming || next === mode) return;
    setMode(next);
    if (next === "live") {
      setLoadedStamp(null);
      setMessages([READY_LIVE]);
    }
    // replay mode auto-loads via the effect above
  }

  async function startStream() {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setIsStreaming(true);
    setMessages([
      {
        id: "user-start",
        type: "status",
        title: "Prompt",
        content: `Run the tumor board presentation for: ${selectedCase.title}`
      }
    ]);

    try {
      const response = await fetch("/api/presentation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: selectedCase.id }),
        signal: controller.signal
      });

      if (!response.ok || !response.body) {
        throw new Error("Presentation stream failed to start.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parsed = parseSseChunk(buffer);
        buffer = parsed.rest;
        if (parsed.events.length > 0) {
          setMessages((current) => [...current, ...parsed.events]);
        }
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        setMessages((current) => [
          ...current,
          {
            id: `error-${Date.now()}`,
            type: "error",
            title: "Stream Error",
            content:
              error instanceof Error ? error.message : "Unknown streaming error"
          }
        ]);
      }
    } finally {
      setIsStreaming(false);
    }
  }

  function stopStream() {
    abortRef.current?.abort();
    setIsStreaming(false);
    setMessages((current) => [
      ...current,
      {
        id: `stopped-${Date.now()}`,
        type: "status",
        title: "Stopped",
        content: "The presentation stream was stopped."
      }
    ]);
  }

  const busy = isStreaming || isLoadingLog;

  return (
    <main className="app-shell">
      {/* Case selector sidebar */}
      <nav className="case-sidebar" aria-label="Case selector">
        <span className="eyebrow sidebar-label">Cases</span>
        {cases.map((c) => {
          const meta = CASE_LABELS[c.id];
          return (
            <button
              key={c.id}
              className={`case-tab${selectedId === c.id ? " active" : ""}${isStreaming ? " disabled" : ""}`}
              onClick={() => selectCase(c.id)}
              aria-current={selectedId === c.id ? "true" : undefined}
              disabled={isStreaming}
            >
              <span className="case-tab-tag">{meta?.tag ?? c.id}</span>
              <span className="case-tab-sub">{meta?.subtitle ?? ""}</span>
            </button>
          );
        })}
      </nav>

      {/* Case packet panel */}
      <aside className="case-panel" aria-label="Case packet">
        <div className="case-heading">
          <span className="eyebrow">Case Packet</span>
          <h1>{selectedCase.title}</h1>
          <a href={selectedCase.source} target="_blank" rel="noreferrer">
            Source article
          </a>
        </div>

        <section className="packet-section">
          <h2>Clinical Summary</h2>
          <p>{selectedCase.case_packet.clinical_summary}</p>
        </section>

        <section className="packet-section">
          <h2>Imaging Findings</h2>
          <p>{selectedCase.case_packet.imaging_findings}</p>
        </section>

        <section className="packet-section">
          <h2>Pathology Report</h2>
          <pre>{selectedCase.case_packet.pathology_report}</pre>
        </section>

        <section className="image-section">
          <div className="image-section-header">
            <h2>Images</h2>
            <span>{imageCountLabel}</span>
          </div>
          <div className="image-grid">
            {selectedCase.images.map((image) => (
              <figure key={image.file}>
                <img src={image.src} alt={image.caption} />
                <figcaption>{image.caption}</figcaption>
              </figure>
            ))}
          </div>
        </section>
      </aside>

      {/* Chat / stream panel */}
      <section className="chat-panel" aria-label="Streaming presentation chat">
        <header className="chat-header">
          <div>
            <span className="eyebrow">LangGraph Protocol</span>
            <h2>Tumor Board Presentation Stream</h2>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            {/* Mode toggle */}
            <div
              role="group"
              aria-label="Source mode"
              style={{
                display: "inline-flex",
                border: "1px solid var(--border, #d8dee9)",
                borderRadius: 999,
                overflow: "hidden"
              }}
            >
              <button
                type="button"
                onClick={() => switchMode("replay")}
                disabled={isStreaming}
                aria-pressed={mode === "replay"}
                style={modeBtnStyle(mode === "replay")}
              >
                <History size={14} aria-hidden="true" />
                Replay
              </button>
              <button
                type="button"
                onClick={() => switchMode("live")}
                disabled={isStreaming}
                aria-pressed={mode === "live"}
                style={modeBtnStyle(mode === "live")}
              >
                <Radio size={14} aria-hidden="true" />
                Live
              </button>
            </div>

            <div className="status-pill" aria-live="polite">
              {isStreaming ? (
                <>
                  <Activity size={15} aria-hidden="true" />
                  Streaming
                </>
              ) : isLoadingLog ? (
                <>
                  <RefreshCw size={15} aria-hidden="true" />
                  Loading
                </>
              ) : (
                <>
                  <CheckCircle2 size={15} aria-hidden="true" />
                  {mode === "replay" ? "Replay" : "Ready"}
                </>
              )}
            </div>
          </div>
        </header>

        <div className="transcript" ref={transcriptRef}>
          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}
        </div>

        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            if (mode === "live") {
              void startStream();
            } else {
              void loadLatest(selectedId);
            }
          }}
        >
          <label htmlFor="presentation-prompt">
            {mode === "live"
              ? "Presentation prompt (live execution)"
              : `Saved run${loadedStamp ? ` · ${loadedStamp}` : " · latest"}`}
          </label>
          <div className="composer-row">
            <input
              id="presentation-prompt"
              readOnly
              value={
                mode === "live"
                  ? `Run the tumor board presentation: ${selectedCase.title}`
                  : `Replay latest saved run: ${selectedCase.title}`
              }
            />
            {mode === "live" ? (
              isStreaming ? (
                <button type="button" className="secondary" onClick={stopStream}>
                  <CircleStop size={18} aria-hidden="true" />
                  Stop
                </button>
              ) : (
                <button type="submit">
                  <Play size={18} aria-hidden="true" />
                  Stream
                </button>
              )
            ) : (
              <button type="submit" disabled={busy}>
                <RefreshCw size={18} aria-hidden="true" />
                Reload latest
              </button>
            )}
          </div>
        </form>
      </section>
    </main>
  );
}

function modeBtnStyle(active: boolean): React.CSSProperties {
  return {
    display: "inline-flex",
    alignItems: "center",
    gap: "0.35rem",
    padding: "0.35rem 0.8rem",
    fontSize: "0.85rem",
    fontWeight: 600,
    border: "none",
    cursor: "pointer",
    background: active ? "var(--accent, #0e7490)" : "transparent",
    color: active ? "#ffffff" : "var(--muted, #64748b)"
  };
}
