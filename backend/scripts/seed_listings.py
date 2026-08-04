"""
Seed script -- populates the listings table with placeholder accommodation
data tied to the 15 destinations from seed_destinations.py.

No external API calls (listings have no embedding column), so this is
free to run and re-run. Safe to re-run: existing listings (matched by
destination + name) are skipped, not duplicated.

Usage:
    python scripts/seed_listings.py

Run from the `backend/` directory so it can import `app.*` and read `.env`.
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.destination import Destination
from app.models.listing import Listing

# ----------------------------------------------------------------------------
# Seed data -- 2 listings per destination, spanning a mix of listing types
# and price points roughly matching each destination's cost_tier.
# Booking URLs are placeholders (real referral/affiliate links per ADR-014
# come later, once actual provider integrations exist).
# ----------------------------------------------------------------------------

LISTINGS_BY_SLUG: dict[str, list[dict]] = {
    "kyoto-japan": [
        {"name": "Kyoto Machiya Inn", "listing_type": "hotel", "price_amount": 180, "currency": "USD", "rating": 4.6},
        {"name": "Gion Guesthouse", "listing_type": "hostel", "price_amount": 45, "currency": "USD", "rating": 4.2},
    ],
    "bali-indonesia": [
        {"name": "Seminyak Beach Villas", "listing_type": "resort", "price_amount": 120, "currency": "USD", "rating": 4.5},
        {"name": "Canggu Surf Hostel", "listing_type": "hostel", "price_amount": 18, "currency": "USD", "rating": 4.3},
    ],
    "reykjavik-iceland": [
        {"name": "Reykjavik Harbor Hotel", "listing_type": "hotel", "price_amount": 260, "currency": "USD", "rating": 4.4},
        {"name": "Northern Lights Apartments", "listing_type": "airbnb", "price_amount": 190, "currency": "USD", "rating": 4.7},
    ],
    "lisbon-portugal": [
        {"name": "Alfama Boutique Hotel", "listing_type": "hotel", "price_amount": 95, "currency": "EUR", "rating": 4.5},
        {"name": "Bairro Alto Loft", "listing_type": "airbnb", "price_amount": 70, "currency": "EUR", "rating": 4.6},
    ],
    "queenstown-new-zealand": [
        {"name": "Lake Wakatipu Lodge", "listing_type": "resort", "price_amount": 240, "currency": "USD", "rating": 4.6},
        {"name": "Queenstown Backpackers", "listing_type": "hostel", "price_amount": 30, "currency": "USD", "rating": 4.1},
    ],
    "mexico-city-mexico": [
        {"name": "Roma Norte Design Hotel", "listing_type": "hotel", "price_amount": 85, "currency": "USD", "rating": 4.5},
        {"name": "Condesa Garden Apartment", "listing_type": "airbnb", "price_amount": 60, "currency": "USD", "rating": 4.7},
    ],
    "santorini-greece": [
        {"name": "Oia Cliffside Suites", "listing_type": "resort", "price_amount": 320, "currency": "EUR", "rating": 4.8},
        {"name": "Fira Budget Rooms", "listing_type": "hotel", "price_amount": 90, "currency": "EUR", "rating": 4.0},
    ],
    "chiang-mai-thailand": [
        {"name": "Old City Boutique Hotel", "listing_type": "hotel", "price_amount": 35, "currency": "USD", "rating": 4.4},
        {"name": "Nimman Digital Nomad Hostel", "listing_type": "hostel", "price_amount": 12, "currency": "USD", "rating": 4.3},
    ],
    "banff-canada": [
        {"name": "Fairmont Banff Springs", "listing_type": "hotel", "price_amount": 450, "currency": "CAD", "rating": 4.7},
        {"name": "Banff Alpine Lodge", "listing_type": "hotel", "price_amount": 210, "currency": "CAD", "rating": 4.3},
    ],
    "marrakech-morocco": [
        {"name": "Medina Riad Retreat", "listing_type": "hotel", "price_amount": 75, "currency": "USD", "rating": 4.6},
        {"name": "Gueliz Budget Stay", "listing_type": "hotel", "price_amount": 30, "currency": "USD", "rating": 3.9},
    ],
    "copenhagen-denmark": [
        {"name": "Nyhavn Design Hotel", "listing_type": "hotel", "price_amount": 240, "currency": "USD", "rating": 4.6},
        {"name": "Norrebro Apartment", "listing_type": "airbnb", "price_amount": 160, "currency": "USD", "rating": 4.5},
    ],
    "cartagena-colombia": [
        {"name": "Walled City Boutique Hotel", "listing_type": "hotel", "price_amount": 110, "currency": "USD", "rating": 4.5},
        {"name": "Getsemani Hostel", "listing_type": "hostel", "price_amount": 20, "currency": "USD", "rating": 4.2},
    ],
    "vienna-austria": [
        {"name": "Ringstrasse Grand Hotel", "listing_type": "hotel", "price_amount": 230, "currency": "EUR", "rating": 4.6},
        {"name": "Neubau Studio Apartment", "listing_type": "airbnb", "price_amount": 95, "currency": "EUR", "rating": 4.5},
    ],
    "ubud-indonesia": [
        {"name": "Ubud Jungle Retreat", "listing_type": "resort", "price_amount": 85, "currency": "USD", "rating": 4.7},
        {"name": "Rice Terrace Guesthouse", "listing_type": "hostel", "price_amount": 15, "currency": "USD", "rating": 4.3},
    ],
    "edinburgh-scotland": [
        {"name": "Royal Mile Historic Hotel", "listing_type": "hotel", "price_amount": 150, "currency": "USD", "rating": 4.5},
        {"name": "New Town Flat", "listing_type": "airbnb", "price_amount": 110, "currency": "USD", "rating": 4.6},
    ],
}


def make_booking_url(slug: str, listing_name: str) -> str:
    """Placeholder booking URL. Real referral/affiliate links (ADR-014) come
    later, once actual booking-provider integrations exist."""
    safe_name = listing_name.lower().replace(" ", "-")
    return f"https://example-booking.com/{slug}/{safe_name}"


async def seed() -> None:
    inserted = 0
    skipped = 0
    missing_destinations = 0

    async with AsyncSessionLocal() as session:
        for slug, listings in LISTINGS_BY_SLUG.items():
            dest_result = await session.execute(select(Destination).where(Destination.slug == slug))
            destination = dest_result.scalar_one_or_none()

            if destination is None:
                print(f"  skip (destination not found): {slug}")
                missing_destinations += 1
                continue

            for listing_data in listings:
                existing = await session.execute(
                    select(Listing).where(
                        Listing.destination_id == destination.id,
                        Listing.name == listing_data["name"],
                    )
                )
                if existing.scalar_one_or_none() is not None:
                    print(f"  skip (already exists): {slug} / {listing_data['name']}")
                    skipped += 1
                    continue

                listing = Listing(
                    destination_id=destination.id,
                    name=listing_data["name"],
                    listing_type=listing_data["listing_type"],
                    price_amount=listing_data["price_amount"],
                    currency=listing_data["currency"],
                    rating=listing_data["rating"],
                    booking_url=make_booking_url(slug, listing_data["name"]),
                    source_name="seed-placeholder",
                    status="published",
                )
                session.add(listing)
                print(f"  inserted: {slug} / {listing_data['name']}")
                inserted += 1

        await session.commit()

    print(
        f"\nDone. Inserted: {inserted}, skipped (already existed): {skipped}, "
        f"missing destinations: {missing_destinations}"
    )


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()