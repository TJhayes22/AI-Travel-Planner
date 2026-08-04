import Link from "next/link";
import { getHealth } from "@/lib/api";

export default async function Home() {
  let backendOk = false;
  try {
    const health = await getHealth();
    backendOk = health.api === "ok" && health.database === "ok";
  } catch {
    backendOk = false;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-6">
      <div className="text-center">
        <p className="mb-2 font-data text-xs uppercase tracking-[0.2em] text-mist">
          AI Travel Planner
        </p>
        <h1 className="font-display text-2xl font-medium text-ink">
          Find a place worth going.
        </h1>
      </div>

      <Link
        href="/search"
        className="border border-navy px-5 py-2 font-data text-xs uppercase tracking-wider text-navy hover:bg-navy hover:text-paper"
      >
        Start searching →
      </Link>

      {/* Minimal dev status indicator -- not final landing-page content. */}
      <span
        className={`mt-8 font-data text-[11px] ${backendOk ? "text-mist" : "text-navy"}`}
      >
        {backendOk ? "· backend connected ·" : "· backend unreachable ·"}
      </span>
    </main>
  );
}