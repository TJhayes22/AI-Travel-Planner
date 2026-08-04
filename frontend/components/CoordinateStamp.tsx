/**
 * The signature design element: real destination coordinates, formatted
 * like a surveyor's stamp. Ties the "field log" concept to real data --
 * every destination in the database has a real latitude/longitude.
 */

function formatCoordinate(lat: number, lng: number): string {
  const latDir = lat >= 0 ? "N" : "S";
  const lngDir = lng >= 0 ? "E" : "W";
  return `${Math.abs(lat).toFixed(3)}°${latDir} ${Math.abs(lng).toFixed(3)}°${lngDir}`;
}

export function CoordinateStamp({
  latitude,
  longitude,
}: {
  latitude: number | null;
  longitude: number | null;
}) {
  if (latitude === null || longitude === null) return null;

  return (
    <span className="inline-flex items-center gap-1 rounded-sm border border-mist/40 px-1.5 py-0.5 font-data text-[11px] tracking-wide text-mist">
      {formatCoordinate(latitude, longitude)}
    </span>
  );
}