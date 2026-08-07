"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { SearchIconButton } from "./SearchIconButton";

export function HeroSearchForm() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl">
      <div className="group flex items-center gap-3 rounded-xl border border-mist/40 bg-paper px-5 py-4 shadow-sm transition-all focus-within:border-navy focus-within:shadow-md">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="quiet mountain town for hiking..."
          className="flex-1 bg-transparent font-body text-base text-ink placeholder:text-slate/60 focus:outline-none focus-visible:outline-none sm:text-lg"
          autoFocus
        />
        <SearchIconButton />
      </div>
    </form>
  );
}