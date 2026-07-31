import { notFound } from "next/navigation";
import Link from "next/link";
import { getDestination } from "@/lib/api";

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
    <main className="mx-auto max-w-2xl p-8">
      <Link href="/search" className="mb-6 inline-block text-sm text-blue-600 hover:underline">
        &larr; Back to search
      </Link>

      <h1 className="text-3xl font-semibold">{destination.name}</h1>
      <p className="mt-1 text-gray-500">
        {[destination.region, destination.country].filter(Boolean).join(", ")}
      </p>

      {destination.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {destination.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {destination.description && (
        <p className="mt-6 text-gray-700 leading-relaxed">{destination.description}</p>
      )}

      <dl className="mt-6 grid grid-cols-2 gap-4 text-sm">
        {destination.climate && (
          <div>
            <dt className="text-gray-400">Climate</dt>
            <dd className="text-gray-700">{destination.climate}</dd>
          </div>
        )}
        {destination.best_season && (
          <div>
            <dt className="text-gray-400">Best time to visit</dt>
            <dd className="text-gray-700">{destination.best_season}</dd>
          </div>
        )}
        {destination.cost_tier && (
          <div>
            <dt className="text-gray-400">Cost tier</dt>
            <dd className="text-gray-700">{"$".repeat(destination.cost_tier)}</dd>
          </div>
        )}
      </dl>

      {destination.listings.length > 0 && (
        <section className="mt-8">
          <h2 className="mb-3 text-lg font-medium">Places to stay</h2>
          <ul className="flex flex-col gap-3">
            {destination.listings.map((listing) => (
              <li key={listing.id} className="rounded-lg border border-gray-200 p-4">
                <div className="flex items-baseline justify-between">
                  <span className="font-medium">{listing.name}</span>
                  {listing.rating && (
                    <span className="text-sm text-gray-500">★ {listing.rating}</span>
                  )}
                </div>
                <div className="mt-1 flex items-center justify-between text-sm text-gray-500">
                  <span className="capitalize">{listing.listing_type}</span>
                  {listing.price_amount && (
                    <span>
                      {listing.currency} {listing.price_amount}/night
                    </span>
                  )}
                </div>
                <a
                  href={listing.booking_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 inline-block text-sm text-blue-600 hover:underline"
                >
                  View / book &rarr;
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}