import Link from "next/link";
import { getFeaturedDestinations } from "@/lib/api";
import { CoordinateStamp } from "@/components/CoordinateStamp";
import { HeroSearchForm } from "@/components/HeroSearchForm";

const STEPS = [
  {
    label: "01",
    title: "Describe what you want",
    body: "No filters to configure. Just say what kind of trip you're after, in your own words.",
  },
  {
    label: "02",
    title: "Matched by meaning",
    body: "Your search is compared against every destination by what it actually is, not just keywords in a description.",
  },
  {
    label: "03",
    title: "Real places, ranked",
    body: "See how closely each result matches, then explore the details before you commit.",
  },
];

export default async function Home() {
  let featured: Awaited<ReturnType<typeof getFeaturedDestinations>> = [];
  try {
    featured = await getFeaturedDestinations(6);
  } catch {
    featured = [];
  }

  return (
    <main className="flex flex-col items-center">
      {/* Hero */}
      <section className="flex w-full flex-col items-center gap-6 px-6 py-24 text-center">
        <p className="font-data text-xs uppercase tracking-[0.2em] text-mist">
          AI Travel Planner
        </p>
        <h1 className="max-w-lg font-display text-3xl font-semibold text-ink sm:text-4xl">
          Find a place worth going.
        </h1>
        <p className="max-w-md font-body text-sm text-slate">
          Describe the trip you want. We match it against real destinations by meaning,
          not keywords.
        </p>
        <HeroSearchForm />
      </section>

      {/* How it works */}
      <section className="w-full border-y border-mist/30 bg-paper px-6 py-16">
        <div className="mx-auto grid max-w-3xl grid-cols-1 gap-10 sm:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.label}>
              <span className="font-data text-xs text-mist">{step.label}</span>
              <h2 className="mt-2 font-display text-lg font-medium text-ink">{step.title}</h2>
              <p className="mt-1 font-body text-sm leading-relaxed text-slate">{step.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Featured destinations */}
      {featured.length > 0 && (
        <section className="w-full max-w-3xl px-6 py-16">
          <p className="mb-6 font-data text-xs uppercase tracking-[0.2em] text-mist">
            From the log
          </p>
          <ul className="flex flex-col gap-4">
            {featured.map((dest) => (
              <li
                key={dest.id}
                className="border border-mist/30 bg-paper p-4 transition-colors hover:border-mist/60"
              >
                <h3 className="font-display text-lg font-medium text-ink">
                  <Link href={`/destinations/${dest.slug}`} className="hover:text-navy">
                    {dest.name}
                  </Link>
                </h3>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <p className="font-body text-sm text-slate">
                    {[dest.region, dest.country].filter(Boolean).join(", ")}
                  </p>
                  <CoordinateStamp latitude={dest.latitude} longitude={dest.longitude} />
                </div>
              </li>
            ))}
          </ul>
          <div className="mt-8 text-center">
            <Link
              href="/search"
              className="font-data text-xs uppercase tracking-wider text-navy hover:text-ink"
            >
              See more →
            </Link>
          </div>
        </section>
      )}
    </main>
  );
}