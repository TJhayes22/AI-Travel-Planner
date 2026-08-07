"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { searchDestinations, SearchResultItem } from "@/lib/api";
import { CoordinateStamp } from "@/components/CoordinateStamp";
import { SearchIconButton } from "@/components/SearchIconButton";

function toFriendlyErrorMessage(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err);

  if (raw.toLowerCase().includes("failed to fetch")) {
    return "Couldn't reach the search service. Check your connection and try again.";
  }
  if (raw.includes("HTTP 5")) {
    return "The search service is having trouble right now. Try again in a moment.";
  }
  if (raw.includes("HTTP 4")) {
    return "That search couldn't be processed. Try rephrasing it.";
  }
  return "Something went wrong. Try again.";
}

type RequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; results: SearchResultItem[] };

function SearchPageInner() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";

  const [query, setQuery] = useState(initialQuery);
  const [state, setState] = useState<RequestState>({ status: "idle" });
  const hasAutoRun = useRef(false);

  const runSearch = useCallback(async (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) return;

    setState({ status: "loading" });
    try {
      const response = await searchDestinations(trimmed);
      setState({ status: "success", results: response.results });
    } catch (err) {
      setState({ status: "error", message: toFriendlyErrorMessage(err) });
    }
  }, []);

  useEffect(() => {
    if (initialQuery && !hasAutoRun.current) {
      hasAutoRun.current = true;
      runSearch(initialQuery);
    }
  }, [initialQuery, runSearch]);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    runSearch(query);
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <header className="mb-10">
        <p className="mb-1 font-data text-xs uppercase tracking-[0.2em] text-mist">
          Field log &mdash; destination search
        </p>
        <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">
          Where are you headed?
        </h1>
      </header>

      <form onSubmit={handleSubmit} className="mb-12">
        <div className="group flex items-center gap-3 rounded-xl border border-mist/40 bg-paper px-5 py-4 shadow-sm transition-all focus-within:border-navy focus-within:shadow-md">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="quiet mountain town for hiking..."
            className="flex-1 bg-transparent font-body text-base text-ink placeholder:text-slate/60 focus:outline-none focus-visible:outline-none sm:text-lg"
          />
          <SearchIconButton loading={state.status === "loading"} />
        </div>
      </form>

      {state.status === "loading" && (
        <ul className="flex flex-col gap-5" aria-label="Loading results">
          {[0, 1, 2].map((i) => (
            <li key={i} className="border border-mist/30 bg-paper p-5">
              <div className="mb-1 flex items-start justify-between gap-3">
                <div className="h-3 w-6 animate-pulse bg-mist/20" />
                <div className="h-3 w-16 animate-pulse bg-mist/20" />
              </div>
              <div className="mb-2 h-6 w-2/3 animate-pulse bg-mist/30" />
              <div className="mb-3 flex items-center gap-2">
                <div className="h-4 w-28 animate-pulse bg-mist/15" />
                <div className="h-4 w-24 animate-pulse bg-mist/15" />
              </div>
              <div className="space-y-1.5">
                <div className="h-3.5 w-full animate-pulse bg-mist/15" />
                <div className="h-3.5 w-full animate-pulse bg-mist/15" />
                <div className="h-3.5 w-2/3 animate-pulse bg-mist/15" />
              </div>
              <div className="mt-3 flex gap-1.5">
                <div className="h-5 w-14 animate-pulse bg-mist/15" />
                <div className="h-5 w-16 animate-pulse bg-mist/15" />
                <div className="h-5 w-12 animate-pulse bg-mist/15" />
              </div>
            </li>
          ))}
        </ul>
      )}

      {state.status === "error" && (
        <div className="border-l-2 border-navy/60 bg-paper p-4 font-body text-sm text-ink animate-fade-in">
          {state.message}
        </div>
      )}

      {state.status === "success" && state.results.length === 0 && (
        <p className="font-body text-sm text-slate animate-fade-in">No destinations matched that search.</p>
      )}

      {state.status === "success" && (
        <ul className="flex flex-col gap-5 animate-fade-in">
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

export default function SearchPage() {
  return (
    <Suspense fallback={null}>
      <SearchPageInner />
    </Suspense>
  );
}