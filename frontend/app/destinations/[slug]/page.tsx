import { notFound } from "next/navigation";
import Link from "next/link";
import { getDestination } from "@/lib/api";
import { CoordinateStamp } from "@/components/CoordinateStamp";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function DestinationPage({ params }: PageProps) {
  const { slug } = await params;
  const destination = await getDestination(slug);

  if (!destination) {
    notFound();
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <Link
        href="/search"
        className="mb-10 inline-block font-data text-xs uppercase tracking-wider text-navy hover:text-ink"
      >
        ← Back to search
      </Link>

      <header className="mb-8 border-b border-mist/30 pb-8">
        <p className="mb-2 font-data text-xs uppercase tracking-[0.2em] text-mist">
          {[destination.region, destination.country].filter(Boolean).join(" · ")}
        </p>
        <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">{destination.name}</h1>
        <div className="mt-3">
          <CoordinateStamp latitude={destination.latitude} longitude={destination.longitude} />
        </div>
      </header>

      {destination.tags.length > 0 && (
        <div className="mb-8 flex flex-wrap gap-1.5">
          {destination.tags.map((tag) => (
            <span
              key={tag}
              className="border border-mist/40 px-2 py-0.5 font-data text-[11px] uppercase tracking-wide text-slate"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {destination.description && (
        <p className="mb-10 font-body text-base leading-relaxed text-ink/85">
          {destination.description}
        </p>
      )}

      <dl className="mb-10 grid grid-cols-1 gap-6 border-y border-mist/30 py-6 sm:grid-cols-3">
        {destination.climate && (
          <div>
            <dt className="font-data text-[11px] uppercase tracking-wider text-mist">Climate</dt>
            <dd className="mt-1 font-body text-sm text-ink">{destination.climate}</dd>
          </div>
        )}
        {destination.best_season && (
          <div>
            <dt className="font-data text-[11px] uppercase tracking-wider text-mist">
              Best season
            </dt>
            <dd className="mt-1 font-body text-sm text-ink">{destination.best_season}</dd>
          </div>
        )}
        {destination.cost_tier && (
          <div>
            <dt className="font-data text-[11px] uppercase tracking-wider text-mist">
              Cost tier
            </dt>
            <dd className="mt-1 font-data text-sm text-navy">
              {"$".repeat(destination.cost_tier)}
            </dd>
          </div>
        )}
      </dl>

      {destination.listings.length > 0 && (
        <section>
          <h2 className="mb-4 font-display text-lg font-medium text-ink">Places to stay</h2>
          <ul className="flex flex-col gap-3">
            {destination.listings.map((listing) => (
              <li key={listing.id} className="border border-mist/30 bg-paper p-4">
                <div className="flex items-baseline justify-between">
                  <span className="font-body font-medium text-ink">{listing.name}</span>
                  {listing.rating && (
                    <span className="font-data text-sm text-navy">★ {listing.rating}</span>
                  )}
                </div>
                <div className="mt-1 flex items-center justify-between font-body text-sm text-slate">
                  <span className="capitalize">{listing.listing_type}</span>
                  {listing.price_amount && (
                    <span className="font-data">
                      {listing.currency} {listing.price_amount}/night
                    </span>
                  )}
                </div>
                <a
                  href={listing.booking_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-block font-data text-xs uppercase tracking-wider text-navy hover:text-ink"
                >
                  View / book →
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}