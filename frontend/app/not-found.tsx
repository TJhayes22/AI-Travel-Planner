import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <p className="font-data text-xs uppercase tracking-[0.2em] text-mist">
        Not found in the log
      </p>
      <h1 className="font-display text-3xl font-semibold text-ink">
        This page hasn&apos;t been charted.
      </h1>
      <p className="max-w-sm font-body text-sm text-slate">
        Whatever you were looking for doesn&apos;t exist, or hasn&apos;t been published yet.
      </p>
      <Link
        href="/search"
        className="mt-4 border border-navy px-5 py-2 font-data text-xs uppercase tracking-wider text-navy hover:bg-navy hover:text-paper"
      >
        Back to search →
      </Link>
    </main>
  );
}