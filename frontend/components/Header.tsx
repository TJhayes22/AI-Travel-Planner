import Link from "next/link";

export function Header() {
  return (
    <header className="border-b border-mist/30 px-6 py-4">
      <Link
        href="/"
        className="font-data text-xs uppercase tracking-[0.2em] text-mist transition-colors hover:text-navy"
      >
        AI Travel Planner
      </Link>
    </header>
  );
}