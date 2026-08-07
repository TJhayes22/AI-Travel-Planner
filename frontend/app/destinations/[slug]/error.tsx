"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-2xl flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="font-data text-xs uppercase tracking-[0.2em] text-mist">
        Log entry unreadable
      </p>
      <h1 className="font-display text-2xl font-semibold text-ink">
        Couldn&apos;t load this destination.
      </h1>
      <p className="max-w-sm font-body text-sm text-slate">
        The backend didn&apos;t respond as expected. This is usually temporary.
      </p>
      <button
        onClick={reset}
        className="mt-2 border border-navy px-5 py-2 font-data text-xs uppercase tracking-wider text-navy hover:bg-navy hover:text-paper"
      >
        Try again →
      </button>
    </main>
  );
}