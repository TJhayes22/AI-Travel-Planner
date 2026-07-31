"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { searchDestinations, SearchResultItem } from "@/lib/api";

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
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-6 text-2xl font-semibold">Find a destination</h1>

      <form onSubmit={handleSubmit} className="mb-8 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. quiet mountain town for hiking"
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={state.status === "loading"}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {state.status === "loading" ? "Searching..." : "Search"}
        </button>
      </form>

      {state.status === "error" && (
        <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          {state.message}
        </div>
      )}

      {state.status === "success" && state.results.length === 0 && (
        <p className="text-sm text-gray-500">No destinations matched that search.</p>
      )}

      {state.status === "success" && (
        <ul className="flex flex-col gap-4">
          {state.results.map((dest) => (
            <li key={dest.id} className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-baseline justify-between">
                <h2 className="text-lg font-medium">
                  <Link href={`/destinations/${dest.slug}`} className="hover:underline">
                    {dest.name}
                  </Link>
                </h2>
                <span className="text-xs text-gray-400">
                  match: {(dest.similarity_score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-sm text-gray-500">
                {[dest.region, dest.country].filter(Boolean).join(", ")}
              </p>
              {dest.description && (
                <p className="mt-2 text-sm text-gray-700">{dest.description}</p>
              )}
              {dest.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {dest.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
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