"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Entry = { text: string; start: number; duration: number };

type TranscriptResp = {
  video_id: string;
  language: string;
  language_name: string;
  is_generated: boolean;
  entries: Entry[];
};

function formatTime(s: number) {
  const total = Math.floor(s);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const sec = total % 60;
  const pad = (n: number) => n.toString().padStart(2, "0");
  return h > 0 ? `${pad(h)}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<TranscriptResp | null>(null);
  const [showTimes, setShowTimes] = useState(true);

  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  async function handleFetch(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setData(null);
    setSummary(null);
    setSummaryError(null);
    if (!url.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/transcript`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Fehler beim Laden.");
      }
      setData(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload(format: "txt" | "srt" | "vtt") {
    if (!data) return;
    const res = await fetch(`${API}/api/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ entries: data.entries, format }),
    });
    if (!res.ok) return;
    const blob = await res.blob();
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `transcript.${format}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  async function handleSummary() {
    if (!data) return;
    setSummary(null);
    setSummaryError(null);
    setSummaryLoading(true);
    try {
      const text = data.entries.map((e) => e.text).join(" ");
      const res = await fetch(`${API}/api/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: text, language: data.language }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Zusammenfassung fehlgeschlagen.");
      }
      const json = await res.json();
      setSummary(json.summary);
    } catch (err) {
      setSummaryError(
        err instanceof Error ? err.message : "Unbekannter Fehler."
      );
    } finally {
      setSummaryLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">
          YouTube Transcript Generator
        </h1>
        <p className="mt-2 text-sm text-neutral-400">
          Link einfügen — das Transkript wird 1:1 von YouTube geholt.
        </p>
      </header>

      <form onSubmit={handleFetch} className="flex gap-2">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          className="flex-1 rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm outline-none focus:border-neutral-600"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
        >
          {loading ? "Lade…" : "Transkript holen"}
        </button>
      </form>

      {error && (
        <p className="mt-4 rounded-md border border-red-900 bg-red-950/50 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {data && (
        <section className="mt-8">
          <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-neutral-400">
            <span>Sprache: {data.language_name} ({data.language})</span>
            <span>·</span>
            <span>{data.is_generated ? "auto-generiert" : "manuell erstellt"}</span>
            <span>·</span>
            <span>{data.entries.length} Segmente</span>
            <div className="ml-auto flex items-center gap-2">
              <label className="flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={showTimes}
                  onChange={(e) => setShowTimes(e.target.checked)}
                />
                Zeitstempel
              </label>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleDownload("txt")}
              className="rounded-md border border-neutral-800 px-3 py-1 text-xs hover:bg-neutral-900"
            >
              .txt herunterladen
            </button>
            <button
              onClick={() => handleDownload("srt")}
              className="rounded-md border border-neutral-800 px-3 py-1 text-xs hover:bg-neutral-900"
            >
              .srt herunterladen
            </button>
            <button
              onClick={() => handleDownload("vtt")}
              className="rounded-md border border-neutral-800 px-3 py-1 text-xs hover:bg-neutral-900"
            >
              .vtt herunterladen
            </button>
            <button
              onClick={handleSummary}
              disabled={summaryLoading}
              className="ml-auto rounded-md border border-neutral-800 bg-neutral-900 px-3 py-1 text-xs hover:bg-neutral-800 disabled:opacity-50"
            >
              {summaryLoading ? "KI denkt nach…" : "KI-Zusammenfassung"}
            </button>
          </div>

          <div className="mt-4 rounded-md border border-neutral-800 bg-neutral-950 p-4">
            <div className="max-h-[60vh] space-y-2 overflow-y-auto text-sm leading-relaxed">
              {data.entries.map((entry, i) => (
                <div key={i} className="flex gap-3">
                  {showTimes && (
                    <span className="w-16 shrink-0 font-mono text-xs text-neutral-500">
                      {formatTime(entry.start)}
                    </span>
                  )}
                  <span>{entry.text}</span>
                </div>
              ))}
            </div>
          </div>

          {(summary || summaryError) && (
            <div className="mt-6 rounded-md border border-neutral-800 bg-neutral-950 p-4">
              <h2 className="mb-2 text-sm font-medium text-neutral-300">
                KI-Zusammenfassung
              </h2>
              {summaryError && (
                <p className="text-sm text-red-300">{summaryError}</p>
              )}
              {summary && (
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-200">
                  {summary}
                </p>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}
