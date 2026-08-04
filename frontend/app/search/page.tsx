"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { searchDestinations, SearchResultItem } from "@/lib/api";
import { CoordinateStamp } from "@/components/CoordinateStamp";

type RequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; results: SearchResultItem[] };

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<RequestState>({ status: "idle" });

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    const trimmed = query.trim();
    if (!trimmed) return;

    setState({ status: "loading" });

    try {
      const response = await searchDestinations(trimmed);
      setState({ status: "success", results: response.results });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Something went wrong.",
      });
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <header className="mb-10">
        <p className="mb-1 font-data text-xs uppercase tracking-[0.2em] text-mist">
          Field log &mdash; destination search
        </p>
        <h1 className="font-display text-4xl font-semibold text-ink">
          Where are you headed?
        </h1>
      </header>

      <form onSubmit={handleSubmit} className="mb-12">
        <div className="flex items-end gap-3 border-b-2 border-ink pb-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="quiet mountain town for hiking..."
            className="flex-1 bg-transparent font-body text-lg text-ink placeholder:text-slate/60 focus:outline-none"
          />
          <button
            type="submit"
            disabled={state.status === "loading"}
            className="font-data text-xs uppercase tracking-wider text-navy hover:text-ink disabled:opacity-40"
          >
            {state.status === "loading" ? "Searching..." : "Search →"}
          </button>
        </div>
      </form>

      {state.status === "error" && (
        <div className="border-l-2 border-navy/60 bg-paper p-4 font-body text-sm text-ink">
          {state.message}
        </div>
      )}

      {state.status === "success" && state.results.length === 0 && (
        <p className="font-body text-sm text-slate">No destinations matched that search.</p>
      )}

      {state.status === "success" && (
        <ul className="flex flex-col gap-5">
          {state.results.map((dest, i) => (
            <li
              key={dest.id}
              className="border border-mist/30 bg-paper p-5 transition-colors hover:border-mist/60"
            >
              <div className="mb-1 flex items-start justify-between gap-3">
                <span className="font-data text-xs text-mist">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="font-data text-xs uppercase tracking-wider text-navy">
                  match {Math.round(dest.similarity_score * 100)}
                </span>
              </div>

              <h2 className="font-display text-xl font-medium text-ink">
                <Link href={`/destinations/${dest.slug}`} className="hover:text-navy">
                  {dest.name}
                </Link>
              </h2>

              <div className="mt-1 flex items-center gap-2">
                <p className="font-body text-sm text-slate">
                  {[dest.region, dest.country].filter(Boolean).join(", ")}
                </p>
                <CoordinateStamp latitude={dest.latitude} longitude={dest.longitude} />
              </div>

              {dest.description && (
                <p className="mt-3 font-body text-sm leading-relaxed text-ink/80">
                  {dest.description}
                </p>
              )}

              {dest.tags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {dest.tags.map((tag) => (
                    <span
                      key={tag}
                      className="border border-mist/40 px-2 py-0.5 font-data text-[11px] uppercase tracking-wide text-slate"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}